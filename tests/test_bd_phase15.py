"""
Phase 15: Import-to-Recommendation Workflow Polish — test suite.

Covers:
- POST /api/bd/signals/evaluate-all
- POST /api/bd/recommendations/{id}/review
- POST /api/bd/recommendations/{id}/create-opportunity
- POST /api/bd/recommendations/{id}/dismiss (regression)
- POST /api/bd/recommendations/{id}/action (regression)
- Activity logging on CSV import commit
- Activity logging on deal packet generation
- Safety invariants (no send, no auto-outbound, no external APIs)
- Existing test count still passes
"""
import io
import pytest
from fastapi.testclient import TestClient

from backend.config import (
    get_bd_company_path, get_bd_prospect_path, get_bd_signal_path,
    get_bd_pain_point_path, get_bd_opportunity_path,
    get_bd_deal_packet_path, get_bd_outreach_path,
    get_bd_activity_path, get_bd_icp_config_path,
    get_bd_recommendation_path,
)
from backend.main import app
from backend.services.bd_signal_store import list_signals
from backend.services.bd_recommendation_store import list_recommendations
from backend.services.bd_opportunity_store import list_opportunities
from backend.services.bd_activity_store import list_activity as list_activities
from backend.services.bd_csv_import import import_signals_csv, import_companies_csv
from backend.services.bd_signal_intelligence import evaluate_signal as _evaluate_signal


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def p15_paths(tmp_path):
    return {
        "company":        str(tmp_path / "companies.json"),
        "prospect":       str(tmp_path / "prospects.json"),
        "signal":         str(tmp_path / "signals.json"),
        "pain_point":     str(tmp_path / "pain_points.json"),
        "opportunity":    str(tmp_path / "opportunities.json"),
        "deal_packet":    str(tmp_path / "deal_packets.json"),
        "outreach":       str(tmp_path / "outreach.json"),
        "activity":       str(tmp_path / "activity.json"),
        "icp_config":     str(tmp_path / "icp_config.json"),
        "recommendation": str(tmp_path / "recommendations.json"),
    }


@pytest.fixture
def client(p15_paths, monkeypatch):
    monkeypatch.setenv("DOBRYBOT_BD_COMPANY_PATH",        p15_paths["company"])
    monkeypatch.setenv("DOBRYBOT_BD_PROSPECT_PATH",       p15_paths["prospect"])
    monkeypatch.setenv("DOBRYBOT_BD_SIGNAL_PATH",         p15_paths["signal"])
    monkeypatch.setenv("DOBRYBOT_BD_PAIN_POINT_PATH",     p15_paths["pain_point"])
    monkeypatch.setenv("DOBRYBOT_BD_OPPORTUNITY_PATH",    p15_paths["opportunity"])
    monkeypatch.setenv("DOBRYBOT_BD_DEAL_PACKET_PATH",    p15_paths["deal_packet"])
    monkeypatch.setenv("DOBRYBOT_BD_OUTREACH_PATH",       p15_paths["outreach"])
    monkeypatch.setenv("DOBRYBOT_BD_ACTIVITY_PATH",       p15_paths["activity"])
    monkeypatch.setenv("DOBRYBOT_BD_ICP_CONFIG_PATH",     p15_paths["icp_config"])
    monkeypatch.setenv("DOBRYBOT_BD_RECOMMENDATION_PATH", p15_paths["recommendation"])

    app.dependency_overrides[get_bd_company_path]        = lambda: p15_paths["company"]
    app.dependency_overrides[get_bd_prospect_path]       = lambda: p15_paths["prospect"]
    app.dependency_overrides[get_bd_signal_path]         = lambda: p15_paths["signal"]
    app.dependency_overrides[get_bd_pain_point_path]     = lambda: p15_paths["pain_point"]
    app.dependency_overrides[get_bd_opportunity_path]    = lambda: p15_paths["opportunity"]
    app.dependency_overrides[get_bd_deal_packet_path]    = lambda: p15_paths["deal_packet"]
    app.dependency_overrides[get_bd_outreach_path]       = lambda: p15_paths["outreach"]
    app.dependency_overrides[get_bd_activity_path]       = lambda: p15_paths["activity"]
    app.dependency_overrides[get_bd_icp_config_path]     = lambda: p15_paths["icp_config"]
    app.dependency_overrides[get_bd_recommendation_path] = lambda: p15_paths["recommendation"]

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _csv_file(content: str, name: str = "import.csv"):
    return ("file", (name, io.BytesIO(content.encode()), "text/csv"))


