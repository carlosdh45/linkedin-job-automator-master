import json
from datetime import datetime
from pathlib import Path

from backend.models.bd import BDICPConfig

_DEFAULT_CONFIG = BDICPConfig()


def load_icp_config(path: str) -> BDICPConfig:
    p = Path(path)
    if not p.exists():
        return BDICPConfig()
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    return BDICPConfig(**data)


def save_icp_config(path: str, config: BDICPConfig) -> BDICPConfig:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(config.model_dump(), f, indent=2)
    return config


def update_icp_config(path: str, updates: dict) -> BDICPConfig:
    config = load_icp_config(path)
    merged = config.model_dump()
    for k, v in updates.items():
        if v is not None:
            merged[k] = v
    merged["updated_at"] = datetime.utcnow().isoformat()
    updated = BDICPConfig(**merged)
    return save_icp_config(path, updated)
