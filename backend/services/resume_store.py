import json
from datetime import datetime
from pathlib import Path

from backend.models.resume_profile import ResumeProfile


def _load(path: str) -> ResumeProfile:
    p = Path(path)
    if not p.exists():
        return ResumeProfile()
    with open(p, encoding="utf-8") as f:
        return ResumeProfile(**json.load(f))


def _save(path: str, profile: ResumeProfile) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(profile.model_dump(mode="json"), f, indent=2)


def get_resume_profile(path: str) -> ResumeProfile:
    return _load(path)


def update_resume_profile(path: str, updates: dict) -> ResumeProfile:
    data = _load(path).model_dump(mode="json")
    data.update(updates)
    data["updated_at"] = datetime.utcnow().isoformat()
    profile = ResumeProfile(**data)
    _save(path, profile)
    return profile
