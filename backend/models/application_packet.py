from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

APPLICATION_STATUSES = [
    "not_started",
    "ready",
    "submitted_manually",
    "interviewing",
    "rejected",
    "offer",
]


class ChecklistItem(BaseModel):
    text: str = ""
    done: bool = False


class ApplicationPacket(BaseModel):
    target_job_title: str = ""
    target_company: str = ""
    job_description: str = ""
    resume_markdown: str = ""
    cover_letter_draft: str = ""
    tailored_summary: str = ""
    skills_emphasis: List[str] = Field(default_factory=list)
    fit_summary: str = ""
    talking_points: List[str] = Field(default_factory=list)
    checklist: List[ChecklistItem] = Field(default_factory=list)
    status: str = "not_started"
    notes: str = ""
    updated_at: Optional[str] = None


class ApplicationPacketUpdate(BaseModel):
    target_job_title: Optional[str] = None
    target_company: Optional[str] = None
    job_description: Optional[str] = None
    resume_markdown: Optional[str] = None
    cover_letter_draft: Optional[str] = None
    tailored_summary: Optional[str] = None
    skills_emphasis: Optional[List[str]] = None
    fit_summary: Optional[str] = None
    talking_points: Optional[List[str]] = None
    checklist: Optional[List[ChecklistItem]] = None
    status: Optional[str] = None
    notes: Optional[str] = None
