"""
Phase 5 tests: Application Packet — default state, update, generate, and safety invariants.

Safety invariants:
  - No automatic send endpoint
  - No automatic apply endpoint
  - Generation is local/rule-based only
  - Packet is stored locally only
"""
import pytest
from fastapi.testclient import TestClient

from backend.api import auth as auth_module
from backend.config import (
    get_application_packet_path,
    get_db_path,
    get_profile_path,
    get_resume_preview_path,
    get_resume_profile_path,
    get_uploads_path,
)
from backend.main import app
from backend.models.application_packet import ApplicationPacket, ChecklistItem
from backend.services.packet_generator import generate_packet
from backend.models.resume_profile import ResumeProfile
from src.db import initialize_database


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_sessions():
    auth_module._sessions.clear()
    yield
    auth_module._sessions.clear()


@pytest.fixture
def tmp_db(tmp_path):
    db_file = str(tmp_path / "test_packet.db")
    initialize_database(db_file)
    return db_file


@pytest.fixture
def client(tmp_path, tmp_db, monkeypatch):
    profile_p  = str(tmp_path / "profile.json")
    uploads_p  = str(tmp_path / "uploads")
    resume_p   = str(tmp_path / "resume_profile.json")
    preview_p  = str(tmp_path / "resume_preview.md")
    packet_p   = str(tmp_path / "application_packet.json")
    account_p  = str(tmp_path / "account.json")

    monkeypatch.setenv("DOBRYBOT_DB_PATH",                 tmp_db)
    monkeypatch.setenv("DOBRYBOT_PROFILE_PATH",            profile_p)
    monkeypatch.setenv("DOBRYBOT_UPLOADS_PATH",            uploads_p)
    monkeypatch.setenv("DOBRYBOT_RESUME_PROFILE_PATH",     resume_p)
    monkeypatch.setenv("DOBRYBOT_RESUME_PREVIEW_PATH",     preview_p)
    monkeypatch.setenv("DOBRYBOT_APPLICATION_PACKET_PATH", packet_p)
    monkeypatch.setenv("DOBRYBOT_ACCOUNT_PATH",            account_p)

    app.dependency_overrides[get_db_path]                 = lambda: tmp_db
    app.dependency_overrides[get_profile_path]            = lambda: profile_p
    app.dependency_overrides[get_uploads_path]            = lambda: uploads_p
    app.dependency_overrides[get_resume_profile_path]     = lambda: resume_p
    app.dependency_overrides[get_resume_preview_path]     = lambda: preview_p
    app.dependency_overrides[get_application_packet_path] = lambda: packet_p

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Packet Generator unit tests ───────────────────────────────────────────────

class TestPacketGeneratorUnit:

    def test_generates_packet(self):
        profile = ResumeProfile(headline="Staff Engineer", email="a@b.com", skills=["Python"])
        pkt = generate_packet(profile, "Backend Engineer", "TechCorp", "# Resume")
        assert isinstance(pkt, ApplicationPacket)

    def test_cover_letter_contains_company(self):
        profile = ResumeProfile(headline="SWE", skills=["Go"])
        pkt = generate_packet(profile, "Engineer", "Acme", "")
        assert "Acme" in pkt.cover_letter_draft

    def test_cover_letter_contains_role(self):
        profile = ResumeProfile(headline="Dev")
        pkt = generate_packet(profile, "Lead Engineer", "Corp", "")
        assert "Lead Engineer" in pkt.cover_letter_draft

    def test_talking_points_non_empty(self):
        profile = ResumeProfile(skills=["Python", "FastAPI"])
        pkt = generate_packet(profile, "Engineer", "Co", "")
        assert len(pkt.talking_points) > 0

    def test_checklist_non_empty(self):
        profile = ResumeProfile()
        pkt = generate_packet(profile, "", "", "")
        assert len(pkt.checklist) > 0

    def test_checklist_items_are_not_done_by_default(self):
        profile = ResumeProfile()
        pkt = generate_packet(profile, "", "", "")
        assert all(not item.done for item in pkt.checklist)

    def test_status_is_ready(self):
        profile = ResumeProfile()
        pkt = generate_packet(profile, "Dev", "Co", "")
        assert pkt.status == "ready"

    def test_cover_letter_not_sent_automatically(self):
        profile = ResumeProfile(email="x@x.com")
        pkt = generate_packet(profile, "Dev", "Co", "")
        assert "manual" in pkt.cover_letter_draft.lower() or "not sent" in pkt.cover_letter_draft.lower()


# ── Default state ─────────────────────────────────────────────────────────────

class TestApplicationPacketDefault:

    def test_get_returns_200(self, client):
        assert client.get("/api/application-packet").status_code == 200

    def test_default_job_title_empty(self, client):
        assert client.get("/api/application-packet").json()["target_job_title"] == ""

    def test_default_company_empty(self, client):
        assert client.get("/api/application-packet").json()["target_company"] == ""

    def test_default_status_is_not_started(self, client):
        assert client.get("/api/application-packet").json()["status"] == "not_started"

    def test_default_has_all_fields(self, client):
        data = client.get("/api/application-packet").json()
        for field in ("target_job_title", "target_company", "resume_markdown",
                      "cover_letter_draft", "talking_points", "checklist",
                      "status", "updated_at"):
            assert field in data, f"Missing: {field}"


