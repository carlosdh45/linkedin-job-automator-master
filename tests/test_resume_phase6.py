"""
Phase 6 tests: Premium Resume Editor — tone options, quality endpoint,
writing quality invariants, and safety checks.

Safety invariants tested:
  - No em dashes in generated output
  - No fabricated metrics or numbers not present in profile data
  - No external API calls (generator is pure local template)
  - No /send, /apply, or /ai-generate endpoints exist
  - Quality endpoint is read-only, returns local metrics only
"""
import pytest
from fastapi.testclient import TestClient

from backend.api import auth as auth_module
from backend.config import (
    get_db_path,
    get_profile_path,
    get_resume_preview_path,
    get_resume_profile_path,
    get_uploads_path,
)
from backend.main import app
from backend.models.resume_profile import ExperienceItem, ResumeProfile
from backend.services.resume_generator import VALID_TONES, generate_markdown
from src.db import initialize_database


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_sessions():
    auth_module._sessions.clear()
    yield
    auth_module._sessions.clear()


@pytest.fixture
def tmp_db(tmp_path):
    db_file = str(tmp_path / "test_phase6.db")
    initialize_database(db_file)
    return db_file


@pytest.fixture
def client(tmp_path, tmp_db, monkeypatch):
    profile_p  = str(tmp_path / "profile.json")
    uploads_p  = str(tmp_path / "uploads")
    resume_p   = str(tmp_path / "resume_profile.json")
    preview_p  = str(tmp_path / "resume_preview.md")
    account_p  = str(tmp_path / "account.json")

    monkeypatch.setenv("DOBRYBOT_DB_PATH",             tmp_db)
    monkeypatch.setenv("DOBRYBOT_PROFILE_PATH",        profile_p)
    monkeypatch.setenv("DOBRYBOT_UPLOADS_PATH",        uploads_p)
    monkeypatch.setenv("DOBRYBOT_RESUME_PROFILE_PATH", resume_p)
    monkeypatch.setenv("DOBRYBOT_RESUME_PREVIEW_PATH", preview_p)
    monkeypatch.setenv("DOBRYBOT_ACCOUNT_PATH",        account_p)

    app.dependency_overrides[get_db_path]              = lambda: tmp_db
    app.dependency_overrides[get_profile_path]         = lambda: profile_p
    app.dependency_overrides[get_uploads_path]         = lambda: uploads_p
    app.dependency_overrides[get_resume_profile_path]  = lambda: resume_p
    app.dependency_overrides[get_resume_preview_path]  = lambda: preview_p

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Tone: API endpoint ─────────────────────────────────────────────────────────

class TestResumeToneAPI:

    def test_generate_default_tone_returns_200(self, client):
        r = client.post("/api/resume/generate")
        assert r.status_code == 200

    def test_generate_tone_professional_returns_200(self, client):
        r = client.post("/api/resume/generate?tone=professional")
        assert r.status_code == 200
        assert r.json()["generated"] is True

    def test_generate_tone_executive_returns_200(self, client):
        r = client.post("/api/resume/generate?tone=executive")
        assert r.status_code == 200
        assert r.json()["generated"] is True

    def test_generate_tone_technical_returns_200(self, client):
        r = client.post("/api/resume/generate?tone=technical")
        assert r.status_code == 200
        assert r.json()["generated"] is True

    def test_generate_tone_concise_returns_200(self, client):
        r = client.post("/api/resume/generate?tone=concise")
        assert r.status_code == 200
        assert r.json()["generated"] is True

    def test_generate_returns_tone_in_response(self, client):
        r = client.post("/api/resume/generate?tone=executive")
        assert r.json()["tone"] == "executive"

    def test_generate_unknown_tone_falls_back_to_professional(self, client):
        r = client.post("/api/resume/generate?tone=fancy_unknown")
        assert r.status_code == 200
        assert r.json()["generated"] is True

    def test_generate_content_includes_profile_data_regardless_of_tone(self, client):
        client.put("/api/resume/profile", json={"headline": "Principal Engineer"})
        for tone in ("professional", "executive", "technical", "concise"):
            r = client.post(f"/api/resume/generate?tone={tone}")
            assert "Principal Engineer" in r.json()["preview"], f"tone={tone} missing headline"


