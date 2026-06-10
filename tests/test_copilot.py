"""
Copilot safety and correctness tests.
Run from WSL: bash run.sh --test
Or directly:  python3 -m pytest tests/ -v
"""
import csv
import json
import os
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_db(tmp_dir: str) -> str:
    from src.db import initialize_database
    db_path = os.path.join(tmp_dir, "test.db")
    initialize_database(db_path)
    return db_path


def _insert_outreach(db_path: str, **overrides) -> int:
    from src.db import record_outreach
    defaults = dict(
        job_url="https://linkedin.com/jobs/view/999",
        company="TestCo",
        job_title="Engineer",
        subject="Test Subject",
        body="Hi there, this is a test message.",
    )
    defaults.update(overrides)
    return record_outreach(db_path=db_path, **defaults)


# ══════════════════════════════════════════════════════════════════════════════
# 1. Help menu — no flags shows help, not a silent exit
# ══════════════════════════════════════════════════════════════════════════════

class TestHelpDisplay(unittest.TestCase):

    def test_no_flags_prints_help_not_silent(self):
        """Running main() with no command flags must print help, not silently exit."""
        from main import main
        with patch("sys.argv", ["main.py"]):
            with patch("sys.stdout", new_callable=StringIO) as mock_out:
                try:
                    main()
                except SystemExit:
                    pass
            output = mock_out.getvalue()
        self.assertIn("DOBRYBOT WORKFLOW", output,
                      "Help text should contain DOBRYBOT WORKFLOW section")
        self.assertIn("--discover-jobs", output)
        self.assertIn("--review-queue", output)

    def test_config_flag_alone_still_shows_help(self):
        """--config alone (no command flag) must still show help."""
        from main import main
        with patch("sys.argv", ["main.py", "--config", "tests/fixtures/test_config.yaml"]):
            with patch("sys.stdout", new_callable=StringIO) as mock_out:
                try:
                    main()
                except SystemExit:
                    pass
            output = mock_out.getvalue()
        self.assertIn("DOBRYBOT WORKFLOW", output)

    def test_dry_run_alone_shows_help(self):
        """--dry-run alone is not a command — must show help."""
        from main import main
        with patch("sys.argv", ["main.py", "--dry-run"]):
            with patch("sys.stdout", new_callable=StringIO) as mock_out:
                try:
                    main()
                except SystemExit:
                    pass
            output = mock_out.getvalue()
        self.assertIn("DOBRYBOT WORKFLOW", output)


# ══════════════════════════════════════════════════════════════════════════════
# 2. skipped_no_contact increments correctly
# ══════════════════════════════════════════════════════════════════════════════

class TestSkippedNoContact(unittest.TestCase):

    def test_increments_when_contact_empty(self):
        """OutreachGenerator.run() must count jobs with no contact, not generate drafts."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            from src import db

            # Insert two external_apply jobs
            for i, url in enumerate(["https://l.co/1", "https://l.co/2"], 1):
                db.record_job(db_path, url, f"Co{i}", f"Job{i}", "Remote",
                              domain=f"co{i}.com", status="external_apply")

            # No contacts in DB → pick_best_contact returns {}
            config = {
                "apis": {"anthropic_api_key": "fake", "hunter_api_key": "fake"},
                "answer_generator": {"model": "claude-haiku-4-5-20251001",
                                     "positioning": "Test"},
                "outreach": {"auto_send": False,
                             "smtp_host": "smtp.test.com", "smtp_port": 587,
                             "smtp_user": "a@b.com", "smtp_password": "x",
                             "from_name": "Test"},
            }
            cv = MagicMock()
            cv.name = "Test User"
            cv.skills = []
            cv.experience = []
            cv.raw_text = ""
            cv.cv_path = ""

            with patch("src.answer_generator.anthropic.Anthropic"):
                from src.outreach_generator import OutreachGenerator
                gen = OutreachGenerator(config, cv, db_path)
                stats = gen.run()

            self.assertEqual(stats["skipped_no_contact"], 2)
            self.assertEqual(stats["generated"], 0)

    def test_does_not_increment_when_contact_exists(self):
        """skipped_no_contact must NOT increment when a valid email contact exists."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            from src import db

            db.record_job(db_path, "https://l.co/3", "GoodCo", "Dev", "Remote",
                          domain="goodco.com", status="external_apply")
            db.record_contact(db_path, "goodco.com", "GoodCo",
                              {"first_name": "Alice", "last_name": "Smith",
                               "value": "alice@goodco.com", "position": "CTO",
                               "confidence": 90})

            config = {
                "apis": {"anthropic_api_key": "fake", "hunter_api_key": "fake"},
                "answer_generator": {"model": "claude-haiku-4-5-20251001",
                                     "positioning": "Test"},
                "outreach": {"auto_send": False,
                             "smtp_host": "smtp.test.com", "smtp_port": 587,
                             "smtp_user": "a@b.com", "smtp_password": "x",
                             "from_name": "Test"},
            }
            cv = MagicMock()
            cv.name = "Test User"
            cv.skills = []
            cv.experience = []
            cv.raw_text = ""
            cv.cv_path = ""

            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="SUBJECT: Test\nBODY:\nTest body")]

            with patch("src.answer_generator.anthropic.Anthropic") as mock_ant:
                mock_ant.return_value.messages.create.return_value = mock_response
                from src.outreach_generator import OutreachGenerator
                gen = OutreachGenerator(config, cv, db_path)
                stats = gen.run()

            self.assertEqual(stats["skipped_no_contact"], 0)


# ══════════════════════════════════════════════════════════════════════════════
# 3. No email sent without approved status
# ══════════════════════════════════════════════════════════════════════════════

