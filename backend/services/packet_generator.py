"""
Local rule-based application packet generator.
No external AI, no network calls, no automatic sending.
Produces cover letter draft, talking points, and checklist from structured profile data.
"""
from __future__ import annotations

from datetime import datetime
from typing import List

from backend.models.application_packet import ApplicationPacket, ChecklistItem
from backend.models.resume_profile import ResumeProfile

DEFAULT_CHECKLIST: List[ChecklistItem] = [
    ChecklistItem(text="Tailor headline and summary to the target job description"),
    ChecklistItem(text="Research the company's mission, products, and recent news"),
    ChecklistItem(text="Customise the cover letter opening paragraph"),
    ChecklistItem(text="Verify all contact information is current and correct"),
    ChecklistItem(text="Proofread resume and cover letter for typos"),
    ChecklistItem(text="Save a PDF copy of your final resume locally"),
    ChecklistItem(text="Find the correct application portal or contact person"),
    ChecklistItem(text="Submit application manually via the company portal"),
    ChecklistItem(text="Record the submission date and role in your tracker"),
    ChecklistItem(text="Send a follow-up email 5–7 business days after submitting"),
]


def _build_cover_letter(profile: ResumeProfile, job_title: str, company: str) -> str:
    name_line = profile.headline or profile.target_role or "a strong candidate"
    location_phrase = f" based in {profile.location}" if profile.location else ""
    skills_sample = ", ".join(profile.skills[:5]) if profile.skills else "my relevant skills"
    summary_text = (
        profile.professional_summary[:300].rstrip(".")
        if profile.professional_summary
        else f"I have hands-on experience with {skills_sample}"
    )
    company_phrase = f"at {company}" if company else "at your organisation"
    role_phrase = f"the {job_title} position" if job_title else "this opportunity"
    target = profile.target_role or job_title or "this field"
    contact = profile.email or "[your email]"
    sign_name = profile.headline or "[Your Name]"

    lines = [
        "Dear Hiring Manager,",
        "",
        f"I am writing to express my strong interest in {role_phrase} {company_phrase}.",
        "",
        f"{summary_text}. My background{location_phrase} has given me hands-on experience with {skills_sample}, "
        f"which aligns closely with what you are looking for.",
        "",
        f"I am particularly excited about this opportunity as it aligns with my goal of {target}. "
        f"I look forward to contributing to your team and would welcome the chance to discuss how my skills fit your needs.",
        "",
        f"Thank you for considering my application. I can be reached at {contact} and am available for an interview at your convenience.",
        "",
        "Prepared for manual submission — not sent automatically.",
        "",
        "Best regards,",
        sign_name,
    ]
    if profile.email:
        lines.append(profile.email)
    if profile.phone:
        lines.append(profile.phone)
    if profile.linkedin_url:
        lines.append(profile.linkedin_url)

    return "\n".join(lines)


def _build_talking_points(profile: ResumeProfile, job_title: str, company: str) -> List[str]:
    points: List[str] = []

    if profile.skills:
        top = ", ".join(profile.skills[:4])
        points.append(f"Core skills: {top}")

    if profile.experience_items:
        latest = profile.experience_items[0]
        if latest.title and latest.company:
            points.append(f"Most recent role: {latest.title} at {latest.company}")
        elif latest.bullets:
            points.append(f"Key accomplishment: {latest.bullets[0]}")

    if profile.professional_summary:
        snippet = profile.professional_summary[:160].rstrip(".,")
        points.append(f"Value proposition: {snippet}")

    if profile.achievements:
        points.append(f"Notable achievement: {profile.achievements[0]}")

    if job_title:
        points.append(f"Role alignment: Applying for {job_title}")

    if company:
        points.append(f"Company research: Look up {company}'s mission and recent news before the interview")

    if not points:
        points = [
            "Prepare a concise 2-minute professional introduction",
            "Highlight 3 accomplishments with measurable outcomes",
            "Research the company's challenges and how your skills address them",
        ]

    return points


def generate_packet(
    profile: ResumeProfile,
    job_title: str,
    company: str,
    resume_md: str,
) -> ApplicationPacket:
    return ApplicationPacket(
        target_job_title=job_title,
        target_company=company,
        resume_markdown=resume_md,
        cover_letter_draft=_build_cover_letter(profile, job_title, company),
        talking_points=_build_talking_points(profile, job_title, company),
        checklist=DEFAULT_CHECKLIST,
        status="ready",
        updated_at=datetime.utcnow().isoformat(),
    )
