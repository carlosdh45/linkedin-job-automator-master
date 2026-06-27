import json
from pathlib import Path
from typing import List, Optional

from backend.models.bd import BDImportHistoryEntry


def _load(path: str) -> List[BDImportHistoryEntry]:
    p = Path(path)
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return [BDImportHistoryEntry(**item) for item in json.load(f)]


def _save(path: str, items: List[BDImportHistoryEntry]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump([item.model_dump() for item in items], f, indent=2)


def list_import_history(path: str) -> List[BDImportHistoryEntry]:
    items = _load(path)
    items.sort(key=lambda e: e.committed_at, reverse=True)
    return items


def get_import_history_entry(path: str, entry_id: str) -> Optional[BDImportHistoryEntry]:
    for e in _load(path):
        if e.id == entry_id:
            return e
    return None


def record_import(path: str, data: dict) -> BDImportHistoryEntry:
    items = _load(path)
    entry = BDImportHistoryEntry(**data)
    items.append(entry)
    _save(path, items)
    return entry


def clear_import_history(path: str) -> None:
    _save(path, [])
