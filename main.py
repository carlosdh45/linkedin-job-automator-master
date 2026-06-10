#!/usr/bin/env python3
"""
DobryBot
---------
Human-in-the-loop opportunity and growth assistant for CorosDev.
Finds, scores, and manages job opportunities and client leads.
Generates reviewable drafts. Never sends or applies automatically.

Nothing is sent or applied without explicit manual review and approval.
No automation without a human in the loop.
"""
import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml

from src import db
from src.config_loader import load_config
from src.cv_parser import parse_cv


# ── Logging setup ─────────────────────────────────────────────────────────────

def setup_logging(logs_dir: str) -> logging.Logger:
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = Path(logs_dir) / f"run_{ts}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)


# ── Discovery ─────────────────────────────────────────────────────────────────

def cmd_discover_jobs(config: dict, logger: logging.Logger, dry_run: bool = False) -> None:
    """Load jobs from CSV, apply filters, save as 'discovered'. No applying."""
    from src.job_filter import load_and_filter_jobs

    db_path = config["paths"]["database"]
    db.initialize_database(db_path)

    logger.info("Loading and filtering jobs from CSV...")
    jobs = load_and_filter_jobs(config["paths"]["jobs_csv"], db_path, config["filters"])
    logger.info(f"{len(jobs)} new jobs found after filters")

    if dry_run:
        print(f"\n[dry-run] Would save {len(jobs)} discovered jobs")
        for job in jobs[:10]:
            print(f"  - {job.get('Job Title')} @ {job.get('Company Name')} ({job.get('Location')})")
        if len(jobs) > 10:
            print(f"  ... and {len(jobs) - 10} more")
        return

    saved = 0
    for job in jobs:
        db.save_discovered_job(db_path, job)
        saved += 1

    print(f"\n── Job Discovery Complete ──")
    print(f"  {'discovered':20s}: {saved}")
    print(f"\nNext step: python main.py --score-jobs")


def cmd_discover_leads(config: dict, logger: logging.Logger, dry_run: bool = False) -> None:
    """Find leads via Hunter.io and save as 'discovered'. No outreach sent."""
    from src.email_finder import run_email_finder
    from src.scorer import LeadScorer

    db_path = config["paths"]["database"]
    db.initialize_database(db_path)

    if not config.get("apis", {}).get("hunter_api_key"):
        print("ERROR: hunter_api_key is required for --discover-leads")
        return

    ef_cfg = config.get("email_finder", {})
    logger.info("Discovering leads via Hunter.io...")

    if dry_run:
        print("[dry-run] Would search Hunter.io for contacts, saving as leads")
        return

    stats = run_email_finder(
        csv_path=config["paths"]["jobs_csv"],
        db_path=db_path,
        api_key=config["apis"]["hunter_api_key"],
        rate_limit_seconds=ef_cfg.get("rate_limit_seconds", 1.0),
        max_domains=ef_cfg.get("max_domains_per_run", 25),
        prefer_external=ef_cfg.get("prefer_external_apply_domains", True),
    )

    # Convert found contacts into leads
    scorer = LeadScorer()
    lead_count = 0
    with db.get_connection(db_path) as conn:
        contacts = conn.execute("SELECT * FROM contacts ORDER BY found_at DESC").fetchall()
        for c in contacts:
            domain = c["domain"]
            company = c["company"] or domain
            contact_name = f"{c['first_name'] or ''} {c['last_name'] or ''}".strip()
            lead_id = db.save_lead(
                db_path=db_path,
                domain=domain,
                company=company,
                contact_name=contact_name,
                contact_email=c["email"] or "",
                contact_role=c["role"] or "",
            )
            if lead_id:
                lead_count += 1

    print(f"\n── Lead Discovery Complete ──")
    for k, v in stats.items():
        print(f"  {k:20s}: {v}")
    print(f"  {'leads_saved':20s}: {lead_count}")
    print(f"\nNext step: python main.py --score-leads")


# ── Scoring ───────────────────────────────────────────────────────────────────

