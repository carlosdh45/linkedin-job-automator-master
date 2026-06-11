"""
Heuristic CV text importer. Local-only, no AI, no external APIs.
Detects structured fields from plain text using regex. Imperfect by design — the
user reviews and confirms before anything is written to their resume profile.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Tuple

from backend.models.cv_import import CVImportPreview

# ── Section-heading detector ──────────────────────────────────────────────────
# Matches lines that look like CV section headings (all-caps or title-cased, alone on a line)
_HEADING_RE = re.compile(
    r"^[ \t]*(SUMMARY|OBJECTIVE|PROFILE|ABOUT ME?|EXPERIENCE|WORK EXPERIENCE|"
    r"EMPLOYMENT(?: HISTORY)?|CAREER|EDUCATION|ACADEMIC|TRAINING|QUALIFICATIONS?|"
    r"SKILLS?|TECHNICAL SKILLS?|CORE COMPETENCIES|COMPETENCIES|KEY SKILLS?|"
    r"CERTIFICATIONS?|LICEN[CS]ES?|AWARDS?|ACHIEVEMENTS?|LANGUAGES?|PROJECTS?|"
    r"SIDE PROJECTS?|PUBLICATIONS?|VOLUNTEER(ING)?|INTERESTS?|HOBBIES|REFERENCES?)[ \t]*:?[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)

_EMAIL_RE = re.compile(r"[\w.+%-]+@[\w.-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"(?<!\d)(\+?[\d][\d\s\-(). ]{5,14}\d)(?!\d)")
_LINKEDIN_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/in/[\w\-]+/?", re.IGNORECASE)
_GITHUB_RE = re.compile(r"https?://(?:www\.)?github\.com/[\w\-]+/?", re.IGNORECASE)
_URL_RE = re.compile(r"https?://[^\s<>\"{}|\\^`\[\]]+", re.IGNORECASE)


def _split_sections(text: str) -> List[Tuple[str, str]]:
    """Return [(heading, content), ...]. First section has heading 'HEADER'."""
    lines = text.splitlines()
    sections: List[Tuple[str, str]] = []
    current_heading = "HEADER"
    current_lines: List[str] = []

    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            sections.append((current_heading, "\n".join(current_lines)))
            current_heading = m.group(1).upper().strip()
            current_lines = []
        else:
            current_lines.append(line)

    sections.append((current_heading, "\n".join(current_lines)))
    return sections


def _extract_list_items(text: str) -> List[str]:
    """Pull items from a section — comma-separated, bulleted, or one-per-line."""
    items: List[str] = []
    for line in text.splitlines():
        line = line.strip().lstrip("-•·*◦▪▸►∙▶").strip()
        if not line:
            continue
        # Comma-separated, no sentence punctuation → treat as skill list
        if "," in line and "." not in line and len(line) < 200:
            for part in line.split(","):
                part = part.strip()
                if part and len(part) < 80:
                    items.append(part)
        elif len(line) < 150:
            items.append(line)
    return [i for i in items if i]


def _extract_experience_headings(text: str) -> List[str]:
    """Return short non-bullet lines from experience section as candidate headings."""
    headings: List[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("-", "•", "*", "·")):
            continue
        if 5 < len(line) < 120:
            headings.append(line)
        if len(headings) >= 20:
            break
    return headings


def parse_cv_text(text: str) -> CVImportPreview:
    """Parse raw CV text and return a CVImportPreview. Pure local heuristics."""
    if not text.strip():
        return CVImportPreview(has_content=False)

    preview = CVImportPreview(raw_text=text, has_content=True)

    # ── Contact info ──────────────────────────────────────────────────────────
    em = _EMAIL_RE.search(text)
    if em:
        preview.detected_email = em.group(0)

    pm = _PHONE_RE.search(text)
    if pm:
        preview.detected_phone = pm.group(1).strip()

    lm = _LINKEDIN_RE.search(text)
    if lm:
        preview.detected_linkedin = lm.group(0).rstrip("/")

    gm = _GITHUB_RE.search(text)
    if gm:
        preview.detected_github = gm.group(0).rstrip("/")

    for url in _URL_RE.findall(text):
        if "linkedin.com" not in url.lower() and "github.com" not in url.lower():
            preview.detected_portfolio = url
            break

    # ── Section-based extraction ──────────────────────────────────────────────
    sections = _split_sections(text)
    unmatched: List[str] = []

    for heading, content in sections:
        hl = heading.lower()

        if any(kw in hl for kw in ("skill", "technical", "competenc", "technolog", "key skill")):
            skills = _extract_list_items(content)
            if skills:
                preview.detected_skills = skills[:50]

        elif any(kw in hl for kw in ("experience", "employment", "work", "career")):
            preview.detected_experience_headings = _extract_experience_headings(content)

        elif any(kw in hl for kw in ("education", "academic", "training", "qualification")):
            entries = _extract_list_items(content)
            if entries:
                preview.detected_education_entries = entries[:10]

        elif any(kw in hl for kw in ("certif", "licen", "award", "achievement")):
            certs = _extract_list_items(content)
            if certs:
                preview.detected_certifications = certs[:20]

        elif heading == "HEADER":
            pass  # contact info already extracted from full text above

        else:
            if content.strip():
                unmatched.append(f"=== {heading} ===\n{content.strip()}")

    if unmatched:
        preview.raw_notes = "\n\n".join(unmatched)[:3000]

    return preview


def save_preview(path: str, preview: CVImportPreview) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(preview.model_dump(), f, indent=2)


def load_preview(path: str) -> CVImportPreview:
    p = Path(path)
    if not p.exists():
        return CVImportPreview()
    with open(p, encoding="utf-8") as f:
        return CVImportPreview(**json.load(f))
