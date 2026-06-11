"""
Local rule-based application packet generator.
No external AI, no network calls, no automatic sending.
Produces cover letter draft, tailored summary, skills emphasis, fit summary,
talking points, and submission checklist from structured profile data + job description.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import List, Set

from backend.models.application_packet import ApplicationPacket, ChecklistItem
from backend.models.resume_profile import ResumeProfile

# Words too common to be useful for job-description matching
_STOP_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "as", "is", "was", "are", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "shall", "can", "need", "you", "we", "they", "he", "she", "it",
    "i", "this", "that", "these", "those", "our", "your", "their", "its", "not",
    "no", "nor", "so", "yet", "both", "either", "neither", "while", "because",
    "since", "unless", "until", "when", "where", "who", "which", "what", "how",
    "if", "then", "than", "also", "just", "only", "even", "well", "still", "each",
    "any", "all", "more", "most", "other", "some", "such", "into", "through",
    "about", "after", "before", "up", "out", "over", "under", "again", "once",
    "here", "there", "much", "very", "own", "same", "too", "during", "between",
    "against", "own", "must", "use", "used", "using", "role", "team", "work",
    "strong", "good", "new", "help", "build", "make", "take", "look", "get",
    "set", "able", "will", "work", "working", "experience", "ability", "skills",
    "skill", "knowledge", "understanding", "responsible", "responsibilities",
    "required", "requirements", "qualification", "qualifications", "plus",
    "preferred", "ideal", "candidate", "position", "opportunity", "job",
}

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
    ChecklistItem(text="Send a follow-up email 5-7 business days after submitting"),
]


def _extract_keywords(text: str) -> Set[str]:
    """Return meaningful lowercase words from text. No external calls."""
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9#+.\-]*", text.lower())
    return {w for w in words if w not in _STOP_WORDS and len(w) > 2}


def _match_skills(skills: List[str], jd_keywords: Set[str]) -> List[str]:
    """Return profile skills whose words overlap with job-description keywords."""
    matched: List[str] = []
    for skill in skills:
        skill_words = _extract_keywords(skill)
        if skill_words & jd_keywords:
            matched.append(skill)
    return matched


def _build_cover_letter(
    profile: ResumeProfile,
    job_title: str,
    company: str,
    jd_keywords: Set[str],
) -> str:
    name_line = profile.headline or profile.target_role or "a strong candidate"
    location_phrase = f" based in {profile.location}" if profile.location else ""
    matched = _match_skills(profile.skills, jd_keywords)
    skills_sample = (
        ", ".join(matched[:5]) if matched
        else ", ".join(profile.skills[:5]) if profile.skills
        else "my relevant skills"
    )
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
        f"{summary_text}. My background{location_phrase} has given me hands-on experience"
        f" with {skills_sample}, which aligns closely with what you are looking for.",
        "",
        f"I am particularly interested in this role because it aligns with my goal of"
        f" {target}. I look forward to contributing to your team and would welcome the"
        f" chance to discuss how my skills fit your needs.",
        "",
        f"Thank you for considering my application. I can be reached at {contact}"
        f" and am available for an interview at your convenience.",
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


def _build_tailored_summary(
    profile: ResumeProfile,
    job_title: str,
    jd_keywords: Set[str],
) -> str:
    """Build a tailored summary from profile data and JD keywords. No invented facts."""
    if not profile.professional_summary and not profile.skills:
        return ""

    base = profile.professional_summary[:300].rstrip(".") if profile.professional_summary else ""
    matched = _match_skills(profile.skills, jd_keywords)[:4]
    role_phrase = f"the {job_title}" if job_title else "this role"

    if matched and jd_keywords:
        skills_str = ", ".join(matched)
        if base:
            return f"{base}. Bringing directly applicable skills in {skills_str} to {role_phrase}."
        return f"Bringing directly applicable skills in {skills_str} to {role_phrase}."

    if base:
        return base + "."
    return ""


def _build_skills_emphasis(profile: ResumeProfile, jd_keywords: Set[str]) -> List[str]:
    """Return profile skills relevant to the job description. No invented skills."""
    if not jd_keywords:
        return profile.skills[:8]
    matched = _match_skills(profile.skills, jd_keywords)
    return matched if matched else profile.skills[:5]


def _build_fit_summary(
    profile: ResumeProfile,
    job_title: str,
    company: str,
    jd_keywords: Set[str],
) -> str:
    """Build a fit summary from profile data. No invented facts or metrics."""
    if not job_title and not jd_keywords:
        return ""

    role_phrase = f"the {job_title} role" if job_title else "this role"
    company_phrase = f" at {company}" if company else ""
    lines: List[str] = []

    matched = _match_skills(profile.skills, jd_keywords)[:5]
    if matched:
        lines.append(
            f"Your skills in {', '.join(matched)} align with the"
            f" requirements for {role_phrase}{company_phrase}."
        )

    if profile.experience_items:
        latest = profile.experience_items[0]
        if latest.title:
            company_ref = f" at {latest.company}" if latest.company else ""
            lines.append(
                f"Your background as {latest.title}{company_ref} provides"
                f" relevant hands-on experience."
            )

    if profile.location:
        lines.append(f"Based in {profile.location}.")

    if not lines:
        return (
            f"Review the job description for {role_phrase} and map your key"
            f" skills accordingly before applying."
        )

    return " ".join(lines)


def _build_talking_points(
    profile: ResumeProfile,
    job_title: str,
    company: str,
    jd_keywords: Set[str],
) -> List[str]:
    points: List[str] = []

    matched = _match_skills(profile.skills, jd_keywords)[:4]
    if matched:
        points.append(f"Directly relevant skills: {', '.join(matched)}")
    elif profile.skills:
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
        points.append(
            f"Company research: Look up {company}'s mission and recent news before the interview"
        )

    if not points:
        points = [
            "Prepare a concise 2-minute professional introduction",
            "Highlight 3 accomplishments with concrete outcomes",
            "Research the company's challenges and how your skills address them",
        ]

    return points


def generate_packet(
    profile: ResumeProfile,
    job_title: str,
    company: str,
    resume_md: str,
    job_description: str = "",
) -> ApplicationPacket:
    """
    Generate a local application packet. No external AI, no network calls.
    Prepared for manual submission only.
    """
    jd_keywords = _extract_keywords(job_description) if job_description else set()

    return ApplicationPacket(
        target_job_title=job_title,
        target_company=company,
        job_description=job_description,
        resume_markdown=resume_md,
        cover_letter_draft=_build_cover_letter(profile, job_title, company, jd_keywords),
        tailored_summary=_build_tailored_summary(profile, job_title, jd_keywords),
        skills_emphasis=_build_skills_emphasis(profile, jd_keywords),
        fit_summary=_build_fit_summary(profile, job_title, company, jd_keywords),
        talking_points=_build_talking_points(profile, job_title, company, jd_keywords),
        checklist=DEFAULT_CHECKLIST,
        status="ready",
        updated_at=datetime.utcnow().isoformat(),
    )
