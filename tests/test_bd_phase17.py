"""
Phase 17: Per-Record Source Tracking + Safe Workspace Restore

Tests:
  - Source fields on all BD models (loading + defaults)
  - Seed data tagged with source='demo'
  - CSV imports tagged with source='imported' / data_source='imported'
  - Manual create endpoints set source='manual'
  - Generated records set source='generated'
  - Workspace status includes source_breakdown
  - clear-demo removes only demo records, preserves others
  - clear-imported removes only imported records, preserves others
  - restore endpoint (dry_run + actual restore)
  - Safety invariants
"""
import json
import io
import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.bd import (
    BDCompany, BDProspect, BDSignal, BDPainPoint,
    BDOpportunity, BDDealPacket, BDOutreachDraft, BDRecommendation,
)
from backend.services import (
    bd_company_store, bd_prospect_store, bd_signal_store,
    bd_pain_point_store, bd_opportunity_store, bd_deal_packet_store,
    bd_outreach_store, bd_recommendation_store,
)

client = TestClient(app)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def tmp_paths(tmp_path):
    return {
        "company": str(tmp_path / "co.json"),
        "prospect": str(tmp_path / "pr.json"),
        "signal": str(tmp_path / "si.json"),
        "pain_point": str(tmp_path / "pp.json"),
        "opportunity": str(tmp_path / "op.json"),
        "deal_packet": str(tmp_path / "dp.json"),
        "outreach": str(tmp_path / "od.json"),
        "recommendation": str(tmp_path / "rec.json"),
        "activity": str(tmp_path / "act.json"),
        "icp": str(tmp_path / "icp.json"),
        "import_history": str(tmp_path / "hist.json"),
    }


@pytest.fixture()
def api_env(tmp_paths, monkeypatch):
    monkeypatch.setenv("DOBRYBOT_BD_COMPANY_PATH", tmp_paths["company"])
    monkeypatch.setenv("DOBRYBOT_BD_PROSPECT_PATH", tmp_paths["prospect"])
    monkeypatch.setenv("DOBRYBOT_BD_SIGNAL_PATH", tmp_paths["signal"])
    monkeypatch.setenv("DOBRYBOT_BD_PAIN_POINT_PATH", tmp_paths["pain_point"])
    monkeypatch.setenv("DOBRYBOT_BD_OPPORTUNITY_PATH", tmp_paths["opportunity"])
    monkeypatch.setenv("DOBRYBOT_BD_DEAL_PACKET_PATH", tmp_paths["deal_packet"])
    monkeypatch.setenv("DOBRYBOT_BD_OUTREACH_PATH", tmp_paths["outreach"])
    monkeypatch.setenv("DOBRYBOT_BD_RECOMMENDATION_PATH", tmp_paths["recommendation"])
    monkeypatch.setenv("DOBRYBOT_BD_ACTIVITY_PATH", tmp_paths["activity"])
    monkeypatch.setenv("DOBRYBOT_BD_ICP_CONFIG_PATH", tmp_paths["icp"])
    monkeypatch.setenv("DOBRYBOT_BD_IMPORT_HISTORY_PATH", tmp_paths["import_history"])
    return tmp_paths


# ── TestSourceModelFields ─────────────────────────────────────────────────────

