import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from backend.models.bd import BDSignal


def _load(path: str) -> List[BDSignal]:
    p = Path(path)
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return [BDSignal(**item) for item in json.load(f)]


def _save(path: str, items: List[BDSignal]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump([item.model_dump() for item in items], f, indent=2)


def list_signals(path: str) -> List[BDSignal]:
    return _load(path)


def get_signal(path: str, signal_id: str) -> Optional[BDSignal]:
    for s in _load(path):
        if s.id == signal_id:
            return s
    return None


def create_signal(path: str, data: dict) -> BDSignal:
    items = _load(path)
    signal = BDSignal(**data)
    items.append(signal)
    _save(path, items)
    return signal


def update_signal(path: str, signal_id: str, updates: dict) -> Optional[BDSignal]:
    items = _load(path)
    for i, s in enumerate(items):
        if s.id == signal_id:
            merged = s.model_dump()
            merged.update({k: v for k, v in updates.items() if v is not None})
            items[i] = BDSignal(**merged)
            _save(path, items)
            return items[i]
    return None


def clear_signals(path: str) -> None:
    _save(path, [])


def replace_all(path: str, signals: List[BDSignal]) -> None:
    _save(path, signals)
