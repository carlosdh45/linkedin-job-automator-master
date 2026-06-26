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


def replace_all(path: str, drafts: List[BDOutreachDraft]) -> None:
    _save(path, drafts)
