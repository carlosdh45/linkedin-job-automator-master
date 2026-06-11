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
    resume_markdown: str = ""
    cover_letter_draft: str = ""
    talking_points: List[str] = Field(default_factory=list)
    checklist: List[ChecklistItem] = Field(default_factory=list)
    status: str = "not_started"
    updated_at: Optional[str] = None


class ApplicationPacketUpdate(BaseModel):
    target_job_title: Optional[str] = None
    target_company: Optional[str] = None
    resume_markdown: Optional[str] = None
    cover_letter_draft: Optional[str] = None
    talking_points: Optional[List[str]] = None
    checklist: Optional[List[ChecklistItem]] = None
    status: Optional[str] = None
