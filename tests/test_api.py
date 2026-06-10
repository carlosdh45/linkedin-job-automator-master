"""
API tests for DobryBot FastAPI backend.

Safety invariants tested:
  - No /send endpoint exists
  - No /apply endpoint exists
  - Approve endpoint enforces Quality Guard (failed/pending blocked, passed allowed)
  - Demo seed/clear make no external calls
"""
import os

import pytest
from fastapi.testclient import TestClient

from backend.config import get_db_path
from backend.main import app
from src.db import initialize_database
from src.seed_data import seed_demo_data


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_db(tmp_path):
    db_file = str(tmp_path / "test_api.db")
    initialize_database(db_file)
    return db_file


@pytest.fixture
def seeded_db(tmp_db):
    seed_demo_data(tmp_db)
    return tmp_db


@pytest.fixture
def client(tmp_db, monkeypatch):
    monkeypatch.setenv("DOBRYBOT_DB_PATH", tmp_db)
    app.dependency_overrides[get_db_path] = lambda: tmp_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_client(seeded_db, monkeypatch):
    monkeypatch.setenv("DOBRYBOT_DB_PATH", seeded_db)
    app.dependency_overrides[get_db_path] = lambda: seeded_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Health ─────────────────────────────────────────────────────────────────────

class TestApiHealth:

    def test_health_returns_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_has_service_name(self, client):
        r = client.get("/health")
        assert r.json()["service"] == "dobrybot-api"

    def test_health_has_timestamp(self, client):
        r = client.get("/health")
        assert "timestamp" in r.json()


# ── Stats ──────────────────────────────────────────────────────────────────────

class TestApiStats:

    def test_stats_returns_dict(self, client):
        r = client.get("/api/stats")
        assert r.status_code == 200
        assert isinstance(r.json(), dict)

    def test_stats_has_known_keys(self, seeded_client):
        r = seeded_client.get("/api/stats")
        data = r.json()
        assert "outreach_pending_review" in data
        assert "outreach_sent" in data

    def test_stats_sent_is_zero_in_fresh_db(self, client):
        r = client.get("/api/stats")
        assert r.json().get("outreach_sent", 0) == 0


# ── Daily Brief ────────────────────────────────────────────────────────────────

class TestApiDailyBrief:

    def test_daily_brief_returns_200(self, seeded_client):
        r = seeded_client.get("/api/daily-brief")
        assert r.status_code == 200

    def test_daily_brief_has_required_keys(self, seeded_client):
        r = seeded_client.get("/api/daily-brief")
        data = r.json()
        for key in ("date", "stats", "top_jobs", "top_leads", "pending_drafts", "recommended_actions"):
            assert key in data, f"Missing key: {key}"

    def test_daily_brief_shows_seeded_jobs(self, seeded_client):
        r = seeded_client.get("/api/daily-brief")
        assert len(r.json()["top_jobs"]) > 0

    def test_daily_brief_shows_seeded_leads(self, seeded_client):
        r = seeded_client.get("/api/daily-brief")
        assert len(r.json()["top_leads"]) > 0

    def test_daily_brief_pending_drafts_total_positive(self, seeded_client):
        r = seeded_client.get("/api/daily-brief")
        assert r.json()["pending_drafts"]["total"] > 0

    def test_daily_brief_recommended_actions_present(self, seeded_client):
        r = seeded_client.get("/api/daily-brief")
        assert len(r.json()["recommended_actions"]) > 0


# ── Jobs ───────────────────────────────────────────────────────────────────────

class TestApiJobs:

    def test_jobs_returns_list(self, seeded_client):
        r = seeded_client.get("/api/jobs")
        assert r.status_code == 200
        assert "jobs" in r.json()

    def test_jobs_filter_by_status(self, seeded_client):
        r = seeded_client.get("/api/jobs?status=scored")
        assert r.status_code == 200
        jobs = r.json()["jobs"]
        assert len(jobs) > 0
        assert all(j["status"] == "scored" for j in jobs)

    def test_jobs_total_matches_list_length(self, seeded_client):
        r = seeded_client.get("/api/jobs")
        data = r.json()
        assert data["total"] == len(data["jobs"])

    def test_jobs_context_data_decoded(self, seeded_client):
        r = seeded_client.get("/api/jobs")
        for job in r.json()["jobs"]:
            assert not isinstance(job.get("context_data"), str), \
                "context_data should be decoded from JSON string"


