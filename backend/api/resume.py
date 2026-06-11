from fastapi import APIRouter, Depends

from backend.config import get_resume_preview_path, get_resume_profile_path
from backend.models.resume_profile import ResumeProfile, ResumeProfileUpdate
from backend.services import resume_generator, resume_store

router = APIRouter(prefix="/resume", tags=["resume"])


def _compute_quality(profile: ResumeProfile) -> dict:
    """Compute local quality/ATS metrics from a resume profile. No external calls."""
    score = 0
    missing: list[str] = []
    sections: dict[str, bool] = {}

    def _check(field_name: str, value: bool, pts: int, label: str) -> None:
        sections[field_name] = value
        if value:
            score_list.append(pts)
        else:
            missing.append(label)

    score_list: list[int] = []
    _check("headline",   bool(profile.headline),              15, "Professional headline")
    _check("summary",    bool(profile.professional_summary),  15, "Professional summary")
    _check("email",      bool(profile.email),                 10, "Email address")
    _check("skills",     bool(profile.skills),                15, "Skills section")
    _check("experience", bool(profile.experience_items),      20, "Work experience")
    _check("education",  bool(profile.education_items),       10, "Education")
    _check("linkedin",   bool(profile.linkedin_url),          10, "LinkedIn URL")

    completeness = min(sum(score_list), 100)

    has_bullets = any(bool(e.bullets) for e in profile.experience_items) if profile.experience_items else False

    ats_checks = [
        {"label": "Professional headline present",        "passed": bool(profile.headline)},
        {"label": "Contact info complete (email + phone)", "passed": bool(profile.email and profile.phone)},
        {"label": "Skills section present",               "passed": bool(profile.skills)},
        {"label": "At least 5 skills listed",             "passed": len(profile.skills) >= 5},
        {"label": "Work experience included",             "passed": bool(profile.experience_items)},
        {"label": "Experience has bullet points",         "passed": has_bullets},
        {"label": "Education section present",            "passed": bool(profile.education_items)},
        {"label": "LinkedIn profile linked",              "passed": bool(profile.linkedin_url)},
    ]
    ats_score = sum(1 for c in ats_checks if c["passed"])

    return {
        "completeness_score": completeness,
        "ats_score": ats_score,
        "ats_total": len(ats_checks),
        "sections": sections,
        "missing_sections": missing,
        "ats_checks": ats_checks,
    }


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
    tone: str = "professional",
    profile_path: str = Depends(get_resume_profile_path),
    preview_path: str = Depends(get_resume_preview_path),
):
    profile = resume_store.get_resume_profile(profile_path)
    md = resume_generator.generate_markdown(profile, tone=tone)
    resume_generator.save_preview(preview_path, md)
    return {"generated": True, "preview": md, "tone": tone}


@router.get("/preview")
async def get_preview(preview_path: str = Depends(get_resume_preview_path)):
    content = resume_generator.load_preview(preview_path)
    return {"preview": content, "has_content": bool(content)}


@router.get("/quality")
async def get_resume_quality(path: str = Depends(get_resume_profile_path)):
    """Return local quality and ATS-readiness metrics. No external calls."""
    profile = resume_store.get_resume_profile(path)
    return _compute_quality(profile)
