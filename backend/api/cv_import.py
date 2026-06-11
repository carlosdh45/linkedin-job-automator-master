"""
CV import endpoints. All processing is local-only — no external APIs, no AI.
Resume profile is only updated after an explicit POST /apply-import call.
"""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends

from backend.config import (
    get_extracted_text_path,
    get_import_preview_path,
    get_profile_path,
    get_resume_profile_path,
    get_uploads_path,
)
from backend.models.cv_import import (
    CVImportApplyRequest,
    CVImportPreview,
    CVImportTextRequest,
)
from backend.services import cv_extractor, cv_importer, resume_store
from backend.services.profile_store import get_profile

router = APIRouter(prefix="/resume", tags=["cv-import"])


@router.post("/extract-cv")
async def extract_cv_text(
    profile_path: str = Depends(get_profile_path),
    uploads_path: str = Depends(get_uploads_path),
    extracted_path: str = Depends(get_extracted_text_path),
) -> dict:
    """Extract text from the uploaded CV file. Local only — nothing is sent anywhere."""
    profile = get_profile(profile_path)
    filename = profile.resume_filename
    if not filename:
        return {"extracted": False, "text": "", "reason": "No CV uploaded yet."}

    # Guard against path traversal — filename is UUID-generated but verify anyway
    if "/" in filename or "\\" in filename or ".." in filename:
        return {"extracted": False, "text": "", "reason": "Invalid stored filename."}

    # Upload endpoint saves under uploads/resumes/<uuid>.<ext>
    file_path = os.path.join(uploads_path, "resumes", filename)
    if not os.path.exists(file_path):
        return {
            "extracted": False,
            "text": "",
            "reason": "The uploaded file is no longer available locally. Please upload it again.",
        }

    text = cv_extractor.extract_text(file_path)
    if text:
        cv_extractor.save_extracted_text(extracted_path, text)
    return {"extracted": bool(text), "text": text}


@router.post("/import-text", response_model=CVImportPreview)
async def import_cv_text(
    body: CVImportTextRequest,
    extracted_path: str = Depends(get_extracted_text_path),
    preview_path: str = Depends(get_import_preview_path),
) -> CVImportPreview:
    """Accept pasted or extracted CV text, run local heuristic analysis, store preview."""
    text = body.text.strip()
    if text:
        cv_extractor.save_extracted_text(extracted_path, text)
    else:
        text = cv_extractor.load_extracted_text(extracted_path)

    preview = cv_importer.parse_cv_text(text)
    cv_importer.save_preview(preview_path, preview)
    return preview


@router.get("/import-preview", response_model=CVImportPreview)
async def get_import_preview(
    preview_path: str = Depends(get_import_preview_path),
) -> CVImportPreview:
    """Return the stored import preview. Safe to call repeatedly."""
    return cv_importer.load_preview(preview_path)


@router.post("/apply-import")
async def apply_import(
    apply_opts: CVImportApplyRequest,
    preview_path: str = Depends(get_import_preview_path),
    resume_path: str = Depends(get_resume_profile_path),
) -> dict:
    """
    Apply detected fields from the import preview into the resume profile.
    This endpoint only runs when explicitly called by the user — nothing is automatic.
    """
    preview = cv_importer.load_preview(preview_path)
    if not preview.has_content:
        return {"applied": False, "reason": "No import preview available. Run /import-text first."}

    current = resume_store.get_resume_profile(resume_path)
    updates: dict = {}

    if apply_opts.apply_email and preview.detected_email and not current.email:
        updates["email"] = preview.detected_email
    if apply_opts.apply_phone and preview.detected_phone and not current.phone:
        updates["phone"] = preview.detected_phone
    if apply_opts.apply_linkedin and preview.detected_linkedin and not current.linkedin_url:
        updates["linkedin_url"] = preview.detected_linkedin
    if apply_opts.apply_github and preview.detected_github and not current.github_url:
        updates["github_url"] = preview.detected_github
    if apply_opts.apply_portfolio and preview.detected_portfolio and not current.portfolio_url:
        updates["portfolio_url"] = preview.detected_portfolio

    if apply_opts.apply_skills and preview.detected_skills:
        merged = list(dict.fromkeys(current.skills + preview.detected_skills))
        updates["skills"] = merged[:60]

    if apply_opts.apply_certifications and preview.detected_certifications:
        merged = list(dict.fromkeys(current.certifications + preview.detected_certifications))
        updates["certifications"] = merged[:30]

    if apply_opts.apply_raw_notes and preview.raw_text:
        updates["raw_cv_notes"] = preview.raw_text[:5000]

    if updates:
        resume_store.update_resume_profile(resume_path, updates)

    return {"applied": True, "fields_updated": list(updates.keys())}
