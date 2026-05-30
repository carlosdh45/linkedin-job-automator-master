import csv
from datetime import datetime, timezone, timedelta
from pathlib import Path
from src import db


def load_and_filter_jobs(csv_path: str, db_path: str, config_filters: dict) -> list:
    processed_urls = db.get_processed_urls(db_path)

    location_kws = [k.lower() for k in config_filters.get("location_keywords", [])]
    title_kws = [k.lower() for k in config_filters.get("title_keywords", [])]
    blacklist = [c.lower() for c in config_filters.get("blacklisted_companies", [])]
    max_days = config_filters.get("max_days_old")

    jobs = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("Job LinkedIn URL", "").strip()
            if not url:
                continue
            if url in processed_urls:
                continue

            company = row.get("Company Name", "").strip()
            title = row.get("Job Title", "").strip()
            location = row.get("Location", "").strip()
            posted_on = row.get("Posted On", "").strip()

            if not _passes_age_filter(posted_on, max_days):
                continue
            if location_kws and not _passes_location_filter(location, location_kws):
                continue
            if title_kws and not _passes_title_filter(title, title_kws):
                continue
            if blacklist and not _passes_blacklist_filter(company, blacklist):
                continue

            jobs.append(row)

    return jobs


def _passes_location_filter(location: str, keywords: list) -> bool:
    loc_lower = location.lower()
    return any(kw in loc_lower for kw in keywords)


def _passes_title_filter(title: str, keywords: list) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in keywords)


def _passes_blacklist_filter(company: str, blacklist: list) -> bool:
    company_lower = company.lower()
    return not any(b in company_lower for b in blacklist)


def _passes_age_filter(posted_on: str, max_days_old) -> bool:
    if not max_days_old or not posted_on:
        return True
    try:
        dt = datetime.fromisoformat(posted_on.replace("Z", "+00:00"))
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_days_old)
        return dt >= cutoff
    except (ValueError, TypeError):
        return True


def get_unique_domains(csv_path: str, db_path: str) -> list:
    all_domains = set()
    searched = set()

    with db.get_connection(db_path) as conn:
        rows = conn.execute("SELECT domain FROM searched_domains").fetchall()
        searched = {r["domain"] for r in rows}

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            domain = row.get("Company Domain", "").strip()
            if domain and domain not in searched:
                all_domains.add(domain)

    return sorted(all_domains)


def get_external_job_domains(db_path: str) -> list:
    with db.get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT DISTINCT domain FROM applied_jobs WHERE status='external_apply' AND domain != ''"
        ).fetchall()

    with db.get_connection(db_path) as conn:
        searched = {
            r["domain"]
            for r in conn.execute("SELECT domain FROM searched_domains").fetchall()
        }

    return [r["domain"] for r in rows if r["domain"] not in searched]
