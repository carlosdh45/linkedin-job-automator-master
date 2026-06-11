"""
Local-only CV text extraction. No external APIs, no network calls.
Supports PDF (pdfplumber) and DOCX (python-docx).
Falls back gracefully — empty string means manual paste should be used.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    try:
        import pdfplumber  # type: ignore

        text_parts: list[str] = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except Exception as exc:
        logger.warning("PDF extraction failed for %s: %s", file_path, exc)
        return ""


def extract_text_from_docx(file_path: str) -> str:
    try:
        import docx  # type: ignore

        doc = docx.Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    except Exception as exc:
        logger.warning("DOCX extraction failed for %s: %s", file_path, exc)
        return ""


def extract_text(file_path: str) -> str:
    """Extract text from PDF or DOCX. Returns empty string on any failure."""
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    if suffix in (".docx", ".doc"):
        return extract_text_from_docx(file_path)
    return ""


def save_extracted_text(output_path: str, text: str) -> None:
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def load_extracted_text(output_path: str) -> str:
    p = Path(output_path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")
