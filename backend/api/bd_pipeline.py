from fastapi import APIRouter, Depends

from backend.config import get_bd_opportunity_path
from backend.models.bd import BDPipelineResponse, BDPipelineStage, BDPipelineDeal
from backend.services.bd_opportunity_store import list_opportunities

router = APIRouter(prefix="/bd/pipeline", tags=["bd-pipeline"])

_STAGE_META = [
    {"slug": "identified", "label": "Identified", "order": 0, "color": "gray"},
    {"slug": "researched", "label": "Researched", "order": 1, "color": "blue"},
    {"slug": "qualified", "label": "Qualified", "order": 2, "color": "violet"},
    {"slug": "engaged", "label": "Engaged", "order": 3, "color": "amber"},
    {"slug": "deal_packet", "label": "Deal Packet", "order": 4, "color": "orange"},
    {"slug": "active", "label": "Active", "order": 5, "color": "green"},
]


@router.get("", response_model=BDPipelineResponse)
def get_pipeline(path: str = Depends(get_bd_opportunity_path)):
    """
    Returns pipeline stages with deal counts and deal cards for kanban view.
    Derived from local opportunity records — no external calls.
    """
    opportunities = list_opportunities(path)

    deals_by_stage: dict[str, list[BDPipelineDeal]] = {s["slug"]: [] for s in _STAGE_META}
    for opp in opportunities:
        if opp.stage in deals_by_stage:
            deals_by_stage[opp.stage].append(
                BDPipelineDeal(
                    id=opp.id,
                    company=opp.company_name,
                    contact=opp.contact_name,
                    score=opp.score,
                    score_label=opp.score_label,
                    stage=opp.stage,
                    last_action=opp.recommended_action or f"Stage: {opp.stage}",
                    pain_points=opp.pain_points,
                )
            )

    stages = [
        BDPipelineStage(
            slug=s["slug"],
            label=s["label"],
            order=s["order"],
            color=s["color"],
            count=len(deals_by_stage.get(s["slug"], [])),
            deals=deals_by_stage.get(s["slug"], []),
        )
        for s in _STAGE_META
    ]

    total_active = sum(s.count for s in stages)
    return BDPipelineResponse(stages=stages, total_active=total_active)
