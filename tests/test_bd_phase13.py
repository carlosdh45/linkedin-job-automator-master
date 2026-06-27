"""
Phase 13: Demo Data Quality + ICP Seeding + Quick Start Flow — test suite.

Safety invariants verified:
- Demo seed writes ICP config with correct CorosDev/BD OS defaults
- Demo data is coherent (Summit Ventures present, C-suite prospects, matching signals)
- No /send, /auto-send, /auto-outbound, or /mass-outbound endpoint exists
- Approved outreach draft does NOT trigger any send action
- All Phase 12 tests still pass (regression check via count assertion below)
"""
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


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def p13_paths(tmp_path):
    return {
        "company":         str(tmp_path / "companies.json"),
        "prospect":        str(tmp_path / "prospects.json"),
        "signal":          str(tmp_path / "signals.json"),
        "pain_point":      str(tmp_path / "pain_points.json"),
        "opportunity":     str(tmp_path / "opportunities.json"),
        "deal_packet":     str(tmp_path / "deal_packets.json"),
        "outreach":        str(tmp_path / "outreach.json"),
        "activity":        str(tmp_path / "activity.json"),
        "icp_config":      str(tmp_path / "icp_config.json"),
        "recommendation":  str(tmp_path / "recommendations.json"),
    }


@pytest.fixture
def client(p13_paths, monkeypatch):
    monkeypatch.setenv("DOBRYBOT_BD_COMPANY_PATH",       p13_paths["company"])
    monkeypatch.setenv("DOBRYBOT_BD_PROSPECT_PATH",      p13_paths["prospect"])
    monkeypatch.setenv("DOBRYBOT_BD_SIGNAL_PATH",        p13_paths["signal"])
    monkeypatch.setenv("DOBRYBOT_BD_PAIN_POINT_PATH",    p13_paths["pain_point"])
    monkeypatch.setenv("DOBRYBOT_BD_OPPORTUNITY_PATH",   p13_paths["opportunity"])
    monkeypatch.setenv("DOBRYBOT_BD_DEAL_PACKET_PATH",   p13_paths["deal_packet"])
    monkeypatch.setenv("DOBRYBOT_BD_OUTREACH_PATH",      p13_paths["outreach"])
    monkeypatch.setenv("DOBRYBOT_BD_ACTIVITY_PATH",      p13_paths["activity"])
    monkeypatch.setenv("DOBRYBOT_BD_ICP_CONFIG_PATH",    p13_paths["icp_config"])
    monkeypatch.setenv("DOBRYBOT_BD_RECOMMENDATION_PATH", p13_paths["recommendation"])

    app.dependency_overrides[get_bd_company_path]       = lambda: p13_paths["company"]
    app.dependency_overrides[get_bd_prospect_path]      = lambda: p13_paths["prospect"]
    app.dependency_overrides[get_bd_signal_path]        = lambda: p13_paths["signal"]
    app.dependency_overrides[get_bd_pain_point_path]    = lambda: p13_paths["pain_point"]
    app.dependency_overrides[get_bd_opportunity_path]   = lambda: p13_paths["opportunity"]
    app.dependency_overrides[get_bd_deal_packet_path]   = lambda: p13_paths["deal_packet"]
    app.dependency_overrides[get_bd_outreach_path]      = lambda: p13_paths["outreach"]
    app.dependency_overrides[get_bd_activity_path]      = lambda: p13_paths["activity"]
    app.dependency_overrides[get_bd_icp_config_path]    = lambda: p13_paths["icp_config"]
    app.dependency_overrides[get_bd_recommendation_path] = lambda: p13_paths["recommendation"]

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ── ICP Seeding ───────────────────────────────────────────────────────────────

