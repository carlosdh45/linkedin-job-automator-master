"""
BD OS CSV import endpoints. Local only. No external API calls.
All data is parsed and stored on-disk. No enrichment, no scraping.
"""
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from backend.config import (
    get_bd_company_path, get_bd_prospect_path, get_bd_signal_path,
    get_bd_activity_path,
)
from backend.models.bd import BDImportResult
from backend.services.bd_csv_import import (
    import_companies_csv, import_prospects_csv, import_signals_csv,
    COMPANIES_TEMPLATE, PROSPECTS_TEMPLATE, SIGNALS_TEMPLATE,
)
from backend.services.bd_activity_store import log_activity
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/bd/import", tags=["bd-import"])

_ALLOWED_TYPE = "text/csv"
_ALLOWED_EXT = ".csv"


def _validate_upload(file: UploadFile) -> None:
    if not file.filename or not file.filename.lower().endswith(_ALLOWED_EXT):
        raise HTTPException(
            status_code=400,
            detail="Only .csv files are accepted. No other file types are processed.",
        )


@router.post("/companies-csv", response_model=BDImportResult)
async def import_companies(
    file: UploadFile = File(...),
    dry_run: bool = Query(default=True, description="Preview without committing"),
    company_path: str = Depends(get_bd_company_path),
    activity_path: str = Depends(get_bd_activity_path),
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
    return result


@router.post("/prospects-csv", response_model=BDImportResult)
async def import_prospects(
    file: UploadFile = File(...),
    dry_run: bool = Query(default=True, description="Preview without committing"),
    prospect_path: str = Depends(get_bd_prospect_path),
    company_path: str = Depends(get_bd_company_path),
    activity_path: str = Depends(get_bd_activity_path),
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
    return result


@router.post("/signals-csv", response_model=BDImportResult)
async def import_signals(
    file: UploadFile = File(...),
    dry_run: bool = Query(default=True, description="Preview without committing"),
    signal_path: str = Depends(get_bd_signal_path),
    company_path: str = Depends(get_bd_company_path),
    activity_path: str = Depends(get_bd_activity_path),
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
