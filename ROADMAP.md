# DobryBot — Roadmap

This roadmap tracks what is built, what is next, and the long-term vision.
The guiding principle: **quality over volume, human review over automation.**

---

## Phase 0 — Safe CLI Core ✅ COMPLETE

Foundation checkpoint. The Python core is the internal engine for all future phases.

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
- [x] Demo mode: `--seed-demo-data` with fully idempotent safe fake data
- [x] Daily brief: top jobs, leads, pending drafts, recommended actions
- [x] 85 passing tests — all mocked, no real API keys needed for CI

---

## Phase 1 — DobryBot Rebrand ✅ COMPLETE

- [x] Product renamed from "CorosDev Opportunity Copilot" to **DobryBot**
- [x] Updated CLI banners, headers, and help text
- [x] Updated README, ROADMAP with DobryBot positioning
- [x] ARCHITECTURE.md documenting the launch-ready system design
- [x] LAUNCH_PLAN.md with phased delivery plan

---

## Phase 2 — Backend API (FastAPI)

Expose the Python core as a proper REST API with authentication and persistence.

- [ ] FastAPI application with structured routers
- [ ] Pydantic request/response schemas
- [ ] SQLAlchemy models wrapping the existing SQLite schema
- [ ] Alembic migrations (replace manual migration system)
- [ ] PostgreSQL support for production
- [ ] JWT authentication (single-user to start)
- [ ] API endpoints for all core workflows:
  - `GET /brief` — daily brief data
  - `GET /jobs`, `GET /leads` — with filter/sort
  - `GET /queue` — review queue
  - `POST /approve/{id}` — approve a draft (Quality Guard enforced)
  - `POST /skip/{id}` — skip a draft
  - `POST /seed` — seed demo data (demo mode only)
- [ ] Safety enforcement at the API layer (no auto-send endpoints)
- [ ] Audit log table: every approve/skip/send logged with timestamp and user

---

## Phase 3 — Frontend Web App (Next.js)

Modern dashboard UI over the FastAPI backend.

- [ ] Next.js + TypeScript project setup
- [ ] Tailwind CSS + shadcn/ui component system
- [ ] Authentication flow (login → JWT cookie)
- [ ] Dashboard layout with sidebar navigation
- [ ] **Daily Brief page** — actionable summary, top moves
- [ ] **Jobs page** — table with filters, score badges, status pipeline
- [ ] **Client Leads page** — similar to Jobs, with industry and pain point view
- [ ] **Review Queue page** — card-based draft review (not bulk-send)
- [ ] **Draft Detail page** — full draft, quality scores, context used
- [ ] Settings page — profile, config overview (read-only)
- [ ] Demo Mode banner — visible indicator when running on seeded data

---

## Phase 4 — Review Queue + Quality Guard UI

The core human-in-the-loop interaction, done right.

- [ ] Side-by-side: draft text | quality scores | context used
- [ ] Colour-coded quality indicators (pass/fail/pending per dimension)
- [ ] In-app editing with live quality re-score (calls Claude)
- [ ] Regenerate with different style in one click
- [ ] Approve button — disabled until Quality Guard passes
- [ ] Skip button — with optional reason
- [ ] Draft history: version comparison if regenerated
- [ ] Batch view: see all pending drafts with quality summary
- [ ] Export approved drafts to CSV

---

## Phase 5 — Demo Mode + Seeded Data

First-run experience and safe evaluation environment.

- [ ] Demo mode flag in config or env var
- [ ] `--seed-demo-data` wired to API endpoint (POST /seed, demo-only)
- [ ] Demo banner visible in all pages when demo data is loaded
- [ ] Clear demo data button in Settings
- [ ] All demo domains use `.test` — zero risk of reaching real people
- [ ] Demo mode blocks `--send-approved` entirely

---

## Phase 6 — Production Hardening

Making DobryBot safe and reliable for real use.

- [ ] Rate limiting on all API routes
- [ ] Input validation and sanitisation
- [ ] Full audit log: every user action logged with actor, timestamp, data
- [ ] Error monitoring (Sentry or equivalent)
- [ ] Health check endpoints
- [ ] Secrets management (env vars only — no secrets in DB or logs)
- [ ] HTTPS enforcement in production
- [ ] Daily send limit enforced at API level (not just CLI)
- [ ] Email opt-out tracking (replied with opt-out → archived, never contacted again)
- [ ] Follow-up cadence enforcement: max 2 messages per contact

---

## Phase 7 — Deployment

Launch DobryBot as a running product.

- [ ] Docker + docker-compose for local development
- [ ] Production Dockerfile (FastAPI + gunicorn)
- [ ] Static export or Vercel deployment for Next.js frontend
- [ ] PostgreSQL on Railway, Supabase, or self-hosted
- [ ] GitHub Actions CI: lint + tests on every push
- [ ] GitHub Actions CD: deploy on merge to main
- [ ] Environment-specific configs (dev / staging / prod)
- [ ] Basic monitoring: uptime check, error rate alert

---

## Future phases (backlog)

- Claude-assisted job scoring for ambiguous roles
- Company website scraping for deeper lead context
- Apollo.io / Clearbit as Hunter.io alternative
- Score history and drift tracking
- Email delivery of daily brief (opt-in)
- Team mode: multiple users, shared DB, per-user queues
- Response rate tracking (manual reply logging)
- Weekly summary report (PDF or Markdown)
