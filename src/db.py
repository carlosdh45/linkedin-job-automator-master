import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Generator


# ── Status enumerations ────────────────────────────────────────────────────────

JOB_STATUSES = {
    "discovered", "scored", "draft_ready", "needs_review",
    "approved", "applied", "rejected", "archived",
    # legacy (kept for backward compatibility)
    "skipped", "failed", "manual_review", "in_progress", "external_apply",
}

LEAD_STATUSES = {
    "discovered", "enriched", "scored", "draft_ready", "needs_review",
    "approved", "contacted", "replied", "not_fit", "archived",
}

OUTREACH_STATUSES = {
    "draft", "needs_review", "approved", "sent", "replied", "skipped", "failed",
}

SCORE_LABELS = {
    range(85, 101): "high_priority",
    range(70, 85):  "good_fit",
    range(50, 70):  "maybe",
    range(0, 50):   "low_fit",
}


def score_label(score: int) -> str:
    for r, label in SCORE_LABELS.items():
        if score in r:
            return label
    return "low_fit"


# ── Connection helper ──────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_connection(db_path: str) -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Schema initialization + migrations ────────────────────────────────────────

def initialize_database(db_path: str) -> None:
    with get_connection(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version    INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS applied_jobs (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                job_url           TEXT NOT NULL UNIQUE,
                company           TEXT NOT NULL,
                title             TEXT NOT NULL,
                location          TEXT,
                domain            TEXT,
                status            TEXT NOT NULL DEFAULT 'discovered',
                external_url      TEXT,
                applied_at        TEXT NOT NULL,
                notes             TEXT,
                job_score         INTEGER DEFAULT 0,
                skill_match_score INTEGER DEFAULT 0,
                score_label       TEXT DEFAULT '',
                skip_reason       TEXT DEFAULT '',
                approved_at       TEXT,
                context_data      TEXT DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_applied_jobs_status  ON applied_jobs(status);
            CREATE INDEX IF NOT EXISTS idx_applied_jobs_company ON applied_jobs(company);

            CREATE TABLE IF NOT EXISTS leads (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                domain         TEXT NOT NULL,
                company        TEXT NOT NULL,
                contact_name   TEXT DEFAULT '',
                contact_email  TEXT DEFAULT '',
                contact_role   TEXT DEFAULT '',
                industry       TEXT DEFAULT '',
                pain_points    TEXT DEFAULT '[]',
                context_data   TEXT DEFAULT '{}',
                lead_score     INTEGER DEFAULT 0,
                score_label    TEXT DEFAULT '',
                status         TEXT NOT NULL DEFAULT 'discovered',
                skip_reason    TEXT DEFAULT '',
                created_at     TEXT NOT NULL,
                updated_at     TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
            CREATE INDEX IF NOT EXISTS idx_leads_domain ON leads(domain);

            CREATE TABLE IF NOT EXISTS contacts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                domain      TEXT NOT NULL,
                company     TEXT,
                first_name  TEXT,
                last_name   TEXT,
                email       TEXT,
                role        TEXT,
                confidence  INTEGER,
                found_at    TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
            CREATE INDEX IF NOT EXISTS idx_contacts_domain ON contacts(domain);

            CREATE TABLE IF NOT EXISTS searched_domains (
                domain      TEXT PRIMARY KEY,
                searched_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS outreach (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                job_url               TEXT NOT NULL,
                company               TEXT NOT NULL,
                job_title             TEXT NOT NULL,
                to_email              TEXT DEFAULT '',
                to_name               TEXT DEFAULT '',
                to_role               TEXT DEFAULT '',
                subject               TEXT NOT NULL,
                body                  TEXT NOT NULL,
                outreach_type         TEXT NOT NULL DEFAULT 'client',
                style                 TEXT DEFAULT 'senior_pm_professional',
                status                TEXT NOT NULL DEFAULT 'needs_review',
                personalization_score INTEGER DEFAULT 0,
                spam_risk_score       INTEGER DEFAULT 50,
                ai_sounding_score     INTEGER DEFAULT 50,
                quality_status        TEXT DEFAULT 'pending',
                quality_reasons       TEXT DEFAULT '[]',
                send_recommendation   TEXT DEFAULT 'revise',
                context_used          TEXT DEFAULT '{}',
                generated_at          TEXT NOT NULL,
                approved_at           TEXT,
                sent_at               TEXT,
                skip_reason           TEXT DEFAULT '',
                failure_reason        TEXT DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_outreach_status ON outreach(status);
            CREATE INDEX IF NOT EXISTS idx_outreach_type   ON outreach(outreach_type);
        """)
        _run_migrations(conn)


_MIGRATIONS = []


def _migration(version: int):
    def decorator(fn):
        _MIGRATIONS.append((version, fn))
        return fn
    return decorator


def _run_migrations(conn: sqlite3.Connection) -> None:
    applied = {r[0] for r in conn.execute("SELECT version FROM schema_migrations").fetchall()}
    for version, fn in sorted(_MIGRATIONS):
        if version not in applied:
            fn(conn)
            conn.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (version, _now()),
            )


@_migration(1)
def _m1_rebuild_applied_jobs(conn: sqlite3.Connection) -> None:
    """Replace the old CHECK-constrained applied_jobs with the new flexible schema."""
    schema_row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='applied_jobs'"
    ).fetchone()
    if not schema_row or "CHECK" not in (schema_row[0] or ""):
        # Nothing to do — table is already on new schema or doesn't exist yet
        return

    conn.executescript("""
        ALTER TABLE applied_jobs RENAME TO _applied_jobs_v1;

        CREATE TABLE applied_jobs (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            job_url           TEXT NOT NULL UNIQUE,
            company           TEXT NOT NULL,
            title             TEXT NOT NULL,
            location          TEXT,
            domain            TEXT,
            status            TEXT NOT NULL DEFAULT 'discovered',
            external_url      TEXT,
            applied_at        TEXT NOT NULL,
            notes             TEXT,
            job_score         INTEGER DEFAULT 0,
            skill_match_score INTEGER DEFAULT 0,
            score_label       TEXT DEFAULT '',
            skip_reason       TEXT DEFAULT '',
            approved_at       TEXT,
            context_data      TEXT DEFAULT '{}'
        );

        INSERT INTO applied_jobs
            (id, job_url, company, title, location, domain, status,
             external_url, applied_at, notes)
        SELECT id, job_url, company, title, location, domain, status,
               external_url, applied_at, notes
        FROM _applied_jobs_v1;

        DROP TABLE _applied_jobs_v1;

        CREATE INDEX IF NOT EXISTS idx_applied_jobs_status  ON applied_jobs(status);
        CREATE INDEX IF NOT EXISTS idx_applied_jobs_company ON applied_jobs(company);
    """)


@_migration(2)
def _m2_add_outreach_quality_columns(conn: sqlite3.Connection) -> None:
    """Add human-in-the-loop and quality columns to outreach."""
    new_cols = [
        ("outreach_type",         "TEXT NOT NULL DEFAULT 'client'"),
        ("style",                 "TEXT DEFAULT 'senior_pm_professional'"),
        ("status",                "TEXT NOT NULL DEFAULT 'needs_review'"),
        ("personalization_score", "INTEGER DEFAULT 0"),
        ("spam_risk_score",       "INTEGER DEFAULT 50"),
        ("ai_sounding_score",     "INTEGER DEFAULT 50"),
        ("quality_status",        "TEXT DEFAULT 'pending'"),
        ("quality_reasons",       "TEXT DEFAULT '[]'"),
        ("send_recommendation",   "TEXT DEFAULT 'revise'"),
        ("context_used",          "TEXT DEFAULT '{}'"),
        ("approved_at",           "TEXT"),
        ("skip_reason",           "TEXT DEFAULT ''"),
        ("failure_reason",        "TEXT DEFAULT ''"),
    ]
    for col, typedef in new_cols:
        try:
            conn.execute(f"ALTER TABLE outreach ADD COLUMN {col} {typedef}")
        except Exception:
            pass
    # Rows already sent keep their sent status
    conn.execute("UPDATE outreach SET status='sent' WHERE sent_at IS NOT NULL AND status='needs_review'")


# ── applied_jobs ──────────────────────────────────────────────────────────────

def record_job(
    db_path: str,
    job_url: str,
    company: str,
    title: str,
    location: str,
    domain: str = "",
    status: str = "discovered",
    external_url: str = "",
    notes: str = "",
) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            """INSERT INTO applied_jobs
                   (job_url, company, title, location, domain, status, external_url, applied_at, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(job_url) DO UPDATE SET
                   status=excluded.status,
                   external_url=excluded.external_url,
                   applied_at=excluded.applied_at,
                   notes=excluded.notes""",
            (job_url, company, title, location, domain, status, external_url, _now(), notes),
        )


def save_discovered_job(db_path: str, job: dict) -> None:
    """Save a job from CSV as discovered (no-op if already exists)."""
    url = job.get("Job LinkedIn URL", "").strip()
    if not url:
        return
    with get_connection(db_path) as conn:
        conn.execute(
            """INSERT OR IGNORE INTO applied_jobs
                   (job_url, company, title, location, domain, status, external_url, applied_at, notes)
               VALUES (?, ?, ?, ?, ?, 'discovered', '', ?, '')""",
            (
                url,
                job.get("Company Name", "").strip(),
                job.get("Job Title", "").strip(),
                job.get("Location", "").strip(),
                job.get("Company Domain", "").strip(),
                _now(),
            ),
        )


def update_job_score(
    db_path: str,
    job_url: str,
    job_score: int,
    skill_match_score: int,
    label: str,
) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            """UPDATE applied_jobs
               SET job_score=?, skill_match_score=?, score_label=?, status='scored'
               WHERE job_url=?""",
            (job_score, skill_match_score, label, job_url),
        )


def approve_job(db_path: str, job_url: str) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            "UPDATE applied_jobs SET status='approved', approved_at=? WHERE job_url=?",
            (_now(), job_url),
        )


def get_jobs_by_status(db_path: str, status: str) -> list:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM applied_jobs WHERE status=? ORDER BY job_score DESC, applied_at DESC",
            (status,),
        ).fetchall()
        return [dict(r) for r in rows]


def is_job_processed(db_path: str, job_url: str) -> bool:
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM applied_jobs WHERE job_url=? AND status NOT IN ('discovered','in_progress')",
            (job_url,),
        ).fetchone()
        return row is not None


def get_processed_urls(db_path: str) -> set:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT job_url FROM applied_jobs WHERE status NOT IN ('discovered','in_progress')"
        ).fetchall()
        return {r["job_url"] for r in rows}


def get_external_jobs(db_path: str) -> list:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM applied_jobs WHERE status='external_apply'"
        ).fetchall()
        return [dict(r) for r in rows]


# ── leads ─────────────────────────────────────────────────────────────────────

def save_lead(
    db_path: str,
    domain: str,
    company: str,
    contact_name: str = "",
    contact_email: str = "",
    contact_role: str = "",
    industry: str = "",
    pain_points: list = None,
    context_data: dict = None,
) -> int:
    pain_json = json.dumps(pain_points or [])
    ctx_json = json.dumps(context_data or {})
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """INSERT OR IGNORE INTO leads
                   (domain, company, contact_name, contact_email, contact_role,
                    industry, pain_points, context_data, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (domain, company, contact_name, contact_email, contact_role,
             industry, pain_json, ctx_json, _now(), _now()),
        )
        return cursor.lastrowid


def update_lead_score(db_path: str, lead_id: int, lead_score: int, label: str) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            "UPDATE leads SET lead_score=?, score_label=?, status='scored', updated_at=? WHERE id=?",
            (lead_score, label, _now(), lead_id),
        )


def get_leads_by_status(db_path: str, status: str) -> list:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM leads WHERE status=? ORDER BY lead_score DESC, created_at DESC",
            (status,),
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["pain_points"] = json.loads(d.get("pain_points") or "[]")
            d["context_data"] = json.loads(d.get("context_data") or "{}")
            result.append(d)
        return result


def update_lead_status(db_path: str, lead_id: int, status: str, skip_reason: str = "") -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            "UPDATE leads SET status=?, skip_reason=?, updated_at=? WHERE id=?",
            (status, skip_reason, _now(), lead_id),
        )


# ── contacts ──────────────────────────────────────────────────────────────────

def record_contact(db_path: str, domain: str, company: str, contact: dict) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            """INSERT OR IGNORE INTO contacts
                   (domain, company, first_name, last_name, email, role, confidence, found_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                domain, company,
                contact.get("first_name", ""),
                contact.get("last_name", ""),
                contact.get("value", ""),
                contact.get("position", ""),
                contact.get("confidence", 0),
                _now(),
            ),
        )


def is_domain_searched(db_path: str, domain: str) -> bool:
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT 1 FROM searched_domains WHERE domain=?", (domain,)
        ).fetchone() is not None


def mark_domain_searched(db_path: str, domain: str) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO searched_domains (domain, searched_at) VALUES (?, ?)",
            (domain, _now()),
        )


def get_contacts_for_domain(db_path: str, domain: str) -> list:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM contacts WHERE domain=? ORDER BY confidence DESC",
            (domain,),
        ).fetchall()
        return [dict(r) for r in rows]


# ── outreach ──────────────────────────────────────────────────────────────────

def record_outreach(
    db_path: str,
    job_url: str,
    company: str,
    job_title: str,
    subject: str,
    body: str,
    to_email: str = "",
    to_name: str = "",
    to_role: str = "",
    outreach_type: str = "client",
    style: str = "senior_pm_professional",
    status: str = "needs_review",
    personalization_score: int = 0,
    spam_risk_score: int = 50,
    ai_sounding_score: int = 50,
    quality_status: str = "pending",
    quality_reasons: list = None,
    send_recommendation: str = "revise",
    context_used: dict = None,
) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """INSERT INTO outreach
                   (job_url, company, job_title, to_email, to_name, to_role,
                    subject, body, outreach_type, style, status,
                    personalization_score, spam_risk_score, ai_sounding_score,
                    quality_status, quality_reasons, send_recommendation, context_used,
                    generated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                job_url, company, job_title, to_email, to_name, to_role,
                subject, body, outreach_type, style, status,
                personalization_score, spam_risk_score, ai_sounding_score,
                quality_status,
                json.dumps(quality_reasons or []),
                send_recommendation,
                json.dumps(context_used or {}),
                _now(),
            ),
        )
        return cursor.lastrowid


def approve_outreach(db_path: str, outreach_id: int) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            "UPDATE outreach SET status='approved', approved_at=? WHERE id=?",
            (_now(), outreach_id),
        )


def skip_outreach(db_path: str, outreach_id: int, reason: str = "") -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            "UPDATE outreach SET status='skipped', skip_reason=? WHERE id=?",
            (reason, outreach_id),
        )


def mark_outreach_sent(db_path: str, outreach_id: int) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            "UPDATE outreach SET sent_at=?, status='sent' WHERE id=?",
            (_now(), outreach_id),
        )


