"""
Outreach Draft CRUD — local persistence only.
Approved = ready for manual execution. Never sends automatically.
"""
from fastapi import APIRouter, Depends, HTTPException

from backend.config import get_bd_outreach_path, get_bd_activity_path
from backend.models.bd import (
    BDOutreachDraft, BDOutreachDraftCreate, BDOutreachDraftUpdate,
)
from backend.services.bd_outreach_store import (
    list_drafts, get_draft, save_draft, update_draft,
)
from backend.services.bd_activity_store import log_activity

router = APIRouter(prefix="/bd/outreach-drafts", tags=["bd-outreach-drafts"])

_SAFETY_NOTICE = "Approved for manual execution only. DobryBot does not send automatically."


@router.get("", response_model=list[BDOutreachDraft])
def get_drafts(path: str = Depends(get_bd_outreach_path)):
    return list_drafts(path)


@router.get("/{draft_id}", response_model=BDOutreachDraft)
def get_draft_by_id(draft_id: str, path: str = Depends(get_bd_outreach_path)):
    draft = get_draft(path, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.post("", response_model=BDOutreachDraft, status_code=201)
def create_draft(
    data: BDOutreachDraftCreate,
    path: str = Depends(get_bd_outreach_path),
    activity_path: str = Depends(get_bd_activity_path),
):
    draft = BDOutreachDraft(
        company_name=data.company_name,
        contact_name=data.contact_name,
        contact_role=data.contact_role,
        message_type=data.message_type,
        subject=data.subject,
        body=data.body,
        tone=data.tone,
        angle=data.angle,
        personalization_score=data.personalization_score,
        spam_risk_score=data.spam_risk_score,
        ai_sounding_score=data.ai_sounding_score,
        notes=data.notes,
        status="draft",
        quality_status="draft",
        source="manual",
    )
    saved = save_draft(path, draft)
    log_activity(activity_path, {
        "entity_type": "draft",
        "entity_id": saved.id,
        "action": "draft_saved",
        "description": f"Draft saved for {saved.company_name} / {saved.contact_name}",
        "metadata": {"company": saved.company_name, "message_type": saved.message_type},
    })
    return saved


@router.put("/{draft_id}", response_model=BDOutreachDraft)
def update_draft_endpoint(
    draft_id: str,
    data: BDOutreachDraftUpdate,
    path: str = Depends(get_bd_outreach_path),
):
    updated = update_draft(path, draft_id, data.model_dump(exclude_none=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Draft not found")
    return updated


@router.post("/{draft_id}/approve", response_model=BDOutreachDraft)
def approve_draft(
    draft_id: str,
    path: str = Depends(get_bd_outreach_path),
    activity_path: str = Depends(get_bd_activity_path),
):
    """
    Mark draft as approved for manual execution.
    DOES NOT send anything. Human must execute manually.
    """
    updated = update_draft(path, draft_id, {"status": "approved", "quality_status": "approved"})
    if not updated:
        raise HTTPException(status_code=404, detail="Draft not found")
    log_activity(activity_path, {
        "entity_type": "draft",
        "entity_id": draft_id,
        "action": "draft_approved",
        "description": f"Draft approved for manual execution — {updated.company_name}",
        "metadata": {"safety": _SAFETY_NOTICE},
    })
    return updated


@router.post("/{draft_id}/reject", response_model=BDOutreachDraft)
def reject_draft(
    draft_id: str,
    path: str = Depends(get_bd_outreach_path),
    activity_path: str = Depends(get_bd_activity_path),
):
    updated = update_draft(path, draft_id, {"status": "rejected", "quality_status": "rejected"})
    if not updated:
        raise HTTPException(status_code=404, detail="Draft not found")
    log_activity(activity_path, {
        "entity_type": "draft",
        "entity_id": draft_id,
        "action": "draft_rejected",
        "description": f"Draft rejected — {updated.company_name}",
        "metadata": {},
    })
    return updated


@router.post("/{draft_id}/needs-research", response_model=BDOutreachDraft)
def needs_research(
    draft_id: str,
    path: str = Depends(get_bd_outreach_path),
    activity_path: str = Depends(get_bd_activity_path),
):
    updated = update_draft(path, draft_id, {"status": "needs_research", "quality_status": "needs_research"})
    if not updated:
        raise HTTPException(status_code=404, detail="Draft not found")
    log_activity(activity_path, {
        "entity_type": "draft",
        "entity_id": draft_id,
        "action": "draft_needs_research",
        "description": f"Draft flagged for research — {updated.company_name}",
        "metadata": {},
    })
    return updated
