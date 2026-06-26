import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from backend.models.bd import BDOpportunity


def _load(path: str) -> List[BDOpportunity]:
    p = Path(path)
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return [BDOpportunity(**item) for item in json.load(f)]


def _save(path: str, items: List[BDOpportunity]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump([item.model_dump() for item in items], f, indent=2)


def list_opportunities(path: str) -> List[BDOpportunity]:
    return _load(path)


def get_opportunity(path: str, opp_id: str) -> Optional[BDOpportunity]:
    for o in _load(path):
        if o.id == opp_id:
            return o
    return None


def create_opportunity(path: str, data: dict) -> BDOpportunity:
    items = _load(path)
    opp = BDOpportunity(**data)
    items.append(opp)
    _save(path, items)
    return opp


def update_opportunity(path: str, opp_id: str, updates: dict) -> Optional[BDOpportunity]:
    items = _load(path)
    for i, o in enumerate(items):
        if o.id == opp_id:
            merged = o.model_dump()
            merged.update({k: v for k, v in updates.items() if v is not None})
            merged["updated_at"] = datetime.utcnow().isoformat()
            items[i] = BDOpportunity(**merged)
            _save(path, items)
            return items[i]
    return None


def clear_opportunities(path: str) -> None:
    _save(path, [])


def replace_all(path: str, opportunities: List[BDOpportunity]) -> None:
    _save(path, opportunities)