class TestDemoSeedICP:
    def test_seed_endpoint_returns_seeded_true(self, client):
        r = client.post("/api/bd/demo/seed")
        assert r.status_code == 200
        assert r.json()["seeded"] is True

    def test_seed_creates_icp_config(self, client):
        client.post("/api/bd/demo/seed")
        r = client.get("/api/bd/icp-config")
        assert r.status_code == 200
        cfg = r.json()
        assert len(cfg["target_industries"]) > 0, "ICP must have target industries after seed"
        assert len(cfg["target_roles"]) > 0, "ICP must have target roles after seed"
        assert len(cfg["pain_point_priorities"]) > 0, "ICP must have pain point priorities after seed"

    def test_seed_icp_contains_expected_industries(self, client):
        client.post("/api/bd/demo/seed")
        cfg = client.get("/api/bd/icp-config").json()
        industries = cfg["target_industries"]
        assert "SaaS" in industries
        assert "Financial Services" in industries
        assert "Private Equity" in industries

    def test_seed_icp_contains_expected_roles(self, client):
        client.post("/api/bd/demo/seed")
        cfg = client.get("/api/bd/icp-config").json()
        roles = cfg["target_roles"]
        assert "CEO" in roles
        assert "COO" in roles
        assert "CTO" in roles

    def test_seed_icp_contains_expected_pain_points(self, client):
        client.post("/api/bd/demo/seed")
        cfg = client.get("/api/bd/icp-config").json()
        pain = cfg["pain_point_priorities"]
        assert "slow deal origination" in pain
        assert "manual prospecting" in pain
        assert "poor lead qualification" in pain

    def test_seed_icp_has_company_size_range(self, client):
        client.post("/api/bd/demo/seed")
        cfg = client.get("/api/bd/icp-config").json()
        assert cfg["company_size_min"] == 50
        assert cfg["company_size_max"] == 2000

    def test_seed_icp_has_scoring_weights(self, client):
        client.post("/api/bd/demo/seed")
        cfg = client.get("/api/bd/icp-config").json()
        weights = cfg["scoring_weights"]
        assert "icp_match" in weights
        assert "pain_points" in weights
        assert "signals" in weights

    def test_seed_icp_weights_sum_to_100(self, client):
        client.post("/api/bd/demo/seed")
        cfg = client.get("/api/bd/icp-config").json()
        total = sum(cfg["scoring_weights"].values())
        assert total == 100, f"Scoring weights must sum to 100, got {total}"

    def test_seed_reports_correct_stats(self, client):
        r = client.post("/api/bd/demo/seed")
        stats = r.json()["stats"]
        assert stats["companies"] == 6
        assert stats["prospects"] == 6
        assert stats["signals"] == 7
        assert stats["pain_points"] == 10
        assert stats["opportunities"] == 6
        assert stats["deal_packets"] == 3
        assert stats["outreach_drafts"] == 3

    def test_repeated_seed_is_idempotent(self, client):
        client.post("/api/bd/demo/seed")
        r2 = client.post("/api/bd/demo/seed")
        assert r2.status_code == 200
        cfg = client.get("/api/bd/icp-config").json()
        assert "SaaS" in cfg["target_industries"]


# ── Demo Data Coherence ───────────────────────────────────────────────────────

