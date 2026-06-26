from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.config import get_bd_activity_path
from backend.models.bd import BDActivity
from backend.services.bd_activity_store import list_activity

router = APIRouter(prefix="/bd/activity", tags=["bd-activity"])


@router.get("", response_model=list[BDActivity])
def get_activity(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    path: str = Depends(get_bd_activity_path),
):
    return list_activity(path, entity_type=entity_type, entity_id=entity_id, limit=limit)