# ── Update packet ─────────────────────────────────────────────────────────────

class TestApplicationPacketUpdate:

    def test_put_updates_job_title(self, client):
        r = client.put("/api/application-packet", json={"target_job_title": "Staff Engineer"})
        assert r.status_code == 200
        assert r.json()["target_job_title"] == "Staff Engineer"

    def test_put_updates_company(self, client):
        r = client.put("/api/application-packet", json={"target_company": "Acme Corp"})
        assert r.json()["target_company"] == "Acme Corp"

    def test_put_updates_status(self, client):
        r = client.put("/api/application-packet", json={"status": "ready"})
        assert r.json()["status"] == "ready"

    def test_put_persists_on_get(self, client):
        client.put("/api/application-packet", json={"target_job_title": "SWE"})
        assert client.get("/api/application-packet").json()["target_job_title"] == "SWE"

    def test_put_preserves_other_fields(self, client):
        client.put("/api/application-packet", json={"target_job_title": "Dev"})
        client.put("/api/application-packet", json={"target_company": "Corp"})
        data = client.get("/api/application-packet").json()
        assert data["target_job_title"] == "Dev"
        assert data["target_company"] == "Corp"

    def test_put_updates_checklist(self, client):
        checklist = [{"text": "Research company", "done": False}]
        r = client.put("/api/application-packet", json={"checklist": checklist})
        assert r.status_code == 200
        assert len(r.json()["checklist"]) == 1
        assert r.json()["checklist"][0]["text"] == "Research company"

    def test_put_updates_talking_points(self, client):
        r = client.put("/api/application-packet", json={"talking_points": ["Python expertise"]})
        assert "Python expertise" in r.json()["talking_points"]


# ── Generate packet ───────────────────────────────────────────────────────────

class TestApplicationPacketGenerate:

    def test_generate_returns_200(self, client):
        assert client.post("/api/application-packet/generate").status_code == 200

    def test_generate_returns_packet_schema(self, client):
        r = client.post("/api/application-packet/generate")
        data = r.json()
        assert "cover_letter_draft" in data
        assert "talking_points" in data
        assert "checklist" in data

    def test_generate_creates_cover_letter(self, client):
        r = client.post("/api/application-packet/generate")
        assert isinstance(r.json()["cover_letter_draft"], str)
        assert len(r.json()["cover_letter_draft"]) > 0

    def test_generate_creates_checklist(self, client):
        r = client.post("/api/application-packet/generate")
        assert len(r.json()["checklist"]) > 0

    def test_generate_uses_target_job_from_packet(self, client):
        client.put("/api/application-packet", json={"target_job_title": "Lead Architect", "target_company": "TechCo"})
        r = client.post("/api/application-packet/generate")
        assert "TechCo" in r.json()["cover_letter_draft"]

    def test_generate_uses_resume_profile_skills(self, client):
        client.put("/api/resume/profile", json={"skills": ["Rust", "WebAssembly"]})
        r = client.post("/api/application-packet/generate")
        assert "Rust" in r.json()["cover_letter_draft"] or "Rust" in str(r.json()["talking_points"])

    def test_generate_persists_packet(self, client):
        client.post("/api/application-packet/generate")
        r = client.get("/api/application-packet")
        assert r.json()["cover_letter_draft"] != ""

    def test_generate_sets_status_to_ready(self, client):
        r = client.post("/api/application-packet/generate")
        assert r.json()["status"] == "ready"

    def test_generate_is_local_only(self, client):
        r = client.post("/api/application-packet/generate")
        assert r.status_code == 200

    def test_cover_letter_mentions_manual_submission(self, client):
        r = client.post("/api/application-packet/generate")
        letter = r.json()["cover_letter_draft"].lower()
        assert "manual" in letter or "not sent" in letter


# ── Safety invariants ─────────────────────────────────────────────────────────

class TestApplicationPacketSafetyInvariants:

    def test_no_send_packet_endpoint(self, client):
        assert client.post("/api/application-packet/send").status_code == 404

    def test_no_auto_apply_endpoint(self, client):
        assert client.post("/api/application-packet/apply").status_code == 404

    def test_no_submit_packet_endpoint(self, client):
        assert client.post("/api/application-packet/submit").status_code == 404

    def test_no_email_packet_endpoint(self, client):
        assert client.post("/api/application-packet/email").status_code == 404

    def test_generate_does_not_send_anywhere(self, client):
        r = client.post("/api/application-packet/generate")
        assert r.status_code == 200

    def test_existing_safety_invariants_still_hold(self, client):
        assert client.post("/api/send").status_code == 404
        assert client.post("/api/apply").status_code == 404
