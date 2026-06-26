import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from backend.models.bd import BDDealPacket


def _load(path: str) -> List[BDDealPacket]:
    p = Path(path)
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return [BDDealPacket(**item) for item in json.load(f)]


def _save(path: str, items: List[BDDealPacket]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump([item.model_dump() for item in items], f, indent=2)


def list_deal_packets(path: str) -> List[BDDealPacket]:
    return _load(path)


def get_deal_packet(path: str, packet_id: str) -> Optional[BDDealPacket]:
    for pkt in _load(path):
        if pkt.id == packet_id:
            return pkt
    return None


def create_deal_packet(path: str, packet: BDDealPacket) -> BDDealPacket:
    items = _load(path)
    items.append(packet)
    _save(path, items)
    return packet


def update_deal_packet(path: str, packet_id: str, updates: dict) -> Optional[BDDealPacket]:
    items = _load(path)
    for i, pkt in enumerate(items):
        if pkt.id == packet_id:
            merged = pkt.model_dump()
            merged.update({k: v for k, v in updates.items() if v is not None})
            merged["updated_at"] = datetime.utcnow().isoformat()
            items[i] = BDDealPacket(**merged)
            _save(path, items)
            return items[i]
    return None


def clear_deal_packets(path: str) -> None:
    _save(path, [])


def replace_all(path: str, packets: List[BDDealPacket]) -> None:
    _save(path, packets)