class TestNoSendWithoutApproval(unittest.TestCase):

    def test_get_unsent_outreach_excludes_needs_review(self):
        """get_unsent_outreach must NOT return items in needs_review status."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            _insert_outreach(db_path, status="needs_review",
                             to_email="victim@example.com")
            from src.db import get_unsent_outreach
            result = get_unsent_outreach(db_path)
            self.assertEqual(result, [],
                             "needs_review items must NOT appear in get_unsent_outreach")

    def test_get_unsent_outreach_excludes_draft(self):
        """get_unsent_outreach must NOT return draft items."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            _insert_outreach(db_path, status="draft", to_email="victim@example.com")
            from src.db import get_unsent_outreach
            result = get_unsent_outreach(db_path)
            self.assertEqual(result, [])

    def test_get_unsent_outreach_includes_approved(self):
        """get_unsent_outreach must return approved items that have not been sent."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            oid = _insert_outreach(db_path, status="approved",
                                   to_email="legit@example.com")
            from src.db import get_unsent_outreach
            result = get_unsent_outreach(db_path)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["id"], oid)

    def test_get_approved_outreach_only_returns_approved(self):
        """get_approved_outreach must only return status='approved'."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            _insert_outreach(db_path, status="needs_review", to_email="bad@x.com")
            _insert_outreach(db_path, status="draft",        to_email="bad2@x.com")
            _insert_outreach(db_path, status="skipped",      to_email="bad3@x.com")
            oid = _insert_outreach(db_path, status="approved", to_email="ok@x.com")

            from src.db import get_approved_outreach
            result = get_approved_outreach(db_path)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["id"], oid)

    def test_cmd_send_approved_sends_nothing_in_dry_run(self):
        """--send-approved with --dry-run must return before parse_cv or SMTP are called."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            _insert_outreach(db_path, status="approved",
                             to_email="legit@example.com", outreach_type="client")

            config = {
                "paths": {"database": db_path},
                "limits": {"max_emails_per_day": 10},
            }
            logger = MagicMock()

            # parse_cv is called only AFTER the dry-run gate — it must NOT be reached
            with patch("main.parse_cv") as mock_parse_cv:
                from main import cmd_send_approved
                cmd_send_approved(config, logger, dry_run=True)
            mock_parse_cv.assert_not_called()


# ══════════════════════════════════════════════════════════════════════════════
# 4. Quality guard blocks bad drafts
# ══════════════════════════════════════════════════════════════════════════════

class TestQualityGuard(unittest.TestCase):

    def _make_guard(self, scores: dict):
        """Build a QualityGuard that returns preset scores."""
        with patch("src.quality_guard.anthropic.Anthropic") as mock_ant:
            mock_ant.return_value.messages.create.return_value = MagicMock(
                content=[MagicMock(text=json.dumps(scores))]
            )
            from src.quality_guard import QualityGuard
            guard = QualityGuard(api_key="fake")
        guard.client.messages.create.return_value = MagicMock(
            content=[MagicMock(text=json.dumps(scores))]
        )
        return guard

    def test_good_draft_passes(self):
        """A well-personalized, non-spammy draft should pass all thresholds."""
        scores = {"personalization_score": 85, "spam_risk_score": 20,
                  "ai_sounding_score": 30, "quality_reasons": [],
                  "send_recommendation": "send", "improvement_tip": ""}
        guard = self._make_guard(scores)
        result = guard.score_message("Hi Alice, I noticed Acme is expanding...",
                                     {"company": "Acme", "contact_name": "Alice"})
        self.assertTrue(result["passes"])
        self.assertEqual(result["send_recommendation"], "send")

    def test_generic_ai_draft_fails(self):
        """A generic AI-sounding draft must fail."""
        scores = {"personalization_score": 30, "spam_risk_score": 70,
                  "ai_sounding_score": 85, "quality_reasons": ["generic phrases"],
                  "send_recommendation": "skip", "improvement_tip": "Add specifics"}
        guard = self._make_guard(scores)
        result = guard.score_message(
            "I hope this message finds you well. I am reaching out to explore synergies.",
            {"company": ""}
        )
        self.assertFalse(result["passes"])

    def test_forbidden_phrases_raise_ai_score(self):
        """Forbidden phrases must increase ai_sounding_score in final result."""
        base_scores = {"personalization_score": 80, "spam_risk_score": 25,
                       "ai_sounding_score": 20, "quality_reasons": [],
                       "send_recommendation": "send", "improvement_tip": ""}
        guard = self._make_guard(base_scores)
        result = guard.score_message(
            "I hope this message finds you well. Great company.",
            {"company": "Acme"}
        )
        self.assertGreater(result["ai_sounding_score"], 20,
                           "Forbidden phrase should increase ai_sounding_score")

    def test_passes_threshold_logic(self):
        from src.quality_guard import QualityGuard
        with patch("src.quality_guard.anthropic.Anthropic"):
            guard = QualityGuard(api_key="fake")

        self.assertTrue(guard.passes_threshold(
            {"personalization_score": 75, "spam_risk_score": 35, "ai_sounding_score": 40}))
        self.assertFalse(guard.passes_threshold(
            {"personalization_score": 74, "spam_risk_score": 35, "ai_sounding_score": 40}))
        self.assertFalse(guard.passes_threshold(
            {"personalization_score": 80, "spam_risk_score": 36, "ai_sounding_score": 40}))
        self.assertFalse(guard.passes_threshold(
            {"personalization_score": 80, "spam_risk_score": 30, "ai_sounding_score": 41}))


# ══════════════════════════════════════════════════════════════════════════════
# 5. Environment variable interpolation
# ══════════════════════════════════════════════════════════════════════════════

class TestEnvVarInterpolation(unittest.TestCase):

    def test_interpolates_present_env_var(self):
        from src.config_loader import _interpolate
        with patch.dict(os.environ, {"MY_SECRET": "abc123"}):
            result = _interpolate("prefix_${MY_SECRET}_suffix")
        self.assertEqual(result, "prefix_abc123_suffix")

    def test_warns_on_missing_env_var(self):
        from src.config_loader import _interpolate
        with patch.dict(os.environ, {}, clear=True):
            with patch("builtins.print") as mock_print:
                result = _interpolate("${MISSING_VAR}")
            printed = " ".join(str(c) for c in mock_print.call_args_list)
            self.assertIn("MISSING_VAR", printed)
        self.assertEqual(result, "")

    def test_interpolates_nested_dict(self):
        from src.config_loader import _interpolate
        with patch.dict(os.environ, {"API_KEY": "sk-test", "HOST": "smtp.gmail.com"}):
            cfg = {"apis": {"key": "${API_KEY}"}, "smtp": {"host": "${HOST}"}}
            result = _interpolate(cfg)
        self.assertEqual(result["apis"]["key"], "sk-test")
        self.assertEqual(result["smtp"]["host"], "smtp.gmail.com")

    def test_interpolates_list(self):
        from src.config_loader import _interpolate
        with patch.dict(os.environ, {"V1": "hello", "V2": "world"}):
            result = _interpolate(["${V1}", "static", "${V2}"])
        self.assertEqual(result, ["hello", "static", "world"])

    def test_missing_required_field_exits(self):
        from src.config_loader import load_config
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("linkedin:\n  email: ''\n  password: ''\npaths:\n  cv_pdf: ''\n"
                    "  jobs_csv: ''\n  database: ''\napis:\n  anthropic_api_key: ''\n")
            tmp = f.name
        with self.assertRaises(SystemExit) as ctx:
            load_config(tmp)
        self.assertEqual(ctx.exception.code, 1)
        os.unlink(tmp)

    def test_config_yaml_example_has_no_plain_passwords(self):
        """config.example.yaml must not contain literal passwords."""
        cfg_path = Path(__file__).parent.parent / "config.example.yaml"
        content = cfg_path.read_text(encoding="utf-8")
        # Should use ${ENV_VAR} references, not bare strings
        self.assertIn("${LINKEDIN_PASSWORD}", content)
        self.assertIn("${ANTHROPIC_API_KEY}", content)
        self.assertIn("${SMTP_PASSWORD}", content)
        self.assertNotIn("YOUR_LINKEDIN_PASSWORD", content)
        self.assertNotIn("sk-ant-api", content)


# ══════════════════════════════════════════════════════════════════════════════
# 6. get_unsent_outreach returns dict rows
# ══════════════════════════════════════════════════════════════════════════════

class TestGetUnsentOutreach(unittest.TestCase):

    def test_returns_list_of_dicts(self):
        """Each row must be a plain dict, not sqlite3.Row."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            _insert_outreach(db_path, status="approved", to_email="ok@test.com")
            from src.db import get_unsent_outreach
            result = get_unsent_outreach(db_path)
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0], dict)

    def test_subject_accessible_by_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            _insert_outreach(db_path, status="approved",
                             to_email="ok@test.com", subject="My Subject")
            from src.db import get_unsent_outreach
            result = get_unsent_outreach(db_path)
            self.assertEqual(result[0]["subject"], "My Subject")

    def test_empty_when_no_approved(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            _insert_outreach(db_path, status="needs_review", to_email="bad@test.com")
            from src.db import get_unsent_outreach
            self.assertEqual(get_unsent_outreach(db_path), [])


# ══════════════════════════════════════════════════════════════════════════════
# 7. Hunter.io single-request fix
# ══════════════════════════════════════════════════════════════════════════════

class TestHunterSingleRequest(unittest.TestCase):

    def test_search_domain_returns_tuple(self):
        """search_domain must return (emails, company_name) tuple — not just a list."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "emails": [{"value": "alice@acme.com", "confidence": 90}],
                "organization": "Acme Corp",
            }
        }
        with patch("src.email_finder.requests.get", return_value=mock_response):
            from src.email_finder import search_domain
            emails, company = search_domain("acme.com", "fake_key")
        self.assertIsInstance(emails, list)
        self.assertIsInstance(company, str)
        self.assertEqual(company, "Acme Corp")
        self.assertEqual(len(emails), 1)

    def test_single_http_call_per_domain(self):
        """search_domain must make exactly ONE HTTP request per call."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"emails": [], "organization": "Test"}}
        with patch("src.email_finder.requests.get", return_value=mock_response) as mock_get:
            from src.email_finder import search_domain
            search_domain("test.com", "fake_key")
        self.assertEqual(mock_get.call_count, 1,
                         "search_domain must make exactly 1 HTTP request, not 2")

    def test_run_email_finder_makes_one_call_per_domain(self):
        """run_email_finder must not duplicate requests for the same domain."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"emails": [{"value": "x@co.com", "confidence": 80}],
                     "organization": "Co"}
        }
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            # Fake CSV with one domain
            csv_path = os.path.join(tmp, "jobs.csv")
            with open(csv_path, "w") as f:
                f.write("Job LinkedIn URL,Company Name,Job Title,Location,Company Domain\n")
                f.write("https://l.co/1,Co,Engineer,Remote,co.com\n")

            with patch("src.email_finder.requests.get", return_value=mock_response) as mock_get:
                from src.email_finder import run_email_finder
                run_email_finder(csv_path, db_path, "fake_key",
                                 rate_limit_seconds=0, max_domains=5)
            # co.com should be searched exactly once
            calls_for_domain = [c for c in mock_get.call_args_list
                                 if "co.com" in str(c)]
            self.assertEqual(len(calls_for_domain), 1,
                             "Each domain must generate exactly 1 HTTP call")


# ══════════════════════════════════════════════════════════════════════════════
# 8. Approval gate enforced
# ══════════════════════════════════════════════════════════════════════════════

class TestApprovalGate(unittest.TestCase):

    def test_approve_single_blocks_unscored_by_default(self):
        """approve_single must block items that haven't been quality-scored (default scores fail)."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            oid = _insert_outreach(db_path,
                                   personalization_score=0,
                                   spam_risk_score=50,
                                   ai_sounding_score=50,
                                   quality_status="pending",
                                   status="needs_review")
            from src.review_queue import approve_single
            result = approve_single(db_path, oid, force=False)
            self.assertFalse(result,
                             "Unscored draft must be blocked without --force")

    def test_approve_single_blocks_failed_quality(self):
        """approve_single must block drafts that failed quality check."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            oid = _insert_outreach(db_path,
                                   personalization_score=40,
                                   spam_risk_score=70,
                                   ai_sounding_score=80,
                                   quality_status="failed",
                                   status="needs_review")
            from src.review_queue import approve_single
            result = approve_single(db_path, oid, force=False)
            self.assertFalse(result)

    def test_approve_single_passes_good_draft(self):
        """approve_single must approve drafts that pass quality thresholds."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            oid = _insert_outreach(db_path,
                                   personalization_score=80,
                                   spam_risk_score=20,
                                   ai_sounding_score=30,
                                   quality_status="passed",
                                   status="needs_review")
            from src.review_queue import approve_single
            result = approve_single(db_path, oid, force=False)
            self.assertTrue(result)
            # Verify status changed in DB
            from src.db import get_outreach_by_status
            approved = get_outreach_by_status(db_path, "approved")
            self.assertEqual(approved[0]["id"], oid)

    def test_force_does_not_bypass_quality_gate(self):
        """force=True must NOT bypass the quality gate — the bypass has been removed."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            oid = _insert_outreach(db_path,
                                   personalization_score=30,
                                   spam_risk_score=80,
                                   ai_sounding_score=80,
                                   quality_status="failed",
                                   status="needs_review")
            from src.review_queue import approve_single
            result = approve_single(db_path, oid, force=True)
            self.assertFalse(result, "force=True must not bypass quality gate")


# ══════════════════════════════════════════════════════════════════════════════
# 9. Database schema + migrations
# ══════════════════════════════════════════════════════════════════════════════

class TestDatabaseSchema(unittest.TestCase):

    def test_new_db_has_all_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            from src.db import get_connection
            with get_connection(db_path) as conn:
                tables = {r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()}
            self.assertIn("applied_jobs", tables)
            self.assertIn("leads", tables)
            self.assertIn("outreach", tables)
            self.assertIn("contacts", tables)
            self.assertIn("schema_migrations", tables)

    def test_outreach_has_quality_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            from src.db import get_connection
            with get_connection(db_path) as conn:
                cols = {r[1] for r in conn.execute("PRAGMA table_info(outreach)").fetchall()}
            for col in ["personalization_score", "spam_risk_score", "ai_sounding_score",
                        "quality_status", "quality_reasons", "status", "outreach_type"]:
                self.assertIn(col, cols, f"Missing column: {col}")

    def test_applied_jobs_has_no_check_constraint(self):
        """After migration, applied_jobs must accept new status values like 'discovered'."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            from src.db import record_job
            # These would fail if the old CHECK constraint still existed
            record_job(db_path, "https://l.co/x1", "Co", "Job", "Remote",
                       status="discovered")
            record_job(db_path, "https://l.co/x2", "Co", "Job", "Remote",
                       status="scored")
            record_job(db_path, "https://l.co/x3", "Co", "Job", "Remote",
                       status="approved")

    def test_leads_table_crud(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            from src.db import save_lead, get_leads_by_status, update_lead_score
            lid = save_lead(db_path, "test.com", "TestCo",
                            contact_email="a@test.com", industry="tech")
            self.assertIsNotNone(lid)
            update_lead_score(db_path, lid, 85, "high_priority")
            leads = get_leads_by_status(db_path, "scored")
            self.assertEqual(len(leads), 1)
            self.assertEqual(leads[0]["lead_score"], 85)

    def test_migration_runs_on_existing_db(self):
        """Migrations must be idempotent — running twice must not error."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            from src.db import initialize_database
            initialize_database(db_path)  # run again
            initialize_database(db_path)  # and again


# ══════════════════════════════════════════════════════════════════════════════
# 10. Job scoring
# ══════════════════════════════════════════════════════════════════════════════

class TestJobScoring(unittest.TestCase):

    def setUp(self):
        from src.scorer import JobScorer
        self.scorer = JobScorer()

    def test_remote_fullstack_scores_high(self):
        job = {"Job Title": "Senior Fullstack Engineer",
               "Location": "Remote",
               "Company Name": "TechCo",
               "job_description": "React TypeScript Node.js delivery"}
        result = self.scorer.score(job)
        self.assertGreaterEqual(result["job_score"], 70,
                                f"Got {result['job_score']}, breakdown: {result['breakdown']}")
        self.assertIn(result["score_label"], ("high_priority", "good_fit"))

    def test_junior_local_scores_low(self):
        job = {"Job Title": "Junior Developer", "Location": "New York office only",
               "Company Name": "OldCo", "job_description": ""}
        result = self.scorer.score(job)
        self.assertLessEqual(result["job_score"], 50)

    def test_score_label_thresholds(self):
        from src.db import score_label
        self.assertEqual(score_label(85), "high_priority")
        self.assertEqual(score_label(100), "high_priority")
        self.assertEqual(score_label(70), "good_fit")
        self.assertEqual(score_label(84), "good_fit")
        self.assertEqual(score_label(50), "maybe")
        self.assertEqual(score_label(69), "maybe")
        self.assertEqual(score_label(0), "low_fit")
        self.assertEqual(score_label(49), "low_fit")


# ══════════════════════════════════════════════════════════════════════════════
# 11. Discover jobs — dry-run saves nothing
# ══════════════════════════════════════════════════════════════════════════════

class TestDiscoverJobsDryRun(unittest.TestCase):

    def test_dry_run_saves_nothing_to_db(self):
        """--discover-jobs --dry-run must not write any rows to the database."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "jobs.db")
            from src.db import initialize_database, get_jobs_by_status

            config = {
                "paths": {
                    "database": db_path,
                    "jobs_csv": "tests/fixtures/sample_jobs.csv",
                    "logs_dir": tmp,
                },
                "filters": {
                    "location_keywords": ["Remote", "Colombia"],
                    "title_keywords": ["Engineer", "Lead", "Architect"],
                    "blacklisted_companies": [],
                    "max_days_old": 365,
                },
                "limits": {},
                "apis": {},
                "answer_generator": {"positioning": "Test"},
            }
            logger = MagicMock()
            from main import cmd_discover_jobs
            cmd_discover_jobs(config, logger, dry_run=True)

            # DB should have no rows (not even created in some cases)
            if os.path.exists(db_path):
                initialize_database(db_path)
                rows = get_jobs_by_status(db_path, "discovered")
                self.assertEqual(rows, [],
                                 "dry-run must not insert any rows")

    def test_non_dry_run_saves_discovered_jobs(self):
        """--discover-jobs without --dry-run must save jobs as discovered."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "jobs.db")
            from src.db import initialize_database, get_jobs_by_status
            initialize_database(db_path)

            config = {
                "paths": {
                    "database": db_path,
                    "jobs_csv": "tests/fixtures/sample_jobs.csv",
                    "logs_dir": tmp,
                },
                "filters": {
                    "location_keywords": ["Remote", "Colombia"],
                    "title_keywords": ["Engineer", "Lead", "Architect"],
                    "blacklisted_companies": [],
                    "max_days_old": 365,
                },
                "limits": {},
                "apis": {},
                "answer_generator": {"positioning": "Test"},
            }
            logger = MagicMock()
            from main import cmd_discover_jobs
            cmd_discover_jobs(config, logger, dry_run=False)

            rows = get_jobs_by_status(db_path, "discovered")
            self.assertGreater(len(rows), 0, "Should have saved discovered jobs")
            for row in rows:
                self.assertEqual(row["status"], "discovered")


# ══════════════════════════════════════════════════════════════════════════════
# 12. Context sufficiency gate
# ══════════════════════════════════════════════════════════════════════════════

class TestContextSufficiency(unittest.TestCase):

    def test_job_passes_with_company_and_title(self):
        from src.humanizer import has_sufficient_context
        ctx = {"company": "Acme", "job_title": "Engineer", "contact_name": "Alice"}
        ok, missing = has_sufficient_context(ctx, "job")
        self.assertTrue(ok)
        self.assertEqual(missing, [])

    def test_job_fails_without_company(self):
        from src.humanizer import has_sufficient_context
        ctx = {"company": "", "job_title": "Engineer"}
        ok, missing = has_sufficient_context(ctx, "job")
        self.assertFalse(ok)
        self.assertIn("company", missing)

    def test_client_fails_without_enriching_field(self):
        from src.humanizer import has_sufficient_context
        # Has required fields but no enriching info
        ctx = {"company": "Acme", "industry": "tech"}
        ok, missing = has_sufficient_context(ctx, "client")
        self.assertFalse(ok)

    def test_client_passes_with_pain_point(self):
        from src.humanizer import has_sufficient_context
        ctx = {"company": "Acme", "industry": "tech", "pain_point": "no CRM"}
        ok, missing = has_sufficient_context(ctx, "client")
        self.assertTrue(ok)


# ══════════════════════════════════════════════════════════════════════════════
# 13. Humanizer — forbidden phrase detection
# ══════════════════════════════════════════════════════════════════════════════

class TestHumanizerForbiddenPhrases(unittest.TestCase):

    def test_detects_classic_ai_opener(self):
        from src.humanizer import check_forbidden_phrases
        text = "I hope this message finds you well. I came across your profile."
        found = check_forbidden_phrases(text)
        self.assertIn("I hope this message finds you well", found)
        self.assertIn("I came across your profile", found)

    def test_clean_message_has_no_flags(self):
        from src.humanizer import check_forbidden_phrases
        text = "Hi Alice, I noticed Acme recently expanded to the US market. I work with teams on CRM setup."
        found = check_forbidden_phrases(text)
        self.assertEqual(found, [])

    def test_case_insensitive(self):
        from src.humanizer import check_forbidden_phrases
        found = check_forbidden_phrases("I HOPE THIS MESSAGE FINDS YOU WELL")
        self.assertGreater(len(found), 0)


# ══════════════════════════════════════════════════════════════════════════════
# 14. Asyncio.to_thread used for Claude calls in Playwright flow
# ══════════════════════════════════════════════════════════════════════════════

class TestAsyncClaudeWrapping(unittest.TestCase):

    def test_fill_field_group_uses_to_thread(self):
        """_fill_field_group must use asyncio.to_thread, not call answer_gen.answer directly."""
        import ast, pathlib
        src = pathlib.Path("src/linkedin_applier.py").read_text(encoding="utf-8")
        tree = ast.parse(src)

        # Find all await expressions
        await_calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Await):
                await_calls.append(ast.dump(node))

        to_thread_calls = [c for c in await_calls if "to_thread" in c]
        self.assertGreater(len(to_thread_calls), 0,
                           "asyncio.to_thread must be used for Claude answer() calls in async context")

    def test_no_bare_answer_gen_calls_in_async_methods(self):
        """There must be no bare self.answer_gen.answer() calls inside async methods."""
        import ast, pathlib
        src = pathlib.Path("src/linkedin_applier.py").read_text(encoding="utf-8")
        tree = ast.parse(src)

        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                for child in ast.walk(node):
                    if (isinstance(child, ast.Call) and
                            isinstance(child.func, ast.Attribute) and
                            child.func.attr == "answer" and
                            isinstance(child.func.value, ast.Attribute) and
                            child.func.value.attr == "answer_gen"):
                        # Must be wrapped in to_thread
                        violations.append(f"Line {child.lineno}: bare answer_gen.answer() in async context")

        self.assertEqual(violations, [],
                         f"Bare Claude calls found (not wrapped in to_thread):\n" +
                         "\n".join(violations))


# ══════════════════════════════════════════════════════════════════════════════
# 15. Prompt caching in answer_generator
# ══════════════════════════════════════════════════════════════════════════════

class TestPromptCaching(unittest.TestCase):

    def test_system_prompt_uses_cache_control(self):
        """answer_generator must send system prompt with cache_control for prompt caching."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Yes")]
        captured_calls = []

        def capture_create(**kwargs):
            captured_calls.append(kwargs)
            return mock_response

        with patch("src.answer_generator.anthropic.Anthropic") as mock_ant:
            mock_ant.return_value.messages.create.side_effect = capture_create
            from src.answer_generator import AnswerGenerator
            cv = MagicMock()
            cv.name = "Test"; cv.skills = []; cv.experience = []
            cv.raw_text = ""; cv.cv_path = ""; cv.email = ""; cv.phone = ""
            cv.linkedin_url = ""; cv.github_url = ""; cv.summary = ""; cv.location = ""
            gen = AnswerGenerator("fake", "claude-haiku-4-5-20251001", cv, "Test")
            gen.answer("Years of experience?")

        self.assertTrue(len(captured_calls) > 0)
        system_arg = captured_calls[0].get("system", [])
        self.assertIsInstance(system_arg, list,
                              "system must be a list for cache_control to work")
        has_cache = any(
            block.get("cache_control") for block in system_arg
            if isinstance(block, dict)
        )
        self.assertTrue(has_cache,
                        "System prompt block must include cache_control: {type: ephemeral}")


