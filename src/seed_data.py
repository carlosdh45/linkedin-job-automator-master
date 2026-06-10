"""
Demo data seeder for safe local testing.

Creates realistic-looking but completely fake jobs, leads, and drafts.
No real emails. No real companies. No external calls.
Uses .test / .example domains so nothing can accidentally reach a real person.
"""

import json
from datetime import datetime, timezone, timedelta
from src import db

_NOW = datetime.now(timezone.utc)
_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _days_ago(n: int) -> str:
    return (_NOW - timedelta(days=n)).strftime(_FMT)


# ── Demo jobs (varied quality levels) ─────────────────────────────────────────

DEMO_JOBS = [
    {
        "job_url": "https://demo.linkedin.com/jobs/view/D001",
        "company": "Apex Digital Solutions",
        "title": "Senior IT Project Manager",
        "location": "Remote - United States",
        "domain": "apex-demo.test",
        "status": "scored",
        "job_score": 88,
        "score_label": "high_priority",
        "notes": "Strong PM role, remote, US company",
    },
    {
        "job_url": "https://demo.linkedin.com/jobs/view/D002",
        "company": "Bridgewater Tech Corp",
        "title": "Delivery Lead – Agile Teams",
        "location": "Remote / LATAM Friendly",
        "domain": "bridgewater-demo.test",
        "status": "scored",
        "job_score": 82,
        "score_label": "good_fit",
        "notes": "Delivery lead, LATAM friendly",
    },
    {
        "job_url": "https://demo.linkedin.com/jobs/view/D003",
        "company": "CloudStream Inc",
        "title": "Technical Project Manager – AEM",
        "location": "Remote",
        "domain": "cloudstream-demo.test",
        "status": "scored",
        "job_score": 79,
        "score_label": "good_fit",
        "notes": "AEM experience is a strong match",
    },
    {
        "job_url": "https://demo.linkedin.com/jobs/view/D004",
        "company": "GrowthStack Platform",
        "title": "Product Manager – AI Features",
        "location": "Hybrid - New York",
        "domain": "growthstack-demo.test",
        "status": "scored",
        "job_score": 64,
        "score_label": "maybe",
        "notes": "Hybrid may be a concern, but AI PM is on-brand",
    },
    {
        "job_url": "https://demo.linkedin.com/jobs/view/D005",
        "company": "OldCo Manufacturing",
        "title": "Junior Project Coordinator",
        "location": "On-site - Chicago",
        "domain": "oldco-demo.test",
        "status": "scored",
        "job_score": 28,
        "score_label": "low_fit",
        "notes": "On-site, junior level, non-tech industry",
    },
    {
        "job_url": "https://demo.linkedin.com/jobs/view/D006",
        "company": "FutureSoft Labs",
        "title": "Solution Architect – Cloud & AI",
        "location": "Remote - Worldwide",
        "domain": "futuresoft-demo.test",
        "status": "discovered",
        "job_score": 0,
        "score_label": "",
        "notes": "Not yet scored",
    },
]


# ── Demo leads (varied quality levels) ────────────────────────────────────────

DEMO_LEADS = [
    {
        "domain": "palmsunrealty-demo.test",
        "company": "Palm Sun Realty Group",
        "contact_name": "Alex Martinez",
        "contact_email": "alex@palmsunrealty-demo.test",
        "contact_role": "Managing Director",
        "industry": "real estate",
        "pain_points": ["manual CRM spreadsheets", "no lead automation"],
        "context_data": {
            "company_size": "15 agents",
            "signal": "Hiring for 'operations coordinator' — likely growing pains",
            "website_age": "outdated website, no chatbot",
        },
        "lead_score": 87,
        "score_label": "high_priority",
        "status": "scored",
    },
    {
        "domain": "precisionlaw-demo.test",
        "company": "Precision Law Group",
        "contact_name": "Jordan Lee",
        "contact_email": "jordan@precisionlaw-demo.test",
        "contact_role": "Operations Manager",
        "industry": "legal / professional services",
        "pain_points": ["document workflow is manual", "no client portal"],
        "context_data": {
            "company_size": "12 attorneys",
            "signal": "Expanded to 2nd office — needs better ops tooling",
        },
        "lead_score": 74,
        "score_label": "good_fit",
        "status": "scored",
    },
    {
        "domain": "breezeburger-demo.test",
        "company": "Breeze Burger Co.",
        "contact_name": "Sam Torres",
        "contact_email": "sam@breezeburger-demo.test",
        "contact_role": "Owner",
        "industry": "restaurant / hospitality",
        "pain_points": ["no online ordering", "manual inventory"],
        "context_data": {
            "company_size": "3 locations",
            "signal": "Recent Google review mentions 'wait times' — ops issue",
        },
        "lead_score": 68,
        "score_label": "maybe",
        "status": "scored",
    },
    {
        "domain": "techlaunchpad-demo.test",
        "company": "TechLaunchpad Startup",
        "contact_name": "",
        "contact_email": "",
        "contact_role": "CEO",
        "industry": "SaaS / startup",
        "pain_points": [],
        "context_data": {},
        "lead_score": 0,
        "score_label": "",
        "status": "discovered",
    },
]