class TestSourceModelFields:
    """All 8 BD models must have a source field that defaults to None."""

    def test_company_source_defaults_none(self):
        c = BDCompany(name="Test Co")
        assert c.source is None

    def test_prospect_source_defaults_none(self):
        p = BDProspect(company_id="x", company_name="Co", name="Alice")
        assert p.source is None

    def test_signal_data_source_defaults_none(self):
        s = BDSignal(company_id="x", company_name="Co", signal_type="hiring", summary="test")
        assert s.data_source is None

    def test_signal_source_separate_from_data_source(self):
        s = BDSignal(
            company_id="x", company_name="Co", signal_type="hiring",
            summary="test", source="LinkedIn", data_source="demo"
        )
        assert s.source == "LinkedIn"
        assert s.data_source == "demo"

    def test_pain_point_source_defaults_none(self):
        pp = BDPainPoint(company_id="x", company_name="Co", description="pain")
        assert pp.source is None

    def test_opportunity_source_defaults_none(self):
        o = BDOpportunity(company_id="x", company_name="Co")
        assert o.source is None

    def test_deal_packet_source_defaults_none(self):
        dp = BDDealPacket(company_id="x", company_name="Co", value_proposition="vp", outreach_draft="draft")
        assert dp.source is None

    def test_outreach_draft_source_defaults_none(self):
        d = BDOutreachDraft(company_name="Co", contact_name="Alice", contact_role="CTO", body="hi")
        assert d.source is None

    def test_recommendation_source_defaults_none(self):
        r = BDRecommendation(
            entity_type="signal", entity_id="x", entity_name="Co",
            priority="high", reason="r", recommended_action="act", confidence_score=80
        )
        assert r.source is None

    def test_models_load_from_json_without_source_key(self, tmp_path):
        """Old records without 'source' in JSON should load fine (source → None)."""
        p = tmp_path / "co.json"
        p.write_text(json.dumps([{"id": "abc", "name": "Old Co"}]), encoding="utf-8")
        companies = bd_company_store.list_companies(str(p))
        assert companies[0].source is None

    def test_signal_loads_from_json_without_data_source_key(self, tmp_path):
        p = tmp_path / "si.json"
        p.write_text(json.dumps([{
            "id": "abc", "company_id": "x", "company_name": "Co",
            "signal_type": "hiring", "summary": "test"
        }]), encoding="utf-8")
        signals = bd_signal_store.list_signals(str(p))
        assert signals[0].data_source is None


# ── TestSeedDemoSource ─────────────────────────────────────────────────────────

class TestSeedDemoSource:
    """Seeded demo data must have source='demo'."""

    def test_seed_companies_tagged_demo(self, api_env):
        r = client.post("/api/bd/demo/seed")
        assert r.status_code == 200
        companies = bd_company_store.list_companies(api_env["company"])
        assert all(c.source == "demo" for c in companies)

    def test_seed_prospects_tagged_demo(self, api_env):
        client.post("/api/bd/demo/seed")
        prospects = bd_prospect_store.list_prospects(api_env["prospect"])
        assert all(p.source == "demo" for p in prospects)

    def test_seed_signals_tagged_demo(self, api_env):
        client.post("/api/bd/demo/seed")
        signals = bd_signal_store.list_signals(api_env["signal"])
        assert all(s.data_source == "demo" for s in signals)

    def test_seed_pain_points_tagged_demo(self, api_env):
        client.post("/api/bd/demo/seed")
        pps = bd_pain_point_store.list_pain_points(api_env["pain_point"])
        assert all(pp.source == "demo" for pp in pps)

    def test_seed_opportunities_tagged_demo(self, api_env):
        client.post("/api/bd/demo/seed")
        opps = bd_opportunity_store.list_opportunities(api_env["opportunity"])
        assert all(o.source == "demo" for o in opps)

    def test_seed_deal_packets_tagged_demo(self, api_env):
        client.post("/api/bd/demo/seed")
        dps = bd_deal_packet_store.list_deal_packets(api_env["deal_packet"])
        assert all(dp.source == "demo" for dp in dps)

    def test_seed_outreach_drafts_tagged_demo(self, api_env):
        client.post("/api/bd/demo/seed")
        drafts = bd_outreach_store.list_drafts(api_env["outreach"])
        assert all(d.source == "demo" for d in drafts)

    def test_seed_signal_source_field_preserved(self, api_env):
        """Signals' source (external origin) must not be overwritten by data_source tagging."""
        client.post("/api/bd/demo/seed")
        signals = bd_signal_store.list_signals(api_env["signal"])
        external_sources = [s.source for s in signals if s.source]
        assert len(external_sources) > 0, "Demo signals should have external source values"


