"""
Local, rule-based Signal Intelligence Engine.

No external API calls. No AI calls. No scraping.
All logic is deterministic and based on local data only.
Results require explicit human review — nothing is sent automatically.
"""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from backend.models.bd import BDSignal, BDCompany, BDOpportunity, BDProspect, BDPainPoint, BDICPConfig

from backend.services.bd_scoring import compute_opportunity_score

_STRENGTH_ORDER = ["low", "medium", "high", "critical"]

_CRITICAL_SIGNAL_TYPES = {"funding", "leadership_change"}
_HIGH_SIGNAL_TYPES = {"hiring", "tech_change", "pain_point"}

_SENIOR_KEYWORDS = {
    "c_suite", "c-suite", "ceo", "cto", "coo", "cfo",
    "vp", "vice president", "director", "head of",
}


# ── Signal strength helpers ───────────────────────────────────────────────────

def _raw_strength(signal_type: str, relevance_score: int) -> str:
    if signal_type in _CRITICAL_SIGNAL_TYPES and relevance_score >= 70:
        return "critical"
    if relevance_score >= 80:
        return "high"
    if signal_type in _CRITICAL_SIGNAL_TYPES and relevance_score >= 50:
        return "high"
    if relevance_score >= 55 or signal_type in _HIGH_SIGNAL_TYPES:
        return "medium"
    return "low"


def _boost(strength: str, boosts: int) -> str:
    idx = _STRENGTH_ORDER.index(strength)
    return _STRENGTH_ORDER[min(idx + boosts, len(_STRENGTH_ORDER) - 1)]


def _has_senior_prospect(prospects: list, company_id: Optional[str]) -> bool:
    for p in prospects:
        if company_id and p.company_id != company_id:
            continue
        if p.seniority:
            s = p.seniority.lower()
            if any(kw in s for kw in _SENIOR_KEYWORDS):
                return True
    return False


def _best_seniority(prospects: list, company_id: Optional[str]) -> Optional[str]:
    priority = ["c_suite", "c-suite", "ceo", "cto", "coo", "cfo", "vp", "vice president", "director", "head of", "manager", "lead"]
    candidates = [
        p for p in prospects
        if not company_id or p.company_id == company_id
    ]
    for kw in priority:
        for p in candidates:
            if p.seniority and kw in p.seniority.lower():
                return p.seniority
    return candidates[0].seniority if candidates else None


def _days_since(detected_at_str: str) -> Optional[int]:
    try:
        detected = date.fromisoformat(detected_at_str[:10])
        return (date.today() - detected).days
    except Exception:
        return None


# ── Public: Signal Evaluation ─────────────────────────────────────────────────

def evaluate_signal(
    signal,
    company,
    icp_config,
    prospects: list,
) -> dict:
    """
    Rule-based signal evaluation. Returns a result dict.
    No external calls. No AI. Human review required before any action.
    """
    strength = _raw_strength(signal.signal_type, signal.relevance_score)

    boosts = 0
    boost_reasons: list[str] = []

    if company and company.icp_match:
        boosts += 1
        boost_reasons.append("ICP match confirmed")

    if company and len(company.pain_points) >= 2:
        boosts += 1
        boost_reasons.append(f"{len(company.pain_points)} pain points detected")

    has_senior = _has_senior_prospect(prospects, signal.company_id)
    if has_senior:
        boosts += 1
        boost_reasons.append("senior prospect linked")

    if icp_config and signal.signal_type in (icp_config.signal_priorities or []):
        boosts += 1
        boost_reasons.append("priority signal type per ICP config")

    if boosts > 0:
        strength = _boost(strength, min(boosts, 2))

    confidence = signal.relevance_score
    if company and company.icp_match:
        confidence = min(100, confidence + 10)
    if has_senior:
        confidence = min(100, confidence + 5)
    confidence = max(10, confidence)

    reason = f"Signal type '{signal.signal_type}' with {signal.relevance_score} relevance"
    if boost_reasons:
        reason += ". Boosts: " + ", ".join(boost_reasons) + "."

    if strength == "critical":
        action = f"Schedule immediate outreach to {signal.company_name} — critical trigger signal"
    elif strength == "high":
        action = f"Research {signal.company_name} and prepare outreach draft this week"
    elif strength == "medium":
        action = f"Add {signal.company_name} to watch list and monitor for follow-up signals"
    else:
        action = f"Log {signal.company_name} signal for future reference"

    return {
        "signal_strength": strength,
        "priority": strength,
        "confidence_score": confidence,
        "reason": reason,
        "recommended_action": action,
    }


# ── Public: Company Evaluation ────────────────────────────────────────────────

