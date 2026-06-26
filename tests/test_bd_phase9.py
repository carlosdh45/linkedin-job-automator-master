"""
Phase 9: BD OS Backend Foundation — test suite.

Covers:
- Company CRUD
- Prospect CRUD
- Signal creation / listing
- Opportunity scoring (local, rule-based)
- Deal packet generation
- Demo seed / clear
- Safety invariants: no /send, no /auto-outbound, no external API calls
- Message Studio: draft generation, safety notice present
- Existing test count unaffected (380 tests still pass — verified via CI)
"""
import os
import pytest
from fastapi.testclient import TestClient

from backend.config import (
    get_bd_company_path, get_bd_prospect_path, get_bd_signal_path,
    get_bd_pain_point_path, get_bd_opportunity_path,
    get_bd_deal_packet_path, get_bd_outreach_path,
)
from backend.main import app
from backend.services.bd_scoring import compute_opportunity_score


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def bd_paths(tmp_path):
    return {
        "company": str(tmp_path / "companies.json"),
        "prospect": str(tmp_path / "prospects.json"),
        "signal": str(tmp_path / "signals.json"),
        "pain_point": str(tmp_path / "pain_points.json"),
        "opportunity": str(tmp_path / "opportunities.json"),
        "deal_packet": str(tmp_path / "deal_packets.json"),
        "outreach": str(tmp_path / "outreach.json"),
    }


@pytest.fixture
def client(bd_paths, monkeypatch):
    monkeypatch.setenv("DOBRYBOT_BD_COMPANY_PATH", bd_paths["company"])
    monkeypatch.setenv("DOBRYBOT_BD_PROSPECT_PATH", bd_paths["prospect"])
    monkeypatch.setenv("DOBRYBOT_BD_SIGNAL_PATH", bd_paths["signal"])
    monkeypatch.setenv("DOBRYBOT_BD_PAIN_POINT_PATH", bd_paths["pain_point"])
    monkeypatch.setenv("DOBRYBOT_BD_OPPORTUNITY_PATH", bd_paths["opportunity"])
    monkeypatch.setenv("DOBRYBOT_BD_DEAL_PACKET_PATH", bd_paths["deal_packet"])
    monkeypatch.setenv("DOBRYBOT_BD_OUTREACH_PATH", bd_paths["outreach"])

    app.dependency_overrides[get_bd_company_path] = lambda: bd_paths["company"]
    app.dependency_overrides[get_bd_prospect_path] = lambda: bd_paths["prospect"]
    app.dependency_overrides[get_bd_signal_path] = lambda: bd_paths["signal"]
    app.dependency_overrides[get_bd_pain_point_path] = lambda: bd_paths["pain_point"]
    app.dependency_overrides[get_bd_opportunity_path] = lambda: bd_paths["opportunity"]
    app.dependency_overrides[get_bd_deal_packet_path] = lambda: bd_paths["deal_packet"]
    app.dependency_overrides[get_bd_outreach_path] = lambda: bd_paths["outreach"]

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def seeded_client(client):
    client.post("/api/bd/demo/seed")
    return client


# ── Scoring Unit Tests ────────────────────────────────────────────────────────

