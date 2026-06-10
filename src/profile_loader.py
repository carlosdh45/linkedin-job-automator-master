"""
User profile loader for CorosDev Opportunity Copilot.

Loads profile.yaml if present; returns safe defaults if not.
The profile drives personalized job/lead scoring and message generation.
"""

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class UserProfile:
    name: str = ""
    location: str = ""
    availability: str = ""
    target_roles: list = field(default_factory=list)
    skills: list = field(default_factory=list)
    seniority: str = ""
    years_experience: str = ""
    languages: list = field(default_factory=list)
    career_goals: list = field(default_factory=list)
    business: dict = field(default_factory=dict)
    outreach_preferences: dict = field(default_factory=dict)

    @property
    def first_name(self) -> str:
        return self.name.split()[0] if self.name else "there"

    @property
    def positioning(self) -> str:
        return self.business.get("positioning", "")

    @property
    def services(self) -> list:
        return self.business.get("services", [])

    @property
    def ideal_clients(self) -> list:
        return self.business.get("ideal_clients", [])

    @property
    def company_name(self) -> str:
        return self.business.get("company_name", "")

    def is_empty(self) -> bool:
        return not self.name and not self.target_roles and not self.skills


def load_profile(path: str = "profile.yaml") -> UserProfile:
    """
    Load user profile from profile.yaml.
    Returns an empty UserProfile if the file does not exist.
    Never raises — missing profile just means less personalization.
    """
    profile_path = Path(path)
    if not profile_path.exists():
        return UserProfile()
    try:
        with open(profile_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return UserProfile(
            name=data.get("name", ""),
            location=data.get("location", ""),
            availability=data.get("availability", ""),
            target_roles=data.get("target_roles", []),
            skills=data.get("skills", []),
            seniority=data.get("seniority", ""),
            years_experience=str(data.get("years_experience", "")),
            languages=data.get("languages", []),
            career_goals=data.get("career_goals", []),
            business=data.get("business", {}),
            outreach_preferences=data.get("outreach_preferences", {}),
        )
    except Exception as e:
        print(f"WARNING: could not load profile from {path}: {e}")
        return UserProfile()
