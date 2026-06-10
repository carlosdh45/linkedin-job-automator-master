import json
from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.config import get_db_path
from src import db as src_db

router = APIRouter()


@router.get("/leads")
def get_leads(
    status: Optional[str] = Query(default=None, description="Filter by status"),
    db_path: str = Depends(get_db_path),
):
    if status:
        leads = src_db.get_leads_by_status(db_path, status)
    else:
        with src_db.get_connection(db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM leads ORDER BY lead_score DESC, created_at DESC"
            ).fetchall()
            leads = []
            for r in rows:
                d = dict(r)
                d["pain_points"] = json.loads(d.get("pain_points") or "[]")
                d["context_data"] = json.loads(d.get("context_data") or "{}")
                leads.append(d)

    return {"leads": leads, "total": len(leads)}