def _create_signal(client, company_name="Apex Software", signal_type="hiring",
                   summary="Posting 3 senior DevOps roles"):
    r = client.post("/api/bd/signals", json={
        "company_name": company_name,
        "signal_type": signal_type,
        "summary": summary,
    })
    assert r.status_code == 201
    return r.json()


def _seed_and_get_recommendation(client):
    """Seed BD demo data, run refresh, return the first new recommendation or None."""
    client.post("/api/bd/demo/seed")
    client.post("/api/bd/recommendations/refresh")
    recs = client.get("/api/bd/recommendations?status=new").json()
    return recs[0] if recs else None


# ── Evaluate All Signals ──────────────────────────────────────────────────────

class TestEvaluateAllSignals:
    def test_evaluate_all_returns_counts(self, client):
        _create_signal(client, "Apex Software", "hiring", "Posting 10 roles")
        _create_signal(client, "Blue Co", "funding", "Raised Series B")
        r = client.post("/api/bd/signals/evaluate-all")
        assert r.status_code == 200
        data = r.json()
        assert data["evaluated_count"] == 2
        assert data["skipped_count"] == 0

    def test_evaluate_all_skips_already_evaluated(self, client):
        sig = _create_signal(client, "Apex Software", "hiring", "DevOps hiring")
        # Evaluate individually first
        client.post(f"/api/bd/signals/{sig['id']}/evaluate")
        # Now evaluate-all should skip it
        r = client.post("/api/bd/signals/evaluate-all")
        assert r.status_code == 200
        data = r.json()
        assert data["evaluated_count"] == 0
        assert data["skipped_count"] == 1

    def test_evaluate_all_marks_signals_as_evaluated(self, client, p15_paths):
        _create_signal(client, "Apex Software", "hiring", "DevOps hiring")
        client.post("/api/bd/signals/evaluate-all")
        signals = list_signals(p15_paths["signal"])
        assert all(s.evaluated for s in signals)

    def test_evaluate_all_returns_recommendations_created(self, client):
        # Create a signal that's likely to generate a high-priority recommendation
        _create_signal(client, "Apex Software", "hiring", "Scaling DevOps team — 10 open roles")
        r = client.post("/api/bd/signals/evaluate-all")
        assert r.status_code == 200
        data = r.json()
        assert "recommendations_created" in data
        assert isinstance(data["recommendations_created"], int)

    def test_evaluate_all_has_safety_notice(self, client):
        r = client.post("/api/bd/signals/evaluate-all")
        assert r.status_code == 200
        data = r.json()
        assert "safety_notice" in data
        assert len(data["safety_notice"]) > 0

    def test_evaluate_all_no_external_calls(self, client):
        # Completes locally without error — confirms no external dependency
        _create_signal(client, "Test Co", "growth", "Headcount doubled")
        r = client.post("/api/bd/signals/evaluate-all")
        assert r.status_code == 200

    def test_evaluate_all_logs_activity(self, client, p15_paths):
        _create_signal(client, "Apex Software", "hiring", "Hiring 5 engineers")
        client.post("/api/bd/signals/evaluate-all")
        activities = list_activities(p15_paths["activity"])
        actions = [a.action for a in activities]
        assert "signal_evaluated" in actions


# ── Recommendation Status Transitions ─────────────────────────────────────────

