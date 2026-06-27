from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.config import get_bd_deal_packet_path, get_bd_activity_path
from backend.models.bd import (
    BDDealPacket, BDDealPacketGenerateRequest, BDChecklistItem,
)
from backend.services.bd_deal_packet_store import (
    list_deal_packets, get_deal_packet, create_deal_packet,
)
from backend.services.bd_activity_store import log_activity

router = APIRouter(prefix="/bd/deal-packets", tags=["bd-deal-packets"])

_SAFETY_NOTICE = "\n\n---\nPrepared for manual review. DobryBot does not send automatically."


def _generate_packet(req: BDDealPacketGenerateRequest) -> BDDealPacket:
    pain_points = req.pain_points or []
    contact_first = req.contact_name.split()[0] if req.contact_name else "there"
    engagement = req.engagement_type or "New Business"

    company_summary = (
        f"{req.company_name} is a prospect identified for {engagement.lower()}. "
        "Intelligence gathered from market signals and public sources."
    )

    if pain_points:
        pp_list = "; ".join(pain_points[:3])
        value_prop = (
            f"We can help {req.company_name} address key challenges: {pp_list}. "
            "Our approach delivers measurable outcomes without disrupting existing operations."
        )
    else:
        value_prop = (
            f"We can help {req.company_name} with targeted solutions aligned to their "
            "growth stage and technical challenges."
        )

    talking_pts: List[str] = []
    for pp in pain_points[:4]:
        talking_pts.append(
            f"Address {pp.lower()}: walk through how similar organizations solved this"
        )
    talking_pts.append("Discuss timeline and implementation approach")
    talking_pts.append("Understand decision-making process and stakeholders")

    first_pp = pain_points[0].lower() if pain_points else "your current priorities"
    outreach_draft = (
        f"Hi {contact_first},\n\n"
        f"I've been following {req.company_name}'s work and noticed some challenges that align "
        f"closely with what we help organizations like yours solve — specifically around {first_pp}.\n\n"
        "We've helped similar teams achieve measurable improvements without a lengthy implementation cycle.\n\n"
        "Would a 20-minute conversation to share what's worked for comparable organizations be worth your time?\n\n"
        f"[Your name]{_SAFETY_NOTICE}"
    )

    checklist = [
        BDChecklistItem(text="Review company background and recent signals"),
        BDChecklistItem(text="Confirm contact details and decision-maker role"),
        BDChecklistItem(text="Validate pain point relevance"),
        BDChecklistItem(text="Review and customize outreach draft"),
        BDChecklistItem(text="Approve in Review Queue before sending"),
    ]

    return BDDealPacket(
        company_id=req.company_id,
        company_name=req.company_name,
        contact_name=req.contact_name,
        contact_role=req.contact_role,
        engagement_type=engagement,
        company_summary=company_summary,
        pain_points=pain_points,
        value_proposition=value_prop,
        talking_points=talking_pts,
        outreach_draft=outreach_draft,
        checklist=checklist,
        status="draft",
        notes=req.notes,
    )


@router.get("", response_model=list[BDDealPacket])
def get_deal_packets(path: str = Depends(get_bd_deal_packet_path)):
    return list_deal_packets(path)


@router.get("/{packet_id}", response_model=BDDealPacket)
def get_deal_packet_by_id(packet_id: str, path: str = Depends(get_bd_deal_packet_path)):
    pkt = get_deal_packet(path, packet_id)
    if not pkt:
        raise HTTPException(status_code=404, detail="Deal packet not found")
    return pkt


@router.post("/generate", response_model=BDDealPacket, status_code=201)
def generate_deal_packet(
    req: BDDealPacketGenerateRequest,
    path: str = Depends(get_bd_deal_packet_path),
    activity_path: str = Depends(get_bd_activity_path),
):
    """
    Generate a local deal packet using rule-based templates. No AI. No external calls.
    The outreach draft is marked for manual review — DobryBot does not send automatically.
    """
    packet = _generate_packet(req)
    packet.updated_at = datetime.utcnow().isoformat()
    saved = create_deal_packet(path, packet)
    log_activity(activity_path, {
        "entity_type": "deal_packet",
        "entity_id": saved.id,
        "action": "deal_packet_generated",
        "description": (
            f"Deal packet generated for {saved.company_name}"
            + (f" / {saved.contact_name}" if saved.contact_name else "")
        ),
        "metadata": {
            "company_name": saved.company_name,
            "contact_name": saved.contact_name,
            "pain_points": saved.pain_points,
        },
    })
    return saved