# ── Demo outreach drafts (varied quality/status levels) ────────────────────────

DEMO_DRAFTS = [
    {
        "job_url": "https://demo.linkedin.com/jobs/view/D001",
        "company": "Apex Digital Solutions",
        "job_title": "Senior IT Project Manager",
        "to_email": "recruiter@apex-demo.test",
        "to_name": "Taylor Reyes",
        "to_role": "Recruiter",
        "subject": "IT Project Manager role — strong PM background, open to remote",
        "body": (
            "Hi Taylor,\n\n"
            "I saw the Senior IT Project Manager role at Apex Digital and it aligns "
            "closely with my background — I've been managing software delivery, "
            "cross-functional teams, and stakeholder communication for the past 7 years.\n\n"
            "I'm based in LATAM and work fully remote across US time zones. Happy to share "
            "more context if the team is open to international candidates.\n\n"
            "Would a 15-minute call make sense?"
        ),
        "outreach_type": "job",
        "style": "recruiter_friendly",
        "status": "needs_review",
        "personalization_score": 80,
        "spam_risk_score": 18,
        "ai_sounding_score": 22,
        "quality_status": "passed",
        "quality_reasons": [],
        "send_recommendation": "send",
        "context_used": {
            "company": "Apex Digital Solutions",
            "job_title": "Senior IT Project Manager",
            "contact_name": "Taylor Reyes",
        },
    },
    {
        "job_url": "https://demo.linkedin.com/jobs/view/D002",
        "company": "Bridgewater Tech Corp",
        "job_title": "Delivery Lead – Agile Teams",
        "to_email": "hiring@bridgewater-demo.test",
        "to_name": "",
        "to_role": "",
        "subject": "Delivery Lead application — Agile delivery across distributed teams",
        "body": (
            "Hi,\n\n"
            "I came across your profile and I was impressed by your company. "
            "I hope this message finds you well. I am reaching out to explore synergies "
            "with Bridgewater Tech Corp and leverage my expertise to provide innovative "
            "solutions that can transform your business in today's fast-paced digital world."
        ),
        "outreach_type": "job",
        "style": "recruiter_friendly",
        "status": "needs_review",
        "personalization_score": 22,
        "spam_risk_score": 78,
        "ai_sounding_score": 91,
        "quality_status": "failed",
        "quality_reasons": [
            "Forbidden phrases: 'I came across your profile', 'I hope this message finds you well'",
            "Extremely generic — could be sent to anyone",
            "No specific role or company context",
        ],
        "send_recommendation": "skip",
        "context_used": {
            "company": "Bridgewater Tech Corp",
            "job_title": "Delivery Lead – Agile Teams",
        },
    },
    {
        "job_url": "lead:palmsunrealty-demo.test",
        "company": "Palm Sun Realty Group",
        "job_title": "Managing Director",
        "to_email": "alex@palmsunrealty-demo.test",
        "to_name": "Alex Martinez",
        "to_role": "Managing Director",
        "subject": "Automating lead follow-up at Palm Sun Realty",
        "body": (
            "Hi Alex,\n\n"
            "I noticed Palm Sun Realty is growing — 15 agents and expanding. "
            "I work with a small nearshore team helping real estate companies "
            "clean up their CRM workflows and automate lead follow-up.\n\n"
            "Not sure if the timing is right, but if you're managing lead tracking "
            "manually or in spreadsheets, I'd be happy to share a few ideas.\n\n"
            "Happy to do a 15-minute call if it's relevant.\n\n"
            "If this isn't relevant right now, just reply and I won't follow up."
        ),
        "outreach_type": "client",
        "style": "client_value_first",
        "status": "needs_review",
        "personalization_score": 84,
        "spam_risk_score": 14,
        "ai_sounding_score": 19,
        "quality_status": "passed",
        "quality_reasons": [],
        "send_recommendation": "send",
        "context_used": {
            "company": "Palm Sun Realty Group",
            "industry": "real estate",
            "pain_point": "manual CRM spreadsheets",
            "contact_name": "Alex Martinez",
            "signal": "Growing team, hiring for operations coordinator",
        },
    },
    {
        "job_url": "https://demo.linkedin.com/jobs/view/D003",
        "company": "CloudStream Inc",
        "job_title": "Technical Project Manager – AEM",
        "to_email": "",
        "to_name": "",
        "to_role": "",
        "subject": "TPM – AEM application",
        "body": "Hi, I am interested in the Technical Project Manager role at CloudStream.",
        "outreach_type": "job",
        "style": "recruiter_friendly",
        "status": "needs_review",
        "personalization_score": 0,
        "spam_risk_score": 50,
        "ai_sounding_score": 50,
        "quality_status": "pending",
        "quality_reasons": ["Quality check not yet run"],
        "send_recommendation": "revise",
        "context_used": {},
    },
    {
        "job_url": "https://demo.linkedin.com/jobs/view/D001",
        "company": "Apex Digital Solutions",
        "job_title": "Senior IT Project Manager",
        "to_email": "cto@apex-demo.test",
        "to_name": "Morgan Chen",
        "to_role": "CTO",
        "subject": "Connecting on the PM role at Apex",
        "body": (
            "Hi Morgan,\n\n"
            "Quick note — I saw the IT Project Manager role and noticed Apex is "
            "scaling the engineering team. I've led delivery for similar-sized "
            "distributed teams, and I'm based in LATAM working fully remote.\n\n"
            "Happy to connect if there's a fit."
        ),
        "outreach_type": "job",
        "style": "warm_networking",
        "status": "approved",
        "personalization_score": 79,
        "spam_risk_score": 20,
        "ai_sounding_score": 25,
        "quality_status": "passed",
        "quality_reasons": [],
        "send_recommendation": "send",
        "context_used": {
            "company": "Apex Digital Solutions",
            "job_title": "Senior IT Project Manager",
            "contact_name": "Morgan Chen",
            "contact_role": "CTO",
        },
    },
]


