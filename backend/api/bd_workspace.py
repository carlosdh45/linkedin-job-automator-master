"""
BD Workspace management endpoints.
All operations are local only. No external API calls. No secrets exposed.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import JSONResponse

from backend.config import (
    get_bd_activity_path,
    get_bd_company_path,
    get_bd_deal_packet_path,
    get_bd_icp_config_path,
    get_bd_import_history_path,
    get_bd_opportunity_path,
    get_bd_outreach_path,
    get_bd_pain_point_path,
    get_bd_prospect_path,
    get_bd_recommendation_path,
    get_bd_signal_path,
)
from backend.models.bd import BDClearResult, BDRestorePreviewResult, BDWorkspaceStatus
from backend.services.bd_activity_store import list_activity, log_activity
from backend.services.bd_company_store import clear_companies, list_companies
from backend.services.bd_deal_packet_store import clear_deal_packets, list_deal_packets
from backend.services.bd_import_history_store import (
    clear_import_history,
    list_import_history,
)
from backend.services.bd_opportunity_store import clear_opportunities, list_opportunities
from backend.services.bd_outreach_store import clear_drafts, list_drafts
from backend.services.bd_pain_point_store import clear_pain_points
from backend.services.bd_prospect_store import clear_prospects, list_prospects
from backend.services.bd_recommendation_store import (
    clear_recommendations,
    list_recommendations,
)
from backend.services.bd_signal_store import clear_signals, list_signals

router = APIRouter(prefix="/bd/workspace", tags=["bd-workspace"])

_CLEAR_ALL_CONFIRM = "CLEAR DOBRYBOT WORKSPACE"


def _icp_configured(icp_path: str) -> bool:
    p = Path(icp_path)
    if not p.exists():
        return False
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        return bool(data.get("target_industries") or data.get("target_roles"))
    except Exception:
        return False


def _health_warnings(companies, prospects, signals, opportunities, drafts, recommendations, icp_ok):
    warnings = []
    if not icp_ok:
        warnings.append("ICP not configured — signal scoring and recommendations may be generic")
    no_domain = [c for c in companies if not c.domain]
    if no_domain:
        warnings.append(f"{len(no_domain)} companies missing domain")
    no_company = [p for p in prospects if not p.company_name]
    if no_company:
        warnings.append(f"{len(no_company)} prospects missing company name")
    unevaluated = [s for s in signals if not s.evaluated]
    if unevaluated:
        warnings.append(f"{len(unevaluated)} signals not yet evaluated")
    new_recs = [r for r in recommendations if r.status == "new"]
    if new_recs:
        warnings.append(f"{len(new_recs)} recommendations pending review")
    unreviewed_drafts = [d for d in drafts if d.status == "draft"]
    if unreviewed_drafts:
        warnings.append(f"{len(unreviewed_drafts)} outreach drafts not yet reviewed")
    return warnings


@router.get("/status", response_model=BDWorkspaceStatus)
def get_workspace_status(
    company_path: str = Depends(get_bd_company_path),
    prospect_path: str = Depends(get_bd_prospect_path),
    signal_path: str = Depends(get_bd_signal_path),
    opportunity_path: str = Depends(get_bd_opportunity_path),
    deal_packet_path: str = Depends(get_bd_deal_packet_path),
    outreach_path: str = Depends(get_bd_outreach_path),
    activity_path: str = Depends(get_bd_activity_path),
    icp_path: str = Depends(get_bd_icp_config_path),
    recommendation_path: str = Depends(get_bd_recommendation_path),
    import_history_path: str = Depends(get_bd_import_history_path),
):
    companies = list_companies(company_path)
    prospects = list_prospects(prospect_path)
    signals = list_signals(signal_path)
    opportunities = list_opportunities(opportunity_path)
    deal_packets = list_deal_packets(deal_packet_path)
    drafts = list_drafts(outreach_path)
    recommendations = list_recommendations(recommendation_path)
    activities = list_activity(activity_path, limit=200)
    import_history = list_import_history(import_history_path)
    icp_ok = _icp_configured(icp_path)

    last_import_date = None
    import_acts = [a for a in activities if a.action == "csv_import_committed"]
    if import_acts:
        last_import_date = import_acts[0].created_at

    last_activity_date = activities[0].created_at if activities else None

    imported_companies = sum(e.imported_count for e in import_history if e.import_type == "companies")
    imported_prospects = sum(e.imported_count for e in import_history if e.import_type == "prospects")
    imported_signals = sum(e.imported_count for e in import_history if e.import_type == "signals")

    warnings = _health_warnings(
        companies, prospects, signals, opportunities, drafts, recommendations, icp_ok
    )

    return BDWorkspaceStatus(
        total_companies=len(companies),
        total_prospects=len(prospects),
        total_signals=len(signals),
        total_opportunities=len(opportunities),
        total_deal_packets=len(deal_packets),
        total_outreach_drafts=len(drafts),
        total_recommendations=len(recommendations),
        imported_companies=imported_companies,
        imported_prospects=imported_prospects,
        imported_signals=imported_signals,
        last_import_date=last_import_date,
        last_activity_date=last_activity_date,
        icp_configured=icp_ok,
        data_health_warnings=warnings,
    )


@router.get("/backup")
def backup_workspace(
    company_path: str = Depends(get_bd_company_path),
    prospect_path: str = Depends(get_bd_prospect_path),
    signal_path: str = Depends(get_bd_signal_path),
    pain_point_path: str = Depends(get_bd_pain_point_path),
    opportunity_path: str = Depends(get_bd_opportunity_path),
    deal_packet_path: str = Depends(get_bd_deal_packet_path),
    outreach_path: str = Depends(get_bd_outreach_path),
    activity_path: str = Depends(get_bd_activity_path),
    icp_path: str = Depends(get_bd_icp_config_path),
    recommendation_path: str = Depends(get_bd_recommendation_path),
    import_history_path: str = Depends(get_bd_import_history_path),
):
    """
    Export a full local workspace backup as JSON.
    No secrets, no .env values, no tokens. Local only.
    """
    def _read_list(path: str):
        p = Path(path)
        if not p.exists():
            return []
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _read_obj(path: str):
        p = Path(path)
        if not p.exists():
            return {}
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    backup = {
        "dobrybot_workspace_backup": True,
        "backup_created_at": datetime.utcnow().isoformat(),
        "local_only": True,
        "safety_notice": (
            "This backup contains local workspace data only. "
            "No secrets or credentials are included."
        ),
        "companies": _read_list(company_path),
        "prospects": _read_list(prospect_path),
        "signals": _read_list(signal_path),
        "pain_points": _read_list(pain_point_path),
        "opportunities": _read_list(opportunity_path),
        "deal_packets": _read_list(deal_packet_path),
        "outreach_drafts": _read_list(outreach_path),
        "recommendations": _read_list(recommendation_path),
        "icp_config": _read_obj(icp_path),
        "activity_log": _read_list(activity_path),
        "import_history": _read_list(import_history_path),
    }

    log_activity(activity_path, {
        "entity_type": "workspace",
        "entity_id": "backup",
        "action": "backup_created",
        "description": "Workspace backup exported locally",
        "metadata": {"local_only": True},
    })

    return JSONResponse(
        content=backup,
        headers={"Content-Disposition": 'attachment; filename="dobrybot_workspace_backup.json"'},
    )


@router.post("/restore-preview", response_model=BDRestorePreviewResult)
def restore_preview(backup: Dict[str, Any] = Body(...)):
    """
    Validate a workspace backup and preview what would be restored.
    No data is persisted or modified.
    """
    warnings = []

    if not backup.get("dobrybot_workspace_backup"):
        warnings.append(
            "Missing 'dobrybot_workspace_backup' key — file may not be a valid DobryBot backup"
        )

    def _count(key: str) -> int:
        val = backup.get(key, [])
        if not isinstance(val, list):
            warnings.append(f"'{key}' is not a list in the backup — skipped")
            return 0
        return len(val)

    companies_count = _count("companies")
    prospects_count = _count("prospects")
    signals_count = _count("signals")
    opportunities_count = _count("opportunities")
    deal_packets_count = _count("deal_packets")
    outreach_drafts_count = _count("outreach_drafts")
    recommendations_count = _count("recommendations")

    total = (
        companies_count + prospects_count + signals_count +
        opportunities_count + deal_packets_count +
        outreach_drafts_count + recommendations_count
    )
    if total == 0:
        warnings.append("Backup appears empty — no records found to restore")

    return BDRestorePreviewResult(
        companies_count=companies_count,
        prospects_count=prospects_count,
        signals_count=signals_count,
        opportunities_count=opportunities_count,
        deal_packets_count=deal_packets_count,
        outreach_drafts_count=outreach_drafts_count,
        recommendations_count=recommendations_count,
        warnings=warnings,
        valid=total > 0,
    )


@router.post("/clear-all", response_model=BDClearResult)
def clear_all_workspace(
    confirm_text: str = Body(..., embed=True),
    company_path: str = Depends(get_bd_company_path),
    prospect_path: str = Depends(get_bd_prospect_path),
    signal_path: str = Depends(get_bd_signal_path),
    pain_point_path: str = Depends(get_bd_pain_point_path),
    opportunity_path: str = Depends(get_bd_opportunity_path),
    deal_packet_path: str = Depends(get_bd_deal_packet_path),
    outreach_path: str = Depends(get_bd_outreach_path),
    activity_path: str = Depends(get_bd_activity_path),
    recommendation_path: str = Depends(get_bd_recommendation_path),
    import_history_path: str = Depends(get_bd_import_history_path),
):
    """
    Clear all BD workspace data. Requires exact confirmation text.
    Irreversible. Local only. Activity log is preserved.
    """
    if confirm_text != _CLEAR_ALL_CONFIRM:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Confirmation text must be exactly: '{_CLEAR_ALL_CONFIRM}'. "
                f"Received: '{confirm_text}'"
            ),
        )

    total_before = (
        len(list_companies(company_path)) +
        len(list_prospects(prospect_path)) +
        len(list_signals(signal_path)) +
        len(list_opportunities(opportunity_path)) +
        len(list_deal_packets(deal_packet_path)) +
        len(list_drafts(outreach_path)) +
        len(list_recommendations(recommendation_path))
    )

    clear_companies(company_path)
    clear_prospects(prospect_path)
    clear_signals(signal_path)
    clear_pain_points(pain_point_path)
    clear_opportunities(opportunity_path)
    clear_deal_packets(deal_packet_path)
    clear_drafts(outreach_path)
    clear_recommendations(recommendation_path)
    clear_import_history(import_history_path)

    log_activity(activity_path, {
        "entity_type": "workspace",
        "entity_id": "clear-all",
        "action": "workspace_cleared",
        "description": f"All BD workspace data cleared. {total_before} records removed.",
        "metadata": {"records_removed": total_before, "local_only": True},
    })

    return BDClearResult(
        cleared=[
            "companies", "prospects", "signals", "pain_points",
            "opportunities", "deal_packets", "outreach_drafts",
            "recommendations", "import_history",
        ],
        records_removed=total_before,
    )


@router.post("/clear-demo")
def clear_demo_unavailable():
    """
    Per-record source tracking is planned for Phase 17.
    Use POST /api/bd/workspace/clear-all with confirmation to clear all workspace data.
    """
    raise HTTPException(
        status_code=400,
        detail=(
            "Source-level clearing requires per-record source tracking (Phase 17). "
            "Use POST /api/bd/workspace/clear-all with confirm_text='CLEAR DOBRYBOT WORKSPACE'."
        ),
    )


@router.post("/clear-imported")
def clear_imported_unavailable():
    """
    Per-record source tracking is planned for Phase 17.
    Use POST /api/bd/workspace/clear-all with confirmation to clear all workspace data.
    """
    raise HTTPException(
        status_code=400,
        detail=(
            "Source-level clearing requires per-record source tracking (Phase 17). "
            "Use POST /api/bd/workspace/clear-all with confirm_text='CLEAR DOBRYBOT WORKSPACE'."
        ),
    )
