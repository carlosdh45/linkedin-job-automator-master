from fastapi import APIRouter, Depends

from backend.config import get_bd_opportunity_path
from backend.models.bd import (
    BDOpportunity, BDOpportunityCreate,
    OpportunityScoreRequest, OpportunityScoreResponse,
)
from backend.services.bd_opportunity_store import list_opportunities, create_opportunity
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