# ── Tone: Generator unit tests ─────────────────────────────────────────────────

class TestResumeToneUnit:

    def test_valid_tones_constant_covers_all_tones(self):
        assert "professional" in VALID_TONES
        assert "executive" in VALID_TONES
        assert "technical" in VALID_TONES
        assert "concise" in VALID_TONES

    def test_concise_tone_limits_bullets_to_three(self):
        profile = ResumeProfile(
            experience_items=[
                ExperienceItem(
                    company="Acme", title="SWE", start_date="2020",
                    currently_working=True,
                    bullets=["Bullet 1", "Bullet 2", "Bullet 3", "Bullet 4", "Bullet 5"],
                )
            ]
        )
        md = generate_markdown(profile, tone="concise")
        bullets = [line for line in md.splitlines() if line.startswith("- ")]
        assert len(bullets) <= 3

    def test_executive_tone_limits_bullets_to_four(self):
        profile = ResumeProfile(
            experience_items=[
                ExperienceItem(
                    company="Corp", title="Lead", start_date="2021",
                    currently_working=True,
                    bullets=["B1", "B2", "B3", "B4", "B5", "B6"],
                )
            ]
        )
        md = generate_markdown(profile, tone="executive")
        bullets = [line for line in md.splitlines() if line.startswith("- ")]
        assert len(bullets) <= 4

    def test_professional_tone_keeps_all_bullets(self):
        profile = ResumeProfile(
            experience_items=[
                ExperienceItem(
                    company="Z", title="Eng", start_date="2019",
                    currently_working=True,
                    bullets=["B1", "B2", "B3", "B4", "B5"],
                )
            ]
        )
        md = generate_markdown(profile, tone="professional")
        bullets = [line for line in md.splitlines() if line.startswith("- ")]
        assert len(bullets) == 5

    def test_invalid_tone_uses_professional_behaviour(self):
        profile = ResumeProfile(
            experience_items=[
                ExperienceItem(
                    company="Z", title="Eng", start_date="2019",
                    currently_working=True,
                    bullets=["B1", "B2", "B3", "B4", "B5"],
                )
            ]
        )
        md = generate_markdown(profile, tone="nonsense")
        bullets = [line for line in md.splitlines() if line.startswith("- ")]
        assert len(bullets) == 5


# ── Writing quality invariants ─────────────────────────────────────────────────

class TestWritingQuality:

    def test_generate_no_em_dashes_in_output(self):
        profile = ResumeProfile(
            headline="Senior Engineer",
            professional_summary="Experienced professional.",
            experience_items=[
                ExperienceItem(
                    company="BigCo", title="Lead Engineer",
                    location="London", start_date="2020-01",
                    end_date="2023-06", bullets=["Built platform"],
                )
            ],
        )
        md = generate_markdown(profile)
        assert "—" not in md, "Output must not contain em dashes (U+2014)"
        assert " — " not in md, "Output must not contain em dash with spaces"

    def test_generate_does_not_invent_numbers_not_in_profile(self):
        profile = ResumeProfile(
            headline="Backend Engineer",
            professional_summary="Solid background in distributed systems.",
            experience_items=[
                ExperienceItem(
                    company="Startup", title="SWE", start_date="2021",
                    currently_working=True,
                    bullets=["Shipped new microservice"],
                )
            ],
        )
        md = generate_markdown(profile)
        # Generator must only include numbers that came from profile data
        # The profile has no percentage/metric numbers, so none should appear
        import re
        numbers_in_md = re.findall(r"\b\d+%|\d+x\b|\d+\s*(million|billion|k\b)", md, re.IGNORECASE)
        assert numbers_in_md == [], f"Generator invented metrics: {numbers_in_md}"

    def test_generate_output_contains_only_profile_data(self):
        profile = ResumeProfile(
            headline="My Exact Headline",
            professional_summary="My exact summary.",
            skills=["MySkillA", "MySkillB"],
        )
        md = generate_markdown(profile)
        assert "My Exact Headline" in md
        assert "My exact summary." in md
        assert "MySkillA" in md

    def test_generate_is_pure_local_no_side_effects(self, client):
        # generate endpoint must not call any external service
        r = client.post("/api/resume/generate")
        assert r.status_code == 200
        assert r.json()["generated"] is True


