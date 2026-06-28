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
from backend.models.bd import (
    BDClearResult, BDRestorePreviewResult, BDRestoreResult, BDWorkspaceStatus,
    BDCompany, BDProspect, BDSignal, BDPainPoint,
    BDOpportunity, BDDealPacket, BDOutreachDraft, BDRecommendation,
)
from backend.services.bd_activity_store import list_activity, log_activity
from backend.services.bd_import_history_store import clear_import_history, list_import_history
from backend.services.bd_icp_store import save_icp_config, load_icp_config
from backend.services import (
    bd_company_store, bd_prospect_store, bd_signal_store, bd_pain_point_store,
    bd_opportunity_store, bd_deal_packet_store, bd_outreach_store, bd_recommendation_store,
)

router = APIRouter(prefix="/bd/workspace", tags=["bd-workspace"])

_CLEAR_ALL_CONFIRM = "CLEAR DOBRYBOT WORKSPACE"
_CLEAR_DEMO_CONFIRM = "CLEAR DEMO DATA"
_CLEAR_IMPORTED_CONFIRM = "CLEAR IMPORTED DATA"
_RESTORE_CONFIRM = "RESTORE DOBRYBOT WORKSPACE"


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


def _source_breakdown(companies, prospects, signals, pain_points, opportunities, deal_packets, drafts, recommendations):
    counts: Dict[str, int] = {}

    def _tally(items, field="source"):
        for item in items:
            src = getattr(item, field, None) or "legacy"
            counts[src] = counts.get(src, 0) + 1

    _tally(companies)
    _tally(prospects)
    _tally(signals, "data_source")
    _tally(pain_points)
    _tally(opportunities)
    _tally(deal_packets)
    _tally(drafts)
    _tally(recommendations)
    return counts