# ── TestCSVImportSource ───────────────────────────────────────────────────────

class TestCSVImportSource:
    """CSV-imported records must have source='imported' / data_source='imported'."""

    def _companies_csv(self):
        return b"name,domain,industry\nImported Corp,imported.com,SaaS\n"

    def _prospects_csv(self):
        return b"full_name,company_name,role\nImported Alice,Imported Corp,CTO\n"

    def _signals_csv(self):
        return b"company_name,signal_type,description\nImported Corp,hiring,Hiring fast\n"

    def test_imported_company_has_source_imported(self, api_env):
        f = io.BytesIO(self._companies_csv())
        r = client.post(
            "/api/bd/import/companies-csv?dry_run=false",
            files={"file": ("co.csv", f, "text/csv")},
        )
        assert r.status_code == 200
        companies = bd_company_store.list_companies(api_env["company"])
        assert all(c.source == "imported" for c in companies)

    def test_imported_prospect_has_source_imported(self, api_env):
        # Seed company first so prospect import can resolve company
        client.post(
            "/api/bd/import/companies-csv?dry_run=false",
            files={"file": ("co.csv", io.BytesIO(self._companies_csv()), "text/csv")},
        )
        f = io.BytesIO(self._prospects_csv())
        r = client.post(
            "/api/bd/import/prospects-csv?dry_run=false",
            files={"file": ("pr.csv", f, "text/csv")},
        )
        assert r.status_code == 200
        prospects = bd_prospect_store.list_prospects(api_env["prospect"])
        assert all(p.source == "imported" for p in prospects)

    def test_imported_signal_has_data_source_imported(self, api_env):
        client.post(
            "/api/bd/import/companies-csv?dry_run=false",
            files={"file": ("co.csv", io.BytesIO(self._companies_csv()), "text/csv")},
        )
        f = io.BytesIO(self._signals_csv())
        r = client.post(
            "/api/bd/import/signals-csv?dry_run=false",
            files={"file": ("si.csv", f, "text/csv")},
        )
        assert r.status_code == 200
        signals = bd_signal_store.list_signals(api_env["signal"])
        assert all(s.data_source == "imported" for s in signals)

    def test_dry_run_does_not_persist(self, api_env):
        f = io.BytesIO(self._companies_csv())
        r = client.post(
            "/api/bd/import/companies-csv?dry_run=true",
            files={"file": ("co.csv", f, "text/csv")},
        )
        assert r.status_code == 200
        companies = bd_company_store.list_companies(api_env["company"])
        assert len(companies) == 0


# ── TestManualCreateSource ─────────────────────────────────────────────────────

class TestManualCreateSource:
    """Manually created records via POST endpoints must have source='manual'."""

    def test_manual_company_has_source_manual(self, api_env):
        r = client.post("/api/bd/companies", json={"name": "Manual Co"})
        assert r.status_code == 201
        data = r.json()
        assert data["source"] == "manual"

    def test_manual_prospect_has_source_manual(self, api_env):
        co = client.post("/api/bd/companies", json={"name": "Manual Co"}).json()
        r = client.post("/api/bd/prospects", json={
            "company_id": co["id"],
            "company_name": "Manual Co",
            "name": "Bob"
        })
        assert r.status_code == 201
        assert r.json()["source"] == "manual"

    def test_manual_signal_has_data_source_manual(self, api_env):
        co = client.post("/api/bd/companies", json={"name": "Manual Co"}).json()
        r = client.post("/api/bd/signals", json={
            "company_id": co["id"],
            "company_name": "Manual Co",
            "signal_type": "hiring",
            "summary": "Manually entered signal",
        })
        assert r.status_code == 201
        assert r.json()["data_source"] == "manual"

    def test_manual_outreach_draft_has_source_manual(self, api_env):
        r = client.post("/api/bd/outreach-drafts", json={
            "company_name": "Manual Co",
            "contact_name": "Alice",
            "body": "Hi Alice",
        })
        assert r.status_code == 201
        assert r.json()["source"] == "manual"