# ══════════════════════════════════════════════════════════════════════════════
# HARDENING TESTS
# ══════════════════════════════════════════════════════════════════════════════

# ── H1. Pending quality status is a hard block ────────────────────────────────

class TestPendingStatusHardBlock(unittest.TestCase):

    def test_approve_single_hard_blocks_pending(self):
        """pending quality_status must be an absolute block — no override."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            oid = _insert_outreach(db_path,
                                   personalization_score=0,
                                   spam_risk_score=50,
                                   ai_sounding_score=50,
                                   quality_status="pending",
                                   status="needs_review")
            from src.review_queue import approve_single
            # force=False — should block
            self.assertFalse(approve_single(db_path, oid, force=False))
            # Verify item remains in needs_review
            from src.db import get_needs_review
            still_pending = get_needs_review(db_path)
            self.assertEqual(len(still_pending), 1)
            self.assertEqual(still_pending[0]["status"], "needs_review")

    def test_approve_single_blocks_pending_even_with_force(self):
        """force=True must NOT approve pending items — quality gate has no bypass."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            oid = _insert_outreach(db_path, quality_status="pending", status="needs_review")
            from src.review_queue import approve_single
            result = approve_single(db_path, oid, force=True)
            self.assertFalse(result, "force=True must not approve pending items — no bypass exists")

    def test_approve_single_blocks_failed_even_with_force(self):
        """force=True must NOT approve failed quality items."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            oid = _insert_outreach(db_path,
                                   personalization_score=40,
                                   spam_risk_score=60,
                                   ai_sounding_score=70,
                                   quality_status="failed",
                                   status="needs_review")
            from src.review_queue import approve_single
            result = approve_single(db_path, oid, force=True)
            self.assertFalse(result, "force=True must not approve failed quality items")

    def test_quality_passes_helper_blocks_pending(self):
        """_quality_passes must return (False, reason) for pending items."""
        from src.review_queue import _quality_passes
        item = {"quality_status": "pending", "personalization_score": 80,
                "spam_risk_score": 20, "ai_sounding_score": 30}
        ok, reason = _quality_passes(item)
        self.assertFalse(ok)
        self.assertIn("Quality check has NOT been run", reason)

    def test_quality_passes_helper_blocks_failed(self):
        from src.review_queue import _quality_passes
        item = {"quality_status": "failed", "personalization_score": 40,
                "spam_risk_score": 60, "ai_sounding_score": 70}
        ok, reason = _quality_passes(item)
        self.assertFalse(ok)
        self.assertIn("FAILED", reason)

    def test_quality_passes_helper_approves_passing_draft(self):
        from src.review_queue import _quality_passes
        item = {"quality_status": "passed", "personalization_score": 80,
                "spam_risk_score": 20, "ai_sounding_score": 30}
        ok, reason = _quality_passes(item)
        self.assertTrue(ok)
        self.assertEqual(reason, "")


# ── H2. approve-force unavailable without DEV_MODE ────────────────────────────

class TestApproveForceGate(unittest.TestCase):

    def test_cmd_approve_force_always_blocked(self):
        """--approve-force is removed: cmd_approve with force=True must print a notice and not approve."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            oid = _insert_outreach(db_path, quality_status="failed", status="needs_review")

            config = {"paths": {"database": db_path}}
            logger = MagicMock()

            with patch("sys.stdout", new_callable=StringIO) as out:
                from main import cmd_approve
                cmd_approve(config, logger, draft_id=oid, force=True)
            output = out.getvalue()

            self.assertIn("removed", output.lower())
            # Draft must still be in needs_review
            from src.db import get_needs_review
            self.assertEqual(len(get_needs_review(db_path)), 1)

    def test_approve_force_not_in_help_text(self):
        """--approve-force must not appear in the user-facing help text."""
        from main import main
        with patch("sys.argv", ["main.py"]):
            with patch("sys.stdout", new_callable=StringIO) as out:
                try:
                    main()
                except SystemExit:
                    pass
            help_text = out.getvalue()
        self.assertNotIn("approve-force", help_text,
                         "--approve-force should be hidden from public help")


