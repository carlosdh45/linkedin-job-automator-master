# CorosDev Opportunity Copilot

> A human-in-the-loop assistant for finding and reaching out to job opportunities and client prospects.
> Built by [CorosDev](https://corosdev.com) for professional use — not a bot, not a spam tool.

---

## What it does

- Discovers job opportunities from a CSV export
- Scores them by skill match, seniority, remote-friendliness, and LATAM compatibility
- Finds client leads via Hunter.io
- Generates personalized outreach drafts using Claude (Anthropic)
- Runs a quality check on every draft before it can be approved
- Lets you review, approve, or skip each draft interactively
- Only sends what you have explicitly approved

**Nothing is sent or applied without your manual review and approval.**

---

## Safety guarantees

| Rule | Enforcement |
|------|-------------|
| No auto-apply to LinkedIn | `--apply` is removed — prints a redirect message and exits |
| No auto-send of emails | `--send-approved` requires manual `--approve ID` first, then types `"yes"` at confirmation |
| Quality gate is mandatory | `personalization ≥ 75` / `spam_risk ≤ 35` / `ai_sounding ≤ 40` — no override |
| Pending/failed drafts are blocked | `quality_status = pending` or `failed` cannot be approved under any circumstances |
| SMTP failures are tracked | Failed sends are marked `status=failed` with a stored `failure_reason` — never marked as sent |
| All secrets via environment vars | `config.yaml` uses `${ENV_VAR}` references only — no plain-text credentials |
| Daily send limit enforced | `limits.max_emails_per_day` in config caps every send run |

---

## Recommended workflow

```bash
# ── Jobs ──────────────────────────────────────────────────────
bash run.sh --discover-jobs            # load jobs from CSV
bash run.sh --score-jobs               # score 0-100 by fit
bash run.sh --draft-job-application    # generate drafts (Claude, no sending)
bash run.sh --review-queue             # review each draft interactively
bash run.sh --approve 42               # approve draft #42 after reading it
bash run.sh --send-approved            # send only approved items

# ── Client Leads ──────────────────────────────────────────────
bash run.sh --discover-leads           # find leads via Hunter.io
bash run.sh --score-leads              # score by ICP fit
bash run.sh --draft-client-outreach    # generate outreach drafts
bash run.sh --review-queue --type client
bash run.sh --approve 7
bash run.sh --send-approved

# ── Reports ───────────────────────────────────────────────────
bash run.sh --daily-brief              # top jobs, top leads, pending drafts
bash run.sh --stats                    # database totals

# ── Safe preview (no writes, no external calls) ───────────────
bash run.sh --discover-jobs --dry-run
bash run.sh --score-jobs --dry-run
bash run.sh --draft-job-application --dry-run
```

---

## Setup

### 1. Clone and install (WSL / Ubuntu)

```bash
git clone https://github.com/CorosDev/opportunity-copilot
cd opportunity-copilot
bash install.sh
```

### 2. Configure credentials

```bash
cp config.example.yaml config.yaml
cp .env.example .env
nano .env          # add your API keys — never commit this file
```

Required env vars:

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Claude API for draft generation and quality scoring |
| `HUNTER_API_KEY` | Hunter.io for contact discovery |
| `LINKEDIN_EMAIL` | LinkedIn login (for session management only) |
| `LINKEDIN_PASSWORD` | LinkedIn login |
| `SMTP_HOST` | SMTP server for sending approved emails |
| `SMTP_USER` | SMTP username |
| `SMTP_PASSWORD` | SMTP app password |

### 3. Prepare your jobs CSV

Export job listings as a CSV with these columns:

```
Job LinkedIn URL, Company Name, Job Title, Location, Posted On, Company Domain
```

Set `paths.jobs_csv` in `config.yaml`.

### 4. Run the test suite

```bash
bash run.sh --test
```

All 70 tests pass without any real API keys or external calls.

---

## Quality gate

Every draft is scored by Claude (Haiku) before it can be approved:

| Dimension | Threshold | What it measures |
|-----------|-----------|-----------------|
| `personalization_score` | ≥ 75 | References specific company/role/person context |
| `spam_risk_score` | ≤ 35 | Not a mass template |
| `ai_sounding_score` | ≤ 40 | Sounds like a real person wrote it |

A draft that fails **any** threshold cannot be approved. There is no bypass.

---

## Scoring

Jobs and leads are scored 0–100 using rule-based matching (no API calls needed):

| Score | Label |
|-------|-------|
| 85–100 | `high_priority` |
| 70–84 | `good_fit` |
| 50–69 | `maybe` |
| 0–49 | `low_fit` |

**Jobs scored on:** skill match (fullstack, AI, PM, delivery, AEM, etc.), remote-friendliness, seniority, industry, LATAM compatibility.

**Leads scored on:** target industry (real estate, SMBs, startups, etc.), pain signals, contact role quality, company size.

---

## Message styles

Drafts are generated in one of 5 styles to avoid AI-sounding text:

| Style | Use case |
|-------|----------|
| `founder_direct` | Short, honest, no fluff — founder to decision-maker |
| `senior_pm_professional` | Professional but not stiff — PM/delivery candidate |
| `warm_networking` | Genuine curiosity, soft ask — no pitch |
| `client_value_first` | Observation → specific value → low-pressure CTA |
| `recruiter_friendly` | Candidate to recruiter — specific role, LATAM-aware |

Forbidden phrases are detected and blocked. Generic AI openers ("I hope this finds you well", "I came across your profile", etc.) raise the `ai_sounding_score` automatically.

---

## Approval flow

```
needs_review
    │
    ├─ --review-queue ──► [A]pprove → approved → --send-approved → sent
    │                   ► [S]kip   → skipped
    │
    └─ --approve ID  ──► approved  → --send-approved → sent
```

Items stay in `needs_review` until you explicitly act on them. **Nothing happens automatically.**

---

## Disabled / deprecated commands

| Command | Status |
|---------|--------|
| `--apply` | **Removed.** Prints a redirect message. No LinkedIn session opened. |
| `--send-outreach` | **Deprecated.** Prints redirect to `--send-approved`. Sends nothing. |
| `--generate-outreach` | Still works, saves as `needs_review`. Does not send. |
| `--find-emails` | Still works. Hunter.io lookup only, no sending. |

---

## Project structure

```
.
├── main.py                    # CLI entry point
├── src/
│   ├── config_loader.py       # YAML + ${ENV_VAR} interpolation
│   ├── db.py                  # SQLite with schema migrations
│   ├── scorer.py              # Rule-based job/lead scoring (0-100)
│   ├── humanizer.py           # Forbidden phrases, message styles, context gate
│   ├── quality_guard.py       # Claude quality scoring (personalization/spam/AI)
│   ├── review_queue.py        # Interactive terminal review queue
│   ├── daily_brief.py         # Daily summary generator
│   ├── answer_generator.py    # Claude outreach generation (prompt-cached)
│   ├── outreach_generator.py  # Legacy outreach flow
│   ├── linkedin_applier.py    # LinkedIn session + Easy Apply (disabled by default)
│   ├── job_filter.py          # CSV filtering
│   ├── email_finder.py        # Hunter.io integration (1 request/domain)
│   └── cv_parser.py           # PDF CV extraction
├── templates/
│   ├── jobs/                  # recruiter_message.md, cover_letter_short.md
│   └── clients/               # first_touch_email.md, follow_up_1.md, follow_up_2.md
├── tests/
│   ├── test_copilot.py        # 70 tests, all mocked, no real API calls
│   └── fixtures/              # sample_jobs.csv, test_config.yaml
├── config.example.yaml        # Config template with ${ENV_VAR} references
├── .env.example               # Secret template
├── install.sh                 # First-time setup
├── run.sh                     # Main runner + test shortcut
├── requirements.txt
└── ROADMAP.md
```

---

## Privacy & compliance

- Contact emails from Hunter.io are stored in `data/jobs.db` — treat as sensitive (GDPR-relevant)
- Every client email includes an opt-out line
- Follow-up cadence is max 2 messages; after follow-up #2, leads are archived
- LinkedIn session cookies live in `session/` (git-ignored, never committed)
- No API key, password, or credential is ever logged or printed to stdout
