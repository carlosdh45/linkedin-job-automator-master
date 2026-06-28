from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from backend.config import (
    get_bd_signal_path, get_bd_company_path, get_bd_prospect_path,
    get_bd_activity_path, get_bd_recommendation_path, get_bd_icp_config_path,
)
from backend.models.bd import BDSignal, BDSignalCreate, BDSignalEvaluationResult, BDEvaluateAllResult
from backend.services.bd_signal_store import list_signals, create_signal, get_signal, update_signal
from backend.services.bd_company_store import get_company, list_companies
from backend.services.bd_prospect_store import list_prospects
from backend.services.bd_activity_store import log_activity
from backend.services.bd_recommendation_store import create_recommendation
from backend.services.bd_icp_store import load_icp_config
from backend.services.bd_signal_intelligence import evaluate_signal as _evaluate_signal

router = APIRouter(prefix="/bd/signals", tags=["bd-signals"])


@router.get("", response_model=list[BDSignal])
def get_signals(path: str = Depends(get_bd_signal_path)):
    return list_signals(path)


@router.post("", response_model=BDSignal, status_code=201)
def create_signal_endpoint(data: BDSignalCreate, path: str = Depends(get_bd_signal_path)):
    payload = data.model_dump()
    if not payload.get("detected_at"):
        payload["detected_at"] = datetime.utcnow().date().isoformat()
    payload["data_source"] = "manual"
    return create_signal(path, payload)


@router.post("/evaluate-all", response_model=BDEvaluateAllResult)
def evaluate_all_signals(
    signal_path: str = Depends(get_bd_signal_path),
    company_path: str = Depends(get_bd_company_path),
    prospect_path: str = Depends(get_bd_prospect_path),
    activity_path: str = Depends(get_bd_activity_path),
    recommendation_path: str = Depends(get_bd_recommendation_path),
    icp_path: str = Depends(get_bd_icp_config_path),
):
    """
    Evaluate all unevaluated signals using local rule-based intelligence.
    No external API calls. Recommendations require explicit human review.
    """
    signals = list_signals(signal_path)
    companies = list_companies(company_path)
    prospects = list_prospects(prospect_path)
    icp_config = load_icp_config(icp_path)

    now = datetime.utcnow().isoformat()
    evaluated = 0
    skipped = 0
    recs_created = 0

    for sig in signals:
        if sig.evaluated:
            skipped += 1
            continue
        company = next((c for c in companies if c.id == sig.company_id), None)
        result = _evaluate_signal(sig, company, icp_config, prospects)

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
            "description": (
                f"Signal from {sig.company_name} evaluated — strength: {result['signal_strength']}"
            ),
            "metadata": {
                "priority": result["priority"],
                "signal_strength": result["signal_strength"],
                "confidence_score": result["confidence_score"],
            },
        })
        evaluated += 1

    return BDEvaluateAllResult(
        evaluated_count=evaluated,
        skipped_count=skipped,
        recommendations_created=recs_created,
    )


@router.post("/{signal_id}/evaluate", response_model=BDSignalEvaluationResult)
def evaluate_signal_endpoint(
    signal_id: str,
    signal_path: str = Depends(get_bd_signal_path),
    company_path: str = Depends(get_bd_company_path),
    prospect_path: str = Depends(get_bd_prospect_path),
    activity_path: str = Depends(get_bd_activity_path),
    recommendation_path: str = Depends(get_bd_recommendation_path),
    icp_path: str = Depends(get_bd_icp_config_path),
):
    """
    Evaluate a signal using local rule-based intelligence.
    No external API calls. Result requires human review.
    """
    signal = get_signal(signal_path, signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    company = get_company(company_path, signal.company_id) if signal.company_id else None
    prospects = list_prospects(prospect_path)
    icp_config = load_icp_config(icp_path)

    result = _evaluate_signal(signal, company, icp_config, prospects)

    update_signal(signal_path, signal_id, {
        "evaluated": True,
        "evaluated_at": datetime.utcnow().isoformat(),
        "signal_strength": result["signal_strength"],
    })

    recommendation_created = False
    if result["priority"] in ("high", "critical"):
        create_recommendation(recommendation_path, {
            "entity_type": "signal",
            "entity_id": signal_id,
            "entity_name": signal.company_name,
            "priority": result["priority"],
            "reason": result["reason"],
            "recommended_action": result["recommended_action"],
            "confidence_score": result["confidence_score"],
            "source": "generated",
        })
        recommendation_created = True

    log_activity(activity_path, {
        "entity_type": "signal",
        "entity_id": signal_id,
        "action": "signal_evaluated",
        "description": f"Signal from {signal.company_name} evaluated — strength: {result['signal_strength']}",
        "metadata": {
            "priority": result["priority"],
            "signal_strength": result["signal_strength"],
            "confidence_score": result["confidence_score"],
        },
    })

    return BDSignalEvaluationResult(
        signal_id=signal_id,
        signal_strength=result["signal_strength"],
        priority=result["priority"],
        confidence_score=result["confidence_score"],
        reason=result["reason"],
        recommended_action=result["recommended_action"],
        recommendation_created=recommendation_created,
    )
