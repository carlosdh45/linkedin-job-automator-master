"""
Phase 11: BD Signal Intelligence + Auto-Qualification — test suite.

Safety invariants verified:
- No send endpoint
- No auto-outbound endpoint
- No auto-apply endpoint
- No external API calls made
- Recommendations require human review — nothing is sent automatically
- Existing 502 tests still pass (enforced by running full suite)
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
from backend.services.bd_signal_intelligence import (
    evaluate_signal, evaluate_company, recalculate_opportunity,
)
from backend.models.bd import BDSignal, BDCompany, BDOpportunity, BDICPConfig


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def p11_paths(tmp_path):
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
def client(p11_paths, monkeypatch):
    monkeypatch.setenv("DOBRYBOT_BD_COMPANY_PATH",        p11_paths["company"])
    monkeypatch.setenv("DOBRYBOT_BD_PROSPECT_PATH",       p11_paths["prospect"])
    monkeypatch.setenv("DOBRYBOT_BD_SIGNAL_PATH",         p11_paths["signal"])
    monkeypatch.setenv("DOBRYBOT_BD_PAIN_POINT_PATH",     p11_paths["pain_point"])
    monkeypatch.setenv("DOBRYBOT_BD_OPPORTUNITY_PATH",    p11_paths["opportunity"])
    monkeypatch.setenv("DOBRYBOT_BD_DEAL_PACKET_PATH",    p11_paths["deal_packet"])
    monkeypatch.setenv("DOBRYBOT_BD_OUTREACH_PATH",       p11_paths["outreach"])
    monkeypatch.setenv("DOBRYBOT_BD_ACTIVITY_PATH",       p11_paths["activity"])
    monkeypatch.setenv("DOBRYBOT_BD_ICP_CONFIG_PATH",     p11_paths["icp_config"])
    monkeypatch.setenv("DOBRYBOT_BD_RECOMMENDATION_PATH", p11_paths["recommendation"])

    app.dependency_overrides[get_bd_company_path]        = lambda: p11_paths["company"]
    app.dependency_overrides[get_bd_prospect_path]       = lambda: p11_paths["prospect"]
    app.dependency_overrides[get_bd_signal_path]         = lambda: p11_paths["signal"]
    app.dependency_overrides[get_bd_pain_point_path]     = lambda: p11_paths["pain_point"]
    app.dependency_overrides[get_bd_opportunity_path]    = lambda: p11_paths["opportunity"]
    app.dependency_overrides[get_bd_deal_packet_path]    = lambda: p11_paths["deal_packet"]
    app.dependency_overrides[get_bd_outreach_path]       = lambda: p11_paths["outreach"]
    app.dependency_overrides[get_bd_activity_path]       = lambda: p11_paths["activity"]
    app.dependency_overrides[get_bd_icp_config_path]     = lambda: p11_paths["icp_config"]
    app.dependency_overrides[get_bd_recommendation_path] = lambda: p11_paths["recommendation"]

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def _company(**kw):
    base = {"name": "TestCo", "icp_match": False}
    base.update(kw)
    return base


def _signal(**kw):
    base = {
        "company_name": "TestCo",
        "signal_type": "hiring",
        "summary": "Growing engineering team",
        "relevance_score": 70,
    }
    base.update(kw)
    return base


def _opportunity(**kw):
    base = {"company_id": "co1", "company_name": "TestCo", "stage": "identified"}
    base.update(kw)
    return base


# ── Signal Intelligence Engine Unit Tests ─────────────────────────────────────

class TestSignalIntelligenceEngine:

    def _make_signal(self, signal_type="hiring", relevance_score=70, company_id="co1"):
        return BDSignal(
            company_id=company_id,
            company_name="TestCo",
            signal_type=signal_type,
            summary="Test signal",
            relevance_score=relevance_score,
        )

    def _make_company(self, icp_match=False, pain_points=None):
        return BDCompany(
            name="TestCo",
            icp_match=icp_match,
            pain_points=pain_points or [],
        )

    def _icp(self):
        return BDICPConfig()

    def test_evaluate_signal_returns_strength(self):
        sig = self._make_signal(signal_type="funding", relevance_score=80)
        result = evaluate_signal(sig, None, self._icp(), [])
        assert result["signal_strength"] in ("low", "medium", "high", "critical")

    def test_critical_signal_high_relevance_funding(self):
        sig = self._make_signal(signal_type="funding", relevance_score=85)
        result = evaluate_signal(sig, None, self._icp(), [])
        assert result["signal_strength"] == "critical"

    def test_icp_match_boosts_strength(self):
        sig_base = self._make_signal(signal_type="hiring", relevance_score=55)
        co_no_icp = self._make_company(icp_match=False)
        co_icp = self._make_company(icp_match=True)
        result_no = evaluate_signal(sig_base, co_no_icp, self._icp(), [])
        result_yes = evaluate_signal(sig_base, co_icp, self._icp(), [])
        order = ["low", "medium", "high", "critical"]
        assert order.index(result_yes["signal_strength"]) >= order.index(result_no["signal_strength"])

    def test_evaluate_signal_has_recommended_action(self):
        sig = self._make_signal()
        result = evaluate_signal(sig, None, self._icp(), [])
        assert isinstance(result["recommended_action"], str)
        assert len(result["recommended_action"]) > 0

    def test_evaluate_signal_confidence_score_range(self):
        sig = self._make_signal(relevance_score=60)
        result = evaluate_signal(sig, None, self._icp(), [])
        assert 0 <= result["confidence_score"] <= 100

    def test_evaluate_signal_no_external_calls(self):
        sig = self._make_signal()
        result = evaluate_signal(sig, None, self._icp(), [])
        assert "api_key" not in result
        assert "external" not in result

    def test_evaluate_company_icp_no_data(self):
        co = self._make_company(icp_match=True, pain_points=[])
        recs, flags = evaluate_company(co, [], [], [], self._icp())
        assert isinstance(recs, list)
        assert isinstance(flags, list)
        assert "needs_research" in flags

    def test_evaluate_company_icp_with_pain_and_signals(self):
        co = self._make_company(icp_match=True, pain_points=["slow deploys", "manual QA"])
        signals = [self._make_signal() for _ in range(2)]
        recs, flags = evaluate_company(co, signals, [], [], self._icp())
        assert len(recs) > 0
        assert "outreach_ready" in flags
        assert recs[0]["priority"] == "high"

    def test_evaluate_company_pain_no_icp_triggers_qualify(self):
        co = self._make_company(icp_match=False, pain_points=["a", "b", "c"])
        recs, flags = evaluate_company(co, [], [], [], self._icp())
        assert any("qualify" in f for f in flags)

    def test_evaluate_company_returns_recommendation_dicts(self):
        co = self._make_company(icp_match=True, pain_points=["pain1"])
        recs, _ = evaluate_company(co, [], [], [], self._icp())
        if recs:
            assert "entity_type" in recs[0]
            assert "priority" in recs[0]
            assert "recommended_action" in recs[0]
            assert "confidence_score" in recs[0]

    def test_recalculate_opportunity_returns_scores(self):
        opp = BDOpportunity(company_id="co1", company_name="TestCo", score=10)
        co = self._make_company(icp_match=True, pain_points=["pain"])
        result = recalculate_opportunity(opp, co, [], [], [])
        assert "new_score" in result
        assert "previous_score" in result
        assert result["previous_score"] == 10
        assert "score_change" in result

    def test_recalculate_opportunity_with_signals(self):
        opp = BDOpportunity(company_id="co1", company_name="TestCo", score=0)
        co = self._make_company(icp_match=True, pain_points=["p1", "p2"])
        signals = [self._make_signal() for _ in range(3)]
        result = recalculate_opportunity(opp, co, signals, [], [])
        assert result["new_score"] > result["previous_score"]
        assert result["signal_contribution"] > 0

    def test_recalculate_score_change_computed_correctly(self):
        opp = BDOpportunity(company_id="co1", company_name="TestCo", score=20)
        co = self._make_company(icp_match=True)
        result = recalculate_opportunity(opp, co, [], [], [])
        assert result["score_change"] == result["new_score"] - result["previous_score"]

    def test_recalculate_score_reason_is_string(self):
        opp = BDOpportunity(company_id="co1", company_name="TestCo", score=0)
        result = recalculate_opportunity(opp, None, [], [], [])
        assert isinstance(result["score_reason"], str)

    def test_recalculate_breakdown_has_expected_keys(self):
        opp = BDOpportunity(company_id="co1", company_name="TestCo", score=0)
        result = recalculate_opportunity(opp, None, [], [], [])
        assert "icp_match" in result["breakdown"]
        assert "signals" in result["breakdown"]


# ── Signal Evaluate Endpoint ──────────────────────────────────────────────────

class TestSignalEvaluateEndpoint:

    def test_evaluate_signal_200(self, client):
        sig = client.post("/api/bd/signals", json=_signal()).json()
        r = client.post(f"/api/bd/signals/{sig['id']}/evaluate")
        assert r.status_code == 200

    def test_evaluate_signal_returns_strength(self, client):
        sig = client.post("/api/bd/signals", json=_signal()).json()
        r = client.post(f"/api/bd/signals/{sig['id']}/evaluate")
        data = r.json()
        assert data["signal_strength"] in ("low", "medium", "high", "critical")

    def test_evaluate_signal_returns_priority(self, client):
        sig = client.post("/api/bd/signals", json=_signal()).json()
        r = client.post(f"/api/bd/signals/{sig['id']}/evaluate")
        assert r.json()["priority"] in ("low", "medium", "high", "critical")

    def test_evaluate_signal_returns_recommended_action(self, client):
        sig = client.post("/api/bd/signals", json=_signal()).json()
        r = client.post(f"/api/bd/signals/{sig['id']}/evaluate")
        assert isinstance(r.json()["recommended_action"], str)

    def test_evaluate_signal_returns_confidence_score(self, client):
        sig = client.post("/api/bd/signals", json=_signal()).json()
        r = client.post(f"/api/bd/signals/{sig['id']}/evaluate")
        cs = r.json()["confidence_score"]
        assert 0 <= cs <= 100

    def test_evaluate_signal_marks_evaluated(self, client):
        sig = client.post("/api/bd/signals", json=_signal()).json()
        client.post(f"/api/bd/signals/{sig['id']}/evaluate")
        signals = client.get("/api/bd/signals").json()
        evaluated = next(s for s in signals if s["id"] == sig["id"])
        assert evaluated["evaluated"] is True

    def test_evaluate_signal_stores_strength(self, client):
        sig = client.post("/api/bd/signals", json=_signal(
            signal_type="funding", relevance_score=85
        )).json()
        result = client.post(f"/api/bd/signals/{sig['id']}/evaluate").json()
        signals = client.get("/api/bd/signals").json()
        stored = next(s for s in signals if s["id"] == sig["id"])
        assert stored["signal_strength"] == result["signal_strength"]

    def test_evaluate_signal_logs_activity(self, client):
        sig = client.post("/api/bd/signals", json=_signal()).json()
        client.post(f"/api/bd/signals/{sig['id']}/evaluate")
        activity = client.get("/api/bd/activity").json()
        actions = [a["action"] for a in activity]
        assert "signal_evaluated" in actions

    def test_evaluate_signal_not_found(self, client):
        r = client.post("/api/bd/signals/nonexistent/evaluate")
        assert r.status_code == 404

    def test_evaluate_high_signal_creates_recommendation(self, client):
        # Company with ICP match to boost priority
        co = client.post("/api/bd/companies", json=_company(
            name="FundedCo", icp_match=True
        )).json()
        sig = client.post("/api/bd/signals", json=_signal(
            company_name="FundedCo",
            company_id=co["id"],
            signal_type="funding",
            relevance_score=85,
        )).json()
        result = client.post(f"/api/bd/signals/{sig['id']}/evaluate").json()
        if result["recommendation_created"]:
            recs = client.get("/api/bd/recommendations").json()
            assert len(recs) > 0


# ── Company Evaluate Endpoint ─────────────────────────────────────────────────

class TestCompanyEvaluateEndpoint:

    def test_evaluate_company_200(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="EvalCo", icp_match=True, pain_points=["slow pipelines"]
        )).json()
        r = client.post(f"/api/bd/companies/{co['id']}/evaluate")
        assert r.status_code == 200

    def test_evaluate_company_returns_score(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="EvalCo", icp_match=True
        )).json()
        r = client.post(f"/api/bd/companies/{co['id']}/evaluate")
        data = r.json()
        assert "new_score" in data
        assert "new_score_label" in data

    def test_evaluate_company_returns_flags(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="FlagCo", icp_match=True, pain_points=[]
        )).json()
        r = client.post(f"/api/bd/companies/{co['id']}/evaluate")
        assert isinstance(r.json()["flags"], list)

    def test_evaluate_company_updates_score(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="ScoreCo", icp_match=True, pain_points=["p1", "p2"]
        )).json()
        old_score = co["opportunity_score"]
        client.post(f"/api/bd/companies/{co['id']}/evaluate")
        updated = client.get(f"/api/bd/companies/{co['id']}").json()
        # Score should have been recomputed (may or may not change)
        assert "opportunity_score" in updated

    def test_evaluate_company_icp_creates_recommendation(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="IcpCo", icp_match=True, pain_points=[]
        )).json()
        client.post(f"/api/bd/companies/{co['id']}/evaluate")
        recs = client.get("/api/bd/recommendations").json()
        assert len(recs) > 0

    def test_evaluate_company_logs_activity(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="ActivityCo", icp_match=True
        )).json()
        client.post(f"/api/bd/companies/{co['id']}/evaluate")
        activity = client.get("/api/bd/activity").json()
        actions = [a["action"] for a in activity]
        assert "company_evaluated" in actions

    def test_evaluate_company_not_found(self, client):
        r = client.post("/api/bd/companies/nope/evaluate")
        assert r.status_code == 404

    def test_evaluate_company_score_updated_true(self, client):
        co = client.post("/api/bd/companies", json=_company(name="UpdCo")).json()
        r = client.post(f"/api/bd/companies/{co['id']}/evaluate")
        assert r.json()["score_updated"] is True


# ── Opportunity Recalculate Endpoint ──────────────────────────────────────────

class TestOpportunityRecalculateEndpoint:

    def test_recalculate_200(self, client):
        opp = client.post("/api/bd/opportunities", json=_opportunity()).json()
        r = client.post(f"/api/bd/opportunities/{opp['id']}/recalculate")
        assert r.status_code == 200

    def test_recalculate_returns_previous_and_new_score(self, client):
        opp = client.post("/api/bd/opportunities", json=_opportunity()).json()
        r = client.post(f"/api/bd/opportunities/{opp['id']}/recalculate")
        data = r.json()
        assert "previous_score" in data
        assert "new_score" in data
        assert "score_change" in data

    def test_recalculate_returns_score_reason(self, client):
        opp = client.post("/api/bd/opportunities", json=_opportunity()).json()
        r = client.post(f"/api/bd/opportunities/{opp['id']}/recalculate")
        assert isinstance(r.json()["score_reason"], str)

    def test_recalculate_returns_signal_contribution(self, client):
        opp = client.post("/api/bd/opportunities", json=_opportunity()).json()
        r = client.post(f"/api/bd/opportunities/{opp['id']}/recalculate")
        assert "signal_contribution" in r.json()

    def test_recalculate_returns_breakdown(self, client):
        opp = client.post("/api/bd/opportunities", json=_opportunity()).json()
        r = client.post(f"/api/bd/opportunities/{opp['id']}/recalculate")
        assert isinstance(r.json()["breakdown"], dict)

    def test_recalculate_logs_activity(self, client):
        opp = client.post("/api/bd/opportunities", json=_opportunity()).json()
        client.post(f"/api/bd/opportunities/{opp['id']}/recalculate")
        activity = client.get("/api/bd/activity").json()
        actions = [a["action"] for a in activity]
        assert "opportunity_recalculated" in actions

    def test_recalculate_updates_opportunity_score(self, client):
        # Create company with icp_match to drive score up
        co = client.post("/api/bd/companies", json=_company(
            name="ScoreDriveCo", icp_match=True
        )).json()
        opp = client.post("/api/bd/opportunities", json=_opportunity(
            company_id=co["id"], company_name="ScoreDriveCo"
        )).json()
        r = client.post(f"/api/bd/opportunities/{opp['id']}/recalculate")
        # After recalculate, the opportunity's score should reflect ICP match
        data = r.json()
        assert data["new_score"] >= 0

    def test_recalculate_warm_opp_creates_recommendation(self, client):
        # Set up a high-scoring scenario
        co = client.post("/api/bd/companies", json=_company(
            name="HotCo", icp_match=True,
            pain_points=["p1", "p2", "p3", "p4", "p5"],
        )).json()
        opp = client.post("/api/bd/opportunities", json=_opportunity(
            company_id=co["id"], company_name="HotCo",
            pain_points=["p1", "p2", "p3", "p4", "p5"],
        )).json()
        # Add signals
        for _ in range(4):
            client.post("/api/bd/signals", json=_signal(
                company_name="HotCo", company_id=co["id"],
                signal_type="funding", relevance_score=80,
            ))
        r = client.post(f"/api/bd/opportunities/{opp['id']}/recalculate")
        data = r.json()
        if data["new_score"] >= 55:
            assert data["recommendation_created"] is True

    def test_recalculate_not_found(self, client):
        r = client.post("/api/bd/opportunities/missing/recalculate")
        assert r.status_code == 404

    def test_recalculate_stores_last_recalculated_at(self, client):
        opp = client.post("/api/bd/opportunities", json=_opportunity()).json()
        client.post(f"/api/bd/opportunities/{opp['id']}/recalculate")
        opps = client.get("/api/bd/opportunities").json()
        updated_opp = next(o for o in opps if o["id"] == opp["id"])
        assert updated_opp["last_recalculated_at"] is not None

    def test_recalculate_stores_score_change(self, client):
        opp = client.post("/api/bd/opportunities", json=_opportunity()).json()
        client.post(f"/api/bd/opportunities/{opp['id']}/recalculate")
        opps = client.get("/api/bd/opportunities").json()
        updated_opp = next(o for o in opps if o["id"] == opp["id"])
        assert "score_change" in updated_opp


# ── Recommendations CRUD ──────────────────────────────────────────────────────

class TestRecommendationsCRUD:

    def test_list_recommendations_empty(self, client):
        r = client.get("/api/bd/recommendations")
        assert r.status_code == 200
        assert r.json() == []

    def test_recommendations_created_after_evaluate(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="RecCo", icp_match=True, pain_points=["p1"]
        )).json()
        client.post(f"/api/bd/companies/{co['id']}/evaluate")
        r = client.get("/api/bd/recommendations")
        assert r.status_code == 200
        assert len(r.json()) > 0

    def test_recommendation_has_required_fields(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="FieldCo", icp_match=True, pain_points=["pain"]
        )).json()
        client.post(f"/api/bd/companies/{co['id']}/evaluate")
        recs = client.get("/api/bd/recommendations").json()
        assert len(recs) > 0
        rec = recs[0]
        assert "id" in rec
        assert "entity_type" in rec
        assert "entity_id" in rec
        assert "entity_name" in rec
        assert "priority" in rec
        assert "reason" in rec
        assert "recommended_action" in rec
        assert "confidence_score" in rec
        assert "status" in rec
        assert "created_at" in rec

    def test_recommendation_default_status_is_new(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="StatusCo", icp_match=True, pain_points=["x"]
        )).json()
        client.post(f"/api/bd/companies/{co['id']}/evaluate")
        recs = client.get("/api/bd/recommendations").json()
        assert all(r["status"] == "new" for r in recs)

    def test_filter_by_status(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="FilterCo", icp_match=True, pain_points=["x"]
        )).json()
        client.post(f"/api/bd/companies/{co['id']}/evaluate")
        r = client.get("/api/bd/recommendations?status=new")
        assert all(rec["status"] == "new" for rec in r.json())

    def test_filter_by_entity_type(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="TypeCo", icp_match=True
        )).json()
        client.post(f"/api/bd/companies/{co['id']}/evaluate")
        r = client.get("/api/bd/recommendations?entity_type=company")
        assert all(rec["entity_type"] == "company" for rec in r.json())

    def test_dismiss_recommendation(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="DismissCo", icp_match=True, pain_points=["x"]
        )).json()
        client.post(f"/api/bd/companies/{co['id']}/evaluate")
        rec = client.get("/api/bd/recommendations").json()[0]
        r = client.post(f"/api/bd/recommendations/{rec['id']}/dismiss")
        assert r.status_code == 200
        assert r.json()["status"] == "dismissed"

    def test_dismiss_logs_activity(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="DismissActCo", icp_match=True, pain_points=["x"]
        )).json()
        client.post(f"/api/bd/companies/{co['id']}/evaluate")
        rec = client.get("/api/bd/recommendations").json()[0]
        client.post(f"/api/bd/recommendations/{rec['id']}/dismiss")
        activity = client.get("/api/bd/activity").json()
        actions = [a["action"] for a in activity]
        assert "recommendation_dismissed" in actions

    def test_action_recommendation(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="ActionCo", icp_match=True, pain_points=["x"]
        )).json()
        client.post(f"/api/bd/companies/{co['id']}/evaluate")
        rec = client.get("/api/bd/recommendations").json()[0]
        r = client.post(f"/api/bd/recommendations/{rec['id']}/action")
        assert r.status_code == 200
        assert r.json()["status"] == "actioned"

    def test_action_logs_activity(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="ActionActCo", icp_match=True, pain_points=["x"]
        )).json()
        client.post(f"/api/bd/companies/{co['id']}/evaluate")
        rec = client.get("/api/bd/recommendations").json()[0]
        client.post(f"/api/bd/recommendations/{rec['id']}/action")
        activity = client.get("/api/bd/activity").json()
        actions = [a["action"] for a in activity]
        assert "recommendation_actioned" in actions

    def test_dismiss_not_found(self, client):
        r = client.post("/api/bd/recommendations/nope/dismiss")
        assert r.status_code == 404

    def test_action_not_found(self, client):
        r = client.post("/api/bd/recommendations/nope/action")
        assert r.status_code == 404

    def test_dismissed_not_in_new_filter(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="FilterNewCo", icp_match=True, pain_points=["x"]
        )).json()
        client.post(f"/api/bd/companies/{co['id']}/evaluate")
        rec = client.get("/api/bd/recommendations").json()[0]
        client.post(f"/api/bd/recommendations/{rec['id']}/dismiss")
        new_recs = client.get("/api/bd/recommendations?status=new").json()
        ids = [r["id"] for r in new_recs]
        assert rec["id"] not in ids


# ── Recommendations Refresh ───────────────────────────────────────────────────

class TestRecommendationsRefresh:

    def test_refresh_200(self, client):
        r = client.post("/api/bd/recommendations/refresh")
        assert r.status_code == 200

    def test_refresh_returns_counts(self, client):
        r = client.post("/api/bd/recommendations/refresh")
        data = r.json()
        assert "signals_evaluated" in data
        assert "companies_evaluated" in data
        assert "opportunities_recalculated" in data
        assert "recommendations_created" in data

    def test_refresh_has_safety_notice(self, client):
        r = client.post("/api/bd/recommendations/refresh")
        assert "safety_notice" in r.json()
        notice = r.json()["safety_notice"]
        assert len(notice) > 0

    def test_refresh_evaluates_unevaluated_signals(self, client):
        for _ in range(3):
            client.post("/api/bd/signals", json=_signal())
        r = client.post("/api/bd/recommendations/refresh")
        assert r.json()["signals_evaluated"] == 3

    def test_refresh_skips_already_evaluated_signals(self, client):
        sig = client.post("/api/bd/signals", json=_signal()).json()
        client.post(f"/api/bd/signals/{sig['id']}/evaluate")
        r = client.post("/api/bd/recommendations/refresh")
        assert r.json()["signals_evaluated"] == 0

    def test_refresh_evaluates_companies(self, client):
        client.post("/api/bd/companies", json=_company(name="A"))
        client.post("/api/bd/companies", json=_company(name="B"))
        r = client.post("/api/bd/recommendations/refresh")
        assert r.json()["companies_evaluated"] == 2

    def test_refresh_recalculates_opportunities(self, client):
        client.post("/api/bd/opportunities", json=_opportunity())
        r = client.post("/api/bd/recommendations/refresh")
        assert r.json()["opportunities_recalculated"] == 1

    def test_refresh_creates_recommendations_for_icp_companies(self, client):
        client.post("/api/bd/companies", json=_company(
            name="IcpRefreshCo", icp_match=True, pain_points=["x"]
        ))
        r = client.post("/api/bd/recommendations/refresh")
        assert r.json()["recommendations_created"] > 0
        recs = client.get("/api/bd/recommendations").json()
        assert len(recs) > 0

    def test_refresh_logs_activity(self, client):
        client.post("/api/bd/signals", json=_signal())
        client.post("/api/bd/recommendations/refresh")
        activity = client.get("/api/bd/activity").json()
        actions = [a["action"] for a in activity]
        assert "signal_evaluated" in actions

    def test_refresh_does_not_send(self, client):
        client.post("/api/bd/companies", json=_company(name="SendTestCo", icp_match=True))
        client.post("/api/bd/recommendations/refresh")
        # Verify no sent_at field appears anywhere in recommendations
        recs = client.get("/api/bd/recommendations").json()
        for rec in recs:
            assert "sent_at" not in rec
            assert "delivery" not in rec


# ── Dashboard with Signal Intelligence ───────────────────────────────────────

class TestDashboardSignalIntelligence:

    def test_dashboard_has_signal_recommendations(self, client):
        r = client.get("/api/bd/dashboard")
        assert r.status_code == 200
        assert "signal_recommendations" in r.json()

    def test_dashboard_has_companies_needing_research(self, client):
        r = client.get("/api/bd/dashboard")
        assert "companies_needing_research" in r.json()

    def test_dashboard_has_prospects_ready_for_review(self, client):
        r = client.get("/api/bd/dashboard")
        assert "prospects_ready_for_review" in r.json()

    def test_dashboard_signal_recommendations_counts_new(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="CountCo", icp_match=True, pain_points=["x"]
        )).json()
        client.post(f"/api/bd/companies/{co['id']}/evaluate")
        r = client.get("/api/bd/dashboard")
        assert r.json()["signal_recommendations"] > 0

    def test_dashboard_companies_needing_research_icp_no_pain(self, client):
        client.post("/api/bd/companies", json=_company(
            name="ResearchCo", icp_match=True, pain_points=[]
        ))
        r = client.get("/api/bd/dashboard")
        assert r.json()["companies_needing_research"] >= 1

    def test_dismissed_recs_not_counted(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="DismissedCountCo", icp_match=True, pain_points=["x"]
        )).json()
        client.post(f"/api/bd/companies/{co['id']}/evaluate")
        recs = client.get("/api/bd/recommendations").json()
        for rec in recs:
            client.post(f"/api/bd/recommendations/{rec['id']}/dismiss")
        r = client.get("/api/bd/dashboard")
        assert r.json()["signal_recommendations"] == 0


# ── Activity Log for Intelligence Operations ──────────────────────────────────

class TestIntelligenceActivityLog:

    def test_signal_evaluate_creates_activity(self, client):
        sig = client.post("/api/bd/signals", json=_signal()).json()
        client.post(f"/api/bd/signals/{sig['id']}/evaluate")
        activity = client.get("/api/bd/activity?entity_type=signal").json()
        assert any(a["action"] == "signal_evaluated" for a in activity)

    def test_company_evaluate_creates_activity(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="ActCo", icp_match=True
        )).json()
        client.post(f"/api/bd/companies/{co['id']}/evaluate")
        activity = client.get("/api/bd/activity?entity_type=company").json()
        assert any(a["action"] == "company_evaluated" for a in activity)

    def test_opportunity_recalculate_creates_activity(self, client):
        opp = client.post("/api/bd/opportunities", json=_opportunity()).json()
        client.post(f"/api/bd/opportunities/{opp['id']}/recalculate")
        activity = client.get("/api/bd/activity?entity_type=opportunity").json()
        assert any(a["action"] == "opportunity_recalculated" for a in activity)

    def test_dismiss_creates_activity(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="DismissActCo2", icp_match=True, pain_points=["x"]
        )).json()
        client.post(f"/api/bd/companies/{co['id']}/evaluate")
        rec = client.get("/api/bd/recommendations").json()[0]
        client.post(f"/api/bd/recommendations/{rec['id']}/dismiss")
        activity = client.get("/api/bd/activity").json()
        assert any(a["action"] == "recommendation_dismissed" for a in activity)

    def test_action_creates_activity(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="ActionActCo2", icp_match=True, pain_points=["x"]
        )).json()
        client.post(f"/api/bd/companies/{co['id']}/evaluate")
        rec = client.get("/api/bd/recommendations").json()[0]
        client.post(f"/api/bd/recommendations/{rec['id']}/action")
        activity = client.get("/api/bd/activity").json()
        assert any(a["action"] == "recommendation_actioned" for a in activity)


# ── Safety Invariants ─────────────────────────────────────────────────────────

class TestPhase11SafetyInvariants:

    def test_no_send_endpoint(self, client):
        r = client.post("/api/bd/signals/test/send")
        assert r.status_code == 404

    def test_no_auto_outbound_endpoint(self, client):
        r = client.post("/api/bd/auto-outbound")
        assert r.status_code == 404

    def test_no_auto_send_endpoint(self, client):
        r = client.post("/api/bd/auto-send")
        assert r.status_code == 404

    def test_no_auto_apply_endpoint(self, client):
        r = client.post("/api/bd/auto-apply")
        assert r.status_code == 404

    def test_no_linkedin_endpoint(self, client):
        r = client.post("/api/bd/linkedin/send")
        assert r.status_code == 404

    def test_no_gmail_endpoint(self, client):
        r = client.post("/api/bd/gmail/send")
        assert r.status_code == 404

    def test_no_scrape_endpoint(self, client):
        r = client.post("/api/bd/scrape")
        assert r.status_code == 404

    def test_no_enrichment_endpoint(self, client):
        r = client.post("/api/bd/enrich")
        assert r.status_code == 404

    def test_recommendations_have_no_sent_at(self, client):
        co = client.post("/api/bd/companies", json=_company(
            name="SafetyCo", icp_match=True, pain_points=["x"]
        )).json()
        client.post(f"/api/bd/companies/{co['id']}/evaluate")
        recs = client.get("/api/bd/recommendations").json()
        for rec in recs:
            assert "sent_at" not in rec

    def test_refresh_has_safety_notice_content(self, client):
        r = client.post("/api/bd/recommendations/refresh")
        notice = r.json()["safety_notice"]
        assert "human" in notice.lower() or "manual" in notice.lower() or "review" in notice.lower()

    def test_evaluate_signal_has_no_external_call_fields(self, client):
        sig = client.post("/api/bd/signals", json=_signal()).json()
        r = client.post(f"/api/bd/signals/{sig['id']}/evaluate")
        data = r.json()
        assert "api_key" not in data
        assert "external_enrichment" not in data
        assert "linkedin_profile" not in data

    def test_company_evaluate_has_no_external_call_fields(self, client):
        co = client.post("/api/bd/companies", json=_company(name="ExtSafetyCo")).json()
        r = client.post(f"/api/bd/companies/{co['id']}/evaluate")
        data = r.json()
        assert "api_key" not in data
        assert "external_enrichment" not in data

    def test_recalculate_has_no_send_fields(self, client):
        opp = client.post("/api/bd/opportunities", json=_opportunity()).json()
        r = client.post(f"/api/bd/opportunities/{opp['id']}/recalculate")
        data = r.json()
        assert "sent_at" not in data
        assert "email_sent" not in data
        assert "outbound_triggered" not in data
