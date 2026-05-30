import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src import db
from src.cv_parser import CVProfile
from src.answer_generator import AnswerGenerator
from src.email_finder import pick_best_contact


class OutreachGenerator:
    def __init__(self, config: dict, cv_profile: CVProfile, db_path: str):
        self.config = config
        self.cv_profile = cv_profile
        self.db_path = db_path
        self.positioning = config["answer_generator"]["positioning"]
        self.answer_gen = AnswerGenerator(
            api_key=config["apis"]["anthropic_api_key"],
            model=config["answer_generator"]["model"],
            cv_profile=cv_profile,
            positioning=self.positioning,
        )

    def run(self) -> dict:
        """
        Legacy outreach generation. Generates drafts with status='needs_review'.
        Nothing is sent automatically — use --send-approved after --review-queue.
        """
        external_jobs = db.get_external_jobs(self.db_path)
        stats = {"generated": 0, "sent": 0, "skipped_no_contact": 0, "errors": 0}

        for job in external_jobs:
            domain = job.get("domain", "")
            company = job.get("company", "")
            job_title = job.get("title", "")
            job_url = job.get("job_url", "")

            contacts = db.get_contacts_for_domain(self.db_path, domain)
            contact = pick_best_contact(contacts)

            if not contact or not contact.get("email", "").strip():
                stats["skipped_no_contact"] += 1
                continue

            try:
                subject, body = self.answer_gen.generate_outreach_email(
                    company=company,
                    job_title=job_title,
                    contact_name=contact.get("first_name", "") + " " + contact.get("last_name", ""),
                    contact_role=contact.get("role", ""),
                    positioning=self.positioning,
                )

                outreach_id = db.record_outreach(
                    db_path=self.db_path,
                    job_url=job_url,
                    company=company,
                    job_title=job_title,
                    subject=subject,
                    body=body,
                    to_email=contact.get("email", ""),
                    to_name=(contact.get("first_name", "") + " " + contact.get("last_name", "")).strip(),
                    to_role=contact.get("role", ""),
                    outreach_type="client",
                    status="needs_review",
                )
                stats["generated"] += 1

                # auto_send is disabled by default and should stay that way.
                # Use --review-queue → --approve ID → --send-approved.
                if self.config["outreach"].get("auto_send") and contact.get("email"):
                    print(
                        "WARNING: auto_send is enabled. This bypasses review. "
                        "Draft saved as needs_review; use --send-approved to send after review."
                    )

            except Exception as e:
                print(f"  Error generating outreach for {company}: {e}")
                stats["errors"] += 1

        return stats

    def _send_email(self, to_email: str, to_name: str, subject: str, body: str) -> tuple:
        """
        Returns (success: bool, error_msg: str).
        Only returns (True, "") when the SMTP server confirms delivery.
        Never marks as sent on any exception.
        """
        cfg = self.config["outreach"]
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{cfg['from_name']} <{cfg['smtp_user']}>"
            msg["To"] = f"{to_name} <{to_email}>" if to_name else to_email
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(cfg["smtp_host"], int(cfg["smtp_port"])) as server:
                server.ehlo()
                server.starttls()
                server.login(cfg["smtp_user"], cfg["smtp_password"])
                refused = server.sendmail(cfg["smtp_user"], [to_email], msg.as_string())
                # sendmail returns a dict of refused recipients; empty means full success
                if refused:
                    return False, f"Recipient refused by server: {refused}"
            return True, ""
        except smtplib.SMTPAuthenticationError as e:
            return False, f"SMTP authentication failed: {e}"
        except smtplib.SMTPRecipientsRefused as e:
            return False, f"Recipient refused: {e}"
        except smtplib.SMTPException as e:
            return False, f"SMTP error: {e}"
        except Exception as e:
            return False, f"Unexpected send error: {e}"
