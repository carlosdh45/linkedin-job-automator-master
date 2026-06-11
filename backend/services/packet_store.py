import json
from datetime import datetime
from pathlib import Path

from backend.models.application_packet import ApplicationPacket


def _load(path: str) -> ApplicationPacket:
    p = Path(path)
    if not p.exists():
        return ApplicationPacket()
    with open(p, encoding="utf-8") as f:
        return ApplicationPacket(**json.load(f))


def _save(path: str, packet: ApplicationPacket) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(packet.model_dump(), f, indent=2)


def get_packet(path: str) -> ApplicationPacket:
    return _load(path)


def update_packet(path: str, updates: dict) -> ApplicationPacket:
    data = _load(path).model_dump()
    data.update(updates)
    data["updated_at"] = datetime.utcnow().isoformat()
    packet = ApplicationPacket(**data)
    _save(path, packet)
    return packet


def save_packet(path: str, packet: ApplicationPacket) -> ApplicationPacket:
    packet.updated_at = datetime.utcnow().isoformat()
    _save(path, packet)
    return packet
