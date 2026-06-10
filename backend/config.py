import os

import yaml


def get_db_path() -> str:
    env = os.environ.get("DOBRYBOT_DB_PATH")
    if env:
        return env
    try:
        with open("config.yaml", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        path = cfg.get("paths", {}).get("database")
        if path:
            return path
    except Exception:
        pass
    return "data/copilot.db"