def cmd_score_jobs(config: dict, logger: logging.Logger, dry_run: bool = False) -> None:
    from src.scorer import JobScorer

    db_path = config["paths"]["database"]
    db.initialize_database(db_path)

    jobs = db.get_jobs_by_status(db_path, "discovered")
    if not jobs:
        print("No discovered jobs to score. Run --discover-jobs first.")
        return

    scorer = JobScorer()
    results = {"high_priority": 0, "good_fit": 0, "maybe": 0, "low_fit": 0}

    for job in jobs:
        result = scorer.score(job)
        results[result["score_label"]] = results.get(result["score_label"], 0) + 1
        logger.info(
            f"  [{result['score_label']:14s}] {result['job_score']:3d}  "
            f"{job.get('title','')} @ {job.get('company','')}"
        )
        if not dry_run:
            db.update_job_score(
                db_path,
                job["job_url"],
                result["job_score"],
                result["skill_match_score"],
                result["score_label"],
            )

    print(f"\n── Job Scoring Complete ──")
    for label, count in results.items():
        print(f"  {label:20s}: {count}")
    if dry_run:
        print("\n[dry-run] No changes saved.")
    else:
        print(f"\nNext step: python main.py --draft-job-application")


def cmd_score_leads(config: dict, logger: logging.Logger, dry_run: bool = False) -> None:
    from src.scorer import LeadScorer

    db_path = config["paths"]["database"]
    db.initialize_database(db_path)

    leads = db.get_leads_by_status(db_path, "discovered")
    if not leads:
        print("No discovered leads to score. Run --discover-leads first.")
        return

    scorer = LeadScorer()
    results = {"high_priority": 0, "good_fit": 0, "maybe": 0, "low_fit": 0}

    for lead in leads:
        result = scorer.score(lead)
        results[result["score_label"]] = results.get(result["score_label"], 0) + 1
        logger.info(
            f"  [{result['score_label']:14s}] {result['lead_score']:3d}  "
            f"{lead.get('company','')} ({lead.get('contact_role','')})"
        )
        if not dry_run:
            db.update_lead_score(db_path, lead["id"], result["lead_score"], result["score_label"])

    print(f"\n── Lead Scoring Complete ──")
    for label, count in results.items():
        print(f"  {label:20s}: {count}")
    if dry_run:
        print("\n[dry-run] No changes saved.")
    else:
        print(f"\nNext step: python main.py --draft-client-outreach")


# ── Draft generation ──────────────────────────────────────────────────────────

