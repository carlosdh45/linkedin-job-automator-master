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


# ── BD OS store paths ─────────────────────────────────────────────────────────

def get_bd_company_path() -> str:
    return os.environ.get("DOBRYBOT_BD_COMPANY_PATH", "data/bd_companies.json")


def get_bd_prospect_path() -> str:
    return os.environ.get("DOBRYBOT_BD_PROSPECT_PATH", "data/bd_prospects.json")


def get_bd_signal_path() -> str:
    return os.environ.get("DOBRYBOT_BD_SIGNAL_PATH", "data/bd_signals.json")


def get_bd_pain_point_path() -> str:
    return os.environ.get("DOBRYBOT_BD_PAIN_POINT_PATH", "data/bd_pain_points.json")


def get_bd_opportunity_path() -> str:
    return os.environ.get("DOBRYBOT_BD_OPPORTUNITY_PATH", "data/bd_opportunities.json")


def get_bd_deal_packet_path() -> str:
    return os.environ.get("DOBRYBOT_BD_DEAL_PACKET_PATH", "data/bd_deal_packets.json")


def get_bd_outreach_path() -> str:
    return os.environ.get("DOBRYBOT_BD_OUTREACH_PATH", "data/bd_outreach_drafts.json")


def get_bd_activity_path() -> str:
    return os.environ.get("DOBRYBOT_BD_ACTIVITY_PATH", "data/bd_activity.json")


def get_bd_icp_config_path() -> str:
    return os.environ.get("DOBRYBOT_BD_ICP_CONFIG_PATH", "data/bd_icp_config.json")
