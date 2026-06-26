from fastapi import APIRouter, Depends, HTTPException

from backend.config import get_bd_opportunity_path, get_bd_activity_path
from backend.models.bd import (
    BDOpportunity, BDOpportunityCreate,
    BDMoveStageRequest, BDMoveStageResponse,
    OpportunityScoreRequest, OpportunityScoreResponse,
    _VALID_STAGES,
)
from backend.services.bd_opportunity_store import list_opportunities, create_opportunity, get_opportunity, update_opportunity
from backend.services.bd_activity_store import log_activity
from backend.services.bd_scoring import compute_opportunity_score

router = APIRouter(prefix="/bd/opportunities", tags=["bd-opportunities"])


@router.get("", response_model=list[BDOpportunity])
def get_opportunities(path: str = Depends(get_bd_opportunity_path)):
    return list_opportunities(path)


@router.post("/score", response_model=OpportunityScoreResponse)
def score_opportunity(req: OpportunityScoreRequest):
    """
    Local rule-based opportunity scoring. No external APIs. No AI calls.
    """
    score, label, breakdown = compute_opportunity_score(
        icp_match=req.icp_match,
        pain_point_count=req.pain_point_count,
        signal_count=req.signal_count,
        company_size=req.company_size,
        prospect_seniority=req.prospect_seniority,
        days_since_last_signal=req.days_since_last_signal,
        existing_relationship=req.existing_relationship,
    )
    return OpportunityScoreResponse(score=score, score_label=label, breakdown=breakdown)


@router.post("", response_model=BDOpportunity, status_code=201)
def create_opportunity_endpoint(
    data: BDOpportunityCreate,
    path: str = Depends(get_bd_opportunity_path),
):
    payload = data.model_dump()
    score, label, _ = compute_opportunity_score(
        icp_match=False,
        pain_point_count=len(payload.get("pain_points", [])),
        signal_count=0,
        company_size=None,
        prospect_seniority=None,
        days_since_last_signal=None,
        existing_relationship=payload.get("stage") in ("engaged", "active"),
    )
    payload["score"] = score
    payload["score_label"] = label
    return create_opportunity(path, payload)


@router.post("/{opp_id}/move-stage", response_model=BDMoveStageResponse)
def move_stage(
    opp_id: str,
    req: BDMoveStageRequest,
    path: str = Depends(get_bd_opportunity_path),
    activity_path: str = Depends(get_bd_activity_path),
):
    """
    Transition an opportunity to a new pipeline stage.
    Records an activity log entry. No external calls.
    """
    if req.stage not in _VALID_STAGES:
        raise HTTPException(status_code=422, detail=f"Invalid stage '{req.stage}'.")
    opp = get_opportunity(path, opp_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    previous_stage = opp.stage
    updated = update_opportunity(path, opp_id, {"stage": req.stage})
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update opportunity")
    activity = log_activity(activity_path, {
        "entity_type": "opportunity",
        "entity_id": opp_id,
        "action": "stage_moved",
        "description": f"{opp.company_name} moved from {previous_stage} → {req.stage}",
        "metadata": {"previous_stage": previous_stage, "new_stage": req.stage},
    })
    return BDMoveStageResponse(
        id=opp_id,
        previous_stage=previous_stage,
        new_stage=req.stage,
        activity_id=activity.id,
    )
