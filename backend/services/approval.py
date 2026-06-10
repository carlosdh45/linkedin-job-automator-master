"""
Approval service — the single point where Quality Guard is enforced for the API.

Rules (same as the CLI — no bypass path exists):
  - quality_status must be 'passed'
  - personalization_score >= 75
  - spam_risk_score       <= 35
  - ai_sounding_score     <= 40
"""

from src import db as src_db
from src.review_queue import quality_passes


def approve_draft(db_path: str, draft_id: int) -> dict:
    """Approve a draft. Quality Guard is always enforced — no bypass."""
    items = src_db.get_needs_review(db_path)
    item = next((i for i in items if i["id"] == draft_id), None)
    if not item:
        return {
            "approved": False,
            "draft_id": draft_id,
            "reason": f"Draft #{draft_id} not found in review queue.",
        }

    ok, reason = quality_passes(item)
    if not ok:
        return {"approved": False, "draft_id": draft_id, "reason": reason}

    src_db.approve_outreach(db_path, draft_id)
    return {"approved": True, "draft_id": draft_id, "message": f"Draft #{draft_id} approved."}


def skip_draft(db_path: str, draft_id: int, reason: str = None) -> dict:
    items = src_db.get_needs_review(db_path)
    item = next((i for i in items if i["id"] == draft_id), None)
    if not item:
        return {"skipped": False, "draft_id": draft_id, "reason": f"Draft #{draft_id} not found."}

    src_db.skip_outreach(db_path, draft_id, reason or "skipped_via_api")
    return {"skipped": True, "draft_id": draft_id}


def mark_needs_research(db_path: str, draft_id: int, note: str = None) -> dict:
    """Flag a draft as needing more research before it can be actioned."""
    items = src_db.get_needs_review(db_path)
    item = next((i for i in items if i["id"] == draft_id), None)
    if not item:
        return {"flagged": False, "draft_id": draft_id, "reason": f"Draft #{draft_id} not found."}

    skip_reason = f"needs_research: {note}" if note else "needs_research"
    src_db.skip_outreach(db_path, draft_id, skip_reason)
    return {"flagged": True, "draft_id": draft_id, "action": "needs_research"}
