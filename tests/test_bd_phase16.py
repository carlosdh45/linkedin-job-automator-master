"""
Phase 16: Workspace Data Management + Export/Backup + Demo vs Real Mode — test suite.

Covers:
- GET /api/bd/workspace/status (counts, ICP, health warnings)
- GET /api/bd/workspace/backup (no secrets, correct keys)
- POST /api/bd/workspace/restore-preview (validate, count, no persist)
- POST /api/bd/workspace/clear-all (requires exact confirm text)
- GET /api/bd/export/companies.csv
- GET /api/bd/export/prospects.csv
- GET /api/bd/export/signals.csv
- GET /api/bd/export/opportunities.csv
- GET /api/bd/export/workspace.json
- GET /api/bd/import/history (created after CSV commit)
- GET /api/bd/import/history/{id}
- Data health warnings
- Safety invariants (no send, no auto-outbound, no external APIs)
- Existing test count still passes
"""
import io
import json
import pytest
from fastapi.testclient import TestClient

from backend.config import (
    get_bd_company_path, get_bd_prospect_path, get_bd_signal_path,
    get_bd_pain_point_path, get_bd_opportunity_path,
    get_bd_deal_packet_path, get_bd_outreach_path,
    get_bd_activity_path, get_bd_icp_config_path,
    get_bd_recommendation_path, get_bd_import_history_path,
)
from backend.main import app
from backend.services.bd_company_store import list_companies
from backend.services.bd_import_history_store import list_import_history


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def p16_paths(tmp_path):
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
        "import_history":  str(tmp_path / "import_history.json"),
    }


@pytest.fixture
def client(p16_paths, monkeypatch):
    monkeypatch.setenv("DOBRYBOT_BD_COMPANY_PATH",         p16_paths["company"])
    monkeypatch.setenv("DOBRYBOT_BD_PROSPECT_PATH",        p16_paths["prospect"])
    monkeypatch.setenv("DOBRYBOT_BD_SIGNAL_PATH",          p16_paths["signal"])
    monkeypatch.setenv("DOBRYBOT_BD_PAIN_POINT_PATH",      p16_paths["pain_point"])
    monkeypatch.setenv("DOBRYBOT_BD_OPPORTUNITY_PATH",     p16_paths["opportunity"])
    monkeypatch.setenv("DOBRYBOT_BD_DEAL_PACKET_PATH",     p16_paths["deal_packet"])
    monkeypatch.setenv("DOBRYBOT_BD_OUTREACH_PATH",        p16_paths["outreach"])
    monkeypatch.setenv("DOBRYBOT_BD_ACTIVITY_PATH",        p16_paths["activity"])
    monkeypatch.setenv("DOBRYBOT_BD_ICP_CONFIG_PATH",      p16_paths["icp_config"])
    monkeypatch.setenv("DOBRYBOT_BD_RECOMMENDATION_PATH",  p16_paths["recommendation"])
    monkeypatch.setenv("DOBRYBOT_BD_IMPORT_HISTORY_PATH",  p16_paths["import_history"])

    app.dependency_overrides[get_bd_company_path]         = lambda: p16_paths["company"]
    app.dependency_overrides[get_bd_prospect_path]        = lambda: p16_paths["prospect"]
    app.dependency_overrides[get_bd_signal_path]          = lambda: p16_paths["signal"]
    app.dependency_overrides[get_bd_pain_point_path]      = lambda: p16_paths["pain_point"]
    app.dependency_overrides[get_bd_opportunity_path]     = lambda: p16_paths["opportunity"]
    app.dependency_overrides[get_bd_deal_packet_path]     = lambda: p16_paths["deal_packet"]
    app.dependency_overrides[get_bd_outreach_path]        = lambda: p16_paths["outreach"]
    app.dependency_overrides[get_bd_activity_path]        = lambda: p16_paths["activity"]
    app.dependency_overrides[get_bd_icp_config_path]      = lambda: p16_paths["icp_config"]
    app.dependency_overrides[get_bd_recommendation_path]  = lambda: p16_paths["recommendation"]
    app.dependency_overrides[get_bd_import_history_path]  = lambda: p16_paths["import_history"]

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _csv(content: str, name: str = "import.csv"):
    return ("file", (name, io.BytesIO(content.encode()), "text/csv"))