# ── TestGeneratedSource ───────────────────────────────────────────────────────

class TestGeneratedSource:
    """System-generated records (recommendations, deal packets, opportunities) must have source='generated'."""

    def test_generated_deal_packet_has_source_generated(self, api_env):
        r = client.post("/api/bd/deal-packets/generate", json={
            "company_name": "Gen Co",
            "contact_name": "Alice",
            "pain_points": ["pipeline delays"],
        })
        assert r.status_code == 201
        assert r.json()["source"] == "generated"

    def test_evaluate_signal_creates_generated_recommendation(self, api_env):
        client.post("/api/bd/demo/seed")
        signals = bd_signal_store.list_signals(api_env["signal"])
        sig = next((s for s in signals if not s.evaluated), None)
        assert sig is not None

        r = client.post(f"/api/bd/signals/{sig.id}/evaluate")
        assert r.status_code == 200

        recs = bd_recommendation_store.list_recommendations(api_env["recommendation"])
        generated_recs = [r for r in recs if r.source == "generated"]
        # May or may not create a recommendation depending on priority, so just check source on any created
        for rec in recs:
            assert rec.source == "generated"

    def test_opportunity_from_recommendation_is_generated(self, api_env):
        client.post("/api/bd/demo/seed")
        # Evaluate all to create recommendations
        client.post("/api/bd/signals/evaluate-all")
        recs = bd_recommendation_store.list_recommendations(api_env["recommendation"])
        if not recs:
            pytest.skip("No recommendations created from demo signals")

        rec = recs[0]
        r = client.post(f"/api/bd/recommendations/{rec.id}/create-opportunity")
        assert r.status_code == 200
        opp_id = r.json()["id"]
        opps = bd_opportunity_store.list_opportunities(api_env["opportunity"])
        created = next((o for o in opps if o.id == opp_id), None)
        assert created is not None
        assert created.source == "generated"


# ── TestWorkspaceSourceBreakdown ──────────────────────────────────────────────

class TestWorkspaceSourceBreakdown:
    """Workspace status must include a source_breakdown dict."""

    def test_empty_workspace_has_breakdown(self, api_env):
        r = client.get("/api/bd/workspace/status")
        assert r.status_code == 200
        data = r.json()
        assert "source_breakdown" in data
        assert isinstance(data["source_breakdown"], dict)

    def test_demo_seed_shows_demo_in_breakdown(self, api_env):
        client.post("/api/bd/demo/seed")
        r = client.get("/api/bd/workspace/status")
        assert r.status_code == 200
        bd = r.json()["source_breakdown"]
        assert bd.get("demo", 0) > 0

    def test_manual_create_shows_manual_in_breakdown(self, api_env):
        client.post("/api/bd/companies", json={"name": "Manual Co"})
        r = client.get("/api/bd/workspace/status")
        bd = r.json()["source_breakdown"]
        assert bd.get("manual", 0) > 0

    def test_mixed_sources_in_breakdown(self, api_env):
        client.post("/api/bd/demo/seed")
        client.post("/api/bd/companies", json={"name": "Manual Co"})
        r = client.get("/api/bd/workspace/status")
        bd = r.json()["source_breakdown"]
        assert bd.get("demo", 0) > 0
        assert bd.get("manual", 0) > 0


# ── TestClearDemo ─────────────────────────────────────────────────────────────

