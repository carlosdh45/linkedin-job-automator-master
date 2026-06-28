"""
BD Recommendations — local signal intelligence recommendations.

No auto-send. No external API calls. All recommendations require explicit human action.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from backend.config import (
    get_bd_recommendation_path, get_bd_company_path, get_bd_signal_path,
    get_bd_opportunity_path, get_bd_prospect_path, get_bd_pain_point_path,
    get_bd_activity_path, get_bd_icp_config_path,
)
from backend.models.bd import (
    BDRecommendation, BDRecommendationRefreshResult, BDOpportunity,
)
from backend.services.bd_recommendation_store import (
    list_recommendations, get_recommendation, create_recommendation,
    update_recommendation, clear_recommendations,
)
from backend.services.bd_company_store import list_companies, get_company, update_company
from backend.services.bd_signal_store import list_signals, get_signal, update_signal
from backend.services.bd_opportunity_store import list_opportunities, update_opportunity, create_opportunity
from backend.services.bd_prospect_store import list_prospects
from backend.services.bd_pain_point_store import list_by_company, list_pain_points
from backend.services.bd_activity_store import log_activity
from backend.services.bd_icp_store import load_icp_config
from backend.services.bd_scoring import compute_opportunity_score
from backend.services.bd_signal_intelligence import (
    evaluate_signal as _eval_signal,
    evaluate_company as _eval_company,
    recalculate_opportunity as _recalc_opp,
)

router = APIRouter(prefix="/bd/recommendations", tags=["bd-recommendations"])


@router.get("", response_model=list[BDRecommendation])
def get_recommendations(
    status: str | None = None,
    entity_type: str | None = None,
    priority: str | None = None,
    limit: int = 100,
    path: str = Depends(get_bd_recommendation_path),
):
    return list_recommendations(path, status=status, entity_type=entity_type, priority=priority, limit=limit)


@router.post("/{rec_id}/review", response_model=BDRecommendation)
def review_recommendation(
    rec_id: str,
    path: str = Depends(get_bd_recommendation_path),
    activity_path: str = Depends(get_bd_activity_path),
):
    """Mark a recommendation as reviewed. No auto-action. Human decides next step."""
    rec = get_recommendation(path, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    updated = update_recommendation(path, rec_id, {"status": "reviewed"})
    log_activity(activity_path, {
        "entity_type": rec.entity_type,
        "entity_id": rec.entity_id,
        "action": "recommendation_reviewed",
        "description": f"Recommendation for {rec.entity_name} marked as reviewed",
        "metadata": {"recommendation_id": rec_id, "priority": rec.priority},
    })
    return updated


@router.post("/{rec_id}/create-opportunity", response_model=BDOpportunity)
def create_opportunity_from_recommendation(
    rec_id: str,
    path: str = Depends(get_bd_recommendation_path),
    opportunity_path: str = Depends(get_bd_opportunity_path),
    signal_path: str = Depends(get_bd_signal_path),
    company_path: str = Depends(get_bd_company_path),
    activity_path: str = Depends(get_bd_activity_path),
):
    """
    Create a BD opportunity from a signal or company recommendation.
    Local only — no auto-outreach. Human review required before any action.
    """
    rec = get_recommendation(path, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    # Resolve company from the recommendation entity
    company = None
    if rec.entity_type == "signal":
        sig = get_signal(signal_path, rec.entity_id)
        if sig and sig.company_id:
            company = get_company(company_path, sig.company_id)
    elif rec.entity_type == "company":
        company = get_company(company_path, rec.entity_id)

    company_id = company.id if company else rec.entity_id
    company_name = company.name if company else rec.entity_name

    score, label, _ = compute_opportunity_score(
        icp_match=company.icp_match if company else False,
        pain_point_count=len(company.pain_points) if company else 0,
        signal_count=0,
        company_size=company.size_estimate if company else None,
        prospect_seniority=None,
        days_since_last_signal=None,
        existing_relationship=False,
    )

    opp = create_opportunity(opportunity_path, {
        "company_id": company_id,
        "company_name": company_name,
        "stage": "identified",
        "pain_points": (company.pain_points[:3] if company else []),
        "value_proposition": rec.recommended_action,
        "recommended_action": rec.recommended_action,
        "score": score,
        "score_label": label,
        "notes": f"Created from {rec.priority} recommendation: {rec.reason}",
        "source": "generated",
    })

    update_recommendation(path, rec_id, {"status": "actioned"})

    log_activity(activity_path, {
        "entity_type": "opportunity",
        "entity_id": opp.id,
        "action": "opportunity_created_from_recommendation",
        "description": (
            f"Opportunity created for {company_name} from {rec.priority} recommendation"
        ),
        "metadata": {"recommendation_id": rec_id, "priority": rec.priority},
    })

    return opp


@router.post("/{rec_id}/dismiss", response_model=BDRecommendation)
def dismiss_recommendation(
    rec_id: str,
    path: str = Depends(get_bd_recommendation_path),
    activity_path: str = Depends(get_bd_activity_path),
):
    rec = get_recommendation(path, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    updated = update_recommendation(path, rec_id, {"status": "dismissed"})
    log_activity(activity_path, {
        "entity_type": rec.entity_type,
        "entity_id": rec.entity_id,
        "action": "recommendation_dismissed",
        "description": f"Recommendation for {rec.entity_name} dismissed",
        "metadata": {"recommendation_id": rec_id, "priority": rec.priority},
    })
    return updated


@router.post("/{rec_id}/action", response_model=BDRecommendation)
def action_recommendation(
    rec_id: str,
    path: str = Depends(get_bd_recommendation_path),
    activity_path: str = Depends(get_bd_activity_path),
):
    rec = get_recommendation(path, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    updated = update_recommendation(path, rec_id, {"status": "actioned"})
    log_activity(activity_path, {
        "entity_type": rec.entity_type,
        "entity_id": rec.entity_id,
        "action": "recommendation_actioned",
        "description": f"Recommendation for {rec.entity_name} marked as actioned",
        "metadata": {"recommendation_id": rec_id, "priority": rec.priority},
    })
    return updated


@router.post("/refresh", response_model=BDRecommendationRefreshResult)
def refresh_recommendations(
    company_path: str = Depends(get_bd_company_path),
    signal_path: str = Depends(get_bd_signal_path),
    opportunity_path: str = Depends(get_bd_opportunity_path),
    prospect_path: str = Depends(get_bd_prospect_path),
    pain_point_path: str = Depends(get_bd_pain_point_path),
    activity_path: str = Depends(get_bd_activity_path),
    recommendation_path: str = Depends(get_bd_recommendation_path),
    icp_path: str = Depends(get_bd_icp_config_path),
):
    """
    Batch re-evaluation of all entities using local rule-based intelligence.
    No external API calls. No auto-send. All results require manual review.
    """
    icp_config = load_icp_config(icp_path)
    companies = list_companies(company_path)
    signals = list_signals(signal_path)
    opportunities = list_opportunities(opportunity_path)
    prospects = list_prospects(prospect_path)
    pain_points = list_pain_points(pain_point_path)

    signals_evaluated = 0
    companies_evaluated = 0
    opps_recalculated = 0
    recs_created = 0
    now = datetime.utcnow().isoformat()

    # ── Evaluate unevaluated signals ─────────────────────────────────────────
    for sig in signals:
        if sig.evaluated:
            continue
        company = next((c for c in companies if c.id == sig.company_id), None)
        result = _eval_signal(sig, company, icp_config, prospects)

        update_signal(signal_path, sig.id, {
            "evaluated": True,
            "evaluated_at": now,
            "signal_strength": result["signal_strength"],
        })

        if result["priority"] in ("high", "critical"):
            create_recommendation(recommendation_path, {
                "entity_type": "signal",
                "entity_id": sig.id,
                "entity_name": sig.company_name,
                "priority": result["priority"],
                "reason": result["reason"],
                "recommended_action": result["recommended_action"],
                "confidence_score": result["confidence_score"],
                "source": "generated",
            })
            recs_created += 1

        log_activity(activity_path, {
            "entity_type": "signal",
            "entity_id": sig.id,
            "action": "signal_evaluated",
            "description": f"Signal from {sig.company_name} evaluated — strength: {result['signal_strength']}",
            "metadata": {
                "priority": result["priority"],
                "signal_strength": result["signal_strength"],
            },
        })
        signals_evaluated += 1

    # ── Evaluate companies ───────────────────────────────────────────────────
    for co in companies:
        co_signals = [s for s in signals if s.company_id == co.id]
        co_pain_points = [p for p in pain_points if p.company_id == co.id]
        co_opps = [o for o in opportunities if o.company_id == co.id]

        recs, flags = _eval_company(co, co_signals, co_pain_points, co_opps, icp_config)
        for rec in recs:
            rec["source"] = "generated"
            create_recommendation(recommendation_path, rec)
            recs_created += 1

        if recs:
            log_activity(activity_path, {
                "entity_type": "company",
                "entity_id": co.id,
                "action": "company_evaluated",
                "description": f"{co.name} evaluated — {len(recs)} recommendation(s) created",
                "metadata": {"flags": flags, "recommendations_created": len(recs)},
            })
        companies_evaluated += 1

    # ── Recalculate opportunities ────────────────────────────────────────────
    for opp in opportunities:
        company = next((c for c in companies if c.id == opp.company_id), None)
        opp_signals = signals
        opp_prospects = prospects
        opp_pain_points = [p for p in pain_points if p.company_id == opp.company_id]

        result = _recalc_opp(opp, company, opp_signals, opp_prospects, opp_pain_points)

        update_opportunity(opportunity_path, opp.id, {
            "score": result["new_score"],
            "score_label": result["new_score_label"],
            "score_change": result["score_change"],
            "score_reason": result["score_reason"],
            "signal_contribution": result["signal_contribution"],
            "last_recalculated_at": now,
        })

        if result["new_score"] >= 55:
            priority = "high" if result["new_score"] >= 75 else "medium"
            create_recommendation(recommendation_path, {
                "entity_type": "opportunity",
                "entity_id": opp.id,
                "entity_name": opp.company_name,
                "priority": priority,
                "reason": (
                    f"Score {result['new_score']} ({result['new_score_label']}): "
                    f"{result['score_reason']}"
                ),
                "recommended_action": (
                    f"Schedule outreach to {opp.company_name}"
                    if result["new_score"] >= 75
                    else f"Prepare outreach draft for {opp.company_name}"
                ),
                "confidence_score": min(100, result["new_score"]),
                "source": "generated",
            })
            recs_created += 1

        change_str = f"{result['score_change']:+d}"
        log_activity(activity_path, {
            "entity_type": "opportunity",
            "entity_id": opp.id,
            "action": "opportunity_recalculated",
            "description": (
                f"{opp.company_name} score: {result['previous_score']} → "
                f"{result['new_score']} ({change_str})"
            ),
            "metadata": {
                "previous_score": result["previous_score"],
                "new_score": result["new_score"],
                "score_change": result["score_change"],
            },
        })
        opps_recalculated += 1

    return BDRecommendationRefreshResult(
        signals_evaluated=signals_evaluated,
        companies_evaluated=companies_evaluated,
        opportunities_recalculated=opps_recalculated,
        recommendations_created=recs_created,
        safety_notice=(
            "Recommendations require explicit human review — "
            "DobryBot does not send or contact anyone automatically."
        ),
    )
