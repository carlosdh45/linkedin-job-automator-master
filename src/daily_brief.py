"""
DobryBot — Daily Opportunity Brief

Sections:
  A. Top 3 Moves Today        (strategic priority actions)
  B. Top Job Opportunities    (scored, with fit analysis)
  C. Top Client Leads         (scored, with lead analysis)
  D. Drafts Ready for Review  (needs_review with quality scores)
  E. Needs More Research      (missing context — research first)
  F. Skips / Low Quality      (why they were deprioritized)
  G. Today's Recommended Actions  (clear numbered action list)

Rules:
- No external calls. Offline, fast, rule-based.
- Never invent company facts. Only show what is in the DB.
- Quality over volume. Prefer 3-5 specific actions over long lists.
- If context is insufficient, recommend research, not outreach.
"""

from datetime import datetime
from src import db

_W = "═" * 72
_S = "─" * 72


# ── Formatting helpers ─────────────────────────────────────────────────────────

def _section(title: str) -> None:
    print(f"\n{_W}")
    print(f"  {title}")
    print(_W)


def _sub(label: str, value: str, width: int = 18) -> None:
    print(f"  {label:<{width}}: {value}")


def _blank() -> None:
    print()


def _label_icon(label: str) -> str:
    return {
        "high_priority": "★★★",
        "good_fit":      "★★ ",
        "maybe":         "★  ",
        "low_fit":       "   ",
    }.get(label, "   ")


def _score_bar(score: int, width: int = 20) -> str:
    filled = round(score / 100 * width)
    return f"[{'█' * filled}{'░' * (width - filled)}] {score}/100"


# ── Section A: Top 3 Moves Today ──────────────────────────────────────────────

def _section_a(stats: dict, profile=None) -> list:
    """Return up to 3 highest-priority actions as strings."""
    moves = []

    approved_count = stats.get("outreach_approved", 0)
    pending_count = stats.get("outreach_pending_review", 0)
    hp_jobs = stats.get("job_high_priority", 0)
    gf_jobs = stats.get("job_good_fit", 0)
    hp_leads = stats.get("lead_high_priority", 0)

    if approved_count:
        moves.append(
            f"Send {approved_count} approved message(s) that are ready to go  →  bash run.sh --send-approved"
        )
    if pending_count:
        moves.append(
            f"Review {pending_count} draft(s) in queue  →  bash run.sh --review-queue"
        )
    if hp_jobs and not approved_count and not pending_count:
        moves.append(
            f"Generate application drafts for {hp_jobs} high-priority job(s)  →  bash run.sh --draft-job-application"
        )
    if gf_jobs and not approved_count and not pending_count and len(moves) < 3:
        moves.append(
            f"Score and review {gf_jobs} good-fit job(s)  →  bash run.sh --score-jobs"
        )
    if hp_leads and len(moves) < 3:
        moves.append(
            f"Generate outreach for {hp_leads} high-potential lead(s)  →  bash run.sh --draft-client-outreach"
        )

    if not moves:
        if not stats.get("job_discovered") and not stats.get("lead_discovered"):
            moves.append("Start discovery  →  bash run.sh --discover-jobs && bash run.sh --discover-leads")
        elif not stats.get("job_scored") and not stats.get("lead_scored"):
            moves.append("Score discovered opportunities  →  bash run.sh --score-jobs && bash run.sh --score-leads")
        else:
            moves.append("All caught up. Run --discover-jobs to find new opportunities.")

    return moves[:3]


# ── Section B: Job opportunity analysis ────────────────────────────────────────

def _job_fit_reasons(job: dict, profile=None) -> list:
    title = (job.get("title") or "").lower()
    location = (job.get("location") or "").lower()
    reasons = []

    if profile and not profile.is_empty():
        for role in profile.target_roles:
            if any(w.lower() in title for w in role.split() if len(w) > 3):
                reasons.append(f"Matches target role: {role}")
                break
        skill_matches = [s for s in profile.skills if s.lower().split()[0] in title]
        if skill_matches:
            reasons.append(f"Skills aligned: {', '.join(skill_matches[:3])}")

    if "remote" in location:
        reasons.append("Remote-friendly")
    if any(kw in location for kw in ["latam", "colombia", "honduras", "latin america", "worldwide"]):
        reasons.append("LATAM-friendly")
    if not reasons:
        reasons.append("Keyword match from scoring")
    return reasons


