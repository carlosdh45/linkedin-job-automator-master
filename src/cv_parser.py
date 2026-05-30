import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CVProfile:
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin_url: str = ""
    github_url: str = ""
    summary: str = ""
    skills: list = field(default_factory=list)
    experience: list = field(default_factory=list)
    education: list = field(default_factory=list)
    raw_text: str = ""
    cv_path: str = ""


def parse_cv(pdf_path: str) -> CVProfile:
    try:
        import pdfplumber
    except ImportError:
        raise RuntimeError("pdfplumber not installed. Run: pip install pdfplumber")

    profile = CVProfile(cv_path=pdf_path)
    text_parts = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    profile.raw_text = "\n".join(text_parts)

    if not profile.raw_text.strip():
        return profile

    contact = _extract_contact_info(profile.raw_text)
    profile.name = contact.get("name", "")
    profile.email = contact.get("email", "")
    profile.phone = contact.get("phone", "")
    profile.linkedin_url = contact.get("linkedin_url", "")
    profile.github_url = contact.get("github_url", "")

    profile.skills = _extract_skills(profile.raw_text)
    profile.experience = _extract_experience(profile.raw_text)
    profile.summary = _extract_summary(profile.raw_text)

    return profile


def _extract_contact_info(text: str) -> dict:
    result = {}

    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
    if email_match:
        result["email"] = email_match.group(0)

    phone_match = re.search(
        r"(?:\+?[\d\s\-().]{7,20})", text
    )
    if phone_match:
        candidate = phone_match.group(0).strip()
        if sum(c.isdigit() for c in candidate) >= 7:
            result["phone"] = candidate

    linkedin_match = re.search(
        r"(?:linkedin\.com/in/|linkedin:\s*)([^\s,]+)", text, re.IGNORECASE
    )
    if linkedin_match:
        result["linkedin_url"] = "https://linkedin.com/in/" + linkedin_match.group(1).strip("/")

    github_match = re.search(
        r"(?:github\.com/|github:\s*)([^\s,]+)", text, re.IGNORECASE
    )
    if github_match:
        result["github_url"] = "https://github.com/" + github_match.group(1).strip("/")

    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines[:5]:
        words = line.split()
        if (
            2 <= len(words) <= 5
            and not re.search(r"[@|/\\:()]", line)
            and not re.search(r"\d", line)
            and all(w[0].isupper() for w in words if w)
            and not any(kw in line.upper() for kw in ("SUMMARY", "ENGINEER", "DEVELOPER", "MANAGER", "LEAD", "PROFILE", "OBJECTIVE"))
        ):
            result["name"] = line.title()
            break

    return result


def _extract_skills(text: str) -> list:
    skills_section = re.search(
        r"(?:skills?|technical skills?|core competenc[yi]|technologies)[:\s]*\n(.*?)(?:\n[A-Z][A-Z\s]{3,}:|\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not skills_section:
        return []

    raw = skills_section.group(1)
    items = re.split(r"[,\n•\|·]", raw)
    skills = [s.strip() for s in items if 2 < len(s.strip()) < 40]
    return skills[:50]


def _extract_summary(text: str) -> str:
    summary_match = re.search(
        r"(?:summary|profile|about me|objective)[:\s]*\n(.*?)(?:\n[A-Z][A-Z\s]{3,}[:\n]|\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if summary_match:
        return summary_match.group(1).strip()[:500]
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for i, line in enumerate(lines[2:8], 2):
        if len(line) > 60:
            return line[:300]
    return ""


def _extract_experience(text: str) -> list:
    exp_section = re.search(
        r"(?:experience|work history|employment)[:\s]*\n(.*?)(?:\n(?:education|skills?|certif)[:\s]*\n|\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not exp_section:
        return []

    raw = exp_section.group(1)
    date_pattern = re.compile(
        r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{4}|"
        r"\d{4}\s*[-–]\s*(?:\d{4}|present|current)",
        re.IGNORECASE,
    )
    entries = date_pattern.split(raw)
    result = []
    for entry in entries[:6]:
        entry = entry.strip()
        if len(entry) > 20:
            lines = [l.strip() for l in entry.split("\n") if l.strip()]
            result.append({"title": lines[0] if lines else "", "description": entry[:300]})
    return result


def profile_to_summary_text(profile: CVProfile) -> str:
    parts = []
    if profile.name:
        parts.append(f"Name: {profile.name}")
    if profile.email:
        parts.append(f"Email: {profile.email}")
    if profile.phone:
        parts.append(f"Phone: {profile.phone}")
    if profile.linkedin_url:
        parts.append(f"LinkedIn: {profile.linkedin_url}")
    if profile.github_url:
        parts.append(f"GitHub: {profile.github_url}")
    if profile.summary:
        parts.append(f"\nSummary:\n{profile.summary}")
    if profile.skills:
        parts.append(f"\nSkills: {', '.join(profile.skills[:30])}")
    if profile.experience:
        exp_lines = [f"  - {e['title']}" for e in profile.experience[:5] if e.get("title")]
        if exp_lines:
            parts.append(f"\nRecent Experience:\n" + "\n".join(exp_lines))

    structured = "\n".join(parts)

    if profile.raw_text and len(profile.raw_text) > len(structured):
        raw_trimmed = profile.raw_text[:2000]
        return f"{structured}\n\n--- Full CV Text ---\n{raw_trimmed}"

    return structured[:2000]