def mark_outreach_failed(db_path: str, outreach_id: int, reason: str) -> None:
    """Mark a send attempt as failed and store the reason. Does NOT mark as sent."""
    with get_connection(db_path) as conn:
        conn.execute(
            "UPDATE outreach SET status='failed', failure_reason=? WHERE id=?",
            (reason[:500], outreach_id),
        )


def get_outreach_by_status(db_path: str, status: str) -> list:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM outreach WHERE status=? ORDER BY generated_at DESC",
            (status,),
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["quality_reasons"] = json.loads(d.get("quality_reasons") or "[]")
            d["context_used"] = json.loads(d.get("context_used") or "{}")
            result.append(d)
        return result


def get_unsent_outreach(db_path: str) -> list:
    """Only returns approved items — never sends needs_review or draft items."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM outreach "
            "WHERE sent_at IS NULL AND to_email != '' AND status = 'approved' "
            "ORDER BY generated_at ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_approved_outreach(db_path: str) -> list:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM outreach WHERE status='approved' AND to_email != '' ORDER BY approved_at ASC"
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["quality_reasons"] = json.loads(d.get("quality_reasons") or "[]")
            d["context_used"] = json.loads(d.get("context_used") or "{}")
            result.append(d)
        return result


def get_needs_review(db_path: str) -> list:
    """Return all items (outreach) pending human review."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM outreach WHERE status='needs_review' ORDER BY generated_at ASC"
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["quality_reasons"] = json.loads(d.get("quality_reasons") or "[]")
            d["context_used"] = json.loads(d.get("context_used") or "{}")
            result.append(d)
        return result