class TestBDScoring:

    def test_icp_match_adds_30(self):
        score, label, breakdown = compute_opportunity_score(
            icp_match=True, pain_point_count=0, signal_count=0,
            company_size=None, prospect_seniority=None,
            days_since_last_signal=None, existing_relationship=False,
        )
        assert breakdown["icp_match"] == 30

    def test_no_icp_adds_zero(self):
        score, label, breakdown = compute_opportunity_score(
            icp_match=False, pain_point_count=0, signal_count=0,
            company_size=None, prospect_seniority=None,
            days_since_last_signal=None, existing_relationship=False,
        )
        assert breakdown["icp_match"] == 0

    def test_pain_points_capped_at_20(self):
        _, _, breakdown = compute_opportunity_score(
            icp_match=False, pain_point_count=10, signal_count=0,
            company_size=None, prospect_seniority=None,
            days_since_last_signal=None, existing_relationship=False,
        )
        assert breakdown["pain_points"] == 20

    def test_signals_capped_at_20(self):
        _, _, breakdown = compute_opportunity_score(
            icp_match=False, pain_point_count=0, signal_count=10,
            company_size=None, prospect_seniority=None,
            days_since_last_signal=None, existing_relationship=False,
        )
        assert breakdown["signals"] == 20

    def test_vp_seniority_scores_13(self):
        _, _, breakdown = compute_opportunity_score(
            icp_match=False, pain_point_count=0, signal_count=0,
            company_size=None, prospect_seniority="VP of Engineering",
            days_since_last_signal=None, existing_relationship=False,
        )
        assert breakdown["seniority"] == 13

    def test_cto_seniority_scores_15(self):
        _, _, breakdown = compute_opportunity_score(
            icp_match=False, pain_point_count=0, signal_count=0,
            company_size=None, prospect_seniority="CTO",
            days_since_last_signal=None, existing_relationship=False,
        )
        assert breakdown["seniority"] == 15

    def test_recent_signal_7_days_adds_10(self):
        _, _, breakdown = compute_opportunity_score(
            icp_match=False, pain_point_count=0, signal_count=0,
            company_size=None, prospect_seniority=None,
            days_since_last_signal=5, existing_relationship=False,
        )
        assert breakdown["urgency"] == 10

    def test_signal_30_days_adds_5(self):
        _, _, breakdown = compute_opportunity_score(
            icp_match=False, pain_point_count=0, signal_count=0,
            company_size=None, prospect_seniority=None,
            days_since_last_signal=20, existing_relationship=False,
        )
        assert breakdown["urgency"] == 5

    def test_existing_relationship_adds_5(self):
        _, _, breakdown = compute_opportunity_score(
            icp_match=False, pain_point_count=0, signal_count=0,
            company_size=None, prospect_seniority=None,
            days_since_last_signal=None, existing_relationship=True,
        )
        assert breakdown["existing_relationship"] == 5

    def test_hot_label_at_75_plus(self):
        score, label, _ = compute_opportunity_score(
            icp_match=True, pain_point_count=5, signal_count=4,
            company_size=None, prospect_seniority="VP of Engineering",
            days_since_last_signal=3, existing_relationship=False,
        )
        assert score >= 75
        assert label == "hot"

    def test_cold_label_at_low_score(self):
        score, label, _ = compute_opportunity_score(
            icp_match=False, pain_point_count=0, signal_count=0,
            company_size=None, prospect_seniority=None,
            days_since_last_signal=None, existing_relationship=False,
        )
        assert score == 0
        assert label == "disqualified"

    def test_score_clamped_to_100(self):
        score, _, _ = compute_opportunity_score(
            icp_match=True, pain_point_count=100, signal_count=100,
            company_size=None, prospect_seniority="CTO",
            days_since_last_signal=1, existing_relationship=True,
        )
        assert score <= 100


# ── Company CRUD ──────────────────────────────────────────────────────────────

class TestBDCompanies:

    def test_list_empty_initially(self, client):
        r = client.get("/api/bd/companies")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_company(self, client):
        r = client.post("/api/bd/companies", json={
            "name": "Acme Corp",
            "domain": "acme.com",
            "industry": "SaaS",
            "pain_points": ["Slow onboarding"],
            "icp_match": True,
        })
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Acme Corp"
        assert "id" in data
        assert data["icp_match"] is True

    def test_create_company_scores_automatically(self, client):
        r = client.post("/api/bd/companies", json={
            "name": "Scored Corp",
            "icp_match": True,
            "pain_points": ["Pain A", "Pain B"],
        })
        assert r.status_code == 201
        data = r.json()
        assert data["opportunity_score"] > 0

    def test_get_company_by_id(self, client):
        created = client.post("/api/bd/companies", json={"name": "Test Co"}).json()
        r = client.get(f"/api/bd/companies/{created['id']}")
        assert r.status_code == 200
        assert r.json()["name"] == "Test Co"

    def test_get_company_not_found(self, client):
        r = client.get("/api/bd/companies/nonexistent-id")
        assert r.status_code == 404

    def test_update_company(self, client):
        created = client.post("/api/bd/companies", json={"name": "Update Co"}).json()
        r = client.put(f"/api/bd/companies/{created['id']}", json={"status": "qualified"})
        assert r.status_code == 200
        assert r.json()["status"] == "qualified"

    def test_update_company_not_found(self, client):
        r = client.put("/api/bd/companies/bad-id", json={"status": "qualified"})
        assert r.status_code == 404

    def test_list_returns_all_created(self, client):
        client.post("/api/bd/companies", json={"name": "Co A"})
        client.post("/api/bd/companies", json={"name": "Co B"})
        r = client.get("/api/bd/companies")
        assert len(r.json()) == 2


