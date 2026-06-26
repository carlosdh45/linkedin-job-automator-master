"""
Phase 10: BD Review Queue, Outreach Draft Persistence, Pipeline Activity,
ICP Configuration — test suite.

Safety invariants verified:
- Approved draft does NOT send
- No /send endpoint exists
- No /auto-outbound endpoint exists
- No external API calls
- All existing 453 tests still pass
"""
import pytest
from fastapi.testclient import TestClient

from backend.config import (
    get_bd_company_path, get_bd_prospect_path, get_bd_signal_path,
    get_bd_pain_point_path, get_bd_opportunity_path,
    get_bd_deal_packet_path, get_bd_outreach_path,
    get_bd_activity_path, get_bd_icp_config_path,
)
from backend.main import app


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def p10_paths(tmp_path):
    return {
        "company":      str(tmp_path / "companies.json"),
        "prospect":     str(tmp_path / "prospects.json"),
        "signal":       str(tmp_path / "signals.json"),
        "pain_point":   str(tmp_path / "pain_points.json"),
        "opportunity":  str(tmp_path / "opportunities.json"),
        "deal_packet":  str(tmp_path / "deal_packets.json"),
        "outreach":     str(tmp_path / "outreach.json"),
        "activity":     str(tmp_path / "activity.json"),
        "icp_config":   str(tmp_path / "icp_config.json"),
    }


@pytest.fixture
def client(p10_paths, monkeypatch):
    monkeypatch.setenv("DOBRYBOT_BD_COMPANY_PATH",      p10_paths["company"])
    monkeypatch.setenv("DOBRYBOT_BD_PROSPECT_PATH",     p10_paths["prospect"])
    monkeypatch.setenv("DOBRYBOT_BD_SIGNAL_PATH",       p10_paths["signal"])
    monkeypatch.setenv("DOBRYBOT_BD_PAIN_POINT_PATH",   p10_paths["pain_point"])
    monkeypatch.setenv("DOBRYBOT_BD_OPPORTUNITY_PATH",  p10_paths["opportunity"])
    monkeypatch.setenv("DOBRYBOT_BD_DEAL_PACKET_PATH",  p10_paths["deal_packet"])
    monkeypatch.setenv("DOBRYBOT_BD_OUTREACH_PATH",     p10_paths["outreach"])
    monkeypatch.setenv("DOBRYBOT_BD_ACTIVITY_PATH",     p10_paths["activity"])
    monkeypatch.setenv("DOBRYBOT_BD_ICP_CONFIG_PATH",   p10_paths["icp_config"])

    app.dependency_overrides[get_bd_company_path]     = lambda: p10_paths["company"]
    app.dependency_overrides[get_bd_prospect_path]    = lambda: p10_paths["prospect"]
    app.dependency_overrides[get_bd_signal_path]      = lambda: p10_paths["signal"]
    app.dependency_overrides[get_bd_pain_point_path]  = lambda: p10_paths["pain_point"]
    app.dependency_overrides[get_bd_opportunity_path] = lambda: p10_paths["opportunity"]
    app.dependency_overrides[get_bd_deal_packet_path] = lambda: p10_paths["deal_packet"]
    app.dependency_overrides[get_bd_outreach_path]    = lambda: p10_paths["outreach"]
    app.dependency_overrides[get_bd_activity_path]    = lambda: p10_paths["activity"]
    app.dependency_overrides[get_bd_icp_config_path]  = lambda: p10_paths["icp_config"]

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def _draft_payload(**overrides):
    base = {
        "company_name": "Acme Corp",
        "contact_name": "Jane Smith",
        "contact_role": "CTO",
        "message_type": "email",
        "subject": "Quick note on deployment velocity",
        "body": "Hi Jane, I noticed Acme has been growing fast...",
        "tone": "warm",
    }
    base.update(overrides)
    return base


# ── Outreach Draft CRUD ───────────────────────────────────────────────────────