def _commit_companies(client, csv_content: str = "name,domain\nAcme Corp,acme.io\n"):
    return client.post(
        "/api/bd/import/companies-csv?dry_run=false",
        files=[_csv(csv_content)],
    )


# ── Workspace Status ───────────────────────────────────────────────────────────

class TestWorkspaceStatus:
    def test_status_returns_200(self, client):
        r = client.get("/api/bd/workspace/status")
        assert r.status_code == 200

    def test_status_zero_counts_on_empty(self, client):
        data = client.get("/api/bd/workspace/status").json()
        assert data["total_companies"] == 0
        assert data["total_prospects"] == 0
        assert data["total_signals"] == 0

    def test_status_counts_companies(self, client):
        client.post("/api/bd/companies", json={"name": "Apex Software"})
        data = client.get("/api/bd/workspace/status").json()
        assert data["total_companies"] == 1

    def test_status_counts_signals(self, client):
        client.post("/api/bd/signals", json={"company_name": "Beta Co", "signal_type": "hiring", "summary": "Hiring"})
        data = client.get("/api/bd/workspace/status").json()
        assert data["total_signals"] == 1

    def test_status_icp_false_when_unconfigured(self, client):
        data = client.get("/api/bd/workspace/status").json()
        assert data["icp_configured"] is False

    def test_status_icp_true_when_configured(self, client):
        client.put("/api/bd/icp-config", json={"target_industries": ["SaaS"], "target_roles": ["CEO"]})
        data = client.get("/api/bd/workspace/status").json()
        assert data["icp_configured"] is True

    def test_status_has_local_only_flag(self, client):
        data = client.get("/api/bd/workspace/status").json()
        assert data["local_only"] is True

    def test_status_has_safety_notice(self, client):
        data = client.get("/api/bd/workspace/status").json()
        assert len(data["safety_notice"]) > 0

    def test_status_imported_counts_reflect_history(self, client, p16_paths):
        _commit_companies(client, "name,domain\nAcme Corp,acme.io\nBeta Inc,beta.io\n")
        data = client.get("/api/bd/workspace/status").json()
        assert data["imported_companies"] == 2

    def test_status_last_import_date_set_after_commit(self, client):
        _commit_companies(client)
        data = client.get("/api/bd/workspace/status").json()
        assert data["last_import_date"] is not None


# ── Data Health Warnings ──────────────────────────────────────────────────────

class TestDataHealthWarnings:
    def test_icp_warning_when_not_configured(self, client):
        data = client.get("/api/bd/workspace/status").json()
        warnings = data["data_health_warnings"]
        assert any("ICP" in w for w in warnings)

    def test_no_icp_warning_when_configured(self, client):
        client.put("/api/bd/icp-config", json={"target_industries": ["SaaS"]})
        data = client.get("/api/bd/workspace/status").json()
        warnings = data["data_health_warnings"]
        assert not any("ICP not configured" in w for w in warnings)

    def test_warning_for_companies_without_domain(self, client):
        client.post("/api/bd/companies", json={"name": "NoDomain Co"})
        data = client.get("/api/bd/workspace/status").json()
        warnings = data["data_health_warnings"]
        assert any("missing domain" in w for w in warnings)

    def test_warning_for_unevaluated_signals(self, client):
        client.post("/api/bd/signals", json={"company_name": "Gamma", "summary": "Hiring"})
        data = client.get("/api/bd/workspace/status").json()
        warnings = data["data_health_warnings"]
        assert any("not yet evaluated" in w for w in warnings)


# ── Backup ────────────────────────────────────────────────────────────────────