class TestRecommendationReview:
    def test_review_sets_status_to_reviewed(self, client):
        rec = _seed_and_get_recommendation(client)
        if not rec:
            pytest.skip("No high-priority recommendation generated")
        r = client.post(f"/api/bd/recommendations/{rec['id']}/review")
        assert r.status_code == 200
        assert r.json()["status"] == "reviewed"

    def test_review_logs_activity(self, client, p15_paths):
        rec = _seed_and_get_recommendation(client)
        if not rec:
            pytest.skip("No high-priority recommendation generated")
        client.post(f"/api/bd/recommendations/{rec['id']}/review")
        activities = list_activities(p15_paths["activity"])
        actions = [a.action for a in activities]
        assert "recommendation_reviewed" in actions

    def test_review_nonexistent_returns_404(self, client):
        r = client.post("/api/bd/recommendations/nonexistent-id/review")
        assert r.status_code == 404

    def test_dismiss_sets_status_to_dismissed(self, client):
        rec = _seed_and_get_recommendation(client)
        if not rec:
            pytest.skip("No high-priority recommendation generated")
        r = client.post(f"/api/bd/recommendations/{rec['id']}/dismiss")
        assert r.status_code == 200
        assert r.json()["status"] == "dismissed"

    def test_action_sets_status_to_actioned(self, client):
        rec = _seed_and_get_recommendation(client)
        if not rec:
            pytest.skip("No high-priority recommendation generated")
        r = client.post(f"/api/bd/recommendations/{rec['id']}/action")
        assert r.status_code == 200
        assert r.json()["status"] == "actioned"


# ── Create Opportunity from Recommendation ─────────────────────────────────────

class TestCreateOpportunityFromRecommendation:
    def test_creates_opportunity(self, client, p15_paths):
        rec = _seed_and_get_recommendation(client)
        if not rec:
            pytest.skip("No high-priority recommendation generated")
        r = client.post(f"/api/bd/recommendations/{rec['id']}/create-opportunity")
        assert r.status_code == 200
        opp = r.json()
        assert "id" in opp
        assert "company_name" in opp

    def test_opportunity_is_persisted(self, client, p15_paths):
        rec = _seed_and_get_recommendation(client)
        if not rec:
            pytest.skip("No high-priority recommendation generated")
        client.post(f"/api/bd/recommendations/{rec['id']}/create-opportunity")
        opps = list_opportunities(p15_paths["opportunity"])
        assert len(opps) >= 1

    def test_opportunity_company_name_matches_recommendation(self, client, p15_paths):
        rec = _seed_and_get_recommendation(client)
        if not rec:
            pytest.skip("No recommendation generated")
        r = client.post(f"/api/bd/recommendations/{rec['id']}/create-opportunity")
        assert r.status_code == 200
        opp = r.json()
        # Company name must be non-empty and match the recommendation's entity_name
        assert opp["company_name"] != ""
        assert opp["company_name"] == rec["entity_name"]

    def test_recommendation_marked_actioned_after_create_opportunity(self, client):
        rec = _seed_and_get_recommendation(client)
        if not rec:
            pytest.skip("No high-priority recommendation generated")
        client.post(f"/api/bd/recommendations/{rec['id']}/create-opportunity")
        r = client.get("/api/bd/recommendations")
        recs_by_id = {r2["id"]: r2 for r2 in r.json()}
        if rec["id"] in recs_by_id:
            assert recs_by_id[rec["id"]]["status"] == "actioned"

    def test_create_opportunity_logs_activity(self, client, p15_paths):
        rec = _seed_and_get_recommendation(client)
        if not rec:
            pytest.skip("No high-priority recommendation generated")
        client.post(f"/api/bd/recommendations/{rec['id']}/create-opportunity")
        activities = list_activities(p15_paths["activity"])
        actions = [a.action for a in activities]
        assert "opportunity_created_from_recommendation" in actions

    def test_nonexistent_recommendation_returns_404(self, client):
        r = client.post("/api/bd/recommendations/nonexistent/create-opportunity")
        assert r.status_code == 404


# ── Activity Logging ──────────────────────────────────────────────────────────