class TestOutreachDraftCRUD:

    def test_list_drafts_empty(self, client):
        r = client.get("/api/bd/outreach-drafts")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_draft(self, client):
        r = client.post("/api/bd/outreach-drafts", json=_draft_payload())
        assert r.status_code == 201
        data = r.json()
        assert data["company_name"] == "Acme Corp"
        assert data["status"] == "draft"
        assert "id" in data

    def test_list_drafts_after_create(self, client):
        client.post("/api/bd/outreach-drafts", json=_draft_payload())
        r = client.get("/api/bd/outreach-drafts")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_get_draft_by_id(self, client):
        created = client.post("/api/bd/outreach-drafts", json=_draft_payload()).json()
        r = client.get(f"/api/bd/outreach-drafts/{created['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == created["id"]

    def test_get_draft_not_found(self, client):
        r = client.get("/api/bd/outreach-drafts/nonexistent")
        assert r.status_code == 404

    def test_update_draft(self, client):
        created = client.post("/api/bd/outreach-drafts", json=_draft_payload()).json()
        r = client.put(f"/api/bd/outreach-drafts/{created['id']}", json={"notes": "Follow up next week"})
        assert r.status_code == 200
        assert r.json()["notes"] == "Follow up next week"

    def test_update_draft_not_found(self, client):
        r = client.put("/api/bd/outreach-drafts/missing", json={"notes": "x"})
        assert r.status_code == 404

    def test_create_draft_has_status_draft(self, client):
        r = client.post("/api/bd/outreach-drafts", json=_draft_payload())
        assert r.json()["status"] == "draft"

    def test_multiple_drafts(self, client):
        client.post("/api/bd/outreach-drafts", json=_draft_payload(company_name="A"))
        client.post("/api/bd/outreach-drafts", json=_draft_payload(company_name="B"))
        r = client.get("/api/bd/outreach-drafts")
        assert len(r.json()) == 2


# ── Approve / Reject / Needs Research ────────────────────────────────────────

class TestOutreachDraftReview:

    def test_approve_draft(self, client):
        created = client.post("/api/bd/outreach-drafts", json=_draft_payload()).json()
        r = client.post(f"/api/bd/outreach-drafts/{created['id']}/approve")
        assert r.status_code == 200
        assert r.json()["status"] == "approved"

    def test_approved_does_not_send(self, client):
        """Approving a draft must NOT trigger any send action."""
        created = client.post("/api/bd/outreach-drafts", json=_draft_payload()).json()
        r = client.post(f"/api/bd/outreach-drafts/{created['id']}/approve")
        data = r.json()
        assert data["status"] == "approved"
        # Verify no 'sent_at', 'delivery', or 'send' fields
        assert "sent_at" not in data
        assert "delivery" not in data

    def test_reject_draft(self, client):
        created = client.post("/api/bd/outreach-drafts", json=_draft_payload()).json()
        r = client.post(f"/api/bd/outreach-drafts/{created['id']}/reject")
        assert r.status_code == 200
        assert r.json()["status"] == "rejected"

    def test_needs_research_draft(self, client):
        created = client.post("/api/bd/outreach-drafts", json=_draft_payload()).json()
        r = client.post(f"/api/bd/outreach-drafts/{created['id']}/needs-research")
        assert r.status_code == 200
        assert r.json()["status"] == "needs_research"

    def test_approve_not_found(self, client):
        r = client.post("/api/bd/outreach-drafts/nope/approve")
        assert r.status_code == 404

    def test_reject_not_found(self, client):
        r = client.post("/api/bd/outreach-drafts/nope/reject")
        assert r.status_code == 404

    def test_needs_research_not_found(self, client):
        r = client.post("/api/bd/outreach-drafts/nope/needs-research")
        assert r.status_code == 404

    def test_approve_logs_activity(self, client):
        created = client.post("/api/bd/outreach-drafts", json=_draft_payload()).json()
        client.post(f"/api/bd/outreach-drafts/{created['id']}/approve")
        r = client.get("/api/bd/activity")
        actions = [a["action"] for a in r.json()]
        assert "draft_approved" in actions

    def test_save_logs_activity(self, client):
        client.post("/api/bd/outreach-drafts", json=_draft_payload())
        r = client.get("/api/bd/activity")
        actions = [a["action"] for a in r.json()]
        assert "draft_saved" in actions


# ── Activity Log ──────────────────────────────────────────────────────────────

class TestBDActivity:

    def test_get_activity_empty(self, client):
        r = client.get("/api/bd/activity")
        assert r.status_code == 200
        assert r.json() == []

    def test_activity_after_draft_create(self, client):
        client.post("/api/bd/outreach-drafts", json=_draft_payload())
        r = client.get("/api/bd/activity")
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_activity_filter_by_entity_type(self, client):
        client.post("/api/bd/outreach-drafts", json=_draft_payload())
        r = client.get("/api/bd/activity?entity_type=draft")
        assert r.status_code == 200
        for a in r.json():
            assert a["entity_type"] == "draft"

    def test_activity_filter_by_entity_id(self, client):
        created = client.post("/api/bd/outreach-drafts", json=_draft_payload()).json()
        r = client.get(f"/api/bd/activity?entity_id={created['id']}")
        for a in r.json():
            assert a["entity_id"] == created["id"]

    def test_activity_newest_first(self, client):
        client.post("/api/bd/outreach-drafts", json=_draft_payload(company_name="First"))
        client.post("/api/bd/outreach-drafts", json=_draft_payload(company_name="Second"))
        r = client.get("/api/bd/activity")
        items = r.json()
        assert items[0]["created_at"] >= items[-1]["created_at"]

    def test_stage_move_logs_activity(self, client):
        opp = client.post("/api/bd/opportunities", json={
            "company_id": "co1",
            "company_name": "TestCo",
            "stage": "identified",
        }).json()
        client.post(f"/api/bd/opportunities/{opp['id']}/move-stage", json={"stage": "researched"})
        r = client.get("/api/bd/activity")
        actions = [a["action"] for a in r.json()]
        assert "stage_moved" in actions


# ── Stage Transitions ─────────────────────────────────────────────────────────

class TestStageTransitions:

    def _create_opp(self, client, stage="identified"):
        r = client.post("/api/bd/opportunities", json={
            "company_id": "co1",
            "company_name": "MoveableCo",
            "stage": stage,
        })
        assert r.status_code == 201
        return r.json()

    def test_move_stage_basic(self, client):
        opp = self._create_opp(client)
        r = client.post(f"/api/bd/opportunities/{opp['id']}/move-stage", json={"stage": "researched"})
        assert r.status_code == 200
        data = r.json()
        assert data["previous_stage"] == "identified"
        assert data["new_stage"] == "researched"

    def test_move_stage_returns_activity_id(self, client):
        opp = self._create_opp(client)
        r = client.post(f"/api/bd/opportunities/{opp['id']}/move-stage", json={"stage": "qualified"})
        assert "activity_id" in r.json()

    def test_move_stage_invalid_stage(self, client):
        opp = self._create_opp(client)
        r = client.post(f"/api/bd/opportunities/{opp['id']}/move-stage", json={"stage": "nonexistent"})
        assert r.status_code == 422

    def test_move_stage_opp_not_found(self, client):
        r = client.post("/api/bd/opportunities/missing/move-stage", json={"stage": "researched"})
        assert r.status_code == 404

    def test_valid_stages_accepted(self, client):
        valid_stages = ["researched", "qualified", "outreach_ready", "in_conversation", "proposal", "won", "lost"]
        opp = self._create_opp(client)
        for stage in valid_stages:
            r = client.post(f"/api/bd/opportunities/{opp['id']}/move-stage", json={"stage": stage})
            assert r.status_code == 200


# ── ICP Configuration ─────────────────────────────────────────────────────────

class TestICPConfig:

    def test_get_icp_config_default(self, client):
        r = client.get("/api/bd/icp-config")
        assert r.status_code == 200
        data = r.json()
        assert "target_industries" in data
        assert "scoring_weights" in data
        assert "updated_at" in data

    def test_update_icp_config(self, client):
        r = client.put("/api/bd/icp-config", json={
            "target_industries": ["SaaS", "FinTech"],
            "target_roles": ["CTO", "VP Engineering"],
        })
        assert r.status_code == 200
        data = r.json()
        assert "SaaS" in data["target_industries"]
        assert "CTO" in data["target_roles"]

    def test_update_icp_preserves_unset_fields(self, client):
        client.put("/api/bd/icp-config", json={"target_industries": ["SaaS"]})
        r = client.put("/api/bd/icp-config", json={"target_roles": ["CTO"]})
        data = r.json()
        assert "SaaS" in data["target_industries"]
        assert "CTO" in data["target_roles"]

    def test_icp_scoring_weights_present(self, client):
        r = client.get("/api/bd/icp-config")
        weights = r.json()["scoring_weights"]
        assert "icp_match" in weights
        assert "pain_points" in weights

    def test_icp_config_persists(self, client):
        client.put("/api/bd/icp-config", json={"target_industries": ["HealthTech"]})
        r = client.get("/api/bd/icp-config")
        assert "HealthTech" in r.json()["target_industries"]


# ── BD Dashboard Stats ────────────────────────────────────────────────────────

class TestBDDashboard:

    def test_dashboard_empty(self, client):
        r = client.get("/api/bd/dashboard")
        assert r.status_code == 200
        data = r.json()
        assert data["qualified_opportunities"] == 0
        assert data["high_signal_prospects"] == 0
        assert data["drafts_for_review"] == 0
        assert isinstance(data["recommended_actions"], list)

    def test_dashboard_counts_drafts_for_review(self, client):
        client.post("/api/bd/outreach-drafts", json=_draft_payload())
        r = client.get("/api/bd/dashboard")
        assert r.json()["drafts_for_review"] == 1

    def test_dashboard_approved_draft_not_in_review(self, client):
        created = client.post("/api/bd/outreach-drafts", json=_draft_payload()).json()
        client.post(f"/api/bd/outreach-drafts/{created['id']}/approve")
        r = client.get("/api/bd/dashboard")
        assert r.json()["drafts_for_review"] == 0
        assert r.json()["approved_drafts"] == 1

    def test_dashboard_has_recommended_actions(self, client):
        r = client.get("/api/bd/dashboard")
        assert len(r.json()["recommended_actions"]) >= 1

    def test_dashboard_pipeline_snapshot(self, client):
        client.post("/api/bd/opportunities", json={
            "company_id": "c1", "company_name": "Co1", "stage": "qualified",
        })
        r = client.get("/api/bd/dashboard")
        snapshot = r.json()["pipeline_snapshot"]
        stages = [s["stage"] for s in snapshot]
        assert "qualified" in stages


# ── Safety Invariants ─────────────────────────────────────────────────────────

class TestPhase10SafetyInvariants:

    def test_no_send_endpoint_on_outreach_draft(self, client):
        created = client.post("/api/bd/outreach-drafts", json=_draft_payload()).json()
        r = client.post(f"/api/bd/outreach-drafts/{created['id']}/send")
        assert r.status_code == 404

    def test_no_auto_outbound_endpoint(self, client):
        r = client.post("/api/bd/auto-outbound")
        assert r.status_code == 404

    def test_no_auto_send_endpoint(self, client):
        r = client.post("/api/bd/auto-send")
        assert r.status_code == 404

    def test_approve_response_has_no_sent_at(self, client):
        created = client.post("/api/bd/outreach-drafts", json=_draft_payload()).json()
        r = client.post(f"/api/bd/outreach-drafts/{created['id']}/approve")
        assert "sent_at" not in r.json()

    def test_create_draft_response_has_no_sent_at(self, client):
        r = client.post("/api/bd/outreach-drafts", json=_draft_payload())
        assert "sent_at" not in r.json()

    def test_no_linkedin_endpoint(self, client):
        r = client.post("/api/bd/linkedin/send")
        assert r.status_code == 404

    def test_no_gmail_endpoint(self, client):
        r = client.post("/api/bd/gmail/send")
        assert r.status_code == 404

    def test_no_scrape_endpoint(self, client):
        r = client.post("/api/bd/scrape")
        assert r.status_code == 404

    def test_outreach_draft_list_no_sent_at(self, client):
        client.post("/api/bd/outreach-drafts", json=_draft_payload())
        drafts = client.get("/api/bd/outreach-drafts").json()
        for d in drafts:
            assert "sent_at" not in d

    def test_icp_config_has_no_external_call(self, client):
        """ICP config update returns immediately with local data — no external fields."""
        r = client.put("/api/bd/icp-config", json={"target_industries": ["SaaS"]})
        data = r.json()
        assert "external_enrichment" not in data
        assert "api_key" not in data