def _job_concerns(job: dict) -> list:
    concerns = []
    score = job.get("job_score", 0)
    location = (job.get("location") or "").lower()

    if score < 60:
        concerns.append(f"Score below good-fit threshold ({score}/100)")
    if "hybrid" in location or "on-site" in location or "onsite" in location:
        concerns.append("On-site or hybrid — may not be fully remote")
    if not job.get("external_url"):
        concerns.append("No direct apply URL in DB yet")
    return concerns


def _job_action(label: str) -> str:
    return {
        "high_priority": "Draft message today →  bash run.sh --draft-job-application",
        "good_fit":      "Review and draft soon",
        "maybe":         "Research company first, then decide",
        "low_fit":       "Skip — not a strong fit",
    }.get(label, "Review manually")


def _job_message_hint(job: dict, profile=None) -> str:
    title = job.get("title", "the role")
    company = job.get("company", "your company")
    name = profile.first_name if profile and not profile.is_empty() else "Carlos"

    top_skills = ""
    if profile and not profile.is_empty() and profile.skills:
        top_skills = f" — {', '.join(profile.skills[:2])}"

    return (
        f'Hi [Name], I saw the {title} role at {company}. '
        f'It looks close to what I\'ve been doing{top_skills} and project delivery. '
        f'I\'m based in LATAM, fully remote. '
        f'Happy to share more if the team is open to international candidates.'
    )


def _print_job(job: dict, idx: int, profile=None) -> None:
    label = job.get("score_label", "")
    score = job.get("job_score", 0)
    icon = _label_icon(label)

    print(f"\n  {icon} [{idx}] {job.get('title', '?')} @ {job.get('company', '?')}")
    print(f"      Location  : {job.get('location', '?')}")
    print(f"      Score     : {_score_bar(score, 16)}  {label}")

    reasons = _job_fit_reasons(job, profile)
    if reasons:
        print(f"      Why fit   : {' | '.join(reasons)}")

    concerns = _job_concerns(job)
    if concerns:
        print(f"      Concerns  : {' | '.join(concerns)}")

    print(f"      Action    : {_job_action(label)}")

    if label in ("high_priority", "good_fit"):
        hint = _job_message_hint(job, profile)
        print(f"      Msg hint  : \"{hint[:110]}...\"" if len(hint) > 110 else f"      Msg hint  : \"{hint}\"")


# ── Section C: Lead analysis ────────────────────────────────────────────────────

def _lead_fit_reasons(lead: dict, profile=None) -> list:
    industry = (lead.get("industry") or "").lower()
    reasons = []

    if profile and not profile.is_empty():
        for ic in profile.ideal_clients:
            if ic.lower() in industry or any(w in industry for w in ic.lower().split() if len(w) > 3):
                reasons.append(f"ICP match: {ic}")
                break
        for svc in profile.services[:3]:
            pain_text = " ".join(str(p) for p in (lead.get("pain_points") or []))
            if any(w in pain_text.lower() for w in svc.lower().split() if len(w) > 4):
                reasons.append(f"Service fit: {svc}")
                break

    pain_points = lead.get("pain_points") or []
    if pain_points:
        reasons.append(f"Pain signal: {pain_points[0]}")

    if not reasons:
        reasons.append("Industry match from scoring")
    return reasons


def _lead_ticket_estimate(score: int) -> str:
    if score >= 85:
        return "$3,000 – $10,000+"
    if score >= 70:
        return "$1,500 – $5,000"
    if score >= 50:
        return "$500 – $3,000"
    return "unclear"


def _lead_outreach_angle(lead: dict, profile=None) -> str:
    pain_points = lead.get("pain_points") or []
    pain = pain_points[0] if pain_points else ""
    company = lead.get("company", "the company")
    ctx = lead.get("context_data") or {}
    signal = ctx.get("signal", "")

    if pain:
        return f"Could help with: {pain}"
    if signal:
        return f"Signal: {signal}"
    if profile and profile.services:
        return f"May need: {profile.services[0]}"
    return "Needs more research before outreach"


