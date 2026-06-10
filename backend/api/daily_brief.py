from datetime import datetime

from fastapi import APIRouter, Depends

from backend.config import get_db_path
from src import db as src_db

router = APIRouter()


@router.get("/daily-brief")
def get_daily_brief(db_path: str = Depends(get_db_path)):
    stats = src_db.get_stats(db_path)

    all_scored_jobs = (
        src_db.get_jobs_by_status(db_path, "scored")
        + src_db.get_jobs_by_status(db_path, "draft_ready")
        + src_db.get_jobs_by_status(db_path, "approved")
    )
    all_scored_jobs.sort(key=lambda j: j.get("job_score", 0), reverse=True)

    all_scored_leads = (
        src_db.get_leads_by_status(db_path, "scored")
        + src_db.get_leads_by_status(db_path, "draft_ready")
    )
    all_scored_leads.sort(key=lambda l: l.get("lead_score", 0), reverse=True)

    pending_drafts = src_db.get_needs_review(db_path)
    approvable = [
        d for d in pending_drafts
        if d.get("quality_status") == "passed"
        and d.get("personalization_score", 0) >= 75
        and d.get("spam_risk_score", 100) <= 35
        and d.get("ai_sounding_score", 100) <= 40
    ]
    blocked = [d for d in pending_drafts if d not in approvable]

    top_jobs = [
        j for j in all_scored_jobs
        if j.get("score_label") in ("high_priority", "good_fit")
    ][:8]
    top_leads = [
        l for l in all_scored_leads
        if l.get("score_label") in ("high_priority", "good_fit")
    ][:6]

    return {
        "date": datetime.now().strftime("%A, %B %d %Y"),
        "stats": stats,
        "top_jobs": top_jobs,
        "top_leads": top_leads,
        "pending_drafts": {
            "total": len(pending_drafts),
            "approvable": approvable,
            "blocked": blocked,
        },
        "recommended_actions": _build_actions(stats, approvable, top_jobs, top_leads),
    }


def _build_actions(stats: dict, approvable: list, top_jobs: list, top_leads: list) -> list:
    actions = []
    if stats.get("outreach_approved", 0):
        actions.append(f"Send {stats['outreach_approved']} approved message(s)")
    if approvable:
        ids = [d["id"] for d in approvable[:3]]
        actions.append(f"Approve {len(approvable)} quality-passed draft(s) — IDs: {ids}")
    if top_jobs:
        top = top_jobs[0]
        actions.append(f"Draft message for: {top.get('title')} @ {top.get('company')}")
    if top_leads:
        top = top_leads[0]
        actions.append(f"Draft outreach for: {top.get('company')} ({top.get('industry', '?')})")
    if not actions:
        actions.append("No urgent actions. Run --discover-jobs to find new opportunities.")
    return actions[:5]
