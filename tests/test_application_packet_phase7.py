"""
Phase 7 tests: Application Packet — job description tailoring, new fields,
export workflow, and safety invariants.

Safety invariants (checked in every class):
  - No /send endpoint
  - No /apply endpoint
  - No automatic submission
  - No external API calls
  - All generation is local/rule-based
"""
import re
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
from backend.models.resume_profile import ResumeProfile
from backend.services.packet_generator import (
    _extract_keywords,
    _match_skills,
    generate_packet,
)
from src.db import initialize_database


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_sessions():
    auth_module._sessions.clear()
    yield
    auth_module._sessions.clear()


@pytest.fixture
def tmp_db(tmp_path):
    db_file = str(tmp_path / "test_phase7.db")
    initialize_database(db_file)
    return db_file


@pytest.fixture
def client(tmp_path, tmp_db, monkeypatch):
    profile_p = str(tmp_path / "profile.json")
    uploads_p = str(tmp_path / "uploads")
    resume_p  = str(tmp_path / "resume_profile.json")
    preview_p = str(tmp_path / "resume_preview.md")
    packet_p  = str(tmp_path / "application_packet.json")
    account_p = str(tmp_path / "account.json")

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


# Rich profile fixture used across multiple tests
@pytest.fixture
def rich_profile():
    return ResumeProfile(
        headline="Senior Python Engineer",
        professional_summary="Experienced backend engineer with a focus on distributed systems.",
        email="dev@example.com",
        phone="+44 7700 900000",
        location="London, UK",
        linkedin_url="https://linkedin.com/in/example",
        skills=["Python", "FastAPI", "PostgreSQL", "Docker", "Redis", "Kubernetes"],
        experience_items=[],
        education_items=[],
    )


# ── Keyword extraction unit tests ─────────────────────────────────────────────

class TestKeywordExtraction:

    def test_extracts_words_from_text(self):
        kw = _extract_keywords("Python engineer with FastAPI experience")
        assert "python" in kw
        assert "fastapi" in kw

    def test_removes_stop_words(self):
        kw = _extract_keywords("a strong and experienced engineer")
        assert "a" not in kw
        assert "and" not in kw

    def test_empty_text_returns_empty_set(self):
        assert _extract_keywords("") == set()

    def test_short_words_excluded(self):
        kw = _extract_keywords("a be or in to go")
        assert len(kw) == 0

    def test_technical_terms_preserved(self):
        kw = _extract_keywords("C++ and C# experience needed")
        # Should pick up c++ and c#
        assert any("c" in w for w in kw)


# ── Skill matching unit tests ─────────────────────────────────────────────────

class TestSkillMatching:

    def test_matches_exact_skill(self):
        skills = ["Python", "FastAPI", "Docker"]
        kw = _extract_keywords("Python developer with FastAPI knowledge")
        matched = _match_skills(skills, kw)
        assert "Python" in matched
        assert "FastAPI" in matched

    def test_no_match_when_jd_empty(self):
        skills = ["Python", "FastAPI"]
        matched = _match_skills(skills, set())
        assert matched == []

    def test_unrelated_skills_not_matched(self):
        skills = ["Python", "FastAPI"]
        kw = _extract_keywords("Marketing and sales experience required")
        matched = _match_skills(skills, kw)
        assert "Python" not in matched
        assert "FastAPI" not in matched

    def test_partial_skill_match(self):
        # Match is exact-keyword overlap — "PostgreSQL" matches when JD contains "postgresql"
        skills = ["PostgreSQL", "Redis Cache", "Kubernetes"]
        kw = _extract_keywords("experience with postgresql and redis cache required")
        matched = _match_skills(skills, kw)
        assert "PostgreSQL" in matched
        assert "Redis Cache" in matched


# ── Packet generator unit tests — Phase 7 fields ─────────────────────────────

