"""
BD OS CSV import endpoints. Local only. No external API calls.
All data is parsed and stored on-disk. No enrichment, no scraping.
"""
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse
from typing import List

from backend.config import (
    get_bd_company_path, get_bd_prospect_path, get_bd_signal_path,
    get_bd_activity_path, get_bd_import_history_path,
)
from backend.models.bd import BDImportResult, BDImportHistoryEntry
from backend.services.bd_csv_import import (
    import_companies_csv, import_prospects_csv, import_signals_csv,
    COMPANIES_TEMPLATE, PROSPECTS_TEMPLATE, SIGNALS_TEMPLATE,
)
from backend.services.bd_activity_store import log_activity
from backend.services.bd_import_history_store import (
    list_import_history, get_import_history_entry, record_import,
)

router = APIRouter(prefix="/bd/import", tags=["bd-import"])

_ALLOWED_TYPE = "text/csv"
_ALLOWED_EXT = ".csv"


def _validate_upload(file: UploadFile) -> None:
    if not file.filename or not file.filename.lower().endswith(_ALLOWED_EXT):
        raise HTTPException(
            status_code=400,
            detail="Only .csv files are accepted. No other file types are processed.",
        )


@router.get("/history", response_model=List[BDImportHistoryEntry])
def get_import_history(
    import_history_path: str = Depends(get_bd_import_history_path),
):
    """Return all committed CSV import records, newest first."""
    return list_import_history(import_history_path)


@router.get("/history/{entry_id}", response_model=BDImportHistoryEntry)
def get_import_history_by_id(
    entry_id: str,
    import_history_path: str = Depends(get_bd_import_history_path),
):
    entry = get_import_history_entry(import_history_path, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Import history entry '{entry_id}' not found")
    return entry


@router.post("/companies-csv", response_model=BDImportResult)
async def import_companies(
    file: UploadFile = File(...),
    dry_run: bool = Query(default=True, description="Preview without committing"),
    company_path: str = Depends(get_bd_company_path),
    activity_path: str = Depends(get_bd_activity_path),
    import_history_path: str = Depends(get_bd_import_history_path),
):
    """
    Import companies from a CSV file. Local only — no external API calls.
    Pass dry_run=false to commit the import.
    """
    _validate_upload(file)
    content = await file.read()
    result = import_companies_csv(content, company_path, dry_run=dry_run)
    if not dry_run and result.imported_count > 0:
        log_activity(activity_path, {
            "entity_type": "import",
            "entity_id": "companies-csv",
            "action": "csv_import_committed",
            "description": (
                f"CSV import committed: {result.imported_count} companies imported, "
                f"{result.duplicate_count} duplicates skipped"
            ),
            "metadata": {
                "import_type": "companies",
                "imported_count": result.imported_count,
                "duplicate_count": result.duplicate_count,
                "skipped_count": result.skipped_count,
            },
        })
        record_import(import_history_path, {
            "import_type": "companies",
            "filename": file.filename or "companies.csv",
            "imported_count": result.imported_count,
            "skipped_count": result.skipped_count,
            "duplicate_count": result.duplicate_count,
            "error_count": result.error_count,
        })
    return result


@router.post("/prospects-csv", response_model=BDImportResult)
async def import_prospects(
    file: UploadFile = File(...),
    dry_run: bool = Query(default=True, description="Preview without committing"),
    prospect_path: str = Depends(get_bd_prospect_path),
    company_path: str = Depends(get_bd_company_path),
    activity_path: str = Depends(get_bd_activity_path),
    import_history_path: str = Depends(get_bd_import_history_path),
):
    """
    Import prospects from a CSV file. Local only — no external API calls.
    Pass dry_run=false to commit the import.
    """
    _validate_upload(file)
    content = await file.read()
    result = import_prospects_csv(content, prospect_path, company_path, dry_run=dry_run)
    if not dry_run and result.imported_count > 0:
        log_activity(activity_path, {
            "entity_type": "import",
            "entity_id": "prospects-csv",
            "action": "csv_import_committed",
            "description": (
                f"CSV import committed: {result.imported_count} prospects imported, "
                f"{result.duplicate_count} duplicates skipped"
            ),
            "metadata": {
                "import_type": "prospects",
                "imported_count": result.imported_count,
                "duplicate_count": result.duplicate_count,
                "skipped_count": result.skipped_count,
            },
        })
        record_import(import_history_path, {
            "import_type": "prospects",
            "filename": file.filename or "prospects.csv",
            "imported_count": result.imported_count,
            "skipped_count": result.skipped_count,
            "duplicate_count": result.duplicate_count,
            "error_count": result.error_count,
        })
    return result


@router.post("/signals-csv", response_model=BDImportResult)
async def import_signals(
    file: UploadFile = File(...),
    dry_run: bool = Query(default=True, description="Preview without committing"),
    signal_path: str = Depends(get_bd_signal_path),
    company_path: str = Depends(get_bd_company_path),
    activity_path: str = Depends(get_bd_activity_path),
    import_history_path: str = Depends(get_bd_import_history_path),
):
    """
    Import signals from a CSV file. Local only — no external API calls.
    Pass dry_run=false to commit the import.
    """
    _validate_upload(file)
    content = await file.read()
    result = import_signals_csv(content, signal_path, company_path, dry_run=dry_run)
    if not dry_run and result.imported_count > 0:
        log_activity(activity_path, {
            "entity_type": "import",
            "entity_id": "signals-csv",
            "action": "csv_import_committed",
            "description": (
                f"CSV import committed: {result.imported_count} signals imported, "
                f"{result.duplicate_count} duplicates skipped"
            ),
            "metadata": {
                "import_type": "signals",
                "imported_count": result.imported_count,
                "duplicate_count": result.duplicate_count,
                "skipped_count": result.skipped_count,
            },
        })
        record_import(import_history_path, {
            "import_type": "signals",
            "filename": file.filename or "signals.csv",
            "imported_count": result.imported_count,
            "skipped_count": result.skipped_count,
            "duplicate_count": result.duplicate_count,
            "error_count": result.error_count,
        })
    return result


@router.get("/templates", response_class=PlainTextResponse)
def get_template(
    type: str = Query(..., description="Template type: companies | prospects | signals"),
):
    """
    Download a CSV template. All templates are generated locally.
    No external calls.
    """
    templates = {
        "companies": (COMPANIES_TEMPLATE, "companies_template.csv"),
        "prospects": (PROSPECTS_TEMPLATE, "prospects_template.csv"),
        "signals": (SIGNALS_TEMPLATE, "signals_template.csv"),
    }
    if type not in templates:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown template type '{type}'. Valid: companies, prospects, signals",
        )
    content, filename = templates[type]
    return PlainTextResponse(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
