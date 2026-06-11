from fastapi import APIRouter, Depends

from backend.config import get_resume_preview_path, get_resume_profile_path
from backend.models.resume_profile import ResumeProfile, ResumeProfileUpdate
from backend.services import resume_generator, resume_store

router = APIRouter(prefix="/resume", tags=["resume"])


@router.get("/profile", response_model=ResumeProfile)
async def get_resume_profile(path: str = Depends(get_resume_profile_path)):
    return resume_store.get_resume_profile(path)


@router.put("/profile", response_model=ResumeProfile)
async def put_resume_profile(
    updates: ResumeProfileUpdate,
    path: str = Depends(get_resume_profile_path),
):
    return resume_store.update_resume_profile(path, updates.model_dump(exclude_none=True))


@router.post("/generate")
async def generate_resume(
    profile_path: str = Depends(get_resume_profile_path),
    preview_path: str = Depends(get_resume_preview_path),
):
    profile = resume_store.get_resume_profile(profile_path)
    md = resume_generator.generate_markdown(profile)
    resume_generator.save_preview(preview_path, md)
    return {"generated": True, "preview": md}


@router.get("/preview")
async def get_preview(preview_path: str = Depends(get_resume_preview_path)):
    content = resume_generator.load_preview(preview_path)
    return {"preview": content, "has_content": bool(content)}
