from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException

from backend.config import get_db_path
from backend.schemas.requests import NeedsResearchRequest, SkipRequest
from backend.services.approval import approve_draft, mark_needs_research, skip_draft
from src import db as src_db

router = APIRouter()


@router.get("/review-queue")
def get_review_queue(db_path: str = Depends(get_db_path)):
    items = src_db.get_needs_review(db_path)
    return {"drafts": items, "total": len(items)}


@router.post("/drafts/{draft_id}/approve")
def approve(draft_id: int, db_path: str = Depends(get_db_path)):
    result = approve_draft(db_path, draft_id)
    if not result["approved"]:
        raise HTTPException(status_code=422, detail=result["reason"])
    return result


@router.post("/drafts/{draft_id}/skip")
def skip(
    draft_id: int,
    body: Optional[SkipRequest] = Body(default=None),
    db_path: str = Depends(get_db_path),
):
    reason = body.reason if body else None
    return skip_draft(db_path, draft_id, reason)


@router.post("/drafts/{draft_id}/needs-research")
def needs_research(
    draft_id: int,
    body: Optional[NeedsResearchRequest] = Body(default=None),
    db_path: str = Depends(get_db_path),
):
    note = body.note if body else None
    return mark_needs_research(db_path, draft_id, note)