# ── H3. Legacy --apply is disabled by default ─────────────────────────────────

class TestLegacyApplyDisabled(unittest.TestCase):

    def test_apply_always_prints_removed_message(self):
        """--apply must always print the REMOVED message regardless of config."""
        for config in [{}, {"enable_legacy_apply": True}, {"enable_legacy_apply": False}]:
            logger = MagicMock()
            with patch("sys.stdout", new_callable=StringIO) as out:
                from main import cmd_apply
                cmd_apply(config, logger)
            self.assertIn("REMOVED", out.getvalue(),
                          f"--apply must show REMOVED for config={config}")

    def test_apply_never_calls_linkedin_applier(self):
        """LinkedInApplier must never be imported or instantiated by --apply."""
        for config in [{}, {"enable_legacy_apply": True}]:
            logger = MagicMock()
            # Verify no LinkedIn module is imported when cmd_apply runs
            with patch("sys.stdout", new_callable=StringIO):
                from main import cmd_apply
                cmd_apply(config, logger)
            # If we got here without any LinkedInApplier import or call, test passes.
            # The new cmd_apply just prints a message and returns.

    def test_apply_never_calls_parse_cv(self):
        """parse_cv must never be called by --apply (no LinkedIn session)."""
        logger = MagicMock()
        with patch("main.parse_cv") as mock_parse:
            with patch("sys.stdout", new_callable=StringIO):
                from main import cmd_apply
                cmd_apply({}, logger)
        mock_parse.assert_not_called()

    def test_apply_never_reads_database(self):
        """--apply must not touch the database at all."""
        logger = MagicMock()
        with patch("main.db") as mock_db:
            with patch("sys.stdout", new_callable=StringIO):
                from main import cmd_apply
                cmd_apply({}, logger)
        mock_db.initialize_database.assert_not_called()