def cmd_draft_job_application(
    config: dict, logger: logging.Logger, dry_run: bool = False, min_score: int = 70
) -> None:
    """Generate cover letter / recruiter message drafts for top-scored jobs."""
    from src.humanizer import has_sufficient_context

    db_path = config["paths"]["database"]
    db.initialize_database(db_path)

    scored_jobs = db.get_jobs_by_status(db_path, "scored")
    eligible = [j for j in scored_jobs if j.get("job_score", 0) >= min_score]

    if not eligible:
        print(f"No scored jobs with score >= {min_score}. Run --score-jobs first.")
        return

    if dry_run:
        print(f"\n[dry-run] Would generate {len(eligible)} job application draft(s):")
        for job in eligible:
            print(f"  - {job.get('title','')} @ {job.get('company','')} "
                  f"(score: {job.get('job_score',0)}, {job.get('score_label','')})")
        print("\n  No CV parsed. No Claude calls. No DB writes.")
        return

    from src.answer_generator import AnswerGenerator
    from src.quality_guard import QualityGuard

    cv_profile = parse_cv(config["paths"]["cv_pdf"])

    logger.info(f"Generating drafts for {len(eligible)} jobs (score >= {min_score})...")

    answer_gen = AnswerGenerator(
        api_key=config["apis"]["anthropic_api_key"],
        model=config["answer_generator"]["model"],
        cv_profile=cv_profile,
        positioning=config["answer_generator"]["positioning"],
    )
    guard = QualityGuard(api_key=config["apis"]["anthropic_api_key"])
    daily_limit = config.get("limits", {}).get("max_drafts_per_day", 10)
    generated = 0

    for job in eligible:
        if generated >= daily_limit:
            logger.info(f"Daily draft limit ({daily_limit}) reached.")
            break

        style = "recruiter_friendly"
        context = {
            "company": job.get("company", ""),
            "job_title": job.get("title", ""),
            "contact_name": "",
            "specific_signal": job.get("score_label", ""),
            "outreach_type": "job",
        }

        ok, missing = has_sufficient_context(context, "job")
        if not ok:
            db.record_job(db_path, job["job_url"], job["company"], job["title"],
                          job.get("location", ""), status="skipped",
                          notes=f"insufficient_context: missing {missing}")
            continue

        try:
            subject, body = answer_gen.generate_outreach_email(
                company=job["company"],
                job_title=job["title"],
                positioning=config["answer_generator"]["positioning"],
                style=style,
            )
        except Exception as e:
            logger.warning(f"Draft generation failed for {job['company']}: {e}")
            continue

        scores = guard.score_message(body, context)

        if not dry_run:
            db.record_outreach(
                db_path=db_path,
                job_url=job["job_url"],
                company=job["company"],
                job_title=job["title"],
                subject=subject,
                body=body,
                outreach_type="job",
                style=style,
                status="needs_review",
                personalization_score=scores.get("personalization_score", 0),
                spam_risk_score=scores.get("spam_risk_score", 100),
                ai_sounding_score=scores.get("ai_sounding_score", 100),
                quality_status="passed" if scores.get("passes") else "failed",
                quality_reasons=scores.get("quality_reasons", []),
                send_recommendation=scores.get("send_recommendation", "revise"),
                context_used=context,
            )
        generated += 1
        logger.info(
            f"  Draft generated: {job['title']} @ {job['company']} "
            f"[{scores.get('send_recommendation','?')}]"
        )

    print(f"\n── Job Application Drafts Complete ──")
    print(f"  {'drafts_generated':20s}: {generated}")
    print(f"\nNext step: python main.py --review-queue")


def cmd_draft_client_outreach(
    config: dict, logger: logging.Logger, dry_run: bool = False, min_score: int = 60
) -> None:
    """Generate personalized outreach drafts for top-scored leads."""
    from src.humanizer import has_sufficient_context

    db_path = config["paths"]["database"]
    db.initialize_database(db_path)

    scored_leads = db.get_leads_by_status(db_path, "scored")
    eligible = [l for l in scored_leads if l.get("lead_score", 0) >= min_score]

    if not eligible:
        print(f"No scored leads with score >= {min_score}. Run --score-leads first.")
        return

    if dry_run:
        print(f"\n[dry-run] Would generate {len(eligible)} client outreach draft(s):")
        for lead in eligible:
            print(f"  - {lead.get('company','')} → {lead.get('contact_name','')} "
                  f"(score: {lead.get('lead_score',0)}, {lead.get('score_label','')})")
        print("\n  No CV parsed. No Claude calls. No DB writes.")
        return

    from src.answer_generator import AnswerGenerator
    from src.quality_guard import QualityGuard

    cv_profile = parse_cv(config["paths"]["cv_pdf"])
    answer_gen = AnswerGenerator(
        api_key=config["apis"]["anthropic_api_key"],
        model=config["answer_generator"]["model"],
        cv_profile=cv_profile,
        positioning=config["answer_generator"]["positioning"],
    )
    guard = QualityGuard(api_key=config["apis"]["anthropic_api_key"])
    daily_limit = config.get("limits", {}).get("max_drafts_per_day", 10)
    generated = skipped = 0

    for lead in eligible:
        if generated >= daily_limit:
            logger.info(f"Daily draft limit ({daily_limit}) reached.")
            break

        style = "client_value_first"
        pain_points = lead.get("pain_points") or []
        context = {
            "company": lead.get("company", ""),
            "role": lead.get("contact_role", ""),
            "contact_name": lead.get("contact_name", ""),
            "contact_role": lead.get("contact_role", ""),
            "industry": lead.get("industry", ""),
            "pain_point": pain_points[0] if pain_points else "",
            "specific_signal": lead.get("score_label", ""),
            "outreach_type": "client",
        }

        ok, missing = has_sufficient_context(context, "client")
        if not ok:
            db.update_lead_status(
                db_path, lead["id"], "not_fit",
                f"insufficient_context_for_personalization: {missing}"
            )
            skipped += 1
            logger.info(f"  Skipped {lead['company']} — insufficient context")
            continue

        try:
            subject, body = answer_gen.generate_outreach_email(
                company=lead["company"],
                job_title=lead.get("contact_role", ""),
                contact_name=lead.get("contact_name", ""),
                contact_role=lead.get("contact_role", ""),
                positioning=config["answer_generator"]["positioning"],
                style=style,
            )
        except Exception as e:
            logger.warning(f"Draft generation failed for {lead['company']}: {e}")
            continue

        scores = guard.score_message(body, context)

        if not dry_run:
            db.record_outreach(
                db_path=db_path,
                job_url=f"lead:{lead['id']}",
                company=lead["company"],
                job_title=lead.get("contact_role", ""),
                subject=subject,
                body=body,
                to_email=lead.get("contact_email", ""),
                to_name=lead.get("contact_name", ""),
                to_role=lead.get("contact_role", ""),
                outreach_type="client",
                style=style,
                status="needs_review",
                personalization_score=scores.get("personalization_score", 0),
                spam_risk_score=scores.get("spam_risk_score", 100),
                ai_sounding_score=scores.get("ai_sounding_score", 100),
                quality_status="passed" if scores.get("passes") else "failed",
                quality_reasons=scores.get("quality_reasons", []),
                send_recommendation=scores.get("send_recommendation", "revise"),
                context_used=context,
            )
            db.update_lead_status(db_path, lead["id"], "draft_ready")
        generated += 1
        logger.info(
            f"  Draft: {lead['company']} → {lead.get('contact_name','')} "
            f"[{scores.get('send_recommendation','?')}]"
        )

    print(f"\n── Client Outreach Drafts Complete ──")
    print(f"  {'drafts_generated':20s}: {generated}")
    print(f"  {'skipped_no_context':20s}: {skipped}")
    print(f"\nNext step: python main.py --review-queue")