def evaluate_company(
    company,
    signals: list,
    pain_points: list,
    opportunities: list,
    icp_config,
) -> tuple[list[dict], list[str]]:
    """
    Rule-based company evaluation. Returns (recommendations, flags).
    No external calls. Recommendations require manual review.
    """
    total_pain_count = len(company.pain_points) + len(pain_points)
    signal_count = len(signals)
    recs: list[dict] = []
    flags: list[str] = []

    def _rec(priority: str, reason: str, action: str, confidence: int) -> dict:
        return {
            "entity_type": "company",
            "entity_id": company.id,
            "entity_name": company.name,
            "priority": priority,
            "reason": reason,
            "recommended_action": action,
            "confidence_score": confidence,
        }

    if company.icp_match and total_pain_count >= 2 and signal_count >= 2:
        flags.append("outreach_ready")
        recs.append(_rec(
            priority="high",
            reason=f"{company.name} is ICP match with {total_pain_count} pain points and {signal_count} signals",
            action=f"Prepare outreach draft for {company.name} — identify top prospect contact",
            confidence=min(100, 60 + total_pain_count * 5 + signal_count * 3),
        ))

    elif company.icp_match and total_pain_count >= 1:
        flags.append("prepare_outreach")
        recs.append(_rec(
            priority="medium",
            reason=f"{company.name} is ICP match with {total_pain_count} pain point(s) documented",
            action=f"Add more signals for {company.name} then prepare outreach draft",
            confidence=min(100, 50 + total_pain_count * 5),
        ))

    elif total_pain_count >= 3 and not company.icp_match:
        flags.append("qualify_icp")
        recs.append(_rec(
            priority="medium",
            reason=f"{company.name} has {total_pain_count} pain points but ICP fit is unconfirmed",
            action=f"Evaluate {company.name} against ICP criteria before investing in outreach",
            confidence=50,
        ))

    elif company.icp_match and total_pain_count == 0:
        flags.append("needs_research")
        recs.append(_rec(
            priority="medium",
            reason=f"{company.name} is ICP match but no pain points documented",
            action=f"Research and document pain points for {company.name}",
            confidence=45,
        ))

    elif signal_count >= 3 and not company.icp_match:
        flags.append("evaluate_icp_fit")
        recs.append(_rec(
            priority="low",
            reason=f"{company.name} has {signal_count} signals but ICP fit not evaluated",
            action=f"Evaluate ICP fit for {company.name} before further investment",
            confidence=40,
        ))

    return recs, flags


# ── Public: Opportunity Recalculation ─────────────────────────────────────────

def recalculate_opportunity(
    opportunity,
    company,
    signals: list,
    prospects: list,
    pain_points: list,
) -> dict:
    """
    Recompute opportunity score from local data only.
    No external calls. Returns a result dict with updated score and breakdown.
    """
    company_signals = [
        s for s in signals
        if s.company_id == opportunity.company_id
        or s.company_name.lower() == opportunity.company_name.lower()
    ]
    signal_count = len(company_signals)

    total_pain_count = max(
        len(opportunity.pain_points),
        len(company.pain_points) + len(pain_points) if company else len(pain_points),
    )

    seniority = _best_seniority(prospects, opportunity.company_id)

    days_since_last_signal: Optional[int] = None
    if company_signals:
        try:
            latest = max(s.detected_at for s in company_signals)
            days_since_last_signal = _days_since(latest)
        except Exception:
            pass

    icp_match = company.icp_match if company else False
    existing_relationship = opportunity.stage in (
        "engaged", "active", "in_conversation", "proposal"
    )

    previous_score = opportunity.score
    new_score, new_label, breakdown = compute_opportunity_score(
        icp_match=icp_match,
        pain_point_count=total_pain_count,
        signal_count=signal_count,
        company_size=company.size_estimate if company else None,
        prospect_seniority=seniority,
        days_since_last_signal=days_since_last_signal,
        existing_relationship=existing_relationship,
    )

    signal_contribution = breakdown.get("signals", 0)
    score_change = new_score - previous_score

    parts: list[str] = []
    if breakdown.get("icp_match"):
        parts.append(f"ICP match (+{breakdown['icp_match']})")
    if breakdown.get("pain_points"):
        parts.append(f"{total_pain_count} pain point(s) (+{breakdown['pain_points']})")
    if breakdown.get("signals"):
        parts.append(f"{signal_count} signal(s) (+{breakdown['signals']})")
    if breakdown.get("seniority"):
        parts.append(f"prospect seniority (+{breakdown['seniority']})")
    if breakdown.get("urgency"):
        parts.append(f"signal urgency (+{breakdown['urgency']})")
    if breakdown.get("existing_relationship"):
        parts.append(f"existing relationship (+{breakdown['existing_relationship']})")

    score_reason = (
        "Score based on: " + ", ".join(parts) if parts
        else "No scoring factors found — add ICP match, pain points, or signals"
    )

    return {
        "previous_score": previous_score,
        "new_score": new_score,
        "score_change": score_change,
        "new_score_label": new_label,
        "signal_contribution": signal_contribution,
        "score_reason": score_reason,
        "breakdown": breakdown,
        "icp_match": icp_match,
    }