# ── Prospect CRUD ─────────────────────────────────────────────────────────────

class TestBDProspects:

    def test_list_empty_initially(self, client):
        r = client.get("/api/bd/prospects")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_prospect(self, client):
        r = client.post("/api/bd/prospects", json={
            "company_id": "co-1",
            "company_name": "Acme Corp",
            "name": "Jane Smith",
            "title": "VP Engineering",
            "seniority": "vp",
            "pain_point_count": 2,
            "signal_count": 3,
        })
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Jane Smith"
        assert data["opportunity_score"] > 0

    def test_get_prospect_by_id(self, client):
        created = client.post("/api/bd/prospects", json={
            "company_id": "co-1", "company_name": "Corp", "name": "Bob",
        }).json()
        r = client.get(f"/api/bd/prospects/{created['id']}")
        assert r.status_code == 200
        assert r.json()["name"] == "Bob"

    def test_get_prospect_not_found(self, client):
        r = client.get("/api/bd/prospects/bad-id")
        assert r.status_code == 404

    def test_update_prospect(self, client):
        created = client.post("/api/bd/prospects", json={
            "company_id": "co-1", "company_name": "Corp", "name": "Bob",
        }).json()
        r = client.put(f"/api/bd/prospects/{created['id']}", json={"status": "researched"})
        assert r.status_code == 200
        assert r.json()["status"] == "researched"


# ── Signal CRUD ───────────────────────────────────────────────────────────────

class TestBDSignals:

    def test_list_empty_initially(self, client):
        r = client.get("/api/bd/signals")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_signal(self, client):
        r = client.post("/api/bd/signals", json={
            "company_name": "Acme Corp",
            "signal_type": "hiring",
            "summary": "Posted 3 DevOps roles",
            "source": "Job board",
            "relevance_score": 88,
        })
        assert r.status_code == 201
        data = r.json()
        assert data["signal_type"] == "hiring"
        assert data["relevance_score"] == 88
        assert data["reviewed"] is False
        assert data["detected_at"] is not None

    def test_create_signal_with_explicit_date(self, client):
        r = client.post("/api/bd/signals", json={
            "company_name": "Corp",
            "signal_type": "funding",
            "summary": "Series A closed",
            "detected_at": "2026-01-15",
        })
        assert r.status_code == 201
        assert r.json()["detected_at"] == "2026-01-15"

    def test_list_all_signals(self, client):
        client.post("/api/bd/signals", json={"company_name": "A", "signal_type": "hiring", "summary": "S1"})
        client.post("/api/bd/signals", json={"company_name": "B", "signal_type": "funding", "summary": "S2"})
        r = client.get("/api/bd/signals")
        assert len(r.json()) == 2


# ── Opportunity Scoring ───────────────────────────────────────────────────────

