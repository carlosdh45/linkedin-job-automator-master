from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CandidateProfile(BaseModel):
    id: str = "default"
    full_name: str = ""
    email: str = ""
    target_roles: List[str] = Field(default_factory=list)
    seniority: str = ""
    preferred_locations: List[str] = Field(default_factory=list)
    remote_preference: str = ""
    salary_expectation: str = ""
    linkedin_url: str = ""
    portfolio_url: str = ""
    github_url: str = ""
    key_skills: List[str] = Field(default_factory=list)
    industries_of_interest: List[str] = Field(default_factory=list)
    resume_filename: Optional[str] = None
    resume_original_filename: Optional[str] = None
    resume_uploaded_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    target_roles: Optional[List[str]] = None
    seniority: Optional[str] = None
    preferred_locations: Optional[List[str]] = None
    remote_preference: Optional[str] = None
    salary_expectation: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    github_url: Optional[str] = None
    key_skills: Optional[List[str]] = None
    industries_of_interest: Optional[List[str]] = None
