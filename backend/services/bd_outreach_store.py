import json
from pathlib import Path
from typing import List, Optional

from backend.models.bd import BDOutreachDraft


def _load(path: str) -> List[BDOutreachDraft]:
    p = Path(path)
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return [BDOutreachDraft(**item) for item in json.load(f)]


def _save(path: str, items: List[BDOutreachDraft]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump([item.model_dump() for item in items], f, indent=2)


def list_drafts(path: str) -> List[BDOutreachDraft]:
    return _load(path)


def get_draft(path: str, draft_id: str) -> Optional[BDOutreachDraft]:
    for d in _load(path):
        if d.id == draft_id:
            return d
    return None


def save_draft(path: str, draft: BDOutreachDraft) -> BDOutreachDraft:
    items = _load(path)
    items.append(draft)
    _save(path, items)
    return draft


def clear_drafts(path: str) -> None:
    _save(path, [])


def update_draft(path: str, draft_id: str, updates: dict) -> Optional[BDOutreachDraft]:
    from datetime import datetime
    items = _load(path)
    for i, d in enumerate(items):
        if d.id == draft_id:
            merged = d.model_dump()
            merged.update({k: v for k, v in updates.items() if v is not None})
            merged["updated_at"] = datetime.utcnow().isoformat()
            items[i] = BDOutreachDraft(**merged)
            _save(path, items)
            return items[i]
    return None


def replace_all(path: str, drafts: List[BDOutreachDraft]) -> None:
    _save(path, drafts)
