# CorosDev Opportunity Copilot — Roadmap

This roadmap tracks what is built, what is next, and the long-term vision.
The guiding principle: **quality over volume, human review over automation.**

---

## Phase 1 — Safety & Setup ✅ COMPLETE

Core pipeline from discovery to reviewed approval. No automation without human sign-off.

- [x] Job discovery from CSV with filters (location, title, age, blacklist)
- [x] Rule-based job scoring (0–100) by skill match, remote, seniority, LATAM fit
- [x] Lead discovery via Hunter.io (1 request per domain, cached)
- [x] Rule-based lead scoring by ICP, pain signals, contact quality
- [x] Claude-powered draft generation with 5 message styles
- [x] Forbidden phrase detection and AI-sounding text scoring
- [x] Quality Guard: personalization ≥ 75 / spam ≤ 35 / ai_sounding ≤ 40
- [x] Interactive terminal review queue (approve / skip / next / quit)
- [x] `--approve ID` + `--send-approved` with confirmation prompt
- [x] SMTP failure tracking (stored as `failed`, never marked as `sent`)
- [x] Daily limit on sends (`limits.max_emails_per_day`)
- [x] Environment variable config (`${ENV_VAR}` in YAML, `.env` file)
- [x] `--apply` removed (prints redirect, no LinkedIn action)
- [x] `--send-outreach` deprecated (redirects to approval workflow)
- [x] 70 passing tests, all mocked — no real API keys needed for CI
- [x] GitHub Actions CI on push and pull request
- [x] Clean private repo structure for CorosDev GitHub organization

---

## Phase 2 — Daily Opportunity Brief ✅ COMPLETE

- [x] `--daily-brief` command: top jobs, top leads, pending drafts, suggested actions
- [x] Actionable suggestions based on DB state
- [x] Database summary section

**Upcoming improvements:**
- [ ] Email delivery of the daily brief (opt-in)
- [ ] Markdown or HTML export of brief
- [ ] Brief personalized by day of week (Mon = discovery, Wed = review, Fri = send)

---

## Phase 3 — Better Scoring

Improve scoring accuracy beyond simple keyword matching.

- [ ] Claude-assisted job scoring for ambiguous roles (batch API calls)
- [ ] Score adjustment based on application success signals
- [ ] Company quality signals: funding, team size, growth indicators
- [ ] Salary/compensation range scoring (parse from job description)
- [ ] Blacklist patterns (not just exact company names)
- [ ] Score history — track score drift on re-discovered jobs
- [ ] LATAM timezone compatibility signal

---

## Phase 4 — Client Lead Enrichment

Deeper context for higher-quality outreach.

- [ ] Company website scraping: extract pain signals, tech stack, team info
- [ ] LinkedIn company page enrichment (public data only)
- [ ] Job posting analysis as a pain signal ("they're hiring for X → need Y")
- [ ] Industry-specific pain point library
- [ ] Context quality score before draft generation
- [ ] Automatic `insufficient_context` escalation with enrichment suggestions
- [ ] Apollo.io or Clearbit integration as alternative to Hunter.io

---

## Phase 5 — Recruiter/Client Draft Review UX

Better tooling for the human review step.

- [ ] Web-based review UI (lightweight Flask/FastAPI, local only)
- [ ] Side-by-side: draft | context used | quality scores | suggested edits
- [ ] In-app editing with live quality re-score
- [ ] Regenerate with different style/prompt in one click
- [ ] Batch approve with quality threshold filter
- [ ] Draft history and version comparison
- [ ] Export approved drafts to CSV for team review

---

## Phase 6 — Optional Dashboard

Analytics and pipeline tracking.

- [ ] Local web dashboard (read-only, no sending from UI)
- [ ] Application pipeline: discovered → scored → drafted → reviewed → sent → replied
- [ ] Response rate tracking (manual reply logging)
- [ ] Skill gap analysis: which job types score consistently low?
- [ ] Weekly summary report (PDF or Markdown)
- [ ] Team mode: multiple users, shared DB, per-user approval queues