# ── Seeder function ────────────────────────────────────────────────────────────

def seed_demo_data(db_path: str) -> dict:
    """
    Populate the local DB with demo jobs, leads, and drafts for safe testing.
    Fully idempotent: reads existing state once, then skips any record that
    already exists.  Running this command multiple times is safe.
    """
    stats = {"jobs_created": 0, "leads_created": 0, "drafts_created": 0, "skipped": 0}

    # Snapshot existing state in a single read (avoids N+1 queries and races)
    with db.get_connection(db_path) as conn:
        existing_job_urls = {
            r[0] for r in conn.execute("SELECT job_url FROM applied_jobs").fetchall()
        }
        existing_lead_domains = {
            r[0] for r in conn.execute("SELECT domain FROM leads").fetchall()
        }
        # Dedup key for drafts: (job_url, style, to_email) — unique across all DEMO_DRAFTS
        existing_draft_keys = {
            (r[0], r[1], r[2])
            for r in conn.execute(
                "SELECT job_url, style, to_email FROM outreach"
            ).fetchall()
        }

    # Jobs — deduplicated by job_url (unique across any status)
    for job in DEMO_JOBS:
        if job["job_url"] in existing_job_urls:
            stats["skipped"] += 1
            continue
        db.record_job(
            db_path,
            job_url=job["job_url"],
            company=job["company"],
            title=job["title"],
            location=job["location"],
            domain=job["domain"],
            status=job["status"],
            notes=job["notes"],
        )
        if job.get("job_score"):
            db.update_job_score(
                db_path, job["job_url"],
                job["job_score"], job["job_score"],
                job["score_label"],
            )
        stats["jobs_created"] += 1

    # Leads — deduplicated by domain
    for lead in DEMO_LEADS:
        if lead["domain"] in existing_lead_domains:
            stats["skipped"] += 1
            continue
        lead_id = db.save_lead(
            db_path,
            domain=lead["domain"],
            company=lead["company"],
            contact_name=lead["contact_name"],
            contact_email=lead["contact_email"],
            contact_role=lead["contact_role"],
            industry=lead["industry"],
            pain_points=lead["pain_points"],
            context_data=lead["context_data"],
        )
        if lead_id and lead.get("lead_score"):
            db.update_lead_score(db_path, lead_id, lead["lead_score"], lead["score_label"])
        if lead_id:
            stats["leads_created"] += 1
        else:
            stats["skipped"] += 1

    # Drafts — deduplicated by (job_url, style, to_email)
    for draft in DEMO_DRAFTS:
        key = (draft["job_url"], draft["style"], draft.get("to_email", ""))
        if key in existing_draft_keys:
            stats["skipped"] += 1
            continue
        db.record_outreach(
            db_path=db_path,
            job_url=draft["job_url"],
            company=draft["company"],
            job_title=draft["job_title"],
            subject=draft["subject"],
            body=draft["body"],
            to_email=draft.get("to_email", ""),
            to_name=draft.get("to_name", ""),
            to_role=draft.get("to_role", ""),
            outreach_type=draft["outreach_type"],
            style=draft["style"],
            status=draft["status"],
            personalization_score=draft["personalization_score"],
            spam_risk_score=draft["spam_risk_score"],
            ai_sounding_score=draft["ai_sounding_score"],
            quality_status=draft["quality_status"],
            quality_reasons=draft.get("quality_reasons", []),
            send_recommendation=draft["send_recommendation"],
            context_used=draft.get("context_used", {}),
        )
        stats["drafts_created"] += 1

    return stats


def clear_demo_data(db_path: str) -> None:
    """Remove all demo records (those using .test domains)."""
    from src.db import get_connection
    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM applied_jobs WHERE domain LIKE '%.test'")
        conn.execute("DELETE FROM leads WHERE domain LIKE '%.test'")
        conn.execute("DELETE FROM outreach WHERE job_url LIKE '%demo.linkedin.com%' OR job_url LIKE 'lead:%'")
        conn.execute("DELETE FROM contacts WHERE domain LIKE '%.test'")
