# DobryBot — Architecture

> Human-in-the-loop opportunity and growth assistant for CorosDev.
> This document describes the launch-ready system design.

---

## Overview

DobryBot is a full-stack platform with three layers:

```
┌─────────────────────────────────────────────────────┐
│  Next.js Frontend (TypeScript + Tailwind + shadcn)  │
│  Dashboard · Review Queue · Brief · Jobs · Leads    │
└───────────────────┬─────────────────────────────────┘
                    │ HTTP / JSON (REST API)
┌───────────────────▼─────────────────────────────────┐
│  FastAPI Backend (Python)                           │
│  Auth · Routers · Schemas · Safety enforcement      │
│  Audit log · Rate limiting · Quality Guard gate     │
└───────────────────┬─────────────────────────────────┘
                    │ SQLAlchemy / SQLModel
┌───────────────────▼─────────────────────────────────┐
│  Python Core Engine (existing — reused as-is)       │
│  scorer · humanizer · quality_guard · db            │
│  daily_brief · review_queue · answer_generator      │
│  seed_data · email_finder · cv_parser               │
└─────────────────────────────────────────────────────┘
                    │
        ┌───────────┴──────────────┐
        │                          │
   SQLite (local dev)        PostgreSQL (prod)
```

The existing Python CLI core is **not replaced** — it becomes the service layer. The FastAPI layer wraps it and exposes REST endpoints. The Next.js layer consumes those endpoints.

---

## Technology stack

### Backend

| Component | Technology | Rationale |
|---|---|---|
| Web framework | FastAPI | Async, typed, auto-docs, fast |
| ORM | SQLAlchemy 2 / SQLModel | Typed models, Alembic migrations |
| DB (local dev) | SQLite | Zero-config, existing schema reused |
| DB (production) | PostgreSQL | Concurrent users, full ACID |
| Migrations | Alembic | Replaces manual migration system |
| Auth | JWT (python-jose + passlib) | Stateless, single-user to start |
| Validation | Pydantic v2 | Already used in the project |
| Task runner | None initially (sync FastAPI) | Add Celery/ARQ when needed |
| LLM integration | Anthropic SDK (existing) | Claude for drafts + quality scoring |

### Frontend

| Component | Technology | Rationale |
|---|---|---|
| Framework | Next.js 14 (App Router) | SSR/SSG, TypeScript first |
| Language | TypeScript | Type safety across API boundary |
| Styling | Tailwind CSS | Utility-first, fast to build |
| Components | shadcn/ui | Accessible, composable, unstyled base |
| State | React Query (TanStack) | Server state, caching, optimistic UI |
| Forms | React Hook Form + Zod | Typed forms, matches Pydantic schemas |
| Charts | Recharts or Tremor | Score visualisations |
| Auth | Next-Auth or custom JWT cookie | Paired with FastAPI JWT |

### Infrastructure

| Component | Technology |
|---|---|
| Containerisation | Docker + docker-compose |
| CI | GitHub Actions |
| CD | GitHub Actions → Fly.io / Railway |
| Frontend hosting | Vercel (or same Docker) |
| Secrets | Environment variables only |
| Monitoring | Sentry (errors) + Uptime Robot |

---

## Data model

The existing SQLite schema is the source of truth. SQLAlchemy models will map 1:1 to these tables:

### `applied_jobs`

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `job_url` | TEXT UNIQUE | Source URL — dedup key |
| `company` | TEXT | |
| `title` | TEXT | |
| `location` | TEXT | |
| `domain` | TEXT | For Hunter.io lookup |
| `status` | TEXT | `discovered → scored → draft_ready → needs_review → approved → applied` |
| `job_score` | INTEGER | 0–100 rule-based |
| `score_label` | TEXT | `high_priority / good_fit / maybe / low_fit` |
| `notes` | TEXT | |
| `applied_at` | TEXT | ISO timestamp |

### `leads`

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `domain` | TEXT | Dedup key |
| `company` | TEXT | |
| `contact_name` | TEXT | |
| `contact_email` | TEXT | |
| `contact_role` | TEXT | |
| `industry` | TEXT | |
| `pain_points` | JSON | List of pain signal strings |
| `context_data` | JSON | Enrichment data |
| `lead_score` | INTEGER | 0–100 |
| `score_label` | TEXT | |
| `status` | TEXT | `discovered → scored → draft_ready → needs_review → approved → contacted` |

### `outreach`

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `job_url` | TEXT | FK to applied_jobs or `lead:<id>` |
| `company` | TEXT | |
| `job_title` | TEXT | |
| `to_email` | TEXT | |
| `to_name` | TEXT | |
| `subject` | TEXT | |
| `body` | TEXT | |
| `outreach_type` | TEXT | `job / client` |
| `style` | TEXT | One of 5 message styles |
| `status` | TEXT | `needs_review → approved → sent` (or `skipped / failed`) |
| `personalization_score` | INTEGER | Quality Guard dimension |
| `spam_risk_score` | INTEGER | Quality Guard dimension |
| `ai_sounding_score` | INTEGER | Quality Guard dimension |
| `quality_status` | TEXT | `pending / passed / failed` |
| `quality_reasons` | JSON | List of failure reasons |
| `send_recommendation` | TEXT | `send / revise / skip` |
| `context_used` | JSON | What context was used in generation |
| `generated_at` | TEXT | |
| `approved_at` | TEXT | NULL until approved |
| `sent_at` | TEXT | NULL until sent |
| `failure_reason` | TEXT | Stored on SMTP failure |