class TestWorkspaceBackup:
    def test_backup_returns_200(self, client):
        r = client.get("/api/bd/workspace/backup")
        assert r.status_code == 200

    def test_backup_has_required_keys(self, client):
        data = client.get("/api/bd/workspace/backup").json()
        required = ["companies", "prospects", "signals", "opportunities",
                    "deal_packets", "outreach_drafts", "recommendations",
                    "icp_config", "activity_log", "import_history"]
        for key in required:
            assert key in data, f"Missing key: {key}"

    def test_backup_has_safety_notice(self, client):
        data = client.get("/api/bd/workspace/backup").json()
        assert "safety_notice" in data
        assert len(data["safety_notice"]) > 0

    def test_backup_local_only_flag(self, client):
        data = client.get("/api/bd/workspace/backup").json()
        assert data["local_only"] is True

    def test_backup_does_not_include_env_or_secrets(self, client):
        raw = client.get("/api/bd/workspace/backup").text
        assert "DOBRYBOT_BD_COMPANY_PATH" not in raw
        assert "DOBRYBOT_BD_SIGNAL_PATH" not in raw
        assert "password" not in raw.lower()
        assert "bearer" not in raw.lower()

    def test_backup_contains_seeded_data(self, client):
        client.post("/api/bd/demo/seed")
        data = client.get("/api/bd/workspace/backup").json()
        assert len(data["companies"]) > 0

    def test_backup_logs_activity(self, client, p16_paths):
        from backend.services.bd_activity_store import list_activity
        client.get("/api/bd/workspace/backup")
        activities = list_activity(p16_paths["activity"])
        actions = [a.action for a in activities]
        assert "backup_created" in actions


# ── Restore Preview ───────────────────────────────────────────────────────────

class TestRestorePreview:
    def test_preview_returns_200_on_valid_backup(self, client):
        payload = {
            "dobrybot_workspace_backup": True,
            "companies": [{"id": "1", "name": "Test"}],
            "prospects": [],
            "signals": [],
            "opportunities": [],
            "deal_packets": [],
            "outreach_drafts": [],
            "recommendations": [],
        }
        r = client.post("/api/bd/workspace/restore-preview", json=payload)
        assert r.status_code == 200

    def test_preview_counts_correctly(self, client):
        payload = {
            "dobrybot_workspace_backup": True,
            "companies": [{"id": "1"}, {"id": "2"}],
            "prospects": [{"id": "3"}],
            "signals": [],
            "opportunities": [],
            "deal_packets": [],
            "outreach_drafts": [],
            "recommendations": [],
        }
        data = client.post("/api/bd/workspace/restore-preview", json=payload).json()
        assert data["companies_count"] == 2
        assert data["prospects_count"] == 1
        assert data["signals_count"] == 0

    def test_preview_warns_on_missing_backup_key(self, client):
        payload = {"companies": [{"id": "1"}]}
        data = client.post("/api/bd/workspace/restore-preview", json=payload).json()
        assert any("dobrybot_workspace_backup" in w for w in data["warnings"])

    def test_preview_warns_on_empty_backup(self, client):
        payload = {"dobrybot_workspace_backup": True}
        data = client.post("/api/bd/workspace/restore-preview", json=payload).json()
        assert any("empty" in w for w in data["warnings"])

    def test_preview_does_not_persist_data(self, client, p16_paths):
        payload = {
            "dobrybot_workspace_backup": True,
            "companies": [{"id": "c1", "name": "Ghost Co"}],
            "prospects": [], "signals": [], "opportunities": [],
            "deal_packets": [], "outreach_drafts": [], "recommendations": [],
        }
        client.post("/api/bd/workspace/restore-preview", json=payload)
        companies = list_companies(p16_paths["company"])
        assert not any(c.name == "Ghost Co" for c in companies)

    def test_preview_has_safety_notice(self, client):
        payload = {"dobrybot_workspace_backup": True, "companies": [{"id": "1"}]}
        data = client.post("/api/bd/workspace/restore-preview", json=payload).json()
        assert "safety_notice" in data
        assert "no data" in data["safety_notice"].lower() or "preview" in data["safety_notice"].lower()