# ── Review & approval ─────────────────────────────────────────────────────────

def cmd_review_queue(config: dict, logger: logging.Logger, filter_type: str = None) -> None:
    """Interactive review queue for all pending drafts."""
    from src.review_queue import show_review_queue
    db_path = config["paths"]["database"]
    db.initialize_database(db_path)
    show_review_queue(db_path, outreach_type=filter_type)


def cmd_approve(config: dict, logger: logging.Logger, draft_id: int, force: bool = False) -> None:
    """Approve a specific draft by ID. Quality gate is always enforced."""
    if force:
        print(
            "NOTE: --approve-force has been removed. The quality gate is always enforced.\n"
            "      Fix the draft quality and use --approve instead."
        )
        return
    from src.review_queue import approve_single
    db_path = config["paths"]["database"]
    db.initialize_database(db_path)
    approve_single(db_path, draft_id)


def cmd_send_approved(config: dict, logger: logging.Logger, dry_run: bool = False) -> None:
    """Send all approved outreach emails. ONLY runs with prior human approval."""
    from src.outreach_generator import OutreachGenerator

    db_path = config["paths"]["database"]
    db.initialize_database(db_path)

    approved = db.get_approved_outreach(db_path)
    client_items = [a for a in approved if a.get("outreach_type") == "client" and a.get("to_email")]

    if not client_items:
        print("No approved client outreach emails to send.")
        return

    daily_limit = config.get("limits", {}).get("max_emails_per_day", 5)
    to_send = client_items[:daily_limit]

    print(f"\nAbout to send {len(to_send)} approved email(s) (daily limit: {daily_limit}):")
    for item in to_send:
        print(f"  → {item['company']}  {item.get('to_email','')}")

    if dry_run:
        print("\n[dry-run] No emails sent.")
        return

    confirm = input(f"\nConfirm send {len(to_send)} email(s)? [yes/N]: ").strip().lower()
    if confirm != "yes":
        print("Cancelled.")
        return

    cv_profile = parse_cv(config["paths"]["cv_pdf"])
    generator = OutreachGenerator(config, cv_profile, db_path)
    sent = errors = 0

    for item in to_send:
        success, error_msg = generator._send_email(
            to_email=item["to_email"],
            to_name=item.get("to_name", ""),
            subject=item["subject"],
            body=item["body"],
        )
        if success:
            db.mark_outreach_sent(db_path, item["id"])
            sent += 1
            logger.info(f"  Sent    → {item['company']} <{item['to_email']}>")
        else:
            db.mark_outreach_failed(db_path, item["id"], error_msg)
            errors += 1
            logger.error(f"  FAILED  → {item['company']} <{item['to_email']}> — {error_msg}")
            print(f"\n  ✗ SEND FAILED: {item['company']} <{item['to_email']}>")
            print(f"    Reason : {error_msg}")
            print(f"    Status : marked as 'failed' in database (not marked as sent)")

    print(f"\n── Send Complete ──")
    print(f"  {'sent':20s}: {sent}")
    print(f"  {'failed':20s}: {errors}")
    if errors:
        print(f"\n  {errors} email(s) failed. Run --stats to see failed outreach.")