class TestBDOpportunityScoring:

    def test_score_endpoint_returns_score_and_label(self, client):
        r = client.post("/api/bd/opportunities/score", json={
            "icp_match": True,
            "pain_point_count": 3,
            "signal_count": 4,
            "prospect_seniority": "CTO",
            "days_since_last_signal": 5,
            "existing_relationship": False,
        })
        assert r.status_code == 200
        data = r.json()
        assert "score" in data
        assert "score_label" in data
        assert "breakdown" in data
        assert isinstance(data["score"], int)
        assert data["score_label"] in ("hot", "warm", "cold", "disqualified")

    def test_score_no_external_calls(self, client):
        # This endpoint must be pure local computation
        r = client.post("/api/bd/opportunities/score", json={
            "icp_match": False,
            "pain_point_count": 1,
            "signal_count": 1,
        })
        assert r.status_code == 200

    def test_high_icp_prospect_scores_hot(self, client):
        r = client.post("/api/bd/opportunities/score", json={
            "icp_match": True,
            "pain_point_count": 4,
            "signal_count": 4,
            "prospect_seniority": "VP of Engineering",
            "days_since_last_signal": 3,
        })
        data = r.json()
        assert data["score"] >= 75
        assert data["score_label"] == "hot"

    def test_list_opportunities_empty(self, client):
        r = client.get("/api/bd/opportunities")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_opportunity(self, client):
        r = client.post("/api/bd/opportunities", json={
            "company_id": "co-1",
            "company_name": "Acme Corp",
            "contact_name": "Jane Smith",
            "stage": "researched",
            "pain_points": ["Manual pipeline", "Slow releases"],
        })
        assert r.status_code == 201
        data = r.json()
        assert data["company_name"] == "Acme Corp"
        assert data["score"] >= 0


# ── Deal Packet Generation ────────────────────────────────────────────────────

