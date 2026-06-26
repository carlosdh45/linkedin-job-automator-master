"""
BD Dashboard stats — derived entirely from local data. No external calls.
"""
from fastapi import APIRouter, Depends

from backend.config import (
    get_bd_opportunity_path, get_bd_prospect_path,
    get_bd_company_path, get_bd_outreach_path,
)
from backend.models.bd import BDDashboardStats
from backend.services.bd_opportunity_store import list_opportunities
from backend.services.bd_prospect_store import list_prospects
from backend.services.bd_company_store import list_companies
from backend.services.bd_outreach_store import list_drafts

router = APIRouter(prefix="/bd/dashboard", tags=["bd-dashboard"])

_STAGE_ORDER = [
    "identified", "researched", "qualified", "outreach_ready",
    "in_conversation", "proposal", "engaged", "deal_packet", "active",
]
_WIN_LOSS = {"won", "lost"}


@router.get("", response_model=BDDashboardStats)
def get_bd_dashboard(
    opp_path: str = Depends(get_bd_opportunity_path),
    prospect_path: str = Depends(get_bd_prospect_path),
    company_path: str = Depends(get_bd_company_path),
    outreach_path: str = Depends(get_bd_outreach_path),
):
    opportunities = list_opportunities(opp_path)
    prospects = list_prospects(prospect_path)
    companies = list_companies(company_path)
    drafts = list_drafts(outreach_path)

    qualified_opps = [o for o in opportunities if o.score_label in ("hot", "warm")]
    hot_opps = [o for o in opportunities if o.score_label == "hot"]
    high_signal = [p for p in prospects if p.signal_count >= 2 or p.score_label in ("hot", "warm")]
    pain_point_cos = [c for c in companies if len(c.pain_points) > 0]
    drafts_for_review = [d for d in drafts if d.status in ("draft", "pending_review")]
    approved = [d for d in drafts if d.status == "approved"]

    # Pipeline snapshot by stage
    stage_counts: dict[str, int] = {}
    for opp in opportunities:
        if opp.stage not in _WIN_LOSS:
            stage_counts[opp.stage] = stage_counts.get(opp.stage, 0) + 1

    pipeline_snapshot = [
        {"stage": stage, "count": stage_counts.get(stage, 0)}
        for stage in _STAGE_ORDER
        if stage_counts.get(stage, 0) > 0
    ]

    # Recommended actions
    actions: list[str] = []
    if hot_opps:
        co = hot_opps[0].company_name
        actions.append(f"Follow up with {co} — highest-scoring opportunity")
    if drafts_for_review:
        actions.append(f"Review {len(drafts_for_review)} outreach draft(s) awaiting approval")
    if pain_point_cos:
        actions.append(f"{len(pain_point_cos)} companies with detected pain points — qualify for outreach")
    if not actions:
        actions.append("Add companies and prospects to start scoring opportunities")

    return BDDashboardStats(
        qualified_opportunities=len(qualified_opps),
        hot_opportunities=len(hot_opps),
        high_signal_prospects=len(high_signal),
        companies_with_pain_points=len(pain_point_cos),
        drafts_for_review=len(drafts_for_review),
        approved_drafts=len(approved),
        pipeline_snapshot=pipeline_snapshot,
        recommended_actions=actions,
    )
