import json
from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.config import get_db_path
from src import db as src_db

router = APIRouter()


@router.get("/jobs")
def get_jobs(
    status: Optional[str] = Query(default=None, description="Filter by status"),
    db_path: str = Depends(get_db_path),
):
    if status:
        jobs = src_db.get_jobs_by_status(db_path, status)
    else:
        with src_db.get_connection(db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM applied_jobs ORDER BY job_score DESC, applied_at DESC"
            ).fetchall()
            jobs = [dict(r) for r in rows]

    for job in jobs:
        raw = job.get("context_data")
        if isinstance(raw, str):
            try:
                job["context_data"] = json.loads(raw)
            except Exception:
                job["context_data"] = {}

    return {"jobs": jobs, "total": len(jobs)}
