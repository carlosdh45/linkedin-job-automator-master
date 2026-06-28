import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from backend.models.bd import BDRecommendation


def _load(path: str) -> List[BDRecommendation]:
    p = Path(path)
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return [BDRecommendation(**item) for item in json.load(f)]


def _save(path: str, items: List[BDRecommendation]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump([item.model_dump() for item in items], f, indent=2)


def list_recommendations(
    path: str,
    status: Optional[str] = None,
    entity_type: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 100,
) -> List[BDRecommendation]:
    items = _load(path)
    if status:
        items = [r for r in items if r.status == status]
    if entity_type:
        items = [r for r in items if r.entity_type == entity_type]
    if priority:
        items = [r for r in items if r.priority == priority]
    items.sort(key=lambda r: r.created_at, reverse=True)
    return items[:limit]


def get_recommendation(path: str, rec_id: str) -> Optional[BDRecommendation]:
    for r in _load(path):
        if r.id == rec_id:
            return r
    return None


def create_recommendation(path: str, data: dict) -> BDRecommendation:
    items = _load(path)
    rec = BDRecommendation(**data)
    items.append(rec)
    _save(path, items)
    return rec


def update_recommendation(path: str, rec_id: str, updates: dict) -> Optional[BDRecommendation]:
    items = _load(path)
    for i, r in enumerate(items):
        if r.id == rec_id:
            merged = r.model_dump()
            merged.update({k: v for k, v in updates.items() if v is not None})
            merged["updated_at"] = datetime.utcnow().isoformat()
            items[i] = BDRecommendation(**merged)
            _save(path, items)
            return items[i]
    return None


def count_by_status(path: str, status: str) -> int:
    return sum(1 for r in _load(path) if r.status == status)


def clear_recommendations(path: str) -> None:
    _save(path, [])


def replace_all(path: str, recommendations: List[BDRecommendation]) -> None:
    _save(path, recommendations)
