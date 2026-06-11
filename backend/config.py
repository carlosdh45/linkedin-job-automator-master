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


def get_profile_path() -> str:
    return os.environ.get("DOBRYBOT_PROFILE_PATH", "data/profile.json")


def get_uploads_path() -> str:
    return os.environ.get("DOBRYBOT_UPLOADS_PATH", "uploads")