# ── Leads ──────────────────────────────────────────────────────────────────────

class TestApiLeads:

    def test_leads_returns_list(self, seeded_client):
        r = seeded_client.get("/api/leads")
        assert r.status_code == 200
        assert "leads" in r.json()

    def test_leads_filter_by_status(self, seeded_client):
        r = seeded_client.get("/api/leads?status=scored")
        data = r.json()
        assert len(data["leads"]) > 0
        assert all(l["status"] == "scored" for l in data["leads"])

    def test_leads_pain_points_is_list(self, seeded_client):
        r = seeded_client.get("/api/leads")
        for lead in r.json()["leads"]:
            assert isinstance(lead["pain_points"], list), "pain_points must be a list"

    def test_leads_context_data_is_dict(self, seeded_client):
        r = seeded_client.get("/api/leads")
        for lead in r.json()["leads"]:
            assert isinstance(lead["context_data"], dict), "context_data must be a dict"


# ── Review Queue ───────────────────────────────────────────────────────────────

class TestApiReviewQueue:

    def test_review_queue_returns_drafts(self, seeded_client):
        r = seeded_client.get("/api/review-queue")
        assert r.status_code == 200
        assert "drafts" in r.json()

    def test_review_queue_total_positive(self, seeded_client):
        r = seeded_client.get("/api/review-queue")
        assert r.json()["total"] > 0

    def test_review_queue_only_needs_review_status(self, seeded_client):
        r = seeded_client.get("/api/review-queue")
        for d in r.json()["drafts"]:
            assert d["status"] == "needs_review"

    def test_review_queue_empty_on_fresh_db(self, client):
        r = client.get("/api/review-queue")
        assert r.json()["total"] == 0


# ── Approval Gate — Quality Guard enforcement ──────────────────────────────────

class TestApiApprovalGate:

    def _find_draft(self, client, quality_status: str):
        r = client.get("/api/review-queue")
        for d in r.json()["drafts"]:
            if d["quality_status"] == quality_status:
                return d["id"]
        return None

    def test_approve_passed_draft_succeeds(self, seeded_client):
        draft_id = self._find_draft(seeded_client, "passed")
        assert draft_id is not None, "Seeded data must include a passed draft"
        r = seeded_client.post(f"/api/drafts/{draft_id}/approve")
        assert r.status_code == 200
        assert r.json()["approved"] is True

    def test_approve_failed_draft_is_blocked(self, seeded_client):
        draft_id = self._find_draft(seeded_client, "failed")
        assert draft_id is not None, "Seeded data must include a failed draft"
        r = seeded_client.post(f"/api/drafts/{draft_id}/approve")
        assert r.status_code == 422

    def test_approve_pending_draft_is_blocked(self, seeded_client):
        draft_id = self._find_draft(seeded_client, "pending")
        assert draft_id is not None, "Seeded data must include a pending draft"
        r = seeded_client.post(f"/api/drafts/{draft_id}/approve")
        assert r.status_code == 422

    def test_approve_nonexistent_draft_is_blocked(self, seeded_client):
        r = seeded_client.post("/api/drafts/999999/approve")
        assert r.status_code == 422

    def test_approved_draft_leaves_review_queue(self, seeded_client):
        draft_id = self._find_draft(seeded_client, "passed")
        seeded_client.post(f"/api/drafts/{draft_id}/approve")
        r = seeded_client.get("/api/review-queue")
        ids = [d["id"] for d in r.json()["drafts"]]
        assert draft_id not in ids

    # ── Forbidden endpoints ──────────────────────────────────────────────────

    def test_no_send_endpoint(self, client):
        assert client.post("/api/send").status_code == 404

    def test_no_apply_endpoint(self, client):
        assert client.post("/api/apply").status_code == 404

    def test_no_send_approved_endpoint(self, client):
        assert client.post("/api/send-approved").status_code == 404

    def test_no_send_outreach_endpoint(self, client):
        assert client.post("/api/send-outreach").status_code == 404


# ── Skip ───────────────────────────────────────────────────────────────────────

