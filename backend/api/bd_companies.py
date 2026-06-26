from fastapi import APIRouter, Depends, HTTPException

from backend.config import get_bd_company_path
from backend.models.bd import BDCompany, BDCompanyCreate, BDCompanyUpdate
from backend.services.bd_company_store import (
    list_companies, get_company, create_company, update_company,
)
from backend.services.bd_scoring import compute_opportunity_score

router = APIRouter(prefix="/bd/companies", tags=["bd-companies"])


@router.get("", response_model=list[BDCompany])
def get_companies(path: str = Depends(get_bd_company_path)):
    return list_companies(path)


@router.get("/{company_id}", response_model=BDCompany)
def get_company_by_id(company_id: str, path: str = Depends(get_bd_company_path)):
    company = get_company(path, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("", response_model=BDCompany, status_code=201)
def create_company_endpoint(data: BDCompanyCreate, path: str = Depends(get_bd_company_path)):
    payload = data.model_dump()
    # Auto-compute initial score
    score, label, _ = compute_opportunity_score(
        icp_match=payload.get("icp_match", False),
        pain_point_count=len(payload.get("pain_points", [])),
        signal_count=0,
        company_size=payload.get("size_estimate"),
        prospect_seniority=None,
        days_since_last_signal=None,
        existing_relationship=False,
    )
    payload["opportunity_score"] = score
    payload["score_label"] = label
    return create_company(path, payload)


@router.put("/{company_id}", response_model=BDCompany)
def update_company_endpoint(
    company_id: str,
    data: BDCompanyUpdate,
    path: str = Depends(get_bd_company_path),
):
    updates = data.model_dump(exclude_none=True)
    updated = update_company(path, company_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Company not found")
    return updated
