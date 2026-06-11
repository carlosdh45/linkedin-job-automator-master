from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ExperienceItem(BaseModel):
    company: str = ""
    title: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    currently_working: bool = False
    bullets: List[str] = Field(default_factory=list)


class ProjectItem(BaseModel):
    name: str = ""
    description: str = ""
    technologies: List[str] = Field(default_factory=list)
    bullets: List[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    institution: str = ""
    degree: str = ""
    dates: str = ""


class ResumeProfile(BaseModel):
    headline: str = ""
    professional_summary: str = ""
    target_role: str = ""
    location: str = ""
    email: str = ""
    phone: str = ""
    linkedin_url: str = ""
    portfolio_url: str = ""
    github_url: str = ""
    skills: List[str] = Field(default_factory=list)
    experience_items: List[ExperienceItem] = Field(default_factory=list)
    project_items: List[ProjectItem] = Field(default_factory=list)
    education_items: List[EducationItem] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ResumeProfileUpdate(BaseModel):
    headline: Optional[str] = None
    professional_summary: Optional[str] = None
    target_role: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    github_url: Optional[str] = None
    skills: Optional[List[str]] = None
    experience_items: Optional[List[ExperienceItem]] = None
    project_items: Optional[List[ProjectItem]] = None
    education_items: Optional[List[EducationItem]] = None
    certifications: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    achievements: Optional[List[str]] = None