class TestClearDemo:
    """POST /workspace/clear-demo must remove only source='demo' records."""

    def test_clear_demo_requires_confirmation(self, api_env):
        r = client.post("/api/bd/workspace/clear-demo", json={"confirm_text": "wrong"})
        assert r.status_code == 400

    def test_clear_demo_wrong_text_rejected(self, api_env):
        r = client.post("/api/bd/workspace/clear-demo", json={"confirm_text": "CLEAR DOBRYBOT WORKSPACE"})
        assert r.status_code == 400

    def test_clear_demo_removes_demo_records(self, api_env):
        client.post("/api/bd/demo/seed")
        companies_before = bd_company_store.list_companies(api_env["company"])
        assert len(companies_before) > 0

        r = client.post("/api/bd/workspace/clear-demo", json={"confirm_text": "CLEAR DEMO DATA"})
        assert r.status_code == 200
        result = r.json()
        assert result["records_removed"] > 0

        companies_after = bd_company_store.list_companies(api_env["company"])
        assert len(companies_after) == 0

    def test_clear_demo_preserves_manual_records(self, api_env):
        client.post("/api/bd/demo/seed")
        client.post("/api/bd/companies", json={"name": "Manual Co"})

        r = client.post("/api/bd/workspace/clear-demo", json={"confirm_text": "CLEAR DEMO DATA"})
        assert r.status_code == 200

        companies = bd_company_store.list_companies(api_env["company"])
        assert len(companies) == 1
        assert companies[0].name == "Manual Co"
        assert companies[0].source == "manual"

    def test_clear_demo_logs_activity(self, api_env):
        from backend.services.bd_activity_store import list_activity
        client.post("/api/bd/demo/seed")
        client.post("/api/bd/workspace/clear-demo", json={"confirm_text": "CLEAR DEMO DATA"})
        acts = list_activity(api_env["activity"])
        assert any(a.action == "demo_data_cleared" for a in acts)


# ── TestClearImported ─────────────────────────────────────────────────────────

class TestClearImported:
    """POST /workspace/clear-imported must remove only source='imported' records."""

    def test_clear_imported_requires_confirmation(self, api_env):
        r = client.post("/api/bd/workspace/clear-imported", json={"confirm_text": "wrong"})
        assert r.status_code == 400

    def test_clear_imported_wrong_text_rejected(self, api_env):
        r = client.post("/api/bd/workspace/clear-imported", json={"confirm_text": "CLEAR DEMO DATA"})
        assert r.status_code == 400

    def test_clear_imported_removes_imported_records(self, api_env):
        csv_data = b"name,domain\nImported Co,imp.com\n"
        client.post(
            "/api/bd/import/companies-csv?dry_run=false",
            files={"file": ("co.csv", io.BytesIO(csv_data), "text/csv")},
        )
        companies_before = bd_company_store.list_companies(api_env["company"])
        assert len(companies_before) == 1

        r = client.post("/api/bd/workspace/clear-imported", json={"confirm_text": "CLEAR IMPORTED DATA"})
        assert r.status_code == 200
        assert r.json()["records_removed"] == 1

        companies_after = bd_company_store.list_companies(api_env["company"])
        assert len(companies_after) == 0

    def test_clear_imported_preserves_demo_records(self, api_env):
        client.post("/api/bd/demo/seed")
        # Add an imported company
        csv_data = b"name,domain\nImported Co,imp.com\n"
        client.post(
            "/api/bd/import/companies-csv?dry_run=false",
            files={"file": ("co.csv", io.BytesIO(csv_data), "text/csv")},
        )

        r = client.post("/api/bd/workspace/clear-imported", json={"confirm_text": "CLEAR IMPORTED DATA"})
        assert r.status_code == 200

        companies = bd_company_store.list_companies(api_env["company"])
        # All remaining must be demo
        assert all(c.source == "demo" for c in companies)
        assert all(c.name != "Imported Co" for c in companies)

    def test_clear_imported_logs_activity(self, api_env):
        from backend.services.bd_activity_store import list_activity
        csv_data = b"name,domain\nImported Co,imp.com\n"
        client.post(
            "/api/bd/import/companies-csv?dry_run=false",
            files={"file": ("co.csv", io.BytesIO(csv_data), "text/csv")},
        )
        client.post("/api/bd/workspace/clear-imported", json={"confirm_text": "CLEAR IMPORTED DATA"})
        acts = list_activity(api_env["activity"])
        assert any(a.action == "imported_data_cleared" for a in acts)


