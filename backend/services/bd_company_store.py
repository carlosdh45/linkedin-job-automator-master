import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from backend.models.bd import BDCompany


def _load(path: str) -> List[BDCompany]:
    p = Path(path)
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return [BDCompany(**item) for item in json.load(f)]


def _save(path: str, items: List[BDCompany]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump([item.model_dump() for item in items], f, indent=2)


def list_companies(path: str) -> List[BDCompany]:
    return _load(path)


def get_company(path: str, company_id: str) -> Optional[BDCompany]:
    for c in _load(path):
        if c.id == company_id:
            return c
    return None


def create_company(path: str, data: dict) -> BDCompany:
    items = _load(path)
    company = BDCompany(**data)
    items.append(company)
    _save(path, items)
    return company


def update_company(path: str, company_id: str, updates: dict) -> Optional[BDCompany]:
    items = _load(path)
    for i, c in enumerate(items):
        if c.id == company_id:
            merged = c.model_dump()
            merged.update({k: v for k, v in updates.items() if v is not None})
            merged["updated_at"] = datetime.utcnow().isoformat()
            items[i] = BDCompany(**merged)
            _save(path, items)
            return items[i]
    return None


def clear_companies(path: str) -> None:
    _save(path, [])


def replace_all(path: str, companies: List[BDCompany]) -> None:
    _save(path, companies)