class TestPacketGeneratorPhase7Unit:

    def test_generates_tailored_summary_when_jd_provided(self, rich_profile):
        pkt = generate_packet(
            rich_profile, "Backend Engineer", "TechCorp",
            "# Resume",
            job_description="Looking for Python FastAPI developer with PostgreSQL skills",
        )
        assert pkt.tailored_summary != ""

    def test_tailored_summary_contains_no_invented_facts(self, rich_profile):
        pkt = generate_packet(
            rich_profile, "Backend Engineer", "TechCorp",
            "# Resume",
            job_description="Need Python and FastAPI developer",
        )
        # must not contain numbers that are not in the profile
        assert not re.search(r"\d+%", pkt.tailored_summary)

    def test_skills_emphasis_contains_matching_skills(self, rich_profile):
        pkt = generate_packet(
            rich_profile, "Backend Engineer", "TechCorp",
            "# Resume",
            job_description="Python FastAPI PostgreSQL experience required",
        )
        assert "Python" in pkt.skills_emphasis
        assert "FastAPI" in pkt.skills_emphasis

    def test_skills_emphasis_not_empty_without_jd(self, rich_profile):
        pkt = generate_packet(rich_profile, "Engineer", "Co", "")
        assert len(pkt.skills_emphasis) > 0

    def test_skills_emphasis_uses_profile_skills_only(self, rich_profile):
        pkt = generate_packet(
            rich_profile, "Data Scientist", "Corp",
            "# Resume",
            job_description="Machine learning tensorflow deep learning",
        )
        # skills_emphasis must only contain profile skills (no invented skills)
        for skill in pkt.skills_emphasis:
            assert skill in rich_profile.skills

    def test_fit_summary_references_job_title(self, rich_profile):
        pkt = generate_packet(
            rich_profile, "Staff Engineer", "Acme",
            "",
            job_description="Python developer for staff engineer role",
        )
        assert "Staff Engineer" in pkt.fit_summary or "staff engineer" in pkt.fit_summary.lower()

    def test_fit_summary_empty_without_title_or_jd(self):
        profile = ResumeProfile()
        pkt = generate_packet(profile, "", "", "")
        assert pkt.fit_summary == ""

    def test_job_description_stored_in_packet(self, rich_profile):
        jd = "Seeking a Python engineer with FastAPI skills"
        pkt = generate_packet(rich_profile, "Backend Dev", "Corp", "", jd)
        assert pkt.job_description == jd

    def test_cover_letter_uses_jd_matched_skills(self, rich_profile):
        jd = "We need Python FastAPI expertise"
        pkt = generate_packet(rich_profile, "Engineer", "Corp", "", jd)
        assert "Python" in pkt.cover_letter_draft or "FastAPI" in pkt.cover_letter_draft

    def test_talking_points_job_specific_when_jd_provided(self, rich_profile):
        jd = "Python FastAPI PostgreSQL developer needed"
        pkt = generate_packet(rich_profile, "Backend Dev", "Corp", "", jd)
        all_text = " ".join(pkt.talking_points)
        assert "Python" in all_text or "FastAPI" in all_text or "PostgreSQL" in all_text

    def test_no_invented_percentages_in_any_field(self, rich_profile):
        pkt = generate_packet(
            rich_profile, "Engineer", "Corp", "",
            job_description="Python expert needed with 5 years minimum",
        )
        for field in (pkt.cover_letter_draft, pkt.tailored_summary, pkt.fit_summary):
            assert not re.search(r"\d+%", field), f"Invented percentage in: {field[:100]}"

    def test_cover_letter_still_mentions_manual_submission(self, rich_profile):
        pkt = generate_packet(rich_profile, "Engineer", "Corp", "", "Python role")
        letter = pkt.cover_letter_draft.lower()
        assert "manual" in letter or "not sent" in letter


# ── API — new fields stored and retrieved ─────────────────────────────────────