def _lead_action(label: str, has_context: bool) -> str:
    if not has_context:
        return "Research company first — not enough context for personalized outreach"
    return {
        "high_priority": "Draft outreach today  →  bash run.sh --draft-client-outreach",
        "good_fit":      "Draft outreach this week",
        "maybe":         "Research more, then draft if context is available",
        "low_fit":       "Skip — not strong ICP fit",
    }.get(label, "Review manually")


def _lead_message_hint(lead: dict, profile=None) -> str:
    company = lead.get("company", "your company")
    contact = lead.get("contact_name", "")
    greeting = f"Hi {contact.split()[0]}," if contact else "Hi,"
    pain_points = lead.get("pain_points") or []
    pain = pain_points[0] if pain_points else "your operations"
    ctx = lead.get("context_data") or {}
    signal = ctx.get("signal", "")

    context_line = signal if signal else f"you're working on {pain}"
    biz = profile.company_name if (profile and not profile.is_empty()) else "our team"

    return (
        f"{greeting} I noticed {context_line}. "
        f"{biz} works with businesses on {pain} — "
        f"not sure if this is relevant, but happy to share a few ideas if useful."
    )


def _print_lead(lead: dict, idx: int, profile=None) -> None:
    label = lead.get("score_label", "")
    score = lead.get("lead_score", 0)
    icon = _label_icon(label)
    ctx = lead.get("context_data") or {}
    has_context = bool(lead.get("contact_email") or ctx.get("signal") or lead.get("pain_points"))

    print(f"\n  {icon} [{idx}] {lead.get('company', '?')}  ({lead.get('industry', '?')})")
    if lead.get("contact_name"):
        print(f"      Contact   : {lead['contact_name']} — {lead.get('contact_role', '?')}")
    print(f"      Score     : {_score_bar(score, 16)}  {label}")
    print(f"      Ticket    : {_lead_ticket_estimate(score)}")

    reasons = _lead_fit_reasons(lead, profile)
    if reasons:
        print(f"      Why fit   : {' | '.join(reasons)}")

    angle = _lead_outreach_angle(lead, profile)
    print(f"      Angle     : {angle}")
    print(f"      Action    : {_lead_action(label, has_context)}")

    if label in ("high_priority", "good_fit") and has_context:
        hint = _lead_message_hint(lead, profile)
        print(f"      Msg hint  : \"{hint[:120]}...\"" if len(hint) > 120 else f"      Msg hint  : \"{hint}\"")


# ── Section D: Drafts ready for review ────────────────────────────────────────

def _pass_fail(score: int, threshold: int, op: str) -> str:
    if op == ">=" and score >= threshold:
        return "PASS"
    if op == "<=" and score <= threshold:
        return "PASS"
    return "FAIL"


def _print_draft(item: dict, idx: int) -> None:
    p = item.get("personalization_score", 0)
    s = item.get("spam_risk_score", 50)
    a = item.get("ai_sounding_score", 50)
    qs = item.get("quality_status", "pending")
    rec = item.get("send_recommendation", "revise")
    typ = item.get("outreach_type", "?")

    can_approve = qs == "passed" and p >= 75 and s <= 35 and a <= 40
    status_icon = "✓" if can_approve else "✗"

    print(f"\n  {status_icon} ID:{item['id']}  [{typ.upper()}]  {item.get('company','?')}")
    if item.get("to_name"):
        print(f"    Contact    : {item['to_name']} <{item.get('to_email','?')}>")
    print(f"    Subject    : {item.get('subject','?')[:60]}")
    print(f"    Quality    : {qs.upper()}  |  Rec: {rec.upper()}")
    print(f"    Scores     : personalization={p}/100 [{_pass_fail(p, 75, '>=')}]  "
          f"spam={s}/100 [{_pass_fail(s, 35, '<=')}]  ai={a}/100 [{_pass_fail(a, 40, '<=')}]")
    if can_approve:
        print(f"    Action     : bash run.sh --approve {item['id']}")
    else:
        reasons = item.get("quality_reasons") or []
        if reasons:
            print(f"    Issues     : {'; '.join(str(r) for r in reasons[:2])}")
        print(f"    Action     : Regenerate  →  bash run.sh --draft-job-application")


# ── Section G: Recommended actions ────────────────────────────────────────────

