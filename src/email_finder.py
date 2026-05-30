import time
import requests
from src import db


CONTACT_PRIORITY = [
    "cto", "chief technology", "vp engineering", "vp of engineering",
    "head of engineering", "tech lead", "engineering manager",
    "director of engineering", "recruiter", "hr", "talent",
]


class HunterAPIError(Exception):
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


def run_email_finder(
    csv_path: str,
    db_path: str,
    api_key: str,
    rate_limit_seconds: float = 1.0,
    max_domains: int = 25,
    prefer_external: bool = True,
) -> dict:
    from src.job_filter import get_external_job_domains, get_unique_domains

    if prefer_external:
        domains = get_external_job_domains(db_path)
        if not domains:
            domains = get_unique_domains(csv_path, db_path)
    else:
        domains = get_unique_domains(csv_path, db_path)

    domains = domains[:max_domains]

    stats = {"searched": 0, "found": 0, "skipped": 0, "errors": 0}

    for domain in domains:
        if db.is_domain_searched(db_path, domain):
            stats["skipped"] += 1
            continue

        try:
            emails, company_name = search_domain(domain, api_key)
            for contact in emails:
                db.record_contact(db_path, domain, company_name, contact)
            db.mark_domain_searched(db_path, domain)
            stats["searched"] += 1
            stats["found"] += len(emails)
        except HunterAPIError as e:
            if e.status_code == 429:
                print(f"  Rate limited by Hunter.io. Waiting 10s...")
                time.sleep(10)
                stats["errors"] += 1
            else:
                print(f"  Hunter.io error for {domain}: {e}")
                stats["errors"] += 1
            db.mark_domain_searched(db_path, domain)
        except Exception as e:
            print(f"  Unexpected error for {domain}: {e}")
            stats["errors"] += 1
            db.mark_domain_searched(db_path, domain)

        time.sleep(rate_limit_seconds)

    return stats


def search_domain(domain: str, api_key: str) -> tuple:
    """Returns (emails, company_name) from a single Hunter.io request."""
    url = "https://api.hunter.io/v2/domain-search"
    params = {"domain": domain, "api_key": api_key, "limit": 10}
    resp = requests.get(url, params=params, timeout=15)

    if resp.status_code == 429:
        raise HunterAPIError("Rate limited", status_code=429)
    if resp.status_code != 200:
        raise HunterAPIError(f"HTTP {resp.status_code}: {resp.text[:200]}", status_code=resp.status_code)

    data = resp.json().get("data", {})
    emails = data.get("emails", [])
    company_name = data.get("organization", domain)
    return emails, company_name


def pick_best_contact(contacts: list) -> dict:
    if not contacts:
        return {}

    for priority_kw in CONTACT_PRIORITY:
        for contact in contacts:
            role = (contact.get("role") or contact.get("position") or "").lower()
            if priority_kw in role:
                return contact

    return sorted(contacts, key=lambda c: c.get("confidence", 0), reverse=True)[0]