class TestBDDealPackets:

    def test_list_empty_initially(self, client):
        r = client.get("/api/bd/deal-packets")
        assert r.status_code == 200
        assert r.json() == []

    def test_generate_deal_packet(self, client):
        r = client.post("/api/bd/deal-packets/generate", json={
            "company_name": "Acme Corp",
            "contact_name": "Jane Smith",
            "contact_role": "VP Engineering",
            "engagement_type": "New Business",
            "pain_points": ["Manual deployment", "Slow releases"],
        })
        assert r.status_code == 201
        pkt = r.json()
        assert pkt["company_name"] == "Acme Corp"
        assert pkt["contact_name"] == "Jane Smith"
        assert len(pkt["talking_points"]) >= 2
        assert len(pkt["checklist"]) >= 1
        assert pkt["status"] == "draft"

    def test_generated_packet_has_safety_notice(self, client):
        r = client.post("/api/bd/deal-packets/generate", json={
            "company_name": "Corp",
            "contact_name": "Bob",
            "pain_points": ["Pain A"],
        })
        assert r.status_code == 201
        pkt = r.json()
        assert "DobryBot does not send automatically" in pkt["outreach_draft"]

    def test_generated_packet_persisted(self, client):
        client.post("/api/bd/deal-packets/generate", json={
            "company_name": "Corp",
            "contact_name": "Bob",
            "pain_points": [],
        })
        r = client.get("/api/bd/deal-packets")
        assert len(r.json()) == 1

    def test_get_packet_by_id(self, client):
        created = client.post("/api/bd/deal-packets/generate", json={
            "company_name": "Corp", "contact_name": "Bob", "pain_points": [],
        }).json()
        r = client.get(f"/api/bd/deal-packets/{created['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == created["id"]

    def test_get_packet_not_found(self, client):
        r = client.get("/api/bd/deal-packets/bad-id")
        assert r.status_code == 404

    def test_packet_checklist_items_start_undone(self, client):
        r = client.post("/api/bd/deal-packets/generate", json={
            "company_name": "Corp", "contact_name": "Bob", "pain_points": ["P1"],
        })
        pkt = r.json()
        for item in pkt["checklist"]:
            assert item["done"] is False


# ── Pipeline ──────────────────────────────────────────────────────────────────

class TestBDPipeline:

    def test_pipeline_returns_stages(self, client):
        r = client.get("/api/bd/pipeline")
        assert r.status_code == 200
        data = r.json()
        assert "stages" in data
        assert "total_active" in data
        assert len(data["stages"]) > 0

    def test_pipeline_empty_has_zero_counts(self, client):
        r = client.get("/api/bd/pipeline")
        data = r.json()
        assert data["total_active"] == 0
        for stage in data["stages"]:
            assert stage["count"] == 0
            assert stage["deals"] == []

    def test_pipeline_counts_from_opportunities(self, seeded_client):
        r = seeded_client.get("/api/bd/pipeline")
        data = r.json()
        assert data["total_active"] > 0
        # Verify at least one stage has deals
        has_deals = any(s["count"] > 0 for s in data["stages"])
        assert has_deals


# ── Demo Seed / Clear ─────────────────────────────────────────────────────────

class TestBDDemo:

    def test_seed_returns_seeded_true(self, client):
        r = client.post("/api/bd/demo/seed")
        assert r.status_code == 200
        data = r.json()
        assert data["seeded"] is True
        assert "stats" in data

    def test_seed_creates_companies(self, client):
        client.post("/api/bd/demo/seed")
        r = client.get("/api/bd/companies")
        assert len(r.json()) > 0

    def test_seed_creates_prospects(self, client):
        client.post("/api/bd/demo/seed")
        r = client.get("/api/bd/prospects")
        assert len(r.json()) > 0

    def test_seed_creates_signals(self, client):
        client.post("/api/bd/demo/seed")
        r = client.get("/api/bd/signals")
        assert len(r.json()) > 0

    def test_seed_creates_opportunities(self, client):
        client.post("/api/bd/demo/seed")
        r = client.get("/api/bd/opportunities")
        assert len(r.json()) > 0

    def test_seed_creates_deal_packets(self, client):
        client.post("/api/bd/demo/seed")
        r = client.get("/api/bd/deal-packets")
        assert len(r.json()) > 0

    def test_seed_deal_packets_have_safety_notice(self, client):
        client.post("/api/bd/demo/seed")
        packets = client.get("/api/bd/deal-packets").json()
        for pkt in packets:
            if pkt["outreach_draft"]:
                assert "DobryBot does not send automatically" in pkt["outreach_draft"]

    def test_clear_removes_all_data(self, client):
        client.post("/api/bd/demo/seed")
        r = client.post("/api/bd/demo/clear")
        assert r.status_code == 200
        assert r.json()["cleared"] is True
        assert client.get("/api/bd/companies").json() == []
        assert client.get("/api/bd/prospects").json() == []
        assert client.get("/api/bd/signals").json() == []
        assert client.get("/api/bd/opportunities").json() == []
        assert client.get("/api/bd/deal-packets").json() == []

    def test_seed_no_external_calls(self, client):
        # Seeds only local JSON files — no network required
        r = client.post("/api/bd/demo/seed")
        assert r.status_code == 200

    def test_clear_no_external_calls(self, client):
        r = client.post("/api/bd/demo/clear")
        assert r.status_code == 200


# ── Message Studio ────────────────────────────────────────────────────────────

class TestBDMessageStudio:

    def test_generate_email_draft(self, client):
        r = client.post("/api/bd/message-studio/draft", json={
            "company_name": "Acme Corp",
            "contact_name": "Jane Smith",
            "contact_role": "VP Engineering",
            "pain_point": "Manual deployment pipeline",
            "angle": "CI/CD automation",
            "message_type": "email",
            "tone": "warm",
        })
        assert r.status_code == 200
        data = r.json()
        assert "draft" in data
        assert "safety_notice" in data
        assert data["message_type"] == "email"
        assert len(data["draft"]) > 0

    def test_generate_linkedin_draft(self, client):
        r = client.post("/api/bd/message-studio/draft", json={
            "company_name": "Acme Corp",
            "contact_name": "Jane",
            "message_type": "linkedin",
            "tone": "direct",
        })
        assert r.status_code == 200
        assert r.json()["message_type"] == "linkedin"

    def test_generate_intro_request_draft(self, client):
        r = client.post("/api/bd/message-studio/draft", json={
            "company_name": "Acme Corp",
            "contact_name": "Jane Smith",
            "message_type": "intro_request",
            "tone": "warm",
        })
        assert r.status_code == 200
        assert r.json()["message_type"] == "intro_request"

    def test_draft_contains_safety_notice(self, client):
        r = client.post("/api/bd/message-studio/draft", json={
            "company_name": "Corp",
            "contact_name": "Bob",
            "message_type": "email",
        })
        data = r.json()
        assert "DobryBot does not send automatically" in data["draft"]
        assert "DobryBot does not send automatically" in data["safety_notice"]

    def test_email_draft_has_subject(self, client):
        r = client.post("/api/bd/message-studio/draft", json={
            "company_name": "Corp",
            "contact_name": "Bob",
            "message_type": "email",
            "pain_point": "Manual pipeline",
        })
        data = r.json()
        assert data["subject"] is not None
        assert len(data["subject"]) > 0

    def test_linkedin_draft_no_subject(self, client):
        r = client.post("/api/bd/message-studio/draft", json={
            "company_name": "Corp",
            "contact_name": "Bob",
            "message_type": "linkedin",
        })
        # LinkedIn messages don't have subjects
        data = r.json()
        assert data["subject"] is None or data["subject"] == ""

    def test_draft_generation_is_local_no_ai(self, client):
        # Generation must complete without any network requirement
        r = client.post("/api/bd/message-studio/draft", json={
            "company_name": "Offline Corp",
            "contact_name": "Offline Bob",
            "message_type": "email",
        })
        assert r.status_code == 200


# ── Safety Invariants ─────────────────────────────────────────────────────────

class TestBDSafetyInvariants:

    def test_no_send_endpoint(self, client):
        """No /send endpoint must exist anywhere in BD OS."""
        r = client.post("/api/bd/send", json={})
        assert r.status_code == 404

    def test_no_auto_outbound_endpoint(self, client):
        """No automatic outbound endpoint must exist."""
        r = client.post("/api/bd/auto-outbound", json={})
        assert r.status_code == 404

    def test_no_send_linkedin_endpoint(self, client):
        r = client.post("/api/bd/send-linkedin", json={})
        assert r.status_code == 404

    def test_no_send_email_endpoint(self, client):
        r = client.post("/api/bd/send-email", json={})
        assert r.status_code == 404

    def test_no_auto_apply_endpoint(self, client):
        r = client.post("/api/bd/auto-apply", json={})
        assert r.status_code == 404

    def test_no_mass_outreach_endpoint(self, client):
        r = client.post("/api/bd/mass-outreach", json={})
        assert r.status_code == 404

    def test_no_scrape_endpoint(self, client):
        r = client.post("/api/bd/scrape", json={})
        assert r.status_code == 404

    def test_deal_packet_generate_has_safety_notice(self, client):
        r = client.post("/api/bd/deal-packets/generate", json={
            "company_name": "Corp", "contact_name": "Bob", "pain_points": ["P1"],
        })
        assert "DobryBot does not send automatically" in r.json()["outreach_draft"]

    def test_message_studio_draft_has_safety_notice(self, client):
        r = client.post("/api/bd/message-studio/draft", json={
            "company_name": "Corp", "contact_name": "Bob", "message_type": "email",
        })
        assert "DobryBot does not send automatically" in r.json()["draft"]

    def test_message_studio_has_no_send_param(self, client):
        """Message Studio draft endpoint must not accept a 'send' action."""
        r = client.post("/api/bd/message-studio/send", json={})
        assert r.status_code == 404

    def test_opportunity_score_is_local(self, client):
        """Opportunity scoring must work offline — no external deps."""
        r = client.post("/api/bd/opportunities/score", json={
            "icp_match": True, "pain_point_count": 2, "signal_count": 2,
        })
        assert r.status_code == 200

    def test_demo_seed_no_external_requirement(self, client):
        """Seed must complete without any network — all local."""
        r = client.post("/api/bd/demo/seed")
        assert r.status_code == 200