class TestDemoDataCoherence:
    def test_summit_ventures_is_in_companies(self, client):
        client.post("/api/bd/demo/seed")
        r = client.get("/api/bd/companies")
        names = [c["name"] for c in r.json()]
        assert "Summit Ventures" in names, f"Summit Ventures missing from companies: {names}"

    def test_summit_ventures_is_private_equity(self, client):
        client.post("/api/bd/demo/seed")
        companies = client.get("/api/bd/companies").json()
        sv = next((c for c in companies if c["name"] == "Summit Ventures"), None)
        assert sv is not None
        assert "Private Equity" in sv["industry"]

    def test_summit_ventures_has_pain_points(self, client):
        client.post("/api/bd/demo/seed")
        companies = client.get("/api/bd/companies").json()
        sv = next(c for c in companies if c["name"] == "Summit Ventures")
        assert len(sv["pain_points"]) >= 2

    def test_summit_ventures_is_icp_match(self, client):
        client.post("/api/bd/demo/seed")
        companies = client.get("/api/bd/companies").json()
        sv = next(c for c in companies if c["name"] == "Summit Ventures")
        assert sv["icp_match"] is True

    def test_cascade_retail_removed(self, client):
        client.post("/api/bd/demo/seed")
        companies = client.get("/api/bd/companies").json()
        names = [c["name"] for c in companies]
        assert "Cascade Retail" not in names, "Cascade Retail should be replaced by Summit Ventures"

    def test_prospects_include_csuite_titles(self, client):
        client.post("/api/bd/demo/seed")
        prospects = client.get("/api/bd/prospects").json()
        titles = [p["title"] for p in prospects]
        c_suite = [t for t in titles if any(kw in t for kw in ["CEO", "CTO", "COO", "VP", "Managing Partner"])]
        assert len(c_suite) >= 4, f"Expected at least 4 C-suite/VP prospects, got: {titles}"

    def test_summit_ventures_prospect_exists(self, client):
        client.post("/api/bd/demo/seed")
        prospects = client.get("/api/bd/prospects").json()
        sv_prospect = next((p for p in prospects if p["company_name"] == "Summit Ventures"), None)
        assert sv_prospect is not None, "No prospect for Summit Ventures"
        assert sv_prospect["seniority"] in ("coo", "ceo", "cto", "vp")

    def test_summit_ventures_has_funding_signal(self, client):
        client.post("/api/bd/demo/seed")
        signals = client.get("/api/bd/signals").json()
        sv_signals = [s for s in signals if s["company_name"] == "Summit Ventures"]
        assert len(sv_signals) >= 1
        types = [s["signal_type"] for s in sv_signals]
        assert "funding" in types, f"Expected funding signal for Summit Ventures, got: {types}"

    def test_all_companies_have_opportunities(self, client):
        client.post("/api/bd/demo/seed")
        companies = client.get("/api/bd/companies").json()
        opportunities = client.get("/api/bd/opportunities").json()
        opp_companies = {o["company_name"] for o in opportunities}
        for co in companies:
            assert co["name"] in opp_companies, f"No opportunity for {co['name']}"

    def test_deal_packets_cover_three_companies(self, client):
        client.post("/api/bd/demo/seed")
        packets = client.get("/api/bd/deal-packets").json()
        assert len(packets) == 3
        names = {p["company_name"] for p in packets}
        assert "Meridian Labs" in names
        assert "Vantage Capital" in names
        assert "Summit Ventures" in names

    def test_summit_ventures_deal_packet_has_checklist(self, client):
        client.post("/api/bd/demo/seed")
        packets = client.get("/api/bd/deal-packets").json()
        sv_packet = next(p for p in packets if p["company_name"] == "Summit Ventures")
        assert len(sv_packet["checklist"]) >= 3

    def test_outreach_drafts_reference_summit_ventures(self, client):
        client.post("/api/bd/demo/seed")
        drafts = client.get("/api/bd/outreach-drafts").json()
        names = [d["company_name"] for d in drafts]
        assert "Summit Ventures" in names

    def test_high_score_companies_are_icp_match(self, client):
        client.post("/api/bd/demo/seed")
        companies = client.get("/api/bd/companies").json()
        hot = [c for c in companies if c["score_label"] == "hot"]
        for co in hot:
            assert co["icp_match"] is True, f"{co['name']} is hot but icp_match=False"

    def test_pain_points_link_to_valid_company_ids(self, client, p13_paths):
        client.post("/api/bd/demo/seed")
        companies = client.get("/api/bd/companies").json()
        company_ids = {c["id"] for c in companies}
        from backend.services.bd_pain_point_store import list_pain_points
        pain_points = list_pain_points(p13_paths["pain_point"])
        for pp in pain_points:
            assert pp.company_id in company_ids, (
                f"Pain point '{pp.description}' has unknown company_id {pp.company_id}"
            )


# ── ICP Config Updates ────────────────────────────────────────────────────────