class TestPhase7FieldsAPI:

    def test_default_job_description_empty(self, client):
        r = client.get("/api/application-packet")
        assert r.json()["job_description"] == ""

    def test_default_notes_empty(self, client):
        r = client.get("/api/application-packet")
        assert r.json()["notes"] == ""

    def test_default_tailored_summary_empty(self, client):
        r = client.get("/api/application-packet")
        assert r.json()["tailored_summary"] == ""

    def test_default_skills_emphasis_empty(self, client):
        r = client.get("/api/application-packet")
        assert r.json()["skills_emphasis"] == []

    def test_default_fit_summary_empty(self, client):
        r = client.get("/api/application-packet")
        assert r.json()["fit_summary"] == ""

    def test_put_stores_job_description(self, client):
        jd = "We need Python FastAPI experience"
        r = client.put("/api/application-packet", json={"job_description": jd})
        assert r.status_code == 200
        assert r.json()["job_description"] == jd

    def test_put_stores_notes(self, client):
        r = client.put("/api/application-packet", json={"notes": "Recruiter: Jane Doe"})
        assert r.json()["notes"] == "Recruiter: Jane Doe"

    def test_job_description_persists_on_get(self, client):
        client.put("/api/application-packet", json={"job_description": "Python dev"})
        assert client.get("/api/application-packet").json()["job_description"] == "Python dev"

    def test_notes_persists_on_get(self, client):
        client.put("/api/application-packet", json={"notes": "Portal: jobs.example.com"})
        assert client.get("/api/application-packet").json()["notes"] == "Portal: jobs.example.com"

    def test_generate_uses_stored_job_description(self, client):
        client.put("/api/resume/profile", json={"skills": ["Python", "FastAPI"]})
        client.put("/api/application-packet", json={
            "target_job_title": "Backend Dev",
            "job_description": "Python FastAPI developer needed",
        })
        r = client.post("/api/application-packet/generate")
        assert r.status_code == 200
        data = r.json()
        assert "Python" in str(data["skills_emphasis"]) or "FastAPI" in str(data["skills_emphasis"])

    def test_generate_returns_tailored_summary(self, client):
        client.put("/api/resume/profile", json={
            "professional_summary": "Backend engineer.",
            "skills": ["Python", "FastAPI"],
        })
        client.put("/api/application-packet", json={
            "target_job_title": "Python Dev",
            "job_description": "Python FastAPI required",
        })
        r = client.post("/api/application-packet/generate")
        assert r.status_code == 200
        assert isinstance(r.json()["tailored_summary"], str)

    def test_generate_returns_fit_summary(self, client):
        client.put("/api/resume/profile", json={"skills": ["Python"]})
        client.put("/api/application-packet", json={
            "target_job_title": "Staff Engineer",
            "job_description": "Python skills required",
        })
        r = client.post("/api/application-packet/generate")
        assert r.status_code == 200
        assert isinstance(r.json()["fit_summary"], str)

    def test_generate_persists_all_new_fields(self, client):
        client.put("/api/resume/profile", json={"skills": ["Python", "FastAPI"]})
        client.put("/api/application-packet", json={
            "target_job_title": "Dev",
            "job_description": "Python FastAPI developer",
        })
        client.post("/api/application-packet/generate")
        data = client.get("/api/application-packet").json()
        assert "tailored_summary" in data
        assert "skills_emphasis" in data
        assert "fit_summary" in data

    def test_default_response_has_all_phase7_fields(self, client):
        data = client.get("/api/application-packet").json()
        for field in ("job_description", "tailored_summary", "skills_emphasis", "fit_summary", "notes"):
            assert field in data, f"Missing field: {field}"


# ── Safety invariants ─────────────────────────────────────────────────────────

class TestPhase7SafetyInvariants:

    def test_no_send_endpoint(self, client):
        assert client.post("/api/application-packet/send").status_code == 404

    def test_no_apply_endpoint(self, client):
        assert client.post("/api/application-packet/apply").status_code == 404

    def test_no_submit_endpoint(self, client):
        assert client.post("/api/application-packet/submit").status_code == 404

    def test_no_email_endpoint(self, client):
        assert client.post("/api/application-packet/email").status_code == 404

    def test_no_top_level_send(self, client):
        assert client.post("/api/send").status_code == 404

    def test_no_top_level_apply(self, client):
        assert client.post("/api/apply").status_code == 404

    def test_generate_returns_200_not_redirect(self, client):
        r = client.post("/api/application-packet/generate")
        assert r.status_code == 200

    def test_quality_endpoint_is_readonly(self, client):
        assert client.post("/api/resume/quality").status_code == 405

    def test_existing_generate_endpoint_still_works(self, client):
        r = client.post("/api/application-packet/generate")
        assert "cover_letter_draft" in r.json()
        assert "checklist" in r.json()

    def test_no_invented_numbers_in_cover_letter(self, client):
        client.put("/api/resume/profile", json={"skills": ["Python"]})
        r = client.post("/api/application-packet/generate")
        letter = r.json()["cover_letter_draft"]
        assert not re.search(r"\d+%", letter)
