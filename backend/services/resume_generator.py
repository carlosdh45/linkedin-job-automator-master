"""
Local rule-based resume generator. No external API calls, no AI, no network requests.
Produces a polished Markdown resume from structured ResumeProfile data.
"""
from __future__ import annotations

from pathlib import Path

from backend.models.resume_profile import ResumeProfile


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {b}" for b in items if b.strip())


def generate_markdown(profile: ResumeProfile) -> str:
    """Build a Markdown resume from structured data. Pure local template — no external calls."""
    lines: list[str] = []

    # ── Header ────────────────────────────────────────────────────────────────
    if profile.headline:
        lines.append(f"# {profile.headline}")
    elif profile.target_role:
        lines.append(f"# {profile.target_role}")
    else:
        lines.append("# My Resume")

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
        lines.append(" · ".join(contact_parts))

    lines.append("\n---\n")

    # ── Summary ───────────────────────────────────────────────────────────────
    if profile.professional_summary:
        lines.append("## Professional Summary\n")
        lines.append(profile.professional_summary)
        lines.append("\n---\n")

    # ── Skills ────────────────────────────────────────────────────────────────
    if profile.skills:
        lines.append("## Skills\n")
        lines.append(", ".join(profile.skills))
        lines.append("\n---\n")

    # ── Experience ────────────────────────────────────────────────────────────
    if profile.experience_items:
        lines.append("## Experience\n")
        for exp in profile.experience_items:
            period = exp.start_date
            if exp.end_date:
                period += f" – {exp.end_date}"
            elif exp.currently_working:
                period += " – Present"

            title_line = f"### {exp.title}" if exp.title else "### (Role)"
            if exp.company:
                title_line += f" — {exp.company}"
            if exp.location:
                title_line += f" · {exp.location}"
            lines.append(title_line)
            if period:
                lines.append(f"*{period}*\n")
            if exp.bullets:
                lines.append(_bullets(exp.bullets))
            lines.append("")
        lines.append("---\n")

    # ── Projects ──────────────────────────────────────────────────────────────
    if profile.project_items:
        lines.append("## Projects\n")
        for proj in profile.project_items:
            lines.append(f"### {proj.name}" if proj.name else "### (Project)")
            if proj.description:
                lines.append(proj.description)
            if proj.technologies:
                lines.append(f"*Technologies: {', '.join(proj.technologies)}*\n")
            if proj.bullets:
                lines.append(_bullets(proj.bullets))
            lines.append("")
        lines.append("---\n")

    # ── Education ─────────────────────────────────────────────────────────────
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

    # ── Certifications ────────────────────────────────────────────────────────
    if profile.certifications:
        lines.append("## Certifications\n")
        lines.append(_bullets(profile.certifications))
        lines.append("\n---\n")

    # ── Languages ─────────────────────────────────────────────────────────────
    if profile.languages:
        lines.append("## Languages\n")
        lines.append(_bullets(profile.languages))
        lines.append("\n---\n")

    # ── Achievements ──────────────────────────────────────────────────────────
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