# ── stats ─────────────────────────────────────────────────────────────────────

def get_stats(db_path: str) -> dict:
    with get_connection(db_path) as conn:
        job_rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM applied_jobs GROUP BY status"
        ).fetchall()
        lead_rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM leads GROUP BY status"
        ).fetchall()
        contacts_count = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
        outreach_count = conn.execute("SELECT COUNT(*) FROM outreach").fetchone()[0]
        outreach_sent = conn.execute(
            "SELECT COUNT(*) FROM outreach WHERE sent_at IS NOT NULL"
        ).fetchone()[0]
        outreach_pending = conn.execute(
            "SELECT COUNT(*) FROM outreach WHERE status='needs_review'"
        ).fetchone()[0]

        stats = {f"job_{r['status']}": r["cnt"] for r in job_rows}
        stats.update({f"lead_{r['status']}": r["cnt"] for r in lead_rows})
        stats["contacts_found"] = contacts_count
        stats["outreach_generated"] = outreach_count
        stats["outreach_sent"] = outreach_sent
        stats["outreach_pending_review"] = outreach_pending
        return stats


# ── exports ───────────────────────────────────────────────────────────────────

def export_contacts_to_csv(db_path: str, output_path: str) -> int:
    import csv
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM contacts ORDER BY domain, confidence DESC").fetchall()
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows([dict(r) for r in rows])
    return len(rows)


def export_outreach_to_csv(db_path: str, output_path: str) -> int:
    import csv
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM outreach ORDER BY generated_at DESC"
        ).fetchall()
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows([dict(r) for r in rows])
    return len(rows)
