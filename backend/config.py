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


def get_resume_profile_path() -> str:
    return os.environ.get("DOBRYBOT_RESUME_PROFILE_PATH", "data/resume_profile.json")


def get_resume_preview_path() -> str:
    return os.environ.get("DOBRYBOT_RESUME_PREVIEW_PATH", "data/resume_preview.md")


def get_extracted_text_path() -> str:
    return os.environ.get("DOBRYBOT_EXTRACTED_TEXT_PATH", "data/resume_extracted_text.txt")


def get_import_preview_path() -> str:
    return os.environ.get("DOBRYBOT_IMPORT_PREVIEW_PATH", "data/resume_import_preview.json")


def get_application_packet_path() -> str:
    return os.environ.get("DOBRYBOT_APPLICATION_PACKET_PATH", "data/application_packet.json")