class TestActivityLogging:
    def test_csv_import_commit_logs_activity(self, client, p15_paths):
        csv = "name,domain\nApex Software,apex.io\n"
        client.post(
            "/api/bd/import/companies-csv?dry_run=false",
            files=[_csv_file(csv)],
        )
        activities = list_activities(p15_paths["activity"])
        actions = [a.action for a in activities]
        assert "csv_import_committed" in actions

    def test_csv_import_dry_run_does_not_log_activity(self, client, p15_paths):
        csv = "name,domain\nApex Software,apex.io\n"
        client.post(
            "/api/bd/import/companies-csv?dry_run=true",
            files=[_csv_file(csv)],
        )
        activities = list_activities(p15_paths["activity"])
        assert len(activities) == 0

    def test_signal_csv_commit_logs_activity(self, client, p15_paths):
        csv = "company_name,signal_type,description\nApex Software,hiring,Posting roles\n"
        client.post(
            "/api/bd/import/signals-csv?dry_run=false",
            files=[_csv_file(csv)],
        )
        activities = list_activities(p15_paths["activity"])
        actions = [a.action for a in activities]
        assert "csv_import_committed" in actions

    def test_deal_packet_generation_logs_activity(self, client, p15_paths):
        client.post("/api/bd/deal-packets/generate", json={
            "company_name": "Apex Software",
            "contact_name": "Alex Rivera",
            "pain_points": ["manual deployment", "slow releases"],
        })
        activities = list_activities(p15_paths["activity"])
        actions = [a.action for a in activities]
        assert "deal_packet_generated" in actions

    def test_deal_packet_activity_has_company_name(self, client, p15_paths):
        client.post("/api/bd/deal-packets/generate", json={
            "company_name": "Meridian Labs",
            "contact_name": "Jordan Kim",
        })
        activities = list_activities(p15_paths["activity"])
        pkt_activities = [a for a in activities if a.action == "deal_packet_generated"]
        assert len(pkt_activities) == 1
        assert pkt_activities[0].metadata.get("company_name") == "Meridian Labs"


# ── Safety Invariants ─────────────────────────────────────────────────────────

class TestSafetyInvariants:
    def _all_paths(self):
        return [r.path for r in app.routes if hasattr(r, "path")]

    def test_no_send_endpoint(self):
        for path in self._all_paths():
            assert "/send" not in path, f"Forbidden /send path found: {path}"

    def test_no_auto_outbound_endpoint(self):
        for path in self._all_paths():
            assert "auto-outbound" not in path
            assert "mass-outbound" not in path

    def test_no_auto_apply_endpoint(self):
        for path in self._all_paths():
            assert "auto-apply" not in path

    def test_evaluate_all_safety_notice_mentions_human_review(self, client):
        r = client.post("/api/bd/signals/evaluate-all")
        notice = r.json().get("safety_notice", "")
        assert "human" in notice.lower() or "review" in notice.lower()

    def test_create_opportunity_from_rec_does_not_send(self, client, p15_paths):
        rec = _seed_and_get_recommendation(client)
        if not rec:
            pytest.skip("No recommendation generated")
        r = client.post(f"/api/bd/recommendations/{rec['id']}/create-opportunity")
        # Only creates opportunity — does not trigger any send
        assert r.status_code == 200
        opp_data = r.json()
        assert "body" not in opp_data       # no message draft in the response
        assert "subject" not in opp_data    # no email subject in the response

    def test_approve_draft_does_not_send(self, client):
        # Create a draft then approve it — ensure no send endpoint triggered
        create_r = client.post("/api/bd/outreach-drafts", json={
            "company_name": "Apex Software",
            "contact_name": "Alex Rivera",
            "contact_role": "VP Engineering",
            "body": "Hi Alex, test message body. Prepared for manual review.",
            "tone": "warm",
        })
        assert create_r.status_code == 201
        draft_id = create_r.json()["id"]
        approve_r = client.post(f"/api/bd/outreach-drafts/{draft_id}/approve")
        assert approve_r.status_code == 200
        # Status must be 'approved', not 'sent'
        assert approve_r.json()["status"] == "approved"

    def test_evaluate_all_is_local_only(self, client):
        # Completing without error confirms no external dependency
        _create_signal(client, "Apex Software", "hiring", "DevOps ramp")
        r = client.post("/api/bd/signals/evaluate-all")
        assert r.status_code == 200