class TestApiSkip:

    def test_skip_with_reason_succeeds(self, seeded_client):
        r = seeded_client.get("/api/review-queue")
        draft_id = r.json()["drafts"][0]["id"]
        r2 = seeded_client.post(
            f"/api/drafts/{draft_id}/skip",
            json={"reason": "not relevant"},
        )
        assert r2.status_code == 200
        assert r2.json()["skipped"] is True

    def test_skip_without_body_succeeds(self, seeded_client):
        r = seeded_client.get("/api/review-queue")
        draft_id = r.json()["drafts"][0]["id"]
        r2 = seeded_client.post(f"/api/drafts/{draft_id}/skip")
        assert r2.status_code == 200
        assert r2.json()["skipped"] is True

    def test_skip_removes_draft_from_queue(self, seeded_client):
        r = seeded_client.get("/api/review-queue")
        draft_id = r.json()["drafts"][0]["id"]
        seeded_client.post(f"/api/drafts/{draft_id}/skip")
        r2 = seeded_client.get("/api/review-queue")
        assert draft_id not in [d["id"] for d in r2.json()["drafts"]]

    def test_skip_nonexistent_returns_skipped_false(self, seeded_client):
        r = seeded_client.post("/api/drafts/999999/skip")
        assert r.status_code == 200
        assert r.json()["skipped"] is False


# ── Needs Research ─────────────────────────────────────────────────────────────

class TestApiNeedsResearch:

    def test_needs_research_flags_draft(self, seeded_client):
        r = seeded_client.get("/api/review-queue")
        draft_id = r.json()["drafts"][0]["id"]
        r2 = seeded_client.post(f"/api/drafts/{draft_id}/needs-research")
        assert r2.status_code == 200
        assert r2.json()["flagged"] is True
        assert r2.json()["action"] == "needs_research"

    def test_needs_research_with_note(self, seeded_client):
        r = seeded_client.get("/api/review-queue")
        draft_id = r.json()["drafts"][0]["id"]
        r2 = seeded_client.post(
            f"/api/drafts/{draft_id}/needs-research",
            json={"note": "Need to find better contact"},
        )
        assert r2.status_code == 200
        assert r2.json()["flagged"] is True

    def test_needs_research_removes_from_queue(self, seeded_client):
        r = seeded_client.get("/api/review-queue")
        draft_id = r.json()["drafts"][0]["id"]
        seeded_client.post(f"/api/drafts/{draft_id}/needs-research")
        r2 = seeded_client.get("/api/review-queue")
        assert draft_id not in [d["id"] for d in r2.json()["drafts"]]

    def test_needs_research_nonexistent_returns_flagged_false(self, seeded_client):
        r = seeded_client.post("/api/drafts/999999/needs-research")
        assert r.status_code == 200
        assert r.json()["flagged"] is False


# ── Demo ───────────────────────────────────────────────────────────────────────

class TestApiDemo:

    def test_seed_returns_stats(self, client):
        r = client.post("/api/demo/seed")
        assert r.status_code == 200
        data = r.json()
        assert data["seeded"] is True
        assert "stats" in data

    def test_seed_creates_jobs(self, client):
        client.post("/api/demo/seed")
        r = client.get("/api/jobs")
        assert r.json()["total"] > 0

    def test_seed_creates_leads(self, client):
        client.post("/api/demo/seed")
        r = client.get("/api/leads")
        assert r.json()["total"] > 0

    def test_seed_creates_drafts(self, client):
        client.post("/api/demo/seed")
        r = client.get("/api/review-queue")
        assert r.json()["total"] > 0

    def test_seed_is_idempotent(self, client):
        client.post("/api/demo/seed")
        r2 = client.post("/api/demo/seed")
        stats = r2.json()["stats"]
        assert stats["jobs_created"] == 0
        assert stats["skipped"] > 0

    def test_clear_removes_demo_records(self, seeded_client):
        r1 = seeded_client.get("/api/jobs")
        count_before = r1.json()["total"]
        seeded_client.post("/api/demo/clear")
        r2 = seeded_client.get("/api/jobs")
        assert r2.json()["total"] < count_before

    def test_seed_makes_no_external_calls(self, client):
        r = client.post("/api/demo/seed")
        assert r.status_code == 200
        assert r.json()["seeded"] is True
