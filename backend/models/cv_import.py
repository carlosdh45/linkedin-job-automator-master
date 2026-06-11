from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class CVImportPreview(BaseModel):
    raw_text: str = ""
    detected_email: str = ""
    detected_phone: str = ""
    detected_linkedin: str = ""
    detected_github: str = ""
    detected_portfolio: str = ""
    detected_skills: List[str] = Field(default_factory=list)
    detected_experience_headings: List[str] = Field(default_factory=list)
    detected_education_entries: List[str] = Field(default_factory=list)
    detected_certifications: List[str] = Field(default_factory=list)
    raw_notes: str = ""
    has_content: bool = False


class CVImportTextRequest(BaseModel):
    text: str = ""


class CVImportApplyRequest(BaseModel):
    """Explicit apply payload — resume profile is only updated after user confirmation."""
    apply_email: bool = True
    apply_phone: bool = True
    apply_linkedin: bool = True
    apply_github: bool = True
    apply_portfolio: bool = True
    apply_skills: bool = True
    apply_certifications: bool = True
    apply_raw_notes: bool = True
