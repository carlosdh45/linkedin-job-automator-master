"""
Local rule-based resume generator. No external API calls, no AI, no network requests.
Produces a polished Markdown resume from structured ResumeProfile data.

Tone options (all purely local, rule-based):
  professional - balanced, standard resume format
  executive    - outcome-focused, shorter bullets, highlights scope
  technical    - includes tech context, more detail per role
  concise      - trimmed bullets (max 3 per role), brief summary
"""
from __future__ import annotations

from pathlib import Path

from backend.models.resume_profile import ResumeProfile

VALID_TONES = {"professional", "executive", "technical", "concise"}


def _bullets(items: list[str], tone: str = "professional") -> str:
    if not items:
        return ""
    if tone == "concise":
        items = items[:3]
    elif tone == "executive":
        items = items[:4]
    return "\n".join(f"- {b.rstrip()}" for b in items if b.strip())


def generate_markdown(profile: ResumeProfile, tone: str = "professional") -> str:
    """Build a Markdown resume from structured data. Pure local template - no external calls."""
    tone = tone.lower() if tone.lower() in VALID_TONES else "professional"
    lines: list[str] = []

    # Header
    if profile.headline:
        lines.append(f"# {profile.headline}")
    elif profile.target_role:
        lines.append(f"# {profile.target_role}")
    else:
        lines.append("# Resume")

    if profile.target_role and profile.headline:
        lines.append(f"**{profile.target_role}**")

    contact_parts: list[str] = []
    if profile.location:
        contact_parts.append(profile.location)
    if profile.email:
        contact_parts.append(profile.email)
    if profile.phone:
        contact_parts.append(profile.phone)
    if profile.linkedin_url:
        contact_parts.append(profile.linkedin_url)
    if profile.github_url:
        contact_parts.append(profile.github_url)
    if profile.portfolio_url:
        contact_parts.append(profile.portfolio_url)
    if contact_parts:
        lines.append(" | ".join(contact_parts))

    lines.append("\n---\n")

    # Summary
    if profile.professional_summary:
        summary = profile.professional_summary.strip()
        if tone == "concise":
            sentences = [s.strip() for s in summary.split(".") if s.strip()]
            trimmed = ". ".join(sentences[:2])
            summary = trimmed + "." if trimmed and not trimmed.endswith(".") else trimmed
        lines.append("## Professional Summary\n")
        lines.append(summary)
        lines.append("\n---\n")

    # Skills
    if profile.skills:
        lines.append("## Skills\n")
        lines.append(" | ".join(profile.skills) if tone == "executive" else ", ".join(profile.skills))
        lines.append("\n---\n")

    # Experience
    if profile.experience_items:
        lines.append("## Experience\n")
        for exp in profile.experience_items:
            period = exp.start_date
            if exp.end_date:
                period += f" - {exp.end_date}"
            elif exp.currently_working:
                period += " - Present"

            title_line = f"### {exp.title}" if exp.title else "### (Role)"
            if exp.company:
                title_line += f" at {exp.company}"
            if exp.location:
                title_line += f" ({exp.location})"
            lines.append(title_line)
            if period:
                lines.append(f"*{period}*\n")
            if exp.bullets:
                lines.append(_bullets(exp.bullets, tone))
            lines.append("")
        lines.append("---\n")

    # Projects
    if profile.project_items:
        lines.append("## Projects\n")
        for proj in profile.project_items:
            lines.append(f"### {proj.name}" if proj.name else "### (Project)")
            if proj.description:
                lines.append(proj.description)
            if proj.technologies:
                lines.append(f"*Stack: {', '.join(proj.technologies)}*\n")
            if proj.bullets:
                lines.append(_bullets(proj.bullets, tone))
            lines.append("")
        lines.append("---\n")

    # Education
    if profile.education_items:
        lines.append("## Education\n")
        for edu in profile.education_items:
            lines.append(f"### {edu.degree}" if edu.degree else "### (Degree)")
            if edu.institution:
                lines.append(f"*{edu.institution}*")
            if edu.dates:
                lines.append(f"*{edu.dates}*")
            lines.append("")
        lines.append("---\n")

    # Certifications
    if profile.certifications:
        lines.append("## Certifications\n")
        lines.append(_bullets(profile.certifications))
        lines.append("\n---\n")

    # Languages
    if profile.languages:
        lines.append("## Languages\n")
        lines.append(", ".join(profile.languages))
        lines.append("\n---\n")

    # Achievements
    if profile.achievements:
        lines.append("## Key Achievements\n")
        lines.append(_bullets(profile.achievements))
        lines.append("")

    return "\n".join(lines)


def save_preview(preview_path: str, content: str) -> None:
    p = Path(preview_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def load_preview(preview_path: str) -> str:
    p = Path(preview_path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")