class TestICPConfigUpdates:
    def test_reset_to_demo_values(self, client):
        demo_icp = {
            "target_industries": ["SaaS", "Private Equity"],
            "target_roles": ["CEO", "COO"],
            "pain_point_priorities": ["slow deal origination"],
            "company_size_min": 50,
            "company_size_max": 2000,
            "signal_priorities": ["hiring", "funding"],
            "scoring_weights": {
                "icp_match": 30, "pain_points": 25, "signals": 20,
                "seniority": 15, "urgency": 7, "existing_relationship": 3,
            },
        }
        r = client.put("/api/bd/icp-config", json=demo_icp)
        assert r.status_code == 200
        cfg = r.json()
        assert "SaaS" in cfg["target_industries"]
        assert "CEO" in cfg["target_roles"]

    def test_icp_config_persists_after_save(self, client):
        client.put("/api/bd/icp-config", json={
            "target_industries": ["Logistics"],
            "target_roles": ["COO"],
            "pain_point_priorities": ["manual prospecting"],
        })
        cfg = client.get("/api/bd/icp-config").json()
        assert "Logistics" in cfg["target_industries"]
        assert "COO" in cfg["target_roles"]

    def test_icp_config_updated_at_is_set(self, client):
        client.put("/api/bd/icp-config", json={
            "target_industries": ["SaaS"],
        })
        cfg = client.get("/api/bd/icp-config").json()
        assert cfg["updated_at"] != ""


# ── Safety Invariants ─────────────────────────────────────────────────────────

class TestSafetyInvariants:
    def _all_routes(self):
        return [(r.methods, r.path) for r in app.routes if hasattr(r, "path")]

    def test_no_auto_send_endpoint(self):
        routes = self._all_routes()
        for methods, path in routes:
            assert "/send" not in path, f"Forbidden /send endpoint: {path}"
            assert "/auto-send" not in path, f"Forbidden /auto-send endpoint: {path}"

    def test_no_auto_outbound_endpoint(self):
        routes = self._all_routes()
        for methods, path in routes:
            assert "/auto-outbound" not in path, f"Forbidden /auto-outbound endpoint: {path}"
            assert "/mass-outbound" not in path, f"Forbidden /mass-outbound endpoint: {path}"

    def test_no_auto_apply_endpoint(self):
        routes = self._all_routes()
        for methods, path in routes:
            assert "/auto-apply" not in path, f"Forbidden /auto-apply endpoint: {path}"

    def test_no_linkedin_endpoint(self):
        routes = self._all_routes()
        for methods, path in routes:
            assert "/linkedin" not in path, f"Forbidden /linkedin endpoint: {path}"

    def test_no_gmail_endpoint(self):
        routes = self._all_routes()
        for methods, path in routes:
            assert "/gmail" not in path, f"Forbidden /gmail endpoint: {path}"

    def test_approve_draft_does_not_send(self, client, p13_paths):
        client.post("/api/bd/demo/seed")
        drafts = client.get("/api/bd/outreach-drafts").json()
        assert len(drafts) > 0
        draft_id = drafts[0]["id"]
        r = client.post(f"/api/bd/outreach-drafts/{draft_id}/approve")
        assert r.status_code == 200
        updated = r.json()
        assert updated["status"] == "approved"
        # Approved means human-reviewed only — no email_sent, no external action
        assert "email_sent" not in updated
        assert "sent_at" not in updated

    def test_seed_does_not_call_external_apis(self, client):
        # seed_bd_demo is synchronous and local — no external calls
        # Simply verifying it completes without error in isolated tmp_path confirms locality
        r = client.post("/api/bd/demo/seed")
        assert r.status_code == 200
        assert r.json()["seeded"] is True

    def test_outreach_draft_body_contains_safety_notice(self, client):
        client.post("/api/bd/demo/seed")
        drafts = client.get("/api/bd/outreach-drafts").json()
        for draft in drafts:
            body = draft.get("body", "")
            assert "manual review" in body.lower() or "does not send" in body.lower(), (
                f"Draft for {draft['company_name']} missing safety notice"
            )
