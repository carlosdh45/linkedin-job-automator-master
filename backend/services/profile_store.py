import json
from datetime import datetime
from pathlib import Path

from backend.models.profile import CandidateProfile


def _load(profile_path: str) -> CandidateProfile:
    path = Path(profile_path)
    if not path.exists():
        return CandidateProfile()
    with open(path, encoding="utf-8") as f:
        return CandidateProfile(**json.load(f))


def _save(profile_path: str, profile: CandidateProfile) -> None:
    path = Path(profile_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile.model_dump(mode="json"), f, indent=2)


def get_profile(profile_path: str) -> CandidateProfile:
    return _load(profile_path)


def update_profile(profile_path: str, updates: dict) -> CandidateProfile:
    data = _load(profile_path).model_dump(mode="json")
    data.update(updates)
    data["updated_at"] = datetime.utcnow().isoformat()
    profile = CandidateProfile(**data)
    _save(profile_path, profile)
    return profile


def set_resume(profile_path: str, filename: str, original_filename: str) -> CandidateProfile:
    data = _load(profile_path).model_dump(mode="json")
    data["resume_filename"] = filename
    data["resume_original_filename"] = original_filename
    data["resume_uploaded_at"] = datetime.utcnow().isoformat()
    data["updated_at"] = datetime.utcnow().isoformat()
    profile = CandidateProfile(**data)
    _save(profile_path, profile)
    return profile
