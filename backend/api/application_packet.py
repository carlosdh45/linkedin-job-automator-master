"""
Application packet endpoints. All generation is local/rule-based.
No automatic sending. No external APIs.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.config import (
    get_application_packet_path,
    get_resume_preview_path,
    get_resume_profile_path,
)
from backend.models.application_packet import ApplicationPacket, ApplicationPacketUpdate
from backend.services import packet_generator, packet_store, resume_generator, resume_store

router = APIRouter(prefix="/application-packet", tags=["application-packet"])


@router.get("", response_model=ApplicationPacket)
async def get_application_packet(
    packet_path: str = Depends(get_application_packet_path),
) -> ApplicationPacket:
    """Return the current application packet."""
    return packet_store.get_packet(packet_path)


@router.put("", response_model=ApplicationPacket)
async def put_application_packet(
    updates: ApplicationPacketUpdate,
    packet_path: str = Depends(get_application_packet_path),
) -> ApplicationPacket:
    """Update the application packet fields manually."""
    return packet_store.update_packet(
        packet_path,
        updates.model_dump(exclude_none=True),
    )


@router.post("/generate", response_model=ApplicationPacket)
async def generate_application_packet(
    packet_path: str = Depends(get_application_packet_path),
    resume_path: str = Depends(get_resume_profile_path),
    preview_path: str = Depends(get_resume_preview_path),
) -> ApplicationPacket:
    """
    Generate a local application packet from the current resume profile.
    Pure rule-based — no external AI or API calls.
    Prepared for manual submission only.
    """
    profile = resume_store.get_resume_profile(resume_path)
    resume_md = resume_generator.load_preview(preview_path)
    if not resume_md:
        resume_md = resume_generator.generate_markdown(profile)

    existing = packet_store.get_packet(packet_path)
    job_title = existing.target_job_title or profile.target_role or ""
    company = existing.target_company or ""
    job_description = existing.job_description or ""

    packet = packet_generator.generate_packet(profile, job_title, company, resume_md, job_description)
    return packet_store.save_packet(packet_path, packet)