@router.get("/status", response_model=BDWorkspaceStatus)
def get_workspace_status(
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
    companies = bd_company_store.list_companies(company_path)
    prospects = bd_prospect_store.list_prospects(prospect_path)
    signals = bd_signal_store.list_signals(signal_path)
    pain_points = bd_pain_point_store.list_pain_points(pain_point_path)
    opportunities = bd_opportunity_store.list_opportunities(opportunity_path)
    deal_packets = bd_deal_packet_store.list_deal_packets(deal_packet_path)
    drafts = bd_outreach_store.list_drafts(outreach_path)
    recommendations = bd_recommendation_store.list_recommendations(recommendation_path)
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

    breakdown = _source_breakdown(
        companies, prospects, signals, pain_points, opportunities, deal_packets, drafts, recommendations
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
        source_breakdown=breakdown,
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
    pain_points_count = _count("pain_points")
    opportunities_count = _count("opportunities")
    deal_packets_count = _count("deal_packets")
    outreach_drafts_count = _count("outreach_drafts")
    recommendations_count = _count("recommendations")

    total = (
        companies_count + prospects_count + signals_count + pain_points_count +
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


@router.post("/restore", response_model=BDRestoreResult)
def restore_workspace(
    backup: Dict[str, Any] = Body(...),
    confirm_text: str = Body(...),
    dry_run: bool = Body(False),
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
):
    """
    Restore workspace from a backup. Use dry_run=true first to preview.
    Requires exact confirmation text. All data is local only.
    """
    if not dry_run and confirm_text != _RESTORE_CONFIRM:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Confirmation text must be exactly: '{_RESTORE_CONFIRM}'. "
                f"Received: '{confirm_text}'"
            ),
        )

    if not backup.get("dobrybot_workspace_backup"):
        raise HTTPException(
            status_code=400,
            detail="Invalid backup: missing 'dobrybot_workspace_backup' marker",
        )

    warnings = []

    def _parse(key: str, model):
        raw = backup.get(key, [])
        if not isinstance(raw, list):
            warnings.append(f"'{key}' is not a list — skipped")
            return []
        result = []
        for item in raw:
            try:
                result.append(model(**item))
            except Exception as exc:
                warnings.append(f"Skipped malformed {key} record: {exc}")
        return result

    companies = _parse("companies", BDCompany)
    prospects = _parse("prospects", BDProspect)
    signals = _parse("signals", BDSignal)
    pain_points = _parse("pain_points", BDPainPoint)
    opportunities = _parse("opportunities", BDOpportunity)
    deal_packets = _parse("deal_packets", BDDealPacket)
    outreach_drafts = _parse("outreach_drafts", BDOutreachDraft)
    recommendations = _parse("recommendations", BDRecommendation)

    if not dry_run:
        bd_company_store.replace_all(company_path, companies)
        bd_prospect_store.replace_all(prospect_path, prospects)
        bd_signal_store.replace_all(signal_path, signals)
        bd_pain_point_store.replace_all(pain_point_path, pain_points)
        bd_opportunity_store.replace_all(opportunity_path, opportunities)
        bd_deal_packet_store.replace_all(deal_packet_path, deal_packets)
        bd_outreach_store.replace_all(outreach_path, outreach_drafts)
        bd_recommendation_store.replace_all(recommendation_path, recommendations)

        icp_raw = backup.get("icp_config")
        if isinstance(icp_raw, dict) and icp_raw:
            try:
                from backend.models.bd import BDICPConfig
                icp = BDICPConfig(**icp_raw)
                save_icp_config(icp_path, icp)
            except Exception as exc:
                warnings.append(f"ICP config restore skipped: {exc}")

        log_activity(activity_path, {
            "entity_type": "workspace",
            "entity_id": "restore",
            "action": "workspace_restored",
            "description": (
                f"Workspace restored from backup: {len(companies)} companies, "
                f"{len(prospects)} prospects, {len(signals)} signals"
            ),
            "metadata": {
                "companies": len(companies),
                "prospects": len(prospects),
                "signals": len(signals),
                "local_only": True,
            },
        })

    return BDRestoreResult(
        dry_run=dry_run,
        companies_restored=len(companies),
        prospects_restored=len(prospects),
        signals_restored=len(signals),
        pain_points_restored=len(pain_points),
        opportunities_restored=len(opportunities),
        deal_packets_restored=len(deal_packets),
        outreach_drafts_restored=len(outreach_drafts),
        recommendations_restored=len(recommendations),
        warnings=warnings,
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
        len(bd_company_store.list_companies(company_path)) +
        len(bd_prospect_store.list_prospects(prospect_path)) +
        len(bd_signal_store.list_signals(signal_path)) +
        len(bd_opportunity_store.list_opportunities(opportunity_path)) +
        len(bd_deal_packet_store.list_deal_packets(deal_packet_path)) +
        len(bd_outreach_store.list_drafts(outreach_path)) +
        len(bd_recommendation_store.list_recommendations(recommendation_path))
    )

    bd_company_store.clear_companies(company_path)
    bd_prospect_store.clear_prospects(prospect_path)
    bd_signal_store.clear_signals(signal_path)
    bd_pain_point_store.clear_pain_points(pain_point_path)
    bd_opportunity_store.clear_opportunities(opportunity_path)
    bd_deal_packet_store.clear_deal_packets(deal_packet_path)
    bd_outreach_store.clear_drafts(outreach_path)
    bd_recommendation_store.clear_recommendations(recommendation_path)
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


@router.post("/clear-demo", response_model=BDClearResult)
def clear_demo_data(
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
):
    """
    Clear only records with source='demo'. Preserves imported, manual, and generated records.
    Requires exact confirmation text.
    """
    if confirm_text != _CLEAR_DEMO_CONFIRM:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Confirmation text must be exactly: '{_CLEAR_DEMO_CONFIRM}'. "
                f"Received: '{confirm_text}'"
            ),
        )

    removed = 0

    def _filter_and_save(store, list_fn, replace_fn, path, source_field="source"):
        nonlocal removed
        items = list_fn(path)
        keep = [i for i in items if getattr(i, source_field, None) != "demo"]
        removed += len(items) - len(keep)
        replace_fn(path, keep)

    _filter_and_save(bd_company_store, bd_company_store.list_companies, bd_company_store.replace_all, company_path)
    _filter_and_save(bd_prospect_store, bd_prospect_store.list_prospects, bd_prospect_store.replace_all, prospect_path)
    _filter_and_save(bd_signal_store, bd_signal_store.list_signals, bd_signal_store.replace_all, signal_path, "data_source")
    _filter_and_save(bd_pain_point_store, bd_pain_point_store.list_pain_points, bd_pain_point_store.replace_all, pain_point_path)
    _filter_and_save(bd_opportunity_store, bd_opportunity_store.list_opportunities, bd_opportunity_store.replace_all, opportunity_path)
    _filter_and_save(bd_deal_packet_store, bd_deal_packet_store.list_deal_packets, bd_deal_packet_store.replace_all, deal_packet_path)
    _filter_and_save(bd_outreach_store, bd_outreach_store.list_drafts, bd_outreach_store.replace_all, outreach_path)
    _filter_and_save(bd_recommendation_store, bd_recommendation_store.list_recommendations, bd_recommendation_store.replace_all, recommendation_path)

    log_activity(activity_path, {
        "entity_type": "workspace",
        "entity_id": "clear-demo",
        "action": "demo_data_cleared",
        "description": f"Demo data cleared. {removed} demo records removed.",
        "metadata": {"records_removed": removed, "source": "demo", "local_only": True},
    })

    return BDClearResult(
        cleared=["demo records across all entity types"],
        records_removed=removed,
    )