# ── Demo data seeder ──────────────────────────────────────────────────────────

def _get_db_for_demo(config_path: str) -> str:
    """Return db path from config file (raw parse, no validation) or a safe default."""
    try:
        with open(config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        path = cfg.get("paths", {}).get("database")
        if path:
            return path
    except Exception:
        pass
    return "data/copilot.db"


def cmd_seed_demo_data(db_path: str) -> None:
    """Populate the local DB with demo jobs, leads, and drafts. No external calls."""
    from src.seed_data import seed_demo_data
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    db.initialize_database(db_path)
    stats = seed_demo_data(db_path)
    print("\n-- Demo Data Seeded --")
    for k, v in stats.items():
        print(f"  {k:20s}: {v}")
    print("\nNext steps:")
    print("  python main.py --stats")
    print("  python main.py --daily-brief")
    print("  python main.py --review-queue")


# ── Legacy commands (kept for backward compatibility) ─────────────────────────

def cmd_apply(config: dict, logger: logging.Logger) -> None:
    """
    DEPRECATED — prints a redirect message and exits. Never submits applications.
    """
    print(
        "\n╔══════════════════════════════════════════════════════════════════╗\n"
        "║  --apply is REMOVED                                              ║\n"
        "║                                                                  ║\n"
        "║  Automatic LinkedIn application submission has been removed.     ║\n"
        "║  Use the DobryBot human-in-the-loop workflow instead:           ║\n"
        "║                                                                  ║\n"
        "║    bash run.sh --discover-jobs                                   ║\n"
        "║    bash run.sh --score-jobs                                      ║\n"
        "║    bash run.sh --draft-job-application                           ║\n"
        "║    bash run.sh --review-queue                                    ║\n"
        "║                                                                  ║\n"
        "║  Nothing was submitted. No LinkedIn session was opened.          ║\n"
        "╚══════════════════════════════════════════════════════════════════╝\n"
    )


def cmd_find_emails(config: dict, logger: logging.Logger) -> None:
    from src.email_finder import run_email_finder

    db_path = config["paths"]["database"]
    db.initialize_database(db_path)

    ef_cfg = config.get("email_finder", {})
    stats = run_email_finder(
        csv_path=config["paths"]["jobs_csv"],
        db_path=db_path,
        api_key=config["apis"]["hunter_api_key"],
        rate_limit_seconds=ef_cfg.get("rate_limit_seconds", 1.0),
        max_domains=ef_cfg.get("max_domains_per_run", 25),
        prefer_external=ef_cfg.get("prefer_external_apply_domains", True),
    )
    print("\n── Email Finder Complete ──")
    for k, v in stats.items():
        print(f"  {k:20s}: {v}")


def cmd_generate_outreach(config: dict, logger: logging.Logger) -> None:
    from src.outreach_generator import OutreachGenerator

    db_path = config["paths"]["database"]
    db.initialize_database(db_path)

    cv_profile = parse_cv(config["paths"]["cv_pdf"])
    generator = OutreachGenerator(config, cv_profile, db_path)
    stats = generator.run()

    print("\n── Outreach Generation Complete ──")
    for k, v in stats.items():
        print(f"  {k:20s}: {v}")


def cmd_send_outreach(config: dict, logger: logging.Logger) -> None:
    """
    DEPRECATED — does not send anything.
    Redirects users to the safe review → approve → send workflow.
    """
    print(
        "\n╔══════════════════════════════════════════════════════════════════╗\n"
        "║  --send-outreach is DEPRECATED and will not send anything        ║\n"
        "║                                                                  ║\n"
        "║  Use the approved workflow instead:                              ║\n"
        "║    1. bash run.sh --review-queue        (review each draft)      ║\n"
        "║    2. bash run.sh --approve <ID>        (approve one draft)      ║\n"
        "║    3. bash run.sh --send-approved       (send approved items)    ║\n"
        "║                                                                  ║\n"
        "║  Nothing was sent. No changes were made.                         ║\n"
        "╚══════════════════════════════════════════════════════════════════╝\n"
    )
    db_path = config.get("paths", {}).get("database")
    if db_path:
        db.initialize_database(db_path)
        pending = db.get_needs_review(db_path)
        if pending:
            print(f"  You have {len(pending)} draft(s) pending review.")
            print("  Run: bash run.sh --review-queue")


def cmd_export_contacts(config: dict, logger: logging.Logger) -> None:
    db_path = config["paths"]["database"]
    db.initialize_database(db_path)
    from pathlib import Path
    from datetime import datetime
    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = str(exports_dir / f"contacts_{ts}.csv")
    count = db.export_contacts_to_csv(db_path, output)
    print(f"Exported {count} contacts → {output}")


def cmd_export_outreach(config: dict, logger: logging.Logger) -> None:
    db_path = config["paths"]["database"]
    db.initialize_database(db_path)
    from pathlib import Path
    from datetime import datetime
    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = str(exports_dir / f"outreach_{ts}.csv")
    count = db.export_outreach_to_csv(db_path, output)
    print(f"Exported {count} outreach drafts → {output}")


def cmd_stats(config: dict, logger: logging.Logger) -> None:
    db_path = config["paths"]["database"]
    db.initialize_database(db_path)
    stats = db.get_stats(db_path)

    print("\n── DobryBot — Stats ──")
    for key, val in sorted(stats.items()):
        print(f"  {key:35s}: {val}")


# ── Daily brief ───────────────────────────────────────────────────────────────

def cmd_daily_brief(config: dict, logger: logging.Logger) -> None:
    from src.daily_brief import generate_brief
    db_path = config["paths"]["database"]
    db.initialize_database(db_path)
    generate_brief(db_path)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    # Ensure UTF-8 output on Windows so box-drawing chars render correctly
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    parser = argparse.ArgumentParser(
        description="DobryBot — human-in-the-loop opportunity and growth assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
━━ DOBRYBOT WORKFLOW (recommended) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Jobs:
    --discover-jobs           Load jobs from CSV, save as discovered
    --score-jobs              Score discovered jobs (0-100)
    --draft-job-application   Generate recruiter messages (drafts only)
    --review-queue            Review, approve or skip drafts

  Clients / Leads:
    --discover-leads          Find leads via Hunter.io
    --score-leads             Score leads by ICP fit
    --draft-client-outreach   Generate personalized outreach (drafts only)
    --review-queue            Review, approve or skip drafts

  Sending (only after manual approval):
    --approve ID              Approve a specific draft by ID
    --send-approved           Send all approved outreach emails

  Reports:
    --daily-brief             Summary: top jobs, top leads, pending drafts
    --stats                   Database statistics

  Utilities:
    --export-contacts         Export contacts to CSV
    --export-outreach         Export outreach drafts to CSV
    --seed-demo-data          Seed DB with safe fake data for local testing

━━ LEGACY (disabled or redirected by default) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    --apply                   Disabled. Requires enable_legacy_apply: true in config.
    --find-emails             Hunter.io domain search (still active)
    --generate-outreach       Generates drafts as needs_review (no sending)
    --send-outreach           DEPRECATED — redirects to --send-approved workflow

━━ FLAGS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    --dry-run                 Preview what would happen without saving
    --config PATH             Path to config.yaml (default: config.yaml)
        """,
    )

    # Copilot workflow
    parser.add_argument("--discover-jobs",          action="store_true")
    parser.add_argument("--score-jobs",             action="store_true")
    parser.add_argument("--draft-job-application",  action="store_true")
    parser.add_argument("--discover-leads",         action="store_true")
    parser.add_argument("--score-leads",            action="store_true")
    parser.add_argument("--draft-client-outreach",  action="store_true")
    parser.add_argument("--review-queue",           action="store_true")
    parser.add_argument("--approve",                type=int, metavar="ID")
    parser.add_argument("--approve-force",          type=int, metavar="ID",
                        help=argparse.SUPPRESS)  # hidden — dev/test use only
    parser.add_argument("--send-approved",          action="store_true")
    parser.add_argument("--daily-brief",            action="store_true")

    # Legacy
    parser.add_argument("--apply",                  action="store_true")
    parser.add_argument("--find-emails",            action="store_true")
    parser.add_argument("--generate-outreach",      action="store_true")
    parser.add_argument("--send-outreach",          action="store_true")
    parser.add_argument("--export-contacts",        action="store_true")
    parser.add_argument("--export-outreach",        action="store_true")
    parser.add_argument("--stats",                  action="store_true")
    parser.add_argument("--seed-demo-data",         action="store_true",
                        help="Seed the local DB with safe demo data for testing")

    # Global flags
    parser.add_argument("--dry-run",   action="store_true", help="Preview without saving")
    parser.add_argument("--config",    default="config.yaml")
    parser.add_argument("--min-score", type=int, default=70,
                        help="Minimum score for draft generation (default: 70)")
    parser.add_argument("--type",      choices=["job", "client"],
                        help="Filter review queue by type")

    args = parser.parse_args()

    # Show help if no command flag is given (exclude --config, --dry-run, --min-score, --type)
    _non_command = {"config", "dry_run", "min_score", "type"}
    command_flags = {k: v for k, v in vars(args).items() if k not in _non_command}
    if not any(v for v in command_flags.values() if v):
        parser.print_help()
        return

    # Early exits — these commands work without a full validated config
    if args.apply:
        cmd_apply({}, logging.getLogger(__name__))
        return
    if args.send_outreach:
        cmd_send_outreach({}, logging.getLogger(__name__))
        return
    if args.seed_demo_data:
        cmd_seed_demo_data(_get_db_for_demo(args.config))
        return
    if args.stats or args.daily_brief or args.review_queue:
        _db = _get_db_for_demo(args.config)
        _log = logging.getLogger(__name__)
        _cfg = {"paths": {"database": _db}}
        if args.stats:
            cmd_stats(_cfg, _log)
        if args.daily_brief:
            cmd_daily_brief(_cfg, _log)
        if args.review_queue:
            cmd_review_queue(_cfg, _log, filter_type=args.type)
        return

    config = load_config(args.config)
    logger = setup_logging(config["paths"].get("logs_dir", "logs"))

    dry = args.dry_run

    if args.discover_jobs:
        cmd_discover_jobs(config, logger, dry_run=dry)
    if args.score_jobs:
        cmd_score_jobs(config, logger, dry_run=dry)
    if args.draft_job_application:
        cmd_draft_job_application(config, logger, dry_run=dry, min_score=args.min_score)
    if args.discover_leads:
        cmd_discover_leads(config, logger, dry_run=dry)
    if args.score_leads:
        cmd_score_leads(config, logger, dry_run=dry)
    if args.draft_client_outreach:
        cmd_draft_client_outreach(config, logger, dry_run=dry, min_score=args.min_score)
    if args.approve:
        cmd_approve(config, logger, args.approve)
    if args.approve_force:
        cmd_approve(config, logger, args.approve_force, force=True)
    if args.send_approved:
        cmd_send_approved(config, logger, dry_run=dry)

    # Legacy
    if args.find_emails:
        cmd_find_emails(config, logger)
    if args.generate_outreach:
        cmd_generate_outreach(config, logger)
    if args.export_contacts:
        cmd_export_contacts(config, logger)
    if args.export_outreach:
        cmd_export_outreach(config, logger)


if __name__ == "__main__":
    main()