# ── Clear All ─────────────────────────────────────────────────────────────────

class TestClearAll:
    def test_clear_all_requires_exact_confirm_text(self, client):
        r = client.post("/api/bd/workspace/clear-all", json={"confirm_text": "wrong"})
        assert r.status_code == 400

    def test_clear_all_wrong_text_does_not_clear(self, client):
        client.post("/api/bd/companies", json={"name": "Apex"})
        client.post("/api/bd/workspace/clear-all", json={"confirm_text": "nope"})
        companies = client.get("/api/bd/companies").json()
        assert len(companies) > 0

    def test_clear_all_succeeds_with_correct_text(self, client):
        client.post("/api/bd/companies", json={"name": "Apex"})
        r = client.post(
            "/api/bd/workspace/clear-all",
            json={"confirm_text": "CLEAR DOBRYBOT WORKSPACE"},
        )
        assert r.status_code == 200

    def test_clear_all_removes_companies(self, client):
        client.post("/api/bd/companies", json={"name": "Apex"})
        client.post(
            "/api/bd/workspace/clear-all",
            json={"confirm_text": "CLEAR DOBRYBOT WORKSPACE"},
        )
        companies = client.get("/api/bd/companies").json()
        assert len(companies) == 0

    def test_clear_all_returns_cleared_list(self, client):
        data = client.post(
            "/api/bd/workspace/clear-all",
            json={"confirm_text": "CLEAR DOBRYBOT WORKSPACE"},
        ).json()
        assert "companies" in data["cleared"]

    def test_clear_all_logs_activity(self, client, p16_paths):
        from backend.services.bd_activity_store import list_activity
        client.post(
            "/api/bd/workspace/clear-all",
            json={"confirm_text": "CLEAR DOBRYBOT WORKSPACE"},
        )
        activities = list_activity(p16_paths["activity"])
        assert any(a.action == "workspace_cleared" for a in activities)

    def test_clear_demo_requires_confirm_text(self, client):
        # Phase 17: clear-demo is now functional — wrong confirm_text returns 400
        r = client.post("/api/bd/workspace/clear-demo", json={"confirm_text": "wrong"})
        assert r.status_code == 400

    def test_clear_imported_requires_confirm_text(self, client):
        # Phase 17: clear-imported is now functional — wrong confirm_text returns 400
        r = client.post("/api/bd/workspace/clear-imported", json={"confirm_text": "wrong"})
        assert r.status_code == 400


# ── Export Endpoints ──────────────────────────────────────────────────────────

class TestExports:
    def test_export_companies_csv_returns_200(self, client):
        r = client.get("/api/bd/export/companies.csv")
        assert r.status_code == 200

    def test_export_companies_csv_has_header(self, client):
        client.post("/api/bd/companies", json={"name": "Apex"})
        text = client.get("/api/bd/export/companies.csv").text
        assert "name" in text.lower()
        assert "Apex" in text

    def test_export_prospects_csv_returns_200(self, client):
        r = client.get("/api/bd/export/prospects.csv")
        assert r.status_code == 200

    def test_export_signals_csv_returns_200(self, client):
        r = client.get("/api/bd/export/signals.csv")
        assert r.status_code == 200

    def test_export_signals_csv_has_header(self, client):
        client.post("/api/bd/signals", json={"company_name": "Gamma", "summary": "Hiring"})
        text = client.get("/api/bd/export/signals.csv").text
        assert "company_name" in text
        assert "Gamma" in text

    def test_export_opportunities_csv_returns_200(self, client):
        r = client.get("/api/bd/export/opportunities.csv")
        assert r.status_code == 200

    def test_export_workspace_json_returns_200(self, client):
        r = client.get("/api/bd/export/workspace.json")
        assert r.status_code == 200

    def test_export_workspace_json_has_companies(self, client):
        data = client.get("/api/bd/export/workspace.json").json()
        assert "companies" in data

    def test_export_workspace_json_local_only(self, client):
        data = client.get("/api/bd/export/workspace.json").json()
        assert data.get("local_only") is True

    def test_export_logs_activity(self, client, p16_paths):
        from backend.services.bd_activity_store import list_activity
        client.get("/api/bd/export/companies.csv")
        activities = list_activity(p16_paths["activity"])
        assert any(a.action == "export_created" for a in activities)

    def test_export_does_not_include_secrets(self, client):
        raw = client.get("/api/bd/export/workspace.json").text
        assert "DOBRYBOT_" not in raw
        assert ".env" not in raw