### `audit_log` (new — Phase 2)

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `action` | TEXT | `approve / skip / send / seed / clear / regenerate` |
| `entity_type` | TEXT | `outreach / job / lead` |
| `entity_id` | INTEGER | |
| `actor` | TEXT | User identifier |
| `timestamp` | TEXT | ISO UTC |
| `detail` | JSON | Action-specific metadata |

---

## API design

### Authentication

```
POST /auth/login          → { token: "..." }
POST /auth/logout
GET  /auth/me
```

### Core workflows

```
GET  /brief               → DailyBriefResponse
GET  /stats               → StatsResponse

GET  /jobs                → JobList (filter: status, score_min, score_max)
GET  /jobs/{id}
POST /jobs/discover       → triggers --discover-jobs (dry-run available)
POST /jobs/score          → triggers --score-jobs

GET  /leads               → LeadList (filter: status, score_min, industry)
GET  /leads/{id}
POST /leads/discover
POST /leads/score

GET  /queue               → OutreachList (filter: type, quality_status)
GET  /queue/{id}
POST /queue/{id}/approve  → Quality Guard checked — returns 409 if not passed
POST /queue/{id}/skip     → { reason?: string }
POST /queue/{id}/regenerate

POST /send/approved       → Sends all approved items (dry_run available, requires confirmation)

POST /demo/seed           → Seeds demo data (demo mode only)
POST /demo/clear          → Clears demo data (demo mode only)
```

### Safety rules enforced at API level

- `POST /queue/{id}/approve` returns `409 Conflict` if `quality_status != 'passed'` — no bypass
- `POST /send/approved` requires `{ confirm: true }` in the body — never auto-fires
- Demo endpoints are blocked unless `DEMO_MODE=true` in env
- All mutating actions are written to `audit_log`

---

## Frontend pages

| Page | Route | Purpose |
|---|---|---|
| Dashboard | `/` | Daily brief summary + top actions |
| Daily Brief | `/brief` | Full daily brief with sections A–G |
| Jobs | `/jobs` | Job pipeline table with filters |
| Job Detail | `/jobs/[id]` | Score breakdown, history, drafts |
| Client Leads | `/leads` | Lead pipeline table with filters |
| Lead Detail | `/leads/[id]` | Score, context, pain points, drafts |
| Review Queue | `/queue` | Card-based draft review |
| Draft Detail | `/queue/[id]` | Full draft + quality scores + edit |
| Safety Center | `/safety` | Audit log, safety status, blocked items |
| Settings | `/settings` | Profile, config overview |
| Demo Mode | `/settings/demo` | Seed/clear demo data |

---

## Safety architecture

Safety is enforced in layers — not a single gate that can be bypassed:

```
Layer 1 — Data layer (db.py)
  · No automatic status transitions
  · Status changes are explicit function calls only

Layer 2 — Core engine (review_queue.py, quality_guard.py)
  · approve_single() checks Quality Guard before any DB write
  · pending and failed quality_status are hard blocks
  · No force-approve path exists

Layer 3 — API layer (FastAPI routers)
  · /approve returns 409 if Quality Guard not passed
  · /send requires explicit confirmation body
  · Demo endpoints blocked unless DEMO_MODE=true
  · All mutations written to audit_log

Layer 4 — Frontend layer (Next.js)
  · Approve button disabled until quality_status = 'passed'
  · Send action requires a confirmation dialog (not just a button)
  · Demo mode banner always visible
  · No "send all" or "bulk approve" shortcut
```

No single layer bypass can enable automatic sending or applying.

---

## Demo mode

Demo mode is a first-class feature:

- Enabled by `DEMO_MODE=true` in environment
- `--seed-demo-data` (CLI) or `POST /demo/seed` (API) populates realistic fake data
- All demo records use `.test` domains — zero risk of real outreach
- Demo mode blocks `POST /send/approved` entirely
- Demo banner visible in all UI pages when demo data is active
- `clear_demo_data()` removes only `.test` domain records — safe to run alongside real data

---

## Existing Python core — reuse strategy

The Python core (`src/`) is kept as-is. The FastAPI layer calls it directly as a library:

```python
# FastAPI router calls core functions directly
from src.daily_brief import generate_brief
from src.db import get_jobs_by_status, get_needs_review
from src.seed_data import seed_demo_data
from src.quality_guard import QualityGuard
from src.scorer import JobScorer, LeadScorer
```

Benefits:
- 85 existing tests continue to pass unchanged
- No rewrite risk — battle-tested logic stays
- FastAPI adds the HTTP layer on top, not a replacement

When the core needs changes (e.g. for async), they are incremental and tested.
