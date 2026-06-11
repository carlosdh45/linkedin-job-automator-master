"""
Phase 3 tests: candidate profile, resume upload, auth, safety invariants.

Safety invariants:
  - No /send or /apply endpoints exist
  - Profile fields contain no send/apply actions
  - Uploaded files stay in the configured uploads path
  - Unsupported file types and oversized files are rejected
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.api import auth as auth_module
from backend.config import get_db_path, get_profile_path, get_uploads_path
from backend.main import app
from src.db import initialize_database


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_sessions():
    auth_module._sessions.clear()
    yield
    auth_module._sessions.clear()


@pytest.fixture
def tmp_db(tmp_path):
    db_file = str(tmp_path / "test_phase3.db")
    initialize_database(db_file)
    return db_file


@pytest.fixture
def tmp_profile(tmp_path):
    return str(tmp_path / "profile.json")


@pytest.fixture
def tmp_uploads(tmp_path):
    return str(tmp_path / "uploads")


@pytest.fixture
def tmp_account(tmp_path):
    return str(tmp_path / "account.json")


@pytest.fixture
def client(tmp_db, tmp_profile, tmp_uploads, tmp_account, monkeypatch):
    monkeypatch.setenv("DOBRYBOT_DB_PATH", tmp_db)
    monkeypatch.setenv("DOBRYBOT_PROFILE_PATH", tmp_profile)
    monkeypatch.setenv("DOBRYBOT_UPLOADS_PATH", tmp_uploads)
    monkeypatch.setenv("DOBRYBOT_ACCOUNT_PATH", tmp_account)
    app.dependency_overrides[get_db_path] = lambda: tmp_db
    app.dependency_overrides[get_profile_path] = lambda: tmp_profile
    app.dependency_overrides[get_uploads_path] = lambda: tmp_uploads
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Profile ────────────────────────────────────────────────────────────────────

class TestProfile:

    def test_get_profile_returns_200(self, client):
        r = client.get("/api/profile")
        assert r.status_code == 200

    def test_get_profile_returns_default_id(self, client):
        assert client.get("/api/profile").json()["id"] == "default"

    def test_get_profile_returns_empty_strings_by_default(self, client):
        data = client.get("/api/profile").json()
        assert data["full_name"] == ""
        assert data["email"] == ""

    def test_get_profile_has_all_required_fields(self, client):
        data = client.get("/api/profile").json()
        for field in (
            "id", "full_name", "email", "target_roles", "seniority",
            "preferred_locations", "remote_preference", "salary_expectation",
            "linkedin_url", "portfolio_url", "github_url", "key_skills",
            "industries_of_interest", "resume_filename", "resume_original_filename",
            "resume_uploaded_at", "created_at", "updated_at",
        ):
            assert field in data, f"Missing profile field: {field}"

    def test_put_profile_updates_full_name(self, client):
        r = client.put("/api/profile", json={"full_name": "Jane Dev"})
        assert r.status_code == 200
        assert r.json()["full_name"] == "Jane Dev"

    def test_put_profile_updates_email(self, client):
        r = client.put("/api/profile", json={"email": "jane@example.com"})
        assert r.json()["email"] == "jane@example.com"

    def test_put_profile_updates_list_fields(self, client):
        r = client.put("/api/profile", json={
            "key_skills": ["Python", "FastAPI", "TypeScript"],
            "target_roles": ["Backend Engineer", "Staff Engineer"],
        })
        data = r.json()
        assert "Python" in data["key_skills"]
        assert "Backend Engineer" in data["target_roles"]

    def test_put_profile_persists_across_get(self, client):
        client.put("/api/profile", json={"full_name": "Persistent Name"})
        assert client.get("/api/profile").json()["full_name"] == "Persistent Name"

    def test_put_profile_preserves_earlier_fields(self, client):
        client.put("/api/profile", json={"full_name": "First Set"})
        client.put("/api/profile", json={"email": "second@example.com"})
        data = client.get("/api/profile").json()
        assert data["full_name"] == "First Set"
        assert data["email"] == "second@example.com"

    def test_put_profile_updates_updated_at(self, client):
        r1 = client.get("/api/profile").json()["updated_at"]
        client.put("/api/profile", json={"seniority": "senior"})
        r2 = client.get("/api/profile").json()["updated_at"]
        # updated_at should change (or at worst stay the same in fast tests)
        assert r2 >= r1


# ── Resume Upload ──────────────────────────────────────────────────────────────

class TestResumeUpload:

    def test_upload_pdf_accepted(self, client):
        r = client.post(
            "/api/profile/resume",
            files={"file": ("my_cv.pdf", b"%PDF-1.4 fake content", "application/pdf")},
        )
        assert r.status_code == 200
        assert r.json()["uploaded"] is True

    def test_upload_docx_accepted(self, client):
        r = client.post(
            "/api/profile/resume",
            files={"file": (
                "my_cv.docx",
                b"PK fake docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )},
        )
        assert r.status_code == 200
        assert r.json()["uploaded"] is True

    def test_upload_txt_rejected(self, client):
        r = client.post(
            "/api/profile/resume",
            files={"file": ("resume.txt", b"plain text", "text/plain")},
        )
        assert r.status_code == 422

    def test_upload_jpg_rejected(self, client):
        r = client.post(
            "/api/profile/resume",
            files={"file": ("photo.jpg", b"\xff\xd8\xff image", "image/jpeg")},
        )
        assert r.status_code == 422

    def test_upload_exe_rejected(self, client):
        r = client.post(
            "/api/profile/resume",
            files={"file": ("mal.exe", b"MZ\x90\x00", "application/octet-stream")},
        )
        assert r.status_code == 422

    def test_upload_html_rejected(self, client):
        r = client.post(
            "/api/profile/resume",
            files={"file": ("cv.html", b"<html>", "text/html")},
        )
        assert r.status_code == 422

    def test_oversized_file_rejected(self, client):
        big = b"x" * (5 * 1024 * 1024 + 1)
        r = client.post(
            "/api/profile/resume",
            files={"file": ("big.pdf", big, "application/pdf")},
        )
        assert r.status_code == 422

    def test_file_at_limit_accepted(self, client):
        at_limit = b"x" * (5 * 1024 * 1024)
        r = client.post(
            "/api/profile/resume",
            files={"file": ("limit.pdf", at_limit, "application/pdf")},
        )
        assert r.status_code == 200

    def test_upload_stores_file_under_uploads_path(self, client, tmp_uploads):
        client.post(
            "/api/profile/resume",
            files={"file": ("cv.pdf", b"%PDF test", "application/pdf")},
        )
        resume_dir = Path(tmp_uploads) / "resumes"
        assert resume_dir.exists()
        assert len(list(resume_dir.glob("*.pdf"))) == 1

    def test_uploaded_file_not_in_project_root(self, client):
        r = client.post(
            "/api/profile/resume",
            files={"file": ("cv.pdf", b"%PDF test", "application/pdf")},
        )
        stored = r.json()["filename"]
        assert not Path(stored).exists(), "File must not be stored in project root"

    def test_upload_updates_profile_resume_filename(self, client):
        client.post(
            "/api/profile/resume",
            files={"file": ("resume.pdf", b"%PDF", "application/pdf")},
        )
        data = client.get("/api/profile").json()
        assert data["resume_filename"] is not None
        assert data["resume_filename"].endswith(".pdf")

    def test_upload_updates_profile_original_filename(self, client):
        client.post(
            "/api/profile/resume",
            files={"file": ("my_resume.pdf", b"%PDF", "application/pdf")},
        )
        data = client.get("/api/profile").json()
        assert data["resume_original_filename"] == "my_resume.pdf"

    def test_upload_sets_resume_uploaded_at(self, client):
        client.post(
            "/api/profile/resume",
            files={"file": ("cv.pdf", b"%PDF", "application/pdf")},
        )
        data = client.get("/api/profile").json()
        assert data["resume_uploaded_at"] is not None

    def test_get_resume_info_404_when_none_uploaded(self, client):
        r = client.get("/api/profile/resume")
        assert r.status_code == 404

    def test_get_resume_info_returns_data_after_upload(self, client):
        client.post(
            "/api/profile/resume",
            files={"file": ("cv.pdf", b"%PDF", "application/pdf")},
        )
        r = client.get("/api/profile/resume")
        assert r.status_code == 200
        assert r.json()["original_filename"] == "cv.pdf"


# ── Auth ───────────────────────────────────────────────────────────────────────

class TestAuth:

    def test_register_creates_account(self, client):
        r = client.post("/api/auth/register", json={
            "email": "dev@example.com",
            "password": "supersecret",
            "full_name": "Dev User",
        })
        assert r.status_code == 200
        assert r.json()["registered"] is True
        assert r.json()["email"] == "dev@example.com"

    def test_register_duplicate_is_rejected(self, client):
        client.post("/api/auth/register", json={"email": "u@x.com", "password": "pw"})
        r = client.post("/api/auth/register", json={"email": "u2@x.com", "password": "pw2"})
        assert r.status_code == 409

    def test_login_returns_token(self, client):
        client.post("/api/auth/register", json={"email": "u@x.com", "password": "secret"})
        r = client.post("/api/auth/login", json={"email": "u@x.com", "password": "secret"})
        assert r.status_code == 200
        assert "token" in r.json()
        assert len(r.json()["token"]) > 0

    def test_login_wrong_password_rejected(self, client):
        client.post("/api/auth/register", json={"email": "u@x.com", "password": "correct"})
        r = client.post("/api/auth/login", json={"email": "u@x.com", "password": "wrong"})
        assert r.status_code == 401

    def test_login_wrong_email_rejected(self, client):
        client.post("/api/auth/register", json={"email": "u@x.com", "password": "pw"})
        r = client.post("/api/auth/login", json={"email": "other@x.com", "password": "pw"})
        assert r.status_code == 401

    def test_me_without_token_returns_401(self, client):
        assert client.get("/api/auth/me").status_code == 401

    def test_me_with_invalid_token_returns_401(self, client):
        r = client.get("/api/auth/me", headers={"Authorization": "Bearer bogus"})
        assert r.status_code == 401

    def test_me_returns_account_with_valid_token(self, client):
        client.post("/api/auth/register", json={
            "email": "u@x.com", "password": "pw", "full_name": "Dev"
        })
        token = client.post("/api/auth/login", json={"email": "u@x.com", "password": "pw"}).json()["token"]
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["email"] == "u@x.com"

    def test_logout_invalidates_token(self, client):
        client.post("/api/auth/register", json={"email": "u@x.com", "password": "pw"})
        token = client.post("/api/auth/login", json={"email": "u@x.com", "password": "pw"}).json()["token"]
        client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401

    def test_logout_without_token_returns_200(self, client):
        r = client.post("/api/auth/logout")
        assert r.status_code == 200
        assert r.json()["logged_out"] is True


# ── Safety invariants ──────────────────────────────────────────────────────────

class TestPhase3SafetyInvariants:

    def test_no_send_endpoint(self, client):
        assert client.post("/api/send").status_code == 404

    def test_no_apply_endpoint(self, client):
        assert client.post("/api/apply").status_code == 404

    def test_no_send_resume_endpoint(self, client):
        assert client.post("/api/profile/send-resume").status_code == 404

    def test_profile_fields_contain_no_send_or_apply(self, client):
        data = client.get("/api/profile").json()
        for key in data:
            assert "send" not in key.lower(), f"Profile field '{key}' contains 'send'"
            assert "apply" not in key.lower(), f"Profile field '{key}' contains 'apply'"

    def test_existing_dangerous_commands_still_disabled(self, client):
        assert client.post("/api/send-approved").status_code == 404
        assert client.post("/api/send-outreach").status_code == 404