# ── Import History ────────────────────────────────────────────────────────────

class TestImportHistory:
    def test_history_empty_initially(self, client):
        data = client.get("/api/bd/import/history").json()
        assert data == []

    def test_history_created_after_company_commit(self, client, p16_paths):
        _commit_companies(client)
        history = list_import_history(p16_paths["import_history"])
        assert len(history) == 1
        assert history[0].import_type == "companies"

    def test_history_endpoint_returns_entries(self, client):
        _commit_companies(client)
        data = client.get("/api/bd/import/history").json()
        assert len(data) == 1
        assert data[0]["import_type"] == "companies"

    def test_history_records_counts(self, client):
        _commit_companies(client, "name,domain\nApex,apex.io\nBeta,beta.io\n")
        data = client.get("/api/bd/import/history").json()
        assert data[0]["imported_count"] == 2

    def test_history_entry_by_id(self, client):
        _commit_companies(client)
        entries = client.get("/api/bd/import/history").json()
        entry_id = entries[0]["id"]
        r = client.get(f"/api/bd/import/history/{entry_id}")
        assert r.status_code == 200
        assert r.json()["id"] == entry_id

    def test_history_entry_not_found_returns_404(self, client):
        r = client.get("/api/bd/import/history/nonexistent-id")
        assert r.status_code == 404

    def test_dry_run_does_not_create_history(self, client, p16_paths):
        client.post(
            "/api/bd/import/companies-csv?dry_run=true",
            files=[_csv("name,domain\nApex,apex.io\n")],
        )
        history = list_import_history(p16_paths["import_history"])
        assert len(history) == 0

    def test_signal_import_creates_history(self, client):
        client.post(
            "/api/bd/import/signals-csv?dry_run=false",
            files=[_csv("company_name,signal_type,description\nApex,hiring,Posting roles\n")],
        )
        data = client.get("/api/bd/import/history").json()
        assert any(e["import_type"] == "signals" for e in data)

    def test_history_has_local_only_flag(self, client):
        _commit_companies(client)
        data = client.get("/api/bd/import/history").json()
        assert data[0]["local_only"] is True


# ── Safety Invariants ─────────────────────────────────────────────────────────

class TestSafetyInvariants:
    def _all_paths(self):
        return [r.path for r in app.routes if hasattr(r, "path")]

    def test_no_send_endpoint(self):
        for path in self._all_paths():
            assert "/send" not in path, f"Forbidden /send path: {path}"

    def test_no_auto_outbound_endpoint(self):
        for path in self._all_paths():
            assert "auto-outbound" not in path
            assert "mass-outbound" not in path

    def test_no_auto_apply_endpoint(self):
        for path in self._all_paths():
            assert "auto-apply" not in path

    def test_workspace_status_has_safety_notice(self, client):
        data = client.get("/api/bd/workspace/status").json()
        notice = data.get("safety_notice", "")
        assert "local" in notice.lower() or "external" in notice.lower()

    def test_backup_does_not_include_credentials(self, client):
        raw = client.get("/api/bd/workspace/backup").text
        assert "token" not in raw.lower() or "dobrybot_workspace_backup" in raw.lower()
        assert "bearer" not in raw.lower()

    def test_clear_all_wrong_confirm_blocked(self, client):
        client.post("/api/bd/companies", json={"name": "Protected"})
        client.post("/api/bd/workspace/clear-all", json={"confirm_text": "yes delete"})
        companies = client.get("/api/bd/companies").json()
        assert len(companies) > 0