@router.post("/clear-imported", response_model=BDClearResult)
def clear_imported_data(
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
):
    """
    Clear only records with source='imported'. Preserves demo, manual, and generated records.
    Requires exact confirmation text.
    """
    if confirm_text != _CLEAR_IMPORTED_CONFIRM:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Confirmation text must be exactly: '{_CLEAR_IMPORTED_CONFIRM}'. "
                f"Received: '{confirm_text}'"
            ),
        )

    removed = 0

    def _filter_and_save(store, list_fn, replace_fn, path, source_field="source"):
        nonlocal removed
        items = list_fn(path)
        keep = [i for i in items if getattr(i, source_field, None) != "imported"]
        removed += len(items) - len(keep)
        replace_fn(path, keep)

    _filter_and_save(bd_company_store, bd_company_store.list_companies, bd_company_store.replace_all, company_path)
    _filter_and_save(bd_prospect_store, bd_prospect_store.list_prospects, bd_prospect_store.replace_all, prospect_path)
    _filter_and_save(bd_signal_store, bd_signal_store.list_signals, bd_signal_store.replace_all, signal_path, "data_source")
    _filter_and_save(bd_pain_point_store, bd_pain_point_store.list_pain_points, bd_pain_point_store.replace_all, pain_point_path)
    _filter_and_save(bd_opportunity_store, bd_opportunity_store.list_opportunities, bd_opportunity_store.replace_all, opportunity_path)
    _filter_and_save(bd_deal_packet_store, bd_deal_packet_store.list_deal_packets, bd_deal_packet_store.replace_all, deal_packet_path)
    _filter_and_save(bd_outreach_store, bd_outreach_store.list_drafts, bd_outreach_store.replace_all, outreach_path)
    _filter_and_save(bd_recommendation_store, bd_recommendation_store.list_recommendations, bd_recommendation_store.replace_all, recommendation_path)

    log_activity(activity_path, {
        "entity_type": "workspace",
        "entity_id": "clear-imported",
        "action": "imported_data_cleared",
        "description": f"Imported data cleared. {removed} imported records removed.",
        "metadata": {"records_removed": removed, "source": "imported", "local_only": True},
    })

    return BDClearResult(
        cleared=["imported records across all entity types"],
        records_removed=removed,
    )
