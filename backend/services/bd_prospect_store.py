import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from backend.models.bd import BDProspect


def _load(path: str) -> List[BDProspect]:
    p = Path(path)
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return [BDProspect(**item) for item in json.load(f)]


def _save(path: str, items: List[BDProspect]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump([item.model_dump() for item in items], f, indent=2)


def list_prospects(path: str) -> List[BDProspect]:
    return _load(path)


def get_prospect(path: str, prospect_id: str) -> Optional[BDProspect]:
    for p in _load(path):
        if p.id == prospect_id:
            return p
    return None


def create_prospect(path: str, data: dict) -> BDProspect:
    items = _load(path)
    prospect = BDProspect(**data)
    items.append(prospect)
    _save(path, items)
    return prospect


def update_prospect(path: str, prospect_id: str, updates: dict) -> Optional[BDProspect]:
    items = _load(path)
    for i, p in enumerate(items):
        if p.id == prospect_id:
            merged = p.model_dump()
            merged.update({k: v for k, v in updates.items() if v is not None})
            merged["updated_at"] = datetime.utcnow().isoformat()
            items[i] = BDProspect(**merged)
            _save(path, items)
            return items[i]
    return None


def clear_prospects(path: str) -> None:
    _save(path, [])


def replace_all(path: str, prospects: List[BDProspect]) -> None:
    _save(path, prospects)
