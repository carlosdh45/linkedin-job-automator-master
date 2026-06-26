import json
from pathlib import Path
from typing import List

from backend.models.bd import BDPainPoint


def _load(path: str) -> List[BDPainPoint]:
    p = Path(path)
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return [BDPainPoint(**item) for item in json.load(f)]


def _save(path: str, items: List[BDPainPoint]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump([item.model_dump() for item in items], f, indent=2)


def list_pain_points(path: str) -> List[BDPainPoint]:
    return _load(path)


def create_pain_point(path: str, data: dict) -> BDPainPoint:
    items = _load(path)
    pp = BDPainPoint(**data)
    items.append(pp)
    _save(path, items)
    return pp


def list_by_company(path: str, company_id: str) -> List[BDPainPoint]:
    return [p for p in _load(path) if p.company_id == company_id]


def clear_pain_points(path: str) -> None:
    _save(path, [])


def replace_all(path: str, pain_points: List[BDPainPoint]) -> None:
    _save(path, pain_points)