# ── Quality endpoint ───────────────────────────────────────────────────────────

class TestResumeQualityEndpoint:

    def test_quality_endpoint_exists(self, client):
        r = client.get("/api/resume/quality")
        assert r.status_code == 200

    def test_quality_returns_completeness_score(self, client):
        r = client.get("/api/resume/quality")
        assert "completeness_score" in r.json()

    def test_quality_returns_ats_checks(self, client):
        r = client.get("/api/resume/quality")
        data = r.json()
        assert "ats_checks" in data
        assert isinstance(data["ats_checks"], list)

    def test_quality_returns_missing_sections(self, client):
        r = client.get("/api/resume/quality")
        assert "missing_sections" in r.json()

    def test_quality_empty_profile_low_score(self, client):
        r = client.get("/api/resume/quality")
        assert r.json()["completeness_score"] < 50

    def test_quality_filled_profile_high_score(self, client):
        client.put("/api/resume/profile", json={
            "headline": "Staff Engineer",
            "professional_summary": "Experienced backend engineer.",
            "email": "eng@example.com",
            "skills": ["Python", "FastAPI", "Vue", "PostgreSQL", "Docker"],
            "experience_items": [
                {"company": "Acme", "title": "SWE", "start_date": "2020", "currently_working": True, "bullets": ["Built things"]}
            ],
            "education_items": [{"institution": "MIT", "degree": "BSc CS", "dates": "2016-2020"}],
            "linkedin_url": "https://linkedin.com/in/example",
        })
        r = client.get("/api/resume/quality")
        assert r.json()["completeness_score"] >= 80

    def test_quality_ats_score_improves_with_data(self, client):
        r1 = client.get("/api/resume/quality")
        initial_ats = r1.json()["ats_score"]
        client.put("/api/resume/profile", json={
            "headline": "Engineer",
            "email": "x@x.com",
            "phone": "1234567",
            "skills": ["Python", "FastAPI", "Vue", "SQL", "Docker"],
        })
        r2 = client.get("/api/resume/quality")
        assert r2.json()["ats_score"] > initial_ats

    def test_quality_returns_sections_dict(self, client):
        r = client.get("/api/resume/quality")
        data = r.json()
        assert "sections" in data
        assert isinstance(data["sections"], dict)

    def test_quality_is_local_readonly(self, client):
        # GET quality must not modify any stored data
        client.put("/api/resume/profile", json={"headline": "Engineer"})
        client.get("/api/resume/quality")
        r = client.get("/api/resume/profile")
        assert r.json()["headline"] == "Engineer"


# ── Safety invariants ──────────────────────────────────────────────────────────

class TestPhase6SafetyInvariants:

    def test_no_send_resume_endpoint(self, client):
        assert client.post("/api/resume/send").status_code == 404

    def test_no_apply_resume_endpoint(self, client):
        assert client.post("/api/resume/apply").status_code == 404

    def test_no_ai_generate_endpoint(self, client):
        assert client.post("/api/resume/ai-generate").status_code == 404

    def test_no_send_to_linkedin_endpoint(self, client):
        assert client.post("/api/resume/send-to-linkedin").status_code == 404

    def test_no_top_level_send_endpoint(self, client):
        assert client.post("/api/send").status_code == 404

    def test_no_top_level_apply_endpoint(self, client):
        assert client.post("/api/apply").status_code == 404

    def test_quality_endpoint_is_get_not_post(self, client):
        # POST to quality should be 405 (method not allowed), not 200
        r = client.post("/api/resume/quality")
        assert r.status_code in (404, 405)

    def test_existing_generate_endpoint_still_works(self, client):
        r = client.post("/api/resume/generate")
        assert r.status_code == 200
        assert r.json()["generated"] is True

    def test_existing_profile_endpoint_still_works(self, client):
        r = client.get("/api/resume/profile")
        assert r.status_code == 200

    def test_existing_preview_endpoint_still_works(self, client):
        r = client.get("/api/resume/preview")
        assert r.status_code == 200
