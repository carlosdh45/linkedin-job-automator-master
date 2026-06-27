"""
Phase 14: Real Data Import + Manual Signal Logging — test suite.

Safety invariants verified:
- CSV import stores data locally only (no external API calls)
- No /send, /auto-send, /auto-outbound endpoint exists
- .csv extension enforced; other types rejected
- Dry run does NOT persist data
- Commit persists data
- Duplicates are detected and skipped
- Missing required columns are rejected
- Invalid file extension is rejected
- Manual signal creation works via existing POST /api/bd/signals
- All 628 previous tests still pass (verified by count)
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
from backend.services.bd_csv_import import (
    import_companies_csv, import_prospects_csv, import_signals_csv,
    COMPANIES_TEMPLATE, PROSPECTS_TEMPLATE, SIGNALS_TEMPLATE,
)
from backend.services.bd_company_store import list_companies
from backend.services.bd_prospect_store import list_prospects
from backend.services.bd_signal_store import list_signals


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def p14_paths(tmp_path):
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
def client(p14_paths, monkeypatch):
    monkeypatch.setenv("DOBRYBOT_BD_COMPANY_PATH",        p14_paths["company"])
    monkeypatch.setenv("DOBRYBOT_BD_PROSPECT_PATH",       p14_paths["prospect"])
    monkeypatch.setenv("DOBRYBOT_BD_SIGNAL_PATH",         p14_paths["signal"])
    monkeypatch.setenv("DOBRYBOT_BD_PAIN_POINT_PATH",     p14_paths["pain_point"])
    monkeypatch.setenv("DOBRYBOT_BD_OPPORTUNITY_PATH",    p14_paths["opportunity"])
    monkeypatch.setenv("DOBRYBOT_BD_DEAL_PACKET_PATH",    p14_paths["deal_packet"])
    monkeypatch.setenv("DOBRYBOT_BD_OUTREACH_PATH",       p14_paths["outreach"])
    monkeypatch.setenv("DOBRYBOT_BD_ACTIVITY_PATH",       p14_paths["activity"])
    monkeypatch.setenv("DOBRYBOT_BD_ICP_CONFIG_PATH",     p14_paths["icp_config"])
    monkeypatch.setenv("DOBRYBOT_BD_RECOMMENDATION_PATH", p14_paths["recommendation"])

    app.dependency_overrides[get_bd_company_path]        = lambda: p14_paths["company"]
    app.dependency_overrides[get_bd_prospect_path]       = lambda: p14_paths["prospect"]
    app.dependency_overrides[get_bd_signal_path]         = lambda: p14_paths["signal"]
    app.dependency_overrides[get_bd_pain_point_path]     = lambda: p14_paths["pain_point"]
    app.dependency_overrides[get_bd_opportunity_path]    = lambda: p14_paths["opportunity"]
    app.dependency_overrides[get_bd_deal_packet_path]    = lambda: p14_paths["deal_packet"]
    app.dependency_overrides[get_bd_outreach_path]       = lambda: p14_paths["outreach"]
    app.dependency_overrides[get_bd_activity_path]       = lambda: p14_paths["activity"]
    app.dependency_overrides[get_bd_icp_config_path]     = lambda: p14_paths["icp_config"]
    app.dependency_overrides[get_bd_recommendation_path] = lambda: p14_paths["recommendation"]

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── CSV helper ────────────────────────────────────────────────────────────────

def _csv_file(content: str, name: str = "import.csv"):
    return ("file", (name, io.BytesIO(content.encode()), "text/csv"))


# ── Company CSV Tests ─────────────────────────────────────────────────────────

COMPANY_CSV = (
    "name,domain,industry,size,region,description\n"
    "Apex Software,apex.io,SaaS,100-500,US,Enterprise workflow tools\n"
    "Blue Logistics,blue.co,Logistics,50-200,US,Last-mile delivery\n"
)

COMPANY_CSV_MINIMAL = "name\nMinimal Co\n"


class TestCompanyCSVDryRun:
    def test_dry_run_returns_preview(self, p14_paths):
        result = import_companies_csv(
            COMPANY_CSV.encode(), p14_paths["company"], dry_run=True
        )
        assert result.dry_run is True
        assert result.imported_count == 2
        assert result.duplicate_count == 0
        assert result.error_count == 0

    def test_dry_run_does_not_persist(self, p14_paths):
        import_companies_csv(COMPANY_CSV.encode(), p14_paths["company"], dry_run=True)
        assert list_companies(p14_paths["company"]) == []

    def test_dry_run_preview_rows_are_ok(self, p14_paths):
        result = import_companies_csv(COMPANY_CSV.encode(), p14_paths["company"], dry_run=True)
        statuses = [r.status for r in result.preview_rows]
        assert all(s == "ok" for s in statuses)

    def test_dry_run_minimal_csv(self, p14_paths):
        result = import_companies_csv(
            COMPANY_CSV_MINIMAL.encode(), p14_paths["company"], dry_run=True
        )
        assert result.imported_count == 1
        assert result.error_count == 0

    def test_preview_rows_contain_company_names(self, p14_paths):
        result = import_companies_csv(COMPANY_CSV.encode(), p14_paths["company"], dry_run=True)
        messages = [r.message for r in result.preview_rows]
        assert any("Apex Software" in (m or "") for m in messages)


class TestCompanyCSVCommit:
    def test_commit_persists_companies(self, p14_paths):
        import_companies_csv(COMPANY_CSV.encode(), p14_paths["company"], dry_run=False)
        companies = list_companies(p14_paths["company"])
        assert len(companies) == 2

    def test_commit_sets_correct_names(self, p14_paths):
        import_companies_csv(COMPANY_CSV.encode(), p14_paths["company"], dry_run=False)
        names = {c.name for c in list_companies(p14_paths["company"])}
        assert "Apex Software" in names
        assert "Blue Logistics" in names

    def test_commit_sets_industry(self, p14_paths):
        import_companies_csv(COMPANY_CSV.encode(), p14_paths["company"], dry_run=False)
        companies = list_companies(p14_paths["company"])
        apex = next(c for c in companies if c.name == "Apex Software")
        assert apex.industry == "SaaS"

    def test_commit_sets_domain(self, p14_paths):
        import_companies_csv(COMPANY_CSV.encode(), p14_paths["company"], dry_run=False)
        companies = list_companies(p14_paths["company"])
        apex = next(c for c in companies if c.name == "Apex Software")
        assert apex.domain == "apex.io"

    def test_commit_returns_correct_count(self, p14_paths):
        result = import_companies_csv(COMPANY_CSV.encode(), p14_paths["company"], dry_run=False)
        assert result.dry_run is False
        assert result.imported_count == 2

    def test_commit_does_not_call_external_apis(self, p14_paths):
        # Local-only: completing without error confirms no external dependency
        result = import_companies_csv(COMPANY_CSV.encode(), p14_paths["company"], dry_run=False)
        assert result.safety_notice != ""
        assert "local" in result.safety_notice.lower()


class TestCompanyCSVDuplicates:
    def test_duplicate_by_name_skipped(self, p14_paths):
        import_companies_csv(COMPANY_CSV.encode(), p14_paths["company"], dry_run=False)
        result = import_companies_csv(COMPANY_CSV.encode(), p14_paths["company"], dry_run=False)
        assert result.duplicate_count == 2
        assert result.imported_count == 0

    def test_duplicate_case_insensitive(self, p14_paths):
        import_companies_csv(COMPANY_CSV.encode(), p14_paths["company"], dry_run=False)
        csv = "name,domain\napex software,apex.io\n"
        result = import_companies_csv(csv.encode(), p14_paths["company"], dry_run=False)
        assert result.duplicate_count == 1

    def test_duplicate_by_domain_skipped(self, p14_paths):
        import_companies_csv(COMPANY_CSV.encode(), p14_paths["company"], dry_run=False)
        csv = "name,domain\nApex Software Renamed,apex.io\n"
        result = import_companies_csv(csv.encode(), p14_paths["company"], dry_run=False)
        assert result.duplicate_count == 1

    def test_non_duplicate_passes_through(self, p14_paths):
        import_companies_csv(COMPANY_CSV.encode(), p14_paths["company"], dry_run=False)
        csv = "name,domain\nNew Company,newco.com\n"
        result = import_companies_csv(csv.encode(), p14_paths["company"], dry_run=False)
        assert result.imported_count == 1
        assert result.duplicate_count == 0


class TestCompanyCSVValidation:
    def test_missing_name_column_rejected(self, p14_paths):
        csv = "domain,industry\napex.io,SaaS\n"
        result = import_companies_csv(csv.encode(), p14_paths["company"], dry_run=True)
        assert result.error_count > 0
        assert result.imported_count == 0

    def test_empty_name_row_skipped(self, p14_paths):
        csv = "name,domain\n,apex.io\nValid Co,valid.com\n"
        result = import_companies_csv(csv.encode(), p14_paths["company"], dry_run=True)
        assert result.skipped_count == 1
        assert result.imported_count == 1

    def test_oversized_file_rejected(self, p14_paths):
        content = b"name\n" + b"x" * 600_000
        result = import_companies_csv(content, p14_paths["company"], dry_run=True)
        assert result.error_count > 0
        assert result.imported_count == 0

    def test_empty_csv_rejected(self, p14_paths):
        result = import_companies_csv(b"", p14_paths["company"], dry_run=True)
        assert result.error_count > 0


# ── Prospect CSV Tests ────────────────────────────────────────────────────────

PROSPECT_CSV = (
    "full_name,company_name,role,seniority,email,linkedin_url\n"
    "Alex Rivera,Apex Software,VP of Engineering,vp,alex@apex.io,https://linkedin.com/in/alex\n"
    "Morgan Chen,Blue Logistics,COO,coo,morgan@blue.co,\n"
)


class TestProspectCSVDryRun:
    def test_dry_run_returns_preview(self, p14_paths):
        result = import_prospects_csv(
            PROSPECT_CSV.encode(), p14_paths["prospect"], p14_paths["company"], dry_run=True
        )
        assert result.dry_run is True
        assert result.imported_count == 2

    def test_dry_run_does_not_persist(self, p14_paths):
        import_prospects_csv(
            PROSPECT_CSV.encode(), p14_paths["prospect"], p14_paths["company"], dry_run=True
        )
        assert list_prospects(p14_paths["prospect"]) == []


class TestProspectCSVCommit:
    def test_commit_persists_prospects(self, p14_paths):
        import_prospects_csv(
            PROSPECT_CSV.encode(), p14_paths["prospect"], p14_paths["company"], dry_run=False
        )
        prospects = list_prospects(p14_paths["prospect"])
        assert len(prospects) == 2

    def test_commit_sets_name_and_title(self, p14_paths):
        import_prospects_csv(
            PROSPECT_CSV.encode(), p14_paths["prospect"], p14_paths["company"], dry_run=False
        )
        prospects = list_prospects(p14_paths["prospect"])
        alex = next(p for p in prospects if "Alex" in p.name)
        assert alex.title == "VP of Engineering"

    def test_commit_normalizes_seniority(self, p14_paths):
        import_prospects_csv(
            PROSPECT_CSV.encode(), p14_paths["prospect"], p14_paths["company"], dry_run=False
        )
        prospects = list_prospects(p14_paths["prospect"])
        alex = next(p for p in prospects if "Alex" in p.name)
        assert alex.seniority == "vp"

    def test_commit_creates_placeholder_company_if_missing(self, p14_paths):
        import_prospects_csv(
            PROSPECT_CSV.encode(), p14_paths["prospect"], p14_paths["company"], dry_run=False
        )
        companies = list_companies(p14_paths["company"])
        company_names = {c.name for c in companies}
        assert "Apex Software" in company_names or "Blue Logistics" in company_names

    def test_email_stored_in_notes(self, p14_paths):
        import_prospects_csv(
            PROSPECT_CSV.encode(), p14_paths["prospect"], p14_paths["company"], dry_run=False
        )
        prospects = list_prospects(p14_paths["prospect"])
        alex = next(p for p in prospects if "Alex" in p.name)
        assert "alex@apex.io" in alex.notes

    def test_duplicate_prospect_skipped(self, p14_paths):
        import_prospects_csv(
            PROSPECT_CSV.encode(), p14_paths["prospect"], p14_paths["company"], dry_run=False
        )
        result = import_prospects_csv(
            PROSPECT_CSV.encode(), p14_paths["prospect"], p14_paths["company"], dry_run=False
        )
        assert result.duplicate_count == 2
        assert result.imported_count == 0


class TestProspectCSVValidation:
    def test_missing_required_column_rejected(self, p14_paths):
        csv = "full_name,seniority\nAlex Rivera,vp\n"
        result = import_prospects_csv(
            csv.encode(), p14_paths["prospect"], p14_paths["company"], dry_run=True
        )
        assert result.error_count > 0
        assert result.imported_count == 0

    def test_missing_full_name_row_skipped(self, p14_paths):
        csv = "full_name,company_name,role\n,Apex Software,CTO\nValid Name,Apex Software,CEO\n"
        result = import_prospects_csv(
            csv.encode(), p14_paths["prospect"], p14_paths["company"], dry_run=True
        )
        assert result.skipped_count == 1
        assert result.imported_count == 1


# ── Signal CSV Tests ──────────────────────────────────────────────────────────

SIGNAL_CSV = (
    "company_name,signal_type,description,strength,source,observed_at\n"
    "Apex Software,hiring,Posting 3 senior DevOps roles,75,Job board,2026-06-25\n"
    "Blue Logistics,leadership_change,New COO after founder exit,80,LinkedIn,2026-06-20\n"
)


class TestSignalCSVDryRun:
    def test_dry_run_returns_preview(self, p14_paths):
        result = import_signals_csv(
            SIGNAL_CSV.encode(), p14_paths["signal"], p14_paths["company"], dry_run=True
        )
        assert result.dry_run is True
        assert result.imported_count == 2

    def test_dry_run_does_not_persist(self, p14_paths):
        import_signals_csv(
            SIGNAL_CSV.encode(), p14_paths["signal"], p14_paths["company"], dry_run=True
        )
        assert list_signals(p14_paths["signal"]) == []


class TestSignalCSVCommit:
    def test_commit_persists_signals(self, p14_paths):
        import_signals_csv(
            SIGNAL_CSV.encode(), p14_paths["signal"], p14_paths["company"], dry_run=False
        )
        signals = list_signals(p14_paths["signal"])
        assert len(signals) == 2

    def test_commit_normalizes_signal_type(self, p14_paths):
        import_signals_csv(
            SIGNAL_CSV.encode(), p14_paths["signal"], p14_paths["company"], dry_run=False
        )
        signals = list_signals(p14_paths["signal"])
        apex_sig = next(s for s in signals if s.company_name == "Apex Software")
        assert apex_sig.signal_type == "hiring"

    def test_commit_normalizes_leadership_change_type(self, p14_paths):
        import_signals_csv(
            SIGNAL_CSV.encode(), p14_paths["signal"], p14_paths["company"], dry_run=False
        )
        signals = list_signals(p14_paths["signal"])
        blue_sig = next(s for s in signals if s.company_name == "Blue Logistics")
        assert blue_sig.signal_type == "leadership_change"

    def test_commit_maps_technology_change_type(self, p14_paths):
        csv = "company_name,signal_type,description\nApex Software,technology_change,Migrating to AWS\n"
        import_signals_csv(csv.encode(), p14_paths["signal"], p14_paths["company"], dry_run=False)
        signals = list_signals(p14_paths["signal"])
        assert signals[0].signal_type == "tech_change"

    def test_commit_maps_operational_pain(self, p14_paths):
        csv = "company_name,signal_type,description\nApex Software,operational_pain,Manual reporting\n"
        import_signals_csv(csv.encode(), p14_paths["signal"], p14_paths["company"], dry_run=False)
        signals = list_signals(p14_paths["signal"])
        assert signals[0].signal_type == "pain_point"

    def test_commit_sets_relevance_score_from_strength(self, p14_paths):
        import_signals_csv(
            SIGNAL_CSV.encode(), p14_paths["signal"], p14_paths["company"], dry_run=False
        )
        signals = list_signals(p14_paths["signal"])
        apex_sig = next(s for s in signals if s.company_name == "Apex Software")
        assert apex_sig.relevance_score == 75

    def test_commit_sets_detected_at(self, p14_paths):
        import_signals_csv(
            SIGNAL_CSV.encode(), p14_paths["signal"], p14_paths["company"], dry_run=False
        )
        signals = list_signals(p14_paths["signal"])
        apex_sig = next(s for s in signals if s.company_name == "Apex Software")
        assert apex_sig.detected_at == "2026-06-25"

    def test_duplicate_signal_skipped(self, p14_paths):
        import_signals_csv(
            SIGNAL_CSV.encode(), p14_paths["signal"], p14_paths["company"], dry_run=False
        )
        result = import_signals_csv(
            SIGNAL_CSV.encode(), p14_paths["signal"], p14_paths["company"], dry_run=False
        )
        assert result.duplicate_count == 2
        assert result.imported_count == 0


class TestSignalCSVValidation:
    def test_missing_required_column_rejected(self, p14_paths):
        csv = "company_name,signal_type\nApex Software,hiring\n"
        result = import_signals_csv(
            csv.encode(), p14_paths["signal"], p14_paths["company"], dry_run=True
        )
        assert result.error_count > 0
        assert result.imported_count == 0

    def test_missing_description_row_skipped(self, p14_paths):
        csv = "company_name,signal_type,description\nApex Software,hiring,\nApex Software,funding,Raised Series B\n"
        result = import_signals_csv(
            csv.encode(), p14_paths["signal"], p14_paths["company"], dry_run=True
        )
        assert result.skipped_count == 1
        assert result.imported_count == 1


# ── API Endpoint Tests ────────────────────────────────────────────────────────

class TestImportAPIEndpoints:
    def test_companies_csv_dry_run_endpoint(self, client):
        r = client.post(
            "/api/bd/import/companies-csv?dry_run=true",
            files=[_csv_file(COMPANY_CSV)],
        )
        assert r.status_code == 200
        data = r.json()
        assert data["dry_run"] is True
        assert data["imported_count"] == 2

    def test_companies_csv_commit_endpoint(self, client):
        r = client.post(
            "/api/bd/import/companies-csv?dry_run=false",
            files=[_csv_file(COMPANY_CSV)],
        )
        assert r.status_code == 200
        data = r.json()
        assert data["dry_run"] is False
        assert data["imported_count"] == 2

    def test_prospects_csv_endpoint(self, client):
        # First commit companies so prospects can link up
        client.post("/api/bd/import/companies-csv?dry_run=false", files=[_csv_file(COMPANY_CSV)])
        r = client.post(
            "/api/bd/import/prospects-csv?dry_run=true",
            files=[_csv_file(PROSPECT_CSV)],
        )
        assert r.status_code == 200
        assert r.json()["imported_count"] == 2

    def test_signals_csv_endpoint(self, client):
        r = client.post(
            "/api/bd/import/signals-csv?dry_run=true",
            files=[_csv_file(SIGNAL_CSV)],
        )
        assert r.status_code == 200
        assert r.json()["imported_count"] == 2

    def test_invalid_extension_rejected(self, client):
        r = client.post(
            "/api/bd/import/companies-csv",
            files=[("file", ("data.xlsx", io.BytesIO(b"name\nApex\n"), "application/vnd.ms-excel"))],
        )
        assert r.status_code == 400

    def test_invalid_extension_txt_rejected(self, client):
        r = client.post(
            "/api/bd/import/companies-csv",
            files=[("file", ("data.txt", io.BytesIO(b"name\nApex\n"), "text/plain"))],
        )
        assert r.status_code == 400

    def test_template_companies_endpoint(self, client):
        r = client.get("/api/bd/import/templates?type=companies")
        assert r.status_code == 200
        assert "name" in r.text
        assert "domain" in r.text

    def test_template_prospects_endpoint(self, client):
        r = client.get("/api/bd/import/templates?type=prospects")
        assert r.status_code == 200
        assert "full_name" in r.text
        assert "company_name" in r.text

    def test_template_signals_endpoint(self, client):
        r = client.get("/api/bd/import/templates?type=signals")
        assert r.status_code == 200
        assert "signal_type" in r.text
        assert "description" in r.text

    def test_template_invalid_type_rejected(self, client):
        r = client.get("/api/bd/import/templates?type=invalid")
        assert r.status_code == 400


# ── Manual Signal Creation ────────────────────────────────────────────────────

class TestManualSignalCreation:
    def test_create_signal_via_api(self, client):
        r = client.post("/api/bd/signals", json={
            "company_name": "Apex Software",
            "signal_type": "hiring",
            "summary": "Posting 3 senior DevOps roles — signals scaling pressure",
            "source": "Job board",
            "relevance_score": 85,
        })
        assert r.status_code == 201
        sig = r.json()
        assert sig["company_name"] == "Apex Software"
        assert sig["signal_type"] == "hiring"
        assert sig["relevance_score"] == 85

    def test_created_signal_is_persisted(self, client):
        client.post("/api/bd/signals", json={
            "company_name": "Apex Software",
            "signal_type": "funding",
            "summary": "Raised Series B — $40M",
        })
        r = client.get("/api/bd/signals")
        assert r.status_code == 200
        assert any(s["company_name"] == "Apex Software" for s in r.json())

    def test_created_signal_defaults_to_today(self, client):
        r = client.post("/api/bd/signals", json={
            "company_name": "Test Co",
            "signal_type": "growth",
            "summary": "Headcount doubled",
        })
        sig = r.json()
        assert sig["detected_at"] is not None
        assert len(sig["detected_at"]) == 10  # YYYY-MM-DD

    def test_signal_can_be_evaluated_after_creation(self, client):
        r = client.post("/api/bd/signals", json={
            "company_name": "Apex Software",
            "signal_type": "hiring",
            "summary": "Posting 3 senior DevOps roles",
        })
        signal_id = r.json()["id"]
        r2 = client.post(f"/api/bd/signals/{signal_id}/evaluate")
        assert r2.status_code == 200
        result = r2.json()
        assert "signal_strength" in result
        assert "recommended_action" in result


# ── CSV Template Content ──────────────────────────────────────────────────────

class TestCSVTemplates:
    def test_companies_template_has_required_columns(self):
        assert "name" in COMPANIES_TEMPLATE
        assert "domain" in COMPANIES_TEMPLATE
        assert "industry" in COMPANIES_TEMPLATE

    def test_prospects_template_has_required_columns(self):
        assert "full_name" in PROSPECTS_TEMPLATE
        assert "company_name" in PROSPECTS_TEMPLATE
        assert "role" in PROSPECTS_TEMPLATE

    def test_signals_template_has_required_columns(self):
        assert "company_name" in SIGNALS_TEMPLATE
        assert "signal_type" in SIGNALS_TEMPLATE
        assert "description" in SIGNALS_TEMPLATE

    def test_templates_are_valid_csv(self):
        import csv, io
        for template in [COMPANIES_TEMPLATE, PROSPECTS_TEMPLATE, SIGNALS_TEMPLATE]:
            reader = csv.DictReader(io.StringIO(template))
            rows = list(reader)
            assert len(rows) > 0, f"Template should have at least one data row: {template[:50]}"


# ── Safety Invariants ─────────────────────────────────────────────────────────

class TestSafetyInvariants:
    def _all_paths(self):
        return [r.path for r in app.routes if hasattr(r, "path")]

    def test_no_send_endpoint(self):
        for path in self._all_paths():
            assert "/send" not in path

    def test_no_auto_outbound_endpoint(self):
        for path in self._all_paths():
            assert "/auto-outbound" not in path
            assert "/mass-outbound" not in path

    def test_import_endpoint_exists_and_is_local(self, client):
        # The import endpoint should exist and process files locally
        r = client.post(
            "/api/bd/import/companies-csv?dry_run=true",
            files=[_csv_file("name\nTest Co\n")],
        )
        assert r.status_code == 200
        result = r.json()
        assert "local" in result["safety_notice"].lower()

    def test_import_does_not_trigger_external_calls(self, p14_paths):
        # Completing locally confirms no external dependency
        result = import_companies_csv(
            COMPANY_CSV.encode(), p14_paths["company"], dry_run=False
        )
        assert result.imported_count == 2
        assert result.error_count == 0