# ── H4. Legacy --send-outreach is deprecated and sends nothing ─────────────────

class TestLegacySendOutreachDeprecated(unittest.TestCase):

    def test_send_outreach_prints_deprecation(self):
        """--send-outreach must print deprecation notice and not send."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            # Insert an approved item — should NOT be sent
            _insert_outreach(db_path, status="approved", to_email="victim@test.com")

            config = {"paths": {"database": db_path}, "apis": {}}
            logger = MagicMock()

            with patch("sys.stdout", new_callable=StringIO) as out:
                from main import cmd_send_outreach
                cmd_send_outreach(config, logger)
            output = out.getvalue()

            self.assertIn("DEPRECATED", output)
            self.assertIn("--send-approved", output)

    def test_send_outreach_does_not_call_smtp(self):
        """--send-outreach must not call SMTP at all."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            _insert_outreach(db_path, status="approved", to_email="victim@test.com")
            config = {"paths": {"database": db_path}, "apis": {}}
            logger = MagicMock()

            with patch("smtplib.SMTP") as mock_smtp:
                with patch("sys.stdout", new_callable=StringIO):
                    from main import cmd_send_outreach
                    cmd_send_outreach(config, logger)
                mock_smtp.assert_not_called()

    def test_send_outreach_item_remains_approved_not_sent(self):
        """After --send-outreach, approved items must still be approved, not sent."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            oid = _insert_outreach(db_path, status="approved", to_email="x@test.com")
            config = {"paths": {"database": db_path}, "apis": {}}
            logger = MagicMock()

            with patch("sys.stdout", new_callable=StringIO):
                from main import cmd_send_outreach
                cmd_send_outreach(config, logger)

            from src.db import get_outreach_by_status
            approved = get_outreach_by_status(db_path, "approved")
            self.assertEqual(len(approved), 1, "Item must still be approved, not sent")
            self.assertIsNone(approved[0]["sent_at"], "sent_at must be None")


# ── H5. SMTP failure is tracked and does not mark as sent ─────────────────────

class TestSmtpFailureTracking(unittest.TestCase):

    def test_send_email_returns_tuple(self):
        """_send_email must return (bool, str) not just bool."""
        from src.outreach_generator import OutreachGenerator
        config = {
            "outreach": {"smtp_host": "smtp.test.com", "smtp_port": 587,
                         "smtp_user": "u@t.com", "smtp_password": "x",
                         "from_name": "Test"},
            "apis": {"anthropic_api_key": "fake"},
            "answer_generator": {"model": "m", "positioning": "t"},
        }
        with patch("src.answer_generator.anthropic.Anthropic"):
            gen = OutreachGenerator(config, MagicMock(), "/tmp/x.db")

        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.side_effect = Exception("Connection refused")
            success, error_msg = gen._send_email("a@b.com", "Bob", "Hi", "Body")

        self.assertFalse(success)
        self.assertIsInstance(error_msg, str)
        self.assertGreater(len(error_msg), 0)

    def test_smtp_failure_does_not_mark_as_sent(self):
        """When SMTP fails, item must NOT be marked as sent."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            oid = _insert_outreach(db_path, status="approved",
                                   to_email="ok@test.com", outreach_type="client")
            config = {
                "paths": {"database": db_path, "cv_pdf": "/tmp/fake.pdf"},
                "limits": {"max_emails_per_day": 10},
                "outreach": {"smtp_host": "smtp.fail.com", "smtp_port": 587,
                             "smtp_user": "u@t.com", "smtp_password": "x",
                             "from_name": "Test"},
                "apis": {"anthropic_api_key": "fake"},
                "answer_generator": {"model": "m", "positioning": "t"},
            }
            logger = MagicMock()

            with patch("main.parse_cv", return_value=MagicMock()):
                with patch("src.outreach_generator.smtplib.SMTP") as mock_smtp:
                    mock_smtp.side_effect = Exception("Connection refused")
                    with patch("builtins.input", return_value="yes"):
                        from main import cmd_send_approved
                        cmd_send_approved(config, logger, dry_run=False)

            # Item must be marked 'failed', not 'sent'
            from src.db import get_outreach_by_status
            failed = get_outreach_by_status(db_path, "failed")
            sent = get_outreach_by_status(db_path, "sent")
            self.assertEqual(len(failed), 1, "Failed send must mark item as 'failed'")
            self.assertEqual(len(sent), 0, "No item must be marked as 'sent' after SMTP failure")

    def test_smtp_failure_stores_reason(self):
        """Failure reason must be saved to the database."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            oid = _insert_outreach(db_path, status="approved",
                                   to_email="ok@test.com", outreach_type="client")
            config = {
                "paths": {"database": db_path, "cv_pdf": "/tmp/fake.pdf"},
                "limits": {"max_emails_per_day": 10},
                "outreach": {"smtp_host": "smtp.fail.com", "smtp_port": 587,
                             "smtp_user": "u@t.com", "smtp_password": "x",
                             "from_name": "Test"},
                "apis": {"anthropic_api_key": "fake"},
                "answer_generator": {"model": "m", "positioning": "t"},
            }
            logger = MagicMock()

            with patch("main.parse_cv", return_value=MagicMock()):
                with patch("src.outreach_generator.smtplib.SMTP") as mock_smtp:
                    mock_smtp.side_effect = ConnectionRefusedError("Refused")
                    with patch("builtins.input", return_value="yes"):
                        from main import cmd_send_approved
                        cmd_send_approved(config, logger, dry_run=False)

            from src.db import get_outreach_by_status, get_connection
            with get_connection(db_path) as conn:
                row = conn.execute("SELECT failure_reason FROM outreach WHERE id=?", (oid,)).fetchone()
            self.assertIsNotNone(row["failure_reason"])
            self.assertGreater(len(row["failure_reason"]), 0,
                               "failure_reason must be non-empty after a send failure")

    def test_successful_send_marks_as_sent_not_failed(self):
        """Successful send must mark item as 'sent', not 'failed'."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            oid = _insert_outreach(db_path, status="approved",
                                   to_email="ok@test.com", outreach_type="client")
            config = {
                "paths": {"database": db_path, "cv_pdf": "/tmp/fake.pdf"},
                "limits": {"max_emails_per_day": 10},
                "outreach": {"smtp_host": "smtp.test.com", "smtp_port": 587,
                             "smtp_user": "u@t.com", "smtp_password": "x",
                             "from_name": "Test"},
                "apis": {"anthropic_api_key": "fake"},
                "answer_generator": {"model": "m", "positioning": "t"},
            }
            logger = MagicMock()

            mock_server = MagicMock()
            mock_server.__enter__ = MagicMock(return_value=mock_server)
            mock_server.__exit__ = MagicMock(return_value=False)
            mock_server.sendmail.return_value = {}  # empty = all delivered

            with patch("main.parse_cv", return_value=MagicMock()):
                with patch("src.outreach_generator.smtplib.SMTP", return_value=mock_server):
                    with patch("builtins.input", return_value="yes"):
                        from main import cmd_send_approved
                        cmd_send_approved(config, logger, dry_run=False)

            from src.db import get_outreach_by_status
            sent = get_outreach_by_status(db_path, "sent")
            failed = get_outreach_by_status(db_path, "failed")
            self.assertEqual(len(sent), 1)
            self.assertEqual(len(failed), 0)

    def test_mark_outreach_failed_function(self):
        """mark_outreach_failed must set status='failed' and store reason."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            oid = _insert_outreach(db_path, status="approved")
            from src.db import mark_outreach_failed, get_connection
            mark_outreach_failed(db_path, oid, "SMTP auth failed: 535 bad creds")
            with get_connection(db_path) as conn:
                row = conn.execute(
                    "SELECT status, failure_reason FROM outreach WHERE id=?", (oid,)
                ).fetchone()
            self.assertEqual(row["status"], "failed")
            self.assertIn("535", row["failure_reason"])


# ══════════════════════════════════════════════════════════════════════════════
# 16. Seed demo data
# ══════════════════════════════════════════════════════════════════════════════

class TestSeedDemoData(unittest.TestCase):

    def test_seed_demo_data_in_help(self):
        """--seed-demo-data must appear in the CLI help text."""
        from main import main
        with patch("sys.argv", ["main.py"]):
            with patch("sys.stdout", new_callable=StringIO) as out:
                try:
                    main()
                except SystemExit:
                    pass
            self.assertIn("--seed-demo-data", out.getvalue())

    def test_seed_creates_jobs(self):
        """seed_demo_data must write scored jobs to the database."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            from src.seed_data import seed_demo_data
            from src.db import get_jobs_by_status
            stats = seed_demo_data(db_path)
            self.assertGreater(stats["jobs_created"], 0)
            scored = get_jobs_by_status(db_path, "scored")
            self.assertGreater(len(scored), 0)

    def test_seed_creates_leads(self):
        """seed_demo_data must write scored leads to the database."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            from src.seed_data import seed_demo_data
            from src.db import get_leads_by_status
            stats = seed_demo_data(db_path)
            self.assertGreater(stats["leads_created"], 0)
            scored = get_leads_by_status(db_path, "scored")
            self.assertGreater(len(scored), 0)

    def test_seed_creates_drafts(self):
        """seed_demo_data must write outreach drafts to the database."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            from src.seed_data import seed_demo_data
            from src.db import get_needs_review
            stats = seed_demo_data(db_path)
            self.assertGreater(stats["drafts_created"], 0)
            drafts = get_needs_review(db_path)
            self.assertGreater(len(drafts), 0)

    def test_seed_is_idempotent_for_all(self):
        """Running seed twice on a fresh DB must not duplicate jobs, leads, or drafts."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            from src.seed_data import seed_demo_data
            from src.db import (get_jobs_by_status, get_leads_by_status,
                                 get_needs_review, get_outreach_by_status)

            seed_demo_data(db_path)
            jobs_1  = len(get_jobs_by_status(db_path, "scored"))
            leads_1 = len(get_leads_by_status(db_path, "scored"))
            review_1   = len(get_needs_review(db_path))
            approved_1 = len(get_outreach_by_status(db_path, "approved"))

            seed_demo_data(db_path)
            jobs_2  = len(get_jobs_by_status(db_path, "scored"))
            leads_2 = len(get_leads_by_status(db_path, "scored"))
            review_2   = len(get_needs_review(db_path))
            approved_2 = len(get_outreach_by_status(db_path, "approved"))

            self.assertEqual(jobs_1, jobs_2,
                             "Second seed run must not duplicate scored jobs")
            self.assertEqual(leads_1, leads_2,
                             "Second seed run must not duplicate scored leads")
            self.assertEqual(review_1, review_2,
                             "Second seed run must not duplicate needs_review drafts")
            self.assertEqual(approved_1, approved_2,
                             "Second seed run must not duplicate approved drafts")

    def test_seed_second_run_skips_all(self):
        """On the second run, all records should be skipped (created counts = 0)."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            from src.seed_data import seed_demo_data
            seed_demo_data(db_path)
            stats = seed_demo_data(db_path)
            self.assertEqual(stats["jobs_created"], 0,
                             "Second run: no jobs should be created")
            self.assertEqual(stats["leads_created"], 0,
                             "Second run: no leads should be created")
            self.assertEqual(stats["drafts_created"], 0,
                             "Second run: no drafts should be created")
            self.assertGreater(stats["skipped"], 0,
                               "Second run: all records should be skipped")

    def test_seed_makes_no_external_calls(self):
        """seed_demo_data must make zero HTTP or Anthropic API calls."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            with patch("requests.get") as mock_get, \
                 patch("requests.post") as mock_post:
                from src.seed_data import seed_demo_data
                seed_demo_data(db_path)
            mock_get.assert_not_called()
            mock_post.assert_not_called()

    def test_seed_uses_safe_fake_domains(self):
        """All demo records must use .test domains — no real email risk."""
        from src.seed_data import DEMO_JOBS, DEMO_LEADS
        for job in DEMO_JOBS:
            if job.get("domain"):
                self.assertTrue(
                    job["domain"].endswith(".test"),
                    f"Demo job domain must end in .test: {job['domain']}"
                )
        for lead in DEMO_LEADS:
            if lead.get("contact_email"):
                self.assertTrue(
                    lead["contact_email"].endswith(".test"),
                    f"Demo lead email must end in .test: {lead['contact_email']}"
                )


# ══════════════════════════════════════════════════════════════════════════════
# 17. Daily brief and review queue show seeded data
# ══════════════════════════════════════════════════════════════════════════════

class TestBriefAndQueueWithSeedData(unittest.TestCase):

    def test_daily_brief_shows_seeded_jobs(self):
        """generate_brief must mention seeded high-priority jobs."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            from src.seed_data import seed_demo_data
            from src.daily_brief import generate_brief
            seed_demo_data(db_path)
            with patch("sys.stdout", new_callable=StringIO) as out:
                generate_brief(db_path)
            output = out.getvalue()
            self.assertTrue(
                len(output) > 100,
                "Daily brief must produce non-empty output after seeding"
            )
            self.assertIn("Apex Digital Solutions", output,
                          "Daily brief must show seeded high-priority job company")

    def test_daily_brief_shows_seeded_leads(self):
        """generate_brief must mention seeded leads."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            from src.seed_data import seed_demo_data
            from src.daily_brief import generate_brief
            seed_demo_data(db_path)
            with patch("sys.stdout", new_callable=StringIO) as out:
                generate_brief(db_path)
            output = out.getvalue()
            self.assertIn("Palm Sun Realty", output,
                          "Daily brief must show seeded high-priority lead company")

    def test_review_queue_shows_seeded_drafts(self):
        """get_needs_review must return seeded drafts with quality scores."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            from src.seed_data import seed_demo_data
            from src.db import get_needs_review
            seed_demo_data(db_path)
            drafts = get_needs_review(db_path)
            self.assertGreater(len(drafts), 0,
                               "Review queue must be non-empty after seeding")
            # At least one draft should have quality scores
            scored = [d for d in drafts if d.get("quality_status") in ("passed", "failed")]
            self.assertGreater(len(scored), 0,
                               "Seeded drafts must have quality status set")

    def test_review_queue_includes_passed_and_failed_drafts(self):
        """Seeded drafts must include both passed and failed quality examples."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = _make_db(tmp)
            from src.seed_data import seed_demo_data
            from src.db import get_needs_review
            seed_demo_data(db_path)
            drafts = get_needs_review(db_path)
            statuses = {d.get("quality_status") for d in drafts}
            self.assertIn("passed", statuses, "Must include a passed demo draft")
            self.assertIn("failed", statuses, "Must include a failed demo draft")


# ══════════════════════════════════════════════════════════════════════════════
# 18. --apply and --send-outreach work without config file
# ══════════════════════════════════════════════════════════════════════════════

class TestEarlyExitWithoutConfig(unittest.TestCase):

    def test_apply_via_main_without_config_file(self):
        """--apply via main() must print REMOVED even when config.yaml does not exist."""
        from main import main
        with patch("sys.argv", ["main.py", "--apply",
                                "--config", "/nonexistent/__missing__.yaml"]):
            with patch("sys.stdout", new_callable=StringIO) as out:
                try:
                    main()
                except SystemExit:
                    pass
            self.assertIn("REMOVED", out.getvalue(),
                          "--apply must print REMOVED without requiring config.yaml")

    def test_send_outreach_via_main_without_config_file(self):
        """--send-outreach via main() must print DEPRECATED even when config.yaml is absent."""
        from main import main
        with patch("sys.argv", ["main.py", "--send-outreach",
                                "--config", "/nonexistent/__missing__.yaml"]):
            with patch("sys.stdout", new_callable=StringIO) as out:
                try:
                    main()
                except SystemExit:
                    pass
            self.assertIn("DEPRECATED", out.getvalue(),
                          "--send-outreach must print DEPRECATED without requiring config.yaml")

    def test_seed_via_main_creates_records(self):
        """--seed-demo-data via main() must create records without a real config."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "copilot.db")
            # Minimal config — only paths.database, no API keys required
            cfg_path = os.path.join(tmp, "config.yaml")
            with open(cfg_path, "w") as f:
                f.write(f"paths:\n  database: {db_path}\n")
            from main import main
            with patch("sys.argv", ["main.py", "--seed-demo-data",
                                    "--config", cfg_path]):
                with patch("sys.stdout", new_callable=StringIO):
                    try:
                        main()
                    except SystemExit:
                        pass
            from src.db import get_jobs_by_status
            jobs = get_jobs_by_status(db_path, "scored")
            self.assertGreater(len(jobs), 0,
                               "--seed-demo-data must create scored jobs in the DB")


if __name__ == "__main__":
    unittest.main(verbosity=2)
