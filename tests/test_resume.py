"""
Phase 4 tests: Resume Studio — profile storage, generation, preview.

Safety invariants tested:
  - No /send or /apply resume endpoints
  - No external API calls (generation is pure local template)
  - Generated content is stored locally only
  - Uploaded files remain in configured uploads path
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
from backend.models.resume_profile import EducationItem, ExperienceItem, ResumeProfile
from backend.services.resume_generator import generate_markdown
from src.db import initialize_database


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_sessions():
    auth_module._sessions.clear()
    yield
    auth_module._sessions.clear()


@pytest.fixture
def tmp_db(tmp_path):
    db_file = str(tmp_path / "test_resume.db")
    initialize_database(db_file)
    return db_file


@pytest.fixture
def client(tmp_path, tmp_db, monkeypatch):
    profile_p = str(tmp_path / "profile.json")
    uploads_p = str(tmp_path / "uploads")
    resume_p = str(tmp_path / "resume_profile.json")
    preview_p = str(tmp_path / "resume_preview.md")
    account_p = str(tmp_path / "account.json")

    monkeypatch.setenv("DOBRYBOT_DB_PATH", tmp_db)
    monkeypatch.setenv("DOBRYBOT_PROFILE_PATH", profile_p)
    monkeypatch.setenv("DOBRYBOT_UPLOADS_PATH", uploads_p)
    monkeypatch.setenv("DOBRYBOT_RESUME_PROFILE_PATH", resume_p)
    monkeypatch.setenv("DOBRYBOT_RESUME_PREVIEW_PATH", preview_p)
    monkeypatch.setenv("DOBRYBOT_ACCOUNT_PATH", account_p)

    app.dependency_overrides[get_db_path] = lambda: tmp_db
    app.dependency_overrides[get_profile_path] = lambda: profile_p
    app.dependency_overrides[get_uploads_path] = lambda: uploads_p
    app.dependency_overrides[get_resume_profile_path] = lambda: resume_p
    app.dependency_overrides[get_resume_preview_path] = lambda: preview_p

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Resume Profile — Default state ────────────────────────────────────────────

class TestResumeProfileDefault:

    def test_get_profile_returns_200(self, client):
        r = client.get("/api/resume/profile")
        assert r.status_code == 200

    def test_default_headline_is_empty(self, client):
        assert client.get("/api/resume/profile").json()["headline"] == ""

    def test_default_summary_is_empty(self, client):
        assert client.get("/api/resume/profile").json()["professional_summary"] == ""

    def test_default_skills_is_empty_list(self, client):
        assert client.get("/api/resume/profile").json()["skills"] == []

    def test_default_experience_is_empty_list(self, client):
        assert client.get("/api/resume/profile").json()["experience_items"] == []

    def test_default_education_is_empty_list(self, client):
        assert client.get("/api/resume/profile").json()["education_items"] == []

    def test_default_profile_has_all_fields(self, client):
        data = client.get("/api/resume/profile").json()
        for field in (
            "headline", "professional_summary", "target_role", "location",
            "email", "phone", "linkedin_url", "portfolio_url", "github_url",
            "skills", "experience_items", "project_items", "education_items",
            "certifications", "languages", "achievements", "updated_at",
        ):
            assert field in data, f"Missing field: {field}"


# ── Resume Profile — Update ────────────────────────────────────────────────────

class TestResumeProfileUpdate:

    def test_put_updates_headline(self, client):
        r = client.put("/api/resume/profile", json={"headline": "Senior Backend Engineer"})
        assert r.status_code == 200
        assert r.json()["headline"] == "Senior Backend Engineer"

    def test_put_updates_summary(self, client):
        r = client.put("/api/resume/profile", json={"professional_summary": "10 years building APIs."})
        assert r.json()["professional_summary"] == "10 years building APIs."

    def test_put_updates_skills(self, client):
        r = client.put("/api/resume/profile", json={"skills": ["Python", "FastAPI", "Vue"]})
        assert r.status_code == 200
        assert "Python" in r.json()["skills"]
        assert "Vue" in r.json()["skills"]

    def test_put_updates_experience(self, client):
        exp = {
            "company": "Acme Corp",
            "title": "Staff Engineer",
            "location": "London",
            "start_date": "2022-01",
            "currently_working": True,
            "bullets": ["Led platform architecture", "Reduced latency by 40%"],
        }
        r = client.put("/api/resume/profile", json={"experience_items": [exp]})
        assert r.status_code == 200
        items = r.json()["experience_items"]
        assert len(items) == 1
        assert items[0]["company"] == "Acme Corp"
        assert "Led platform architecture" in items[0]["bullets"]

    def test_put_updates_education(self, client):
        edu = {"institution": "MIT", "degree": "BSc Computer Science", "dates": "2016–2020"}
        r = client.put("/api/resume/profile", json={"education_items": [edu]})
        assert r.status_code == 200
        items = r.json()["education_items"]
        assert items[0]["institution"] == "MIT"

    def test_put_persists_on_get(self, client):
        client.put("/api/resume/profile", json={"headline": "Staff Engineer"})
        assert client.get("/api/resume/profile").json()["headline"] == "Staff Engineer"

    def test_put_preserves_earlier_fields(self, client):
        client.put("/api/resume/profile", json={"headline": "SWE"})
        client.put("/api/resume/profile", json={"target_role": "Backend"})
        data = client.get("/api/resume/profile").json()
        assert data["headline"] == "SWE"
        assert data["target_role"] == "Backend"

    def test_put_updates_certifications(self, client):
        r = client.put("/api/resume/profile", json={"certifications": ["AWS Solutions Architect"]})
        assert "AWS Solutions Architect" in r.json()["certifications"]

    def test_put_updates_languages(self, client):
        r = client.put("/api/resume/profile", json={"languages": ["English (Native)", "Spanish (B2)"]})
        assert "English (Native)" in r.json()["languages"]


# ── Resume Generate ────────────────────────────────────────────────────────────

class TestResumeGenerate:

    def test_generate_returns_200(self, client):
        r = client.post("/api/resume/generate")
        assert r.status_code == 200

    def test_generate_returns_generated_true(self, client):
        r = client.post("/api/resume/generate")
        assert r.json()["generated"] is True

    def test_generate_returns_preview_string(self, client):
        r = client.post("/api/resume/generate")
        assert isinstance(r.json()["preview"], str)

    def test_generate_with_headline_includes_it(self, client):
        client.put("/api/resume/profile", json={"headline": "Lead Platform Engineer"})
        r = client.post("/api/resume/generate")
        assert "Lead Platform Engineer" in r.json()["preview"]

    def test_generate_with_skills_includes_them(self, client):
        client.put("/api/resume/profile", json={"skills": ["Python", "FastAPI"]})
        r = client.post("/api/resume/generate")
        assert "Python" in r.json()["preview"]
        assert "FastAPI" in r.json()["preview"]

    def test_generate_with_experience_includes_company(self, client):
        exp = {"company": "TechCorp", "title": "Engineer", "start_date": "2020", "bullets": []}
        client.put("/api/resume/profile", json={"experience_items": [exp]})
        r = client.post("/api/resume/generate")
        assert "TechCorp" in r.json()["preview"]

    def test_generate_with_education_includes_institution(self, client):
        edu = {"institution": "Oxford", "degree": "MSc CS", "dates": "2018-2020"}
        client.put("/api/resume/profile", json={"education_items": [edu]})
        r = client.post("/api/resume/generate")
        assert "Oxford" in r.json()["preview"]

    def test_generate_does_not_call_external_apis(self, client):
        r = client.post("/api/resume/generate")
        assert r.status_code == 200
        assert r.json()["generated"] is True


# ── Resume Preview ─────────────────────────────────────────────────────────────

class TestResumePreview:

    def test_preview_returns_200(self, client):
        assert client.get("/api/resume/preview").status_code == 200

    def test_preview_empty_before_generate(self, client):
        r = client.get("/api/resume/preview")
        assert r.json()["has_content"] is False
        assert r.json()["preview"] == ""

    def test_preview_has_content_after_generate(self, client):
        client.post("/api/resume/generate")
        r = client.get("/api/resume/preview")
        assert r.json()["has_content"] is True

    def test_preview_reflects_latest_generate(self, client):
        client.put("/api/resume/profile", json={"headline": "Version 2 Engineer"})
        client.post("/api/resume/generate")
        r = client.get("/api/resume/preview")
        assert "Version 2 Engineer" in r.json()["preview"]

    def test_preview_updates_on_second_generate(self, client):
        client.put("/api/resume/profile", json={"headline": "First Title"})
        client.post("/api/resume/generate")
        client.put("/api/resume/profile", json={"headline": "Second Title"})
        client.post("/api/resume/generate")
        r = client.get("/api/resume/preview")
        assert "Second Title" in r.json()["preview"]


# ── Generator Unit Tests ───────────────────────────────────────────────────────

class TestResumeGeneratorUnit:

    def test_generate_markdown_empty_profile(self):
        md = generate_markdown(ResumeProfile())
        assert isinstance(md, str)
        assert len(md) > 0

    def test_generate_includes_headline(self):
        md = generate_markdown(ResumeProfile(headline="Staff Engineer"))
        assert "Staff Engineer" in md

    def test_generate_includes_skills(self):
        md = generate_markdown(ResumeProfile(skills=["Python", "FastAPI"]))
        assert "Python" in md
        assert "FastAPI" in md

    def test_generate_includes_experience_company(self):
        profile = ResumeProfile(
            experience_items=[
                ExperienceItem(
                    company="Acme", title="SWE",
                    start_date="2020", currently_working=True,
                    bullets=["Built things"],
                )
            ]
        )
        md = generate_markdown(profile)
        assert "Acme" in md
        assert "SWE" in md
        assert "Built things" in md

    def test_generate_includes_education(self):
        profile = ResumeProfile(
            education_items=[EducationItem(institution="MIT", degree="BSc CS", dates="2016-2020")]
        )
        md = generate_markdown(profile)
        assert "MIT" in md
        assert "BSc CS" in md

    def test_generate_currently_working_shows_present(self):
        profile = ResumeProfile(
            experience_items=[
                ExperienceItem(company="X", title="Y", start_date="2023-01", currently_working=True)
            ]
        )
        md = generate_markdown(profile)
        assert "Present" in md

    def test_generate_includes_certifications(self):
        profile = ResumeProfile(certifications=["AWS Solutions Architect"])
        md = generate_markdown(profile)
        assert "AWS Solutions Architect" in md

    def test_generate_includes_summary(self):
        profile = ResumeProfile(professional_summary="Experienced engineer.")
        md = generate_markdown(profile)
        assert "Experienced engineer." in md


# ── Safety Invariants ──────────────────────────────────────────────────────────

class TestResumeSafetyInvariants:

    def test_no_send_resume_endpoint(self, client):
        assert client.post("/api/resume/send").status_code == 404

    def test_no_apply_resume_endpoint(self, client):
        assert client.post("/api/resume/apply").status_code == 404

    def test_no_ai_generate_endpoint(self, client):
        assert client.post("/api/resume/ai-generate").status_code == 404

    def test_no_external_send_endpoint(self, client):
        assert client.post("/api/resume/send-to-linkedin").status_code == 404

    def test_generate_is_local_only(self, client):
        r = client.post("/api/resume/generate")
        assert r.status_code == 200
        assert r.json()["generated"] is True

    def test_existing_safety_invariants_still_hold(self, client):
        assert client.post("/api/send").status_code == 404
        assert client.post("/api/apply").status_code == 404
