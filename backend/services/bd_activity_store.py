import json
from pathlib import Path
from typing import List, Optional

from backend.models.bd import BDActivity


def _load(path: str) -> List[BDActivity]:
    p = Path(path)
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return [BDActivity(**item) for item in json.load(f)]


def _save(path: str, items: List[BDActivity]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump([item.model_dump() for item in items], f, indent=2)


def list_activity(
    path: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    limit: int = 100,
) -> List[BDActivity]:
    items = _load(path)
    if entity_type:
        items = [a for a in items if a.entity_type == entity_type]
    if entity_id:
        items = [a for a in items if a.entity_id == entity_id]
    # newest first
    items.sort(key=lambda a: a.created_at, reverse=True)
    return items[:limit]


def log_activity(path: str, data: dict) -> BDActivity:
    items = _load(path)
    activity = BDActivity(**data)
    items.append(activity)
    _save(path, items)
    return activity


def clear_activity(path: str) -> None:
    _save(path, [])