def _build_actions(
    stats: dict,
    approvable_drafts: list,
    high_jobs: list,
    high_leads: list,
    research_needed: list,
) -> list:
    actions = []

    # 1. Send approved
    approved = stats.get("outreach_approved", 0)
    if approved:
        actions.append(f"Send {approved} already-approved email(s):  bash run.sh --send-approved")

    # 2. Approve passing drafts
    if approvable_drafts:
        ids = " ".join(str(d["id"]) for d in approvable_drafts[:3])
        actions.append(
            f"Review + approve {len(approvable_drafts)} quality-passed draft(s):  bash run.sh --review-queue"
            + (f"  (IDs: {ids})" if approvable_drafts else "")
        )

    # 3. Apply to / draft for top jobs
    if high_jobs:
        top = high_jobs[0]
        actions.append(
            f"Draft message for: {top.get('title', '?')} @ {top.get('company', '?')}  "
            f"→  bash run.sh --draft-job-application"
        )

    # 4. Draft for top leads
    if high_leads:
        top = high_leads[0]
        actions.append(
            f"Draft outreach for: {top.get('company', '?')} ({top.get('industry', '?')})  "
            f"→  bash run.sh --draft-client-outreach"
        )

    # 5. Research
    if research_needed:
        companies = ", ".join(
            (r.get("company") or r.get("title", "?")) for r in research_needed[:3]
        )
        actions.append(f"Research before outreach: {companies}")

    if not actions:
        actions.append("No urgent actions. Run --discover-jobs to find new opportunities.")

    return actions[:7]


# ── Main brief generator ───────────────────────────────────────────────────────

