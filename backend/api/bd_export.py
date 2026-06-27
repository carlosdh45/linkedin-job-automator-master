"""
BD OS export endpoints. All exports are generated locally.
No external API calls. No secrets included.
"""
import csv
import io
import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse

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
from backend.services.bd_activity_store import log_activity
from backend.services.bd_company_store import list_companies
from backend.services.bd_opportunity_store import list_opportunities
from backend.services.bd_prospect_store import list_prospects
from backend.services.bd_signal_store import list_signals

router = APIRouter(prefix="/bd/export", tags=["bd-export"])

_SAFETY_NOTICE = "Exported locally. No external APIs called. No secrets included."


def _csv_stream(rows: list[dict], fieldnames: list[str], filename: str) -> StreamingResponse:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/companies.csv")
def export_companies(
    company_path: str = Depends(get_bd_company_path),
    activity_path: str = Depends(get_bd_activity_path),
):
    companies = list_companies(company_path)
    rows = [
        {
            "id": c.id,
            "name": c.name,
            "domain": c.domain or "",
            "industry": c.industry or "",
            "size_estimate": c.size_estimate or "",
            "status": c.status,
            "icp_match": str(c.icp_match),
            "opportunity_score": c.opportunity_score,
            "score_label": c.score_label,
            "created_at": c.created_at,
        }
        for c in companies
    ]
    log_activity(activity_path, {
        "entity_type": "workspace",
        "entity_id": "export",
        "action": "export_created",
        "description": f"Companies CSV exported ({len(rows)} records)",
        "metadata": {"export_type": "companies", "count": len(rows), "local_only": True},
    })
    return _csv_stream(
        rows,
        ["id", "name", "domain", "industry", "size_estimate", "status",
         "icp_match", "opportunity_score", "score_label", "created_at"],
        "dobrybot_companies.csv",
    )


@router.get("/prospects.csv")
def export_prospects(
    prospect_path: str = Depends(get_bd_prospect_path),
    activity_path: str = Depends(get_bd_activity_path),
):
    prospects = list_prospects(prospect_path)
    rows = [
        {
            "id": p.id,
            "name": p.name,
            "company_name": p.company_name,
            "title": p.title or "",
            "seniority": p.seniority or "",
            "status": p.status,
            "opportunity_score": p.opportunity_score,
            "score_label": p.score_label,
            "created_at": p.created_at,
        }
        for p in prospects
    ]
    log_activity(activity_path, {
        "entity_type": "workspace",
        "entity_id": "export",
        "action": "export_created",
        "description": f"Prospects CSV exported ({len(rows)} records)",
        "metadata": {"export_type": "prospects", "count": len(rows), "local_only": True},
    })
    return _csv_stream(
        rows,
        ["id", "name", "company_name", "title", "seniority", "status",
         "opportunity_score", "score_label", "created_at"],
        "dobrybot_prospects.csv",
    )


@router.get("/signals.csv")
def export_signals(
    signal_path: str = Depends(get_bd_signal_path),
    activity_path: str = Depends(get_bd_activity_path),
):
    signals = list_signals(signal_path)
    rows = [
        {
            "id": s.id,
            "company_name": s.company_name,
            "signal_type": s.signal_type,
            "summary": s.summary,
            "relevance_score": s.relevance_score,
            "signal_strength": s.signal_strength,
            "evaluated": str(s.evaluated),
            "detected_at": s.detected_at,
            "created_at": s.created_at,
        }
        for s in signals
    ]
    log_activity(activity_path, {
        "entity_type": "workspace",
        "entity_id": "export",
        "action": "export_created",
        "description": f"Signals CSV exported ({len(rows)} records)",
        "metadata": {"export_type": "signals", "count": len(rows), "local_only": True},
    })
    return _csv_stream(
        rows,
        ["id", "company_name", "signal_type", "summary", "relevance_score",
         "signal_strength", "evaluated", "detected_at", "created_at"],
        "dobrybot_signals.csv",
    )


@router.get("/opportunities.csv")
def export_opportunities(
    opportunity_path: str = Depends(get_bd_opportunity_path),
    activity_path: str = Depends(get_bd_activity_path),
):
    opportunities = list_opportunities(opportunity_path)
    rows = [
        {
            "id": o.id,
            "company_name": o.company_name,
            "contact_name": o.contact_name or "",
            "stage": o.stage,
            "score": o.score,
            "score_label": o.score_label,
            "value_proposition": o.value_proposition or "",
            "created_at": o.created_at,
        }
        for o in opportunities
    ]
    log_activity(activity_path, {
        "entity_type": "workspace",
        "entity_id": "export",
        "action": "export_created",
        "description": f"Opportunities CSV exported ({len(rows)} records)",
        "metadata": {"export_type": "opportunities", "count": len(rows), "local_only": True},
    })
    return _csv_stream(
        rows,
        ["id", "company_name", "contact_name", "stage", "score",
         "score_label", "value_proposition", "created_at"],
        "dobrybot_opportunities.csv",
    )


@router.get("/workspace.json")
def export_workspace_json(
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
    Export a lightweight workspace JSON summary. Same as backup but via /export.
    """
    def _read(path: str):
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

    data = {
        "exported_at": datetime.utcnow().isoformat(),
        "local_only": True,
        "safety_notice": _SAFETY_NOTICE,
        "companies": _read(company_path),
        "prospects": _read(prospect_path),
        "signals": _read(signal_path),
        "pain_points": _read(pain_point_path),
        "opportunities": _read(opportunity_path),
        "deal_packets": _read(deal_packet_path),
        "outreach_drafts": _read(outreach_path),
        "recommendations": _read(recommendation_path),
        "icp_config": _read_obj(icp_path),
        "import_history": _read(import_history_path),
    }

    log_activity(activity_path, {
        "entity_type": "workspace",
        "entity_id": "export",
        "action": "export_created",
        "description": "Workspace JSON exported",
        "metadata": {"export_type": "workspace_json", "local_only": True},
    })

    return JSONResponse(
        content=data,
        headers={"Content-Disposition": 'attachment; filename="dobrybot_workspace.json"'},
    )
