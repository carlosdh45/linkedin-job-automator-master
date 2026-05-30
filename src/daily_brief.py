"""
Daily Brief: terminal summary of top jobs, top leads, pending drafts, and recommendations.
"""

from datetime import datetime
from src import db

_SEP = "─" * 72
_WIDE = "═" * 72


def _section(title: str):
    print(f"\n{_WIDE}")
    print(f"  {title}")
    print(_WIDE)


def _row(label: str, value, width: int = 30):
    print(f"  {label:<{width}}: {value}")


def generate_brief(db_path: str) -> None:
    today = datetime.now().strftime("%A, %B %d %Y")
    print(f"\n{'═' * 72}")
    print(f"  DAILY BRIEF  —  {today}")
    print(f"{'═' * 72}")

    stats = db.get_stats(db_path)

    # ── Jobs ──────────────────────────────────────────────────────────────────
    _section("TOP JOB OPPORTUNITIES")
    high_jobs = db.get_jobs_by_status(db_path, "scored")
    high_jobs = [j for j in high_jobs if j.get("score_label") in ("high_priority", "good_fit")]
    high_jobs = high_jobs[:10]

    if high_jobs:
        print(f"  {'#':3}  {'Score':5}  {'Label':14}  {'Title':<35}  Company")
        print(f"  {_SEP}")
        for i, j in enumerate(high_jobs, 1):
            score = j.get("job_score", 0)
            label = j.get("score_label", "")
            title = (j.get("title") or "")[:34]
            company = (j.get("company") or "")[:25]
            print(f"  {i:3}.  {score:3d}    {label:<14}  {title:<35}  {company}")
    else:
        print("  No scored jobs yet. Run --discover-jobs then --score-jobs.")

    # ── Leads ─────────────────────────────────────────────────────────────────
    _section("TOP CLIENT LEADS")
    high_leads = db.get_leads_by_status(db_path, "scored")
    high_leads = [l for l in high_leads if l.get("score_label") in ("high_priority", "good_fit")]
    high_leads = high_leads[:10]

    if high_leads:
        print(f"  {'#':3}  {'Score':5}  {'Label':14}  {'Company':<30}  Contact")
        print(f"  {_SEP}")
        for i, l in enumerate(high_leads, 1):
            score = l.get("lead_score", 0)
            label = l.get("score_label", "")
            company = (l.get("company") or "")[:29]
            contact = (l.get("contact_name") or "")[:20]
            print(f"  {i:3}.  {score:3d}    {label:<14}  {company:<30}  {contact}")
    else:
        print("  No scored leads yet. Run --discover-leads then --score-leads.")

    # ── Drafts pending review ─────────────────────────────────────────────────
    _section("DRAFTS PENDING REVIEW")
    pending = db.get_needs_review(db_path)

    if pending:
        job_drafts = [d for d in pending if d.get("outreach_type") == "job"]
        client_drafts = [d for d in pending if d.get("outreach_type") == "client"]
        passable = [d for d in pending if d.get("quality_status") == "passed"]
        print(f"  Total pending    : {len(pending)}")
        print(f"  Job drafts       : {len(job_drafts)}")
        print(f"  Client drafts    : {len(client_drafts)}")
        print(f"  Quality: passed  : {len(passable)}")
        print(f"  Quality: needs work: {len(pending) - len(passable)}")
        print(f"\n  Run: python main.py --review-queue")
    else:
        print("  No drafts pending review.")

    # ── Discarded leads ───────────────────────────────────────────────────────
    _section("DISCARDED / SKIPPED (last run)")
    not_fit_leads = db.get_leads_by_status(db_path, "not_fit")
    if not_fit_leads:
        print(f"  {len(not_fit_leads)} leads marked not_fit:")
        for l in not_fit_leads[:5]:
            reason = (l.get("skip_reason") or "")[:60]
            print(f"  - {l.get('company','')}  →  {reason}")
        if len(not_fit_leads) > 5:
            print(f"  ... and {len(not_fit_leads) - 5} more")
    else:
        print("  None.")

    # ── Today's suggestions ───────────────────────────────────────────────────
    _section("SUGGESTED ACTIONS FOR TODAY")
    suggestions = _build_suggestions(stats, high_jobs, high_leads, pending)
    if suggestions:
        for i, s in enumerate(suggestions, 1):
            print(f"  {i}. {s}")
    else:
        print("  Nothing to do — system is up to date.")

    # ── Overall stats ─────────────────────────────────────────────────────────
    _section("DATABASE SUMMARY")
    key_stats = [
        ("job_discovered", "Jobs discovered"),
        ("job_scored", "Jobs scored"),
        ("job_applied", "Jobs applied"),
        ("lead_discovered", "Leads discovered"),
        ("lead_scored", "Leads scored"),
        ("lead_contacted", "Leads contacted"),
        ("outreach_generated", "Outreach generated"),
        ("outreach_sent", "Outreach sent"),
        ("outreach_pending_review", "Drafts pending review"),
        ("contacts_found", "Contacts found"),
    ]
    for key, label in key_stats:
        val = stats.get(key, 0)
        if val:
            _row(label, val)

    print(f"\n{'═' * 72}\n")


def _build_suggestions(stats: dict, high_jobs: list, high_leads: list, pending: list) -> list:
    suggestions = []

    discovered_jobs = stats.get("job_discovered", 0)
    if discovered_jobs > 0:
        suggestions.append(f"Score {discovered_jobs} discovered job(s): python main.py --score-jobs")

    discovered_leads = stats.get("lead_discovered", 0)
    if discovered_leads > 0:
        suggestions.append(f"Score {discovered_leads} discovered lead(s): python main.py --score-leads")

    if high_jobs and not pending:
        suggestions.append(
            f"Generate job application drafts ({len(high_jobs)} eligible): "
            "python main.py --draft-job-application"
        )

    if high_leads and not pending:
        suggestions.append(
            f"Generate client outreach drafts ({len(high_leads)} eligible): "
            "python main.py --draft-client-outreach"
        )

    if pending:
        passable = [d for d in pending if d.get("quality_status") == "passed"]
        if passable:
            suggestions.append(
                f"Review {len(passable)} quality-passed draft(s): python main.py --review-queue"
            )
        failing = [d for d in pending if d.get("quality_status") != "passed"]
        if failing:
            suggestions.append(
                f"Regenerate {len(failing)} low-quality draft(s) with more context"
            )

    approved = stats.get("outreach_approved", 0)
    if approved:
        suggestions.append(f"Send {approved} approved email(s): python main.py --send-approved")

    if not suggestions:
        if not stats.get("job_discovered"):
            suggestions.append("Discover new jobs: python main.py --discover-jobs")
        if not stats.get("lead_discovered"):
            suggestions.append("Discover new leads: python main.py --discover-leads")

    return suggestions
