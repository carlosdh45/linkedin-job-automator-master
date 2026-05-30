"""
Interactive CLI for reviewing, approving, editing, or skipping outreach drafts.
No external dependencies — plain terminal output only.

APPROVAL RULES (enforced in code, no bypass):
  - quality_status must be 'passed'
  - personalization_score >= 75
  - spam_risk_score        <= 35
  - ai_sounding_score      <= 40

There is no CLI path that bypasses these rules.
Tests that need to create approved items should call db.approve_outreach() directly.
"""

import logging
import textwrap
from src import db
from src.quality_guard import format_quality_report

logger = logging.getLogger(__name__)

_SEP  = "─" * 72
_WIDE = "═" * 72


def _hr():
    print(_SEP)


def _header(text: str):
    print(f"\n{_WIDE}")
    print(f"  {text}")
    print(_WIDE)


def _wrap(text: str, width: int = 68, indent: str = "  ") -> str:
    lines = []
    for paragraph in text.split("\n"):
        if paragraph.strip():
            lines.extend(textwrap.wrap(paragraph, width=width,
                                       initial_indent=indent,
                                       subsequent_indent=indent))
        else:
            lines.append("")
    return "\n".join(lines)


def quality_passes(item: dict) -> tuple:
    """
    Returns (ok: bool, reason: str).
    This is the single source of truth for whether a draft may be approved.
    No override exists.
    """
    status = item.get("quality_status") or "pending"

    if status == "pending":
        return False, (
            "Quality check has NOT been run on this draft.\n"
            "  Run --draft-job-application or --draft-client-outreach to score it first."
        )

    if status == "failed":
        p = item.get("personalization_score", 0)
        s = item.get("spam_risk_score", 50)
        a = item.get("ai_sounding_score", 50)
        fails = []
        if p < 75:
            fails.append(f"personalization {p}/100 (need ≥75)")
        if s > 35:
            fails.append(f"spam_risk {s}/100 (need ≤35)")
        if a > 40:
            fails.append(f"ai_sounding {a}/100 (need ≤40)")
        reason = "Quality check FAILED:\n  " + "\n  ".join(fails) if fails else "Quality check marked failed."
        return False, reason + "\n  Regenerate with --draft-job-application or --draft-client-outreach."

    # status == "passed" — verify scores still meet thresholds
    p = item.get("personalization_score", 0)
    s = item.get("spam_risk_score", 50)
    a = item.get("ai_sounding_score", 50)
    fails = []
    if p < 75:
        fails.append(f"personalization {p}/100 (need ≥75)")
    if s > 35:
        fails.append(f"spam_risk {s}/100 (need ≤35)")
    if a > 40:
        fails.append(f"ai_sounding {a}/100 (need ≤40)")

    if fails:
        return False, "Score mismatch:\n  " + "\n  ".join(fails)

    return True, ""


# Backward-compat alias used by existing tests
_quality_passes = quality_passes


# ── Interactive review queue ───────────────────────────────────────────────────

def show_review_queue(db_path: str, outreach_type: str = None) -> None:
    """Interactive review loop for all 'needs_review' drafts."""
    items = db.get_needs_review(db_path)

    if outreach_type:
        items = [i for i in items if i.get("outreach_type") == outreach_type]

    if not items:
        print("\nNo drafts pending review.")
        return

    _header(f"REVIEW QUEUE  —  {len(items)} draft(s) pending")

    approved_count = skipped_count = 0

    for idx, item in enumerate(items, 1):
        _show_draft(item, idx, len(items))
        ok, reason = quality_passes(item)

        if not ok:
            print(f"\n  ✗ Cannot approve: {reason.splitlines()[0]}")
        else:
            print("\n  ✓ Quality check passed — ready to approve")

        while True:
            try:
                choice = input("\n  Action [A=approve / S=skip / N=next / Q=quit]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nReview interrupted.")
                _print_session_summary(approved_count, skipped_count)
                return

            if choice == "a":
                if not ok:
                    print(f"  ✗ Cannot approve: {reason}")
                    print("  Regenerate this draft to fix quality issues.")
                    break
                db.approve_outreach(db_path, item["id"])
                approved_count += 1
                print(f"  ✓ Draft #{item['id']} approved.")
                break

            elif choice == "s":
                reason_txt = input("  Skip reason (optional): ").strip()
                db.skip_outreach(db_path, item["id"], reason_txt or "skipped_in_review")
                skipped_count += 1
                print(f"  Draft #{item['id']} skipped.")
                break

            elif choice in ("n", ""):
                break

            elif choice == "q":
                _print_session_summary(approved_count, skipped_count)
                return

            else:
                print("  Invalid choice. Use A, S, N, or Q.")

    _print_session_summary(approved_count, skipped_count)


# ── Single-item approval (used by --approve ID) ────────────────────────────────

def approve_single(db_path: str, draft_id: int, force: bool = False) -> bool:
    """
    Approve a single draft by ID.
    The `force` parameter is accepted for test compatibility but has no effect —
    the quality gate is always enforced.
    Returns True if approved, False if blocked.
    """
    items = db.get_needs_review(db_path)
    item = next((i for i in items if i["id"] == draft_id), None)
    if not item:
        print(f"Draft #{draft_id} not found in needs_review queue.")
        return False

    ok, reason = quality_passes(item)

    if not ok:
        print(f"Draft #{draft_id} blocked:")
        print(f"  {reason}")
        print("  Fix the draft quality before approving.")
        return False

    db.approve_outreach(db_path, draft_id)
    print(f"Draft #{draft_id} approved.")
    return True


# ── Display helpers ───────────────────────────────────────────────────────────

def _show_draft(item: dict, idx: int, total: int) -> None:
    _hr()
    print(f"\n  [{idx}/{total}]  Draft ID: {item['id']}  |  Type: {item.get('outreach_type','?').upper()}")
    print(f"  Company  : {item.get('company','?')}")
    print(f"  Role     : {item.get('job_title','?')}")
    if item.get("to_name"):
        print(f"  Contact  : {item['to_name']}  <{item.get('to_email','?')}>")
        if item.get("to_role"):
            print(f"  Contact role: {item['to_role']}")
    print(f"  Style    : {item.get('style','?')}")
    print(f"  Quality  : {item.get('quality_status','pending').upper()}")

    if item.get("quality_status") not in ("pending", None):
        print(f"\n  Quality scores:")
        print(format_quality_report(item))

    print(f"\n  Subject: {item.get('subject','(no subject)')}")
    print()
    print(_wrap(item.get("body", "")))

    ctx = item.get("context_used") or {}
    if ctx:
        print(f"\n  Context used:")
        for k, v in ctx.items():
            if v:
                print(f"    {k}: {str(v)[:80]}")


def _print_session_summary(approved: int, skipped: int) -> None:
    print(f"\n{'─' * 40}")
    print(f"  Session complete — approved: {approved}  skipped: {skipped}")
    print()


def show_single_draft(db_path: str, draft_id: int) -> None:
    """Display a single draft by ID."""
    items = db.get_needs_review(db_path)
    match = next((i for i in items if i["id"] == draft_id), None)
    if not match:
        approved_list = db.get_outreach_by_status(db_path, "approved")
        match = next((i for i in approved_list if i["id"] == draft_id), None)
    if not match:
        print(f"Draft #{draft_id} not found or already processed.")
        return
    _show_draft(match, 1, 1)
