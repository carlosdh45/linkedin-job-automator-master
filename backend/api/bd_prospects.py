from fastapi import APIRouter, Depends, HTTPException

from backend.config import get_bd_prospect_path
from backend.models.bd import BDProspect, BDProspectCreate, BDProspectUpdate
from backend.services.bd_prospect_store import (
    list_prospects, get_prospect, create_prospect, update_prospect,
)
from backend.services.bd_scoring import compute_opportunity_score

router = APIRouter(prefix="/bd/prospects", tags=["bd-prospects"])


@router.get("", response_model=list[BDProspect])
def get_prospects(path: str = Depends(get_bd_prospect_path)):
    return list_prospects(path)


@router.get("/{prospect_id}", response_model=BDProspect)
def get_prospect_by_id(prospect_id: str, path: str = Depends(get_bd_prospect_path)):
    prospect = get_prospect(path, prospect_id)
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return prospect


@router.post("", response_model=BDProspect, status_code=201)
def create_prospect_endpoint(data: BDProspectCreate, path: str = Depends(get_bd_prospect_path)):
    payload = data.model_dump()
    score, label, _ = compute_opportunity_score(
        icp_match=False,
        pain_point_count=payload.get("pain_point_count", 0),
        signal_count=payload.get("signal_count", 0),
        company_size=None,
        prospect_seniority=payload.get("seniority"),
        days_since_last_signal=None,
        existing_relationship=False,
    )
    payload["opportunity_score"] = score
    payload["score_label"] = label
    payload["source"] = "manual"
    return create_prospect(path, payload)


@router.put("/{prospect_id}", response_model=BDProspect)
def update_prospect_endpoint(
    prospect_id: str,
    data: BDProspectUpdate,
    path: str = Depends(get_bd_prospect_path),
):
    updates = data.model_dump(exclude_none=True)
    updated = update_prospect(path, prospect_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return updated
