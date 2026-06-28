from fastapi import APIRouter, Depends, HTTPException

from backend.config import (
    get_bd_company_path, get_bd_signal_path, get_bd_pain_point_path,
    get_bd_opportunity_path, get_bd_activity_path, get_bd_recommendation_path,
    get_bd_icp_config_path,
)
from backend.models.bd import (
    BDCompany, BDCompanyCreate, BDCompanyUpdate, BDCompanyEvaluationResult,
)
from backend.services.bd_company_store import (
    list_companies, get_company, create_company, update_company,
)
from backend.services.bd_signal_store import list_signals
from backend.services.bd_pain_point_store import list_by_company
from backend.services.bd_opportunity_store import list_opportunities
from backend.services.bd_activity_store import log_activity
from backend.services.bd_recommendation_store import create_recommendation
from backend.services.bd_icp_store import load_icp_config
from backend.services.bd_scoring import compute_opportunity_score
from backend.services.bd_signal_intelligence import evaluate_company as _evaluate_company

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
    payload["source"] = "manual"
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


@router.post("/{company_id}/evaluate", response_model=BDCompanyEvaluationResult)
def evaluate_company_endpoint(
    company_id: str,
    company_path: str = Depends(get_bd_company_path),
    signal_path: str = Depends(get_bd_signal_path),
    pain_point_path: str = Depends(get_bd_pain_point_path),
    opportunity_path: str = Depends(get_bd_opportunity_path),
    activity_path: str = Depends(get_bd_activity_path),
    recommendation_path: str = Depends(get_bd_recommendation_path),
    icp_path: str = Depends(get_bd_icp_config_path),
):
    """
    Evaluate a company using local rule-based intelligence.
    No external API calls. Results require human review.
    """
    company = get_company(company_path, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    signals = [s for s in list_signals(signal_path) if s.company_id == company_id]
    pain_points = list_by_company(pain_point_path, company_id)
    opportunities = [o for o in list_opportunities(opportunity_path) if o.company_id == company_id]
    icp_config = load_icp_config(icp_path)

    recs, flags = _evaluate_company(company, signals, pain_points, opportunities, icp_config)

    for rec in recs:
        rec["source"] = "generated"
        create_recommendation(recommendation_path, rec)

    # Recompute score with current signal and pain-point counts
    total_pain = len(company.pain_points) + len(pain_points)
    new_score, new_label, _ = compute_opportunity_score(
        icp_match=company.icp_match,
        pain_point_count=total_pain,
        signal_count=len(signals),
        company_size=company.size_estimate,
        prospect_seniority=None,
        days_since_last_signal=None,
        existing_relationship=False,
    )
    update_company(company_path, company_id, {
        "opportunity_score": new_score,
        "score_label": new_label,
    })

    if recs:
        log_activity(activity_path, {
            "entity_type": "company",
            "entity_id": company_id,
            "action": "company_evaluated",
            "description": f"{company.name} evaluated — {len(recs)} recommendation(s) created",
            "metadata": {"flags": flags, "recommendations_created": len(recs)},
        })

    return BDCompanyEvaluationResult(
        company_id=company_id,
        recommendations_created=len(recs),
        score_updated=True,
        new_score=new_score,
        new_score_label=new_label,
        flags=flags,
    )
