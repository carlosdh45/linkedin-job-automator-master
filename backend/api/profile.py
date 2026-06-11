import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from backend.config import get_profile_path, get_uploads_path
from backend.models.profile import CandidateProfile, ProfileUpdate
from backend.services.profile_store import get_profile, set_resume, update_profile

router = APIRouter(tags=["profile"])

_ALLOWED_SUFFIXES = {".pdf", ".docx"}
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB


@router.get("/profile", response_model=CandidateProfile)
async def read_profile(profile_path: str = Depends(get_profile_path)):
    return get_profile(profile_path)


@router.put("/profile", response_model=CandidateProfile)
async def write_profile(
    updates: ProfileUpdate,
    profile_path: str = Depends(get_profile_path),
):
    return update_profile(profile_path, updates.model_dump(exclude_none=True))


@router.post("/profile/resume")
async def upload_resume(
    file: UploadFile = File(...),
    profile_path: str = Depends(get_profile_path),
    uploads_path: str = Depends(get_uploads_path),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=422,
            detail="Unsupported file type. Only PDF and DOCX are accepted.",
        )
    content = await file.read()
    if len(content) > _MAX_BYTES:
        raise HTTPException(
            status_code=422,
            detail="File too large. Maximum allowed size is 5 MB.",
        )
    resume_dir = Path(uploads_path) / "resumes"
    resume_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    (resume_dir / stored_name).write_bytes(content)
    profile = set_resume(profile_path, stored_name, file.filename or stored_name)
    return {
        "uploaded": True,
        "filename": stored_name,
        "original_filename": file.filename,
        "profile": profile.model_dump(mode="json"),
    }


@router.get("/profile/resume")
async def get_resume_info(profile_path: str = Depends(get_profile_path)):
    profile = get_profile(profile_path)
    if not profile.resume_filename:
        raise HTTPException(status_code=404, detail="No resume uploaded yet.")
    return {
        "filename": profile.resume_filename,
        "original_filename": profile.resume_original_filename,
        "uploaded_at": profile.resume_uploaded_at,
    }