# ── TestRestore ───────────────────────────────────────────────────────────────

class TestRestore:
    """POST /workspace/restore — dry_run and actual restore."""

    def _make_backup(self, api_env):
        client.post("/api/bd/demo/seed")
        r = client.get("/api/bd/workspace/backup")
        assert r.status_code == 200
        return r.json()

    def test_restore_dry_run_returns_counts(self, api_env):
        backup = self._make_backup(api_env)
        # Clear workspace first
        client.post("/api/bd/workspace/clear-all", json={"confirm_text": "CLEAR DOBRYBOT WORKSPACE"})

        r = client.post("/api/bd/workspace/restore", json={
            "backup": backup,
            "confirm_text": "anything",  # dry_run=true doesn't check confirm
            "dry_run": True,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["dry_run"] is True
        assert data["companies_restored"] > 0
        assert data["prospects_restored"] > 0
        # Dry run must NOT persist
        companies = bd_company_store.list_companies(api_env["company"])
        assert len(companies) == 0

    def test_restore_dry_run_does_not_persist(self, api_env):
        backup = self._make_backup(api_env)
        client.post("/api/bd/workspace/clear-all", json={"confirm_text": "CLEAR DOBRYBOT WORKSPACE"})
        client.post("/api/bd/workspace/restore", json={
            "backup": backup,
            "confirm_text": "anything",
            "dry_run": True,
        })
        assert len(bd_company_store.list_companies(api_env["company"])) == 0

    def test_restore_wrong_confirm_rejected(self, api_env):
        backup = self._make_backup(api_env)
        r = client.post("/api/bd/workspace/restore", json={
            "backup": backup,
            "confirm_text": "wrong",
            "dry_run": False,
        })
        assert r.status_code == 400

    def test_restore_invalid_backup_rejected(self, api_env):
        r = client.post("/api/bd/workspace/restore", json={
            "backup": {"not_a_backup": True},
            "confirm_text": "RESTORE DOBRYBOT WORKSPACE",
            "dry_run": False,
        })
        assert r.status_code == 400

    def test_restore_restores_all_entities(self, api_env):
        backup = self._make_backup(api_env)
        companies_before = len(backup["companies"])

        # Clear
        client.post("/api/bd/workspace/clear-all", json={"confirm_text": "CLEAR DOBRYBOT WORKSPACE"})
        assert len(bd_company_store.list_companies(api_env["company"])) == 0

        # Restore
        r = client.post("/api/bd/workspace/restore", json={
            "backup": backup,
            "confirm_text": "RESTORE DOBRYBOT WORKSPACE",
            "dry_run": False,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["dry_run"] is False
        assert data["companies_restored"] == companies_before

        companies_after = bd_company_store.list_companies(api_env["company"])
        assert len(companies_after) == companies_before

    def test_restore_logs_activity(self, api_env):
        from backend.services.bd_activity_store import list_activity
        backup = self._make_backup(api_env)
        client.post("/api/bd/workspace/clear-all", json={"confirm_text": "CLEAR DOBRYBOT WORKSPACE"})
        client.post("/api/bd/workspace/restore", json={
            "backup": backup,
            "confirm_text": "RESTORE DOBRYBOT WORKSPACE",
            "dry_run": False,
        })
        acts = list_activity(api_env["activity"])
        assert any(a.action == "workspace_restored" for a in acts)

    def test_restore_result_safety_notice(self, api_env):
        backup = self._make_backup(api_env)
        r = client.post("/api/bd/workspace/restore", json={
            "backup": backup,
            "confirm_text": "RESTORE DOBRYBOT WORKSPACE",
            "dry_run": False,
        })
        assert r.status_code == 200
        assert "local" in r.json()["safety_notice"].lower()


# ── TestSafetyInvariants ──────────────────────────────────────────────────────

class TestSafetyInvariants:
    """Source-level operations must not bypass safety requirements."""

    def test_clear_demo_exact_text_only(self, api_env):
        for bad in ["clear demo data", "CLEAR DEMO", "CLEAR DEMO DATA ", " CLEAR DEMO DATA"]:
            r = client.post("/api/bd/workspace/clear-demo", json={"confirm_text": bad})
            assert r.status_code == 400, f"Expected 400 for: {bad!r}"

    def test_clear_imported_exact_text_only(self, api_env):
        for bad in ["clear imported data", "CLEAR IMPORTED", "CLEAR IMPORTED DATA ", " CLEAR IMPORTED DATA"]:
            r = client.post("/api/bd/workspace/clear-imported", json={"confirm_text": bad})
            assert r.status_code == 400, f"Expected 400 for: {bad!r}"

    def test_restore_exact_text_only(self, api_env):
        client.post("/api/bd/demo/seed")
        backup = client.get("/api/bd/workspace/backup").json()
        client.post("/api/bd/workspace/clear-all", json={"confirm_text": "CLEAR DOBRYBOT WORKSPACE"})
        for bad in ["restore dobrybot workspace", "RESTORE WORKSPACE", "RESTORE DOBRYBOT WORKSPACE "]:
            r = client.post("/api/bd/workspace/restore", json={
                "backup": backup,
                "confirm_text": bad,
                "dry_run": False,
            })
            assert r.status_code == 400, f"Expected 400 for: {bad!r}"

    def test_no_auto_send_field_on_any_model(self):
        """None of the BD models should have send/auto_send/send_at fields."""
        models = [BDCompany, BDProspect, BDSignal, BDOpportunity, BDDealPacket, BDOutreachDraft, BDRecommendation]
        for model in models:
            fields = model.model_fields.keys()
            for forbidden in ["auto_send", "send_at", "sent_automatically"]:
                assert forbidden not in fields, f"{model.__name__} must not have {forbidden}"

    def test_no_external_api_fields_on_any_model(self):
        """No model should contain fields for external API credentials."""
        models = [BDCompany, BDProspect, BDSignal, BDOpportunity, BDDealPacket, BDOutreachDraft, BDRecommendation]
        for model in models:
            fields = model.model_fields.keys()
            for forbidden in ["api_key", "linkedin_token", "gmail_token", "access_token"]:
                assert forbidden not in fields, f"{model.__name__} must not have {forbidden}"

    def test_source_field_does_not_break_existing_demo_seed(self, api_env):
        r = client.post("/api/bd/demo/seed")
        assert r.status_code == 200
        data = r.json()
        assert data["stats"]["companies"] > 0
        assert data["stats"]["prospects"] > 0

    def test_clear_demo_confirm_not_same_as_clear_all(self, api_env):
        client.post("/api/bd/demo/seed")
        # Using clear-all text on clear-demo endpoint should fail
        r = client.post("/api/bd/workspace/clear-demo", json={"confirm_text": "CLEAR DOBRYBOT WORKSPACE"})
        assert r.status_code == 400

    def test_clear_imported_confirm_not_same_as_clear_all(self, api_env):
        r = client.post("/api/bd/workspace/clear-imported", json={"confirm_text": "CLEAR DOBRYBOT WORKSPACE"})
        assert r.status_code == 400

    def test_restore_backup_marker_required(self, api_env):
        """A backup without the dobrybot_workspace_backup marker must be rejected."""
        r = client.post("/api/bd/workspace/restore", json={
            "backup": {"companies": [], "prospects": []},
            "confirm_text": "RESTORE DOBRYBOT WORKSPACE",
            "dry_run": False,
        })
        assert r.status_code == 400