def generate_brief(db_path: str, profile=None) -> None:
    today = datetime.now().strftime("%A, %B %d %Y")

    print(f"\n{_W}")
    if profile and not profile.is_empty():
        print(f"  DOBRYBOT — Daily Brief  |  {today}")
        print(f"  Profile: {profile.name}  |  {profile.location}")
    else:
        print(f"  DOBRYBOT — Daily Brief  |  {today}")
    print(_W)

    stats = db.get_stats(db_path)

    # ── Load data ────────────────────────────────────────────────────────────
    all_scored_jobs = (
        db.get_jobs_by_status(db_path, "scored") +
        db.get_jobs_by_status(db_path, "draft_ready") +
        db.get_jobs_by_status(db_path, "approved")
    )
    all_scored_jobs.sort(key=lambda j: j.get("job_score", 0), reverse=True)

    high_priority_jobs = [j for j in all_scored_jobs if j.get("score_label") == "high_priority"]
    good_fit_jobs      = [j for j in all_scored_jobs if j.get("score_label") == "good_fit"]
    maybe_jobs         = [j for j in all_scored_jobs if j.get("score_label") == "maybe"]
    low_jobs           = [j for j in all_scored_jobs if j.get("score_label") == "low_fit"]

    all_scored_leads = (
        db.get_leads_by_status(db_path, "scored") +
        db.get_leads_by_status(db_path, "draft_ready")
    )
    all_scored_leads.sort(key=lambda l: l.get("lead_score", 0), reverse=True)

    high_priority_leads = [l for l in all_scored_leads if l.get("score_label") == "high_priority"]
    good_fit_leads      = [l for l in all_scored_leads if l.get("score_label") == "good_fit"]
    low_leads           = [l for l in all_scored_leads if l.get("score_label") in ("maybe", "low_fit")]

    pending_drafts  = db.get_needs_review(db_path)
    approvable      = [d for d in pending_drafts if d.get("quality_status") == "passed"
                       and d.get("personalization_score", 0) >= 75
                       and d.get("spam_risk_score", 100) <= 35
                       and d.get("ai_sounding_score", 100) <= 40]
    blocked_drafts  = [d for d in pending_drafts if d not in approvable]

    # Research needed: jobs/leads without enough context
    unscored_jobs  = db.get_jobs_by_status(db_path, "discovered")
    unscored_leads = db.get_leads_by_status(db_path, "discovered")
    research_needed = []
    for j in maybe_jobs:
        if not j.get("external_url") and not j.get("context_data"):
            research_needed.append(j)
    for l in all_scored_leads:
        if not l.get("contact_email") and not (l.get("context_data") or {}).get("signal"):
            research_needed.append(l)

    # ── A. Top 3 Moves Today ─────────────────────────────────────────────────
    _section("A.  TOP 3 MOVES TODAY")
    moves = _section_a(stats, profile)
    for i, move in enumerate(moves, 1):
        print(f"\n  {i}. {move}")
    _blank()

    # ── B. Top Job Opportunities ─────────────────────────────────────────────
    top_jobs = (high_priority_jobs + good_fit_jobs)[:8]
    _section(f"B.  TOP JOB OPPORTUNITIES  ({len(top_jobs)} showing)")

    if not top_jobs:
        print("\n  No scored jobs yet. Run:")
        print("    bash run.sh --discover-jobs")
        print("    bash run.sh --score-jobs")
    else:
        for i, job in enumerate(top_jobs, 1):
            _print_job(job, i, profile)
            print()

    # ── C. Top Client Leads ──────────────────────────────────────────────────
    top_leads = (high_priority_leads + good_fit_leads)[:6]
    _section(f"C.  TOP CLIENT LEADS  ({len(top_leads)} showing)")

    if not top_leads:
        print("\n  No scored leads yet. Run:")
        print("    bash run.sh --discover-leads")
        print("    bash run.sh --score-leads")
    else:
        for i, lead in enumerate(top_leads, 1):
            _print_lead(lead, i, profile)
            print()

    # ── D. Drafts Ready for Review ───────────────────────────────────────────
    _section(f"D.  DRAFTS PENDING REVIEW  ({len(pending_drafts)} total  |  "
             f"{len(approvable)} approvable  |  {len(blocked_drafts)} blocked)")

    if not pending_drafts:
        print("\n  No drafts pending. Generate with:")
        print("    bash run.sh --draft-job-application")
        print("    bash run.sh --draft-client-outreach")
    else:
        if approvable:
            print(f"\n  Ready to approve ({len(approvable)}):")
            for i, d in enumerate(approvable[:5], 1):
                _print_draft(d, i)
        if blocked_drafts:
            print(f"\n  Blocked — quality issues ({len(blocked_drafts)}):")
            for i, d in enumerate(blocked_drafts[:3], 1):
                _print_draft(d, i)

    # ── E. Needs More Research ───────────────────────────────────────────────
    _section(f"E.  NEEDS MORE RESEARCH  ({len(research_needed)} items)")

    needs_research_display = (research_needed + unscored_jobs[:3] + unscored_leads[:3])[:8]
    if not needs_research_display:
        print("\n  Nothing flagged for research.")
    else:
        for item in needs_research_display:
            company = item.get("company") or item.get("title", "?")
            item_type = "JOB" if "job_url" in item and "domain" in item else "LEAD"
            missing = []
            if not item.get("contact_email") and not item.get("external_url"):
                missing.append("no contact or apply URL")
            if not (item.get("context_data") or {}):
                missing.append("no enrichment data")
            if not item.get("score_label"):
                missing.append("not yet scored")
            missing_str = " | ".join(missing) if missing else "review manually"
            print(f"  • [{item_type}] {company}  →  {missing_str}")

    # ── F. Skips / Low Quality ───────────────────────────────────────────────
    low_all = (low_jobs + low_leads)[:8]
    _section(f"F.  SKIPS / LOW QUALITY  ({len(low_all)} items)")

    if not low_all:
        print("\n  No low-quality items.")
    else:
        for item in low_all:
            company = item.get("company") or item.get("title", "?")
            score = item.get("job_score") or item.get("lead_score") or 0
            label = item.get("score_label", "?")
            item_type = "JOB" if "job_url" in item else "LEAD"
            print(f"  • [{item_type}] {company:<35} Score: {score:3d}  Label: {label}")

    # ── G. Today's Recommended Actions ───────────────────────────────────────
    _section("G.  TODAY'S RECOMMENDED ACTIONS")

    actions = _build_actions(stats, approvable, high_priority_jobs, high_priority_leads, research_needed)
    for i, action in enumerate(actions, 1):
        print(f"\n  {i}. {action}")

    # ── Footer ───────────────────────────────────────────────────────────────
    print(f"\n{_W}")
    print(f"  DB summary: "
          f"jobs_discovered={stats.get('job_discovered',0)} | "
          f"scored={stats.get('job_scored',0)} | "
          f"drafts_pending={stats.get('outreach_pending_review',0)} | "
          f"sent={stats.get('outreach_sent',0)}")
    print(_W)
    _blank()
