from fastapi import APIRouter, Depends

from backend.config import (
    get_bd_company_path, get_bd_prospect_path, get_bd_signal_path,
    get_bd_pain_point_path, get_bd_opportunity_path,
    get_bd_deal_packet_path, get_bd_outreach_path,
)
from backend.services.bd_seed import seed_bd_demo, clear_bd_demo

router = APIRouter(prefix="/bd/demo", tags=["bd-demo"])


@router.post("/seed")
def bd_seed(
    company_path: str = Depends(get_bd_company_path),
    prospect_path: str = Depends(get_bd_prospect_path),
    signal_path: str = Depends(get_bd_signal_path),
    pain_point_path: str = Depends(get_bd_pain_point_path),
    opportunity_path: str = Depends(get_bd_opportunity_path),
    deal_packet_path: str = Depends(get_bd_deal_packet_path),
    outreach_path: str = Depends(get_bd_outreach_path),
):
    """Seed BD OS with local demo data. No external calls."""
    stats = seed_bd_demo(
        company_path, prospect_path, signal_path,
        pain_point_path, opportunity_path, deal_packet_path, outreach_path,
    )
    return {"seeded": True, "stats": stats}


@router.post("/clear")
def bd_clear(
    company_path: str = Depends(get_bd_company_path),
    prospect_path: str = Depends(get_bd_prospect_path),
    signal_path: str = Depends(get_bd_signal_path),
    pain_point_path: str = Depends(get_bd_pain_point_path),
    opportunity_path: str = Depends(get_bd_opportunity_path),
    deal_packet_path: str = Depends(get_bd_deal_packet_path),
    outreach_path: str = Depends(get_bd_outreach_path),
):
    """Clear all BD OS data. No external calls."""
    clear_bd_demo(
        company_path, prospect_path, signal_path,
        pain_point_path, opportunity_path, deal_packet_path, outreach_path,
    )
    return {"cleared": True}
