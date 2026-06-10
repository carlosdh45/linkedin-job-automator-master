# DobryBot Launch Plan

## Product Vision

DobryBot is a safe, human-in-the-loop opportunity and growth assistant for CorosDev. It discovers job opportunities and client leads, scores them, generates reviewable drafts, and surfaces them for human review and approval — but it never acts on your behalf without explicit human sign-off. Every outreach message is a draft until a human approves it. Every action is visible, reversible, and logged.

DobryBot is not an automation bot. It is a decision-support platform.

## Non-Negotiable Safety Principles

- No automatic email sending
- No automatic job applying
- No direct LinkedIn submission
- No Quality Guard bypass
- No approving failed or pending drafts
- No secrets committed
- All risky actions logged
- Demo mode makes no external calls

## Phase 0 — Safe CLI Core

Current completed state:

- Python CLI core
- SQLite local DB
- Daily Brief
- Review Queue
- Quality Guard
- Seed demo data
- Safety-disabled legacy commands
- 85/85 tests passing

Acceptance criteria:

- Tests pass
- Demo data works
- Daily Brief shows useful data
- Review Queue works
- Dangerous commands remain disabled

## Phase 1 — Backend API Foundation

Goal:
Add FastAPI backend around the existing Python core.

Scope:

- `backend/` folder
- FastAPI app
- API health check
- API config loading
- Service layer wrapping existing core modules
- SQLite local support
- Pydantic schemas
- Audit log foundation
- Demo mode support

Initial endpoints:

- GET /health
- GET /api/stats
- GET /api/daily-brief
- GET /api/jobs
- GET /api/leads
- GET /api/review-queue
- POST /api/demo/seed
- POST /api/demo/clear
- POST /api/drafts/{id}/approve
- POST /api/drafts/{id}/skip
- POST /api/drafts/{id}/needs-research

Safety:

- No send endpoint in Phase 1
- No apply endpoint ever
- Approval endpoint must enforce Quality Guard

Acceptance criteria:

- API starts locally
- API returns seeded demo data
- Tests pass
- No external calls in demo mode

## Phase 2 — Web App Foundation

Goal:
Build production-quality web UI.

Stack:

- Next.js
- TypeScript
- Tailwind CSS
- Component library or clean internal UI components

Pages:

- Dashboard
- Daily Brief
- Jobs
- Client Leads
- Review Queue
- Safety Center
- Settings/Profile

Acceptance criteria:

- Web app loads locally
- Connects to FastAPI
- Shows seeded demo data
- No send button
- No apply button
- Safety Center is visible

## Phase 3 — Review and Approval Workflow

Goal:
Make human-in-the-loop review excellent.

Features:

- Draft detail view
- Quality Guard score display
- Approve, skip, needs research
- Edit draft before approval
- Audit log entries
- Confirmation dialogs for approval
- Block failed/pending drafts

Acceptance criteria:

- Failed/pending drafts cannot be approved
- Passed drafts can be approved
- Every action is logged
- No sending occurs

## Phase 4 — Profile and Scoring Improvements

Goal:
Make scoring and recommendations smarter.

Features:

- Profile editor
- Target role weights
- Ideal client profile settings
- Skill matching
- Client ICP matching
- Recommendation explanations
- Better ranking logic

Acceptance criteria:

- Profile changes affect scoring
- Daily Brief explains why each item matters
- No invented facts

## Phase 5 — Integrations in Controlled Mode

Goal:
Add external discovery carefully.

Possible integrations:

- Job source CSV import
- Manual lead CSV import
- Hunter.io enrichment only after explicit user action
- Optional email draft export
- Optional CRM export

Rules:

- External calls require explicit action
- No automatic sending
- No automatic applying
- No scraping that violates platform rules

Acceptance criteria:

- Integrations are off by default
- User must trigger external calls
- Logs show every external call

## Phase 6 — Production Hardening

Goal:
Prepare for real deployment.

Features:

- Auth
- Roles and permissions
- PostgreSQL support
- Migrations
- Environment validation
- Structured logging
- Error handling
- Rate limiting
- Backup strategy
- Deployment scripts
- Security review

Acceptance criteria:

- No secrets in repo
- Production env documented
- DB migrations work
- Access controlled

## Phase 7 — Internal Beta

Goal:
Use DobryBot safely inside CorosDev.

Beta process:

- Demo with seeded data
- CTO review
- Internal testing
- Manual CSV imports
- Review Queue validation
- Feedback collection
- Iteration plan

Acceptance criteria:

- Douglas/CTO can review working UI
- Team understands safety constraints
- No real outreach without approval

## Phase 8 — Launch

Goal:
Launch DobryBot as a CorosDev internal product, then evaluate external SaaS potential.

Launch checklist:

- Documentation complete
- Tests passing
- Deployment ready
- Demo data reset
- Audit logs enabled
- Auth enabled
- Safety Center visible
- No auto-send/apply paths

## Immediate Next Steps

1. Commit current stable CLI core.
2. Create backend FastAPI skeleton.
3. Expose stats/daily brief/review queue via API.
4. Build web dashboard shell.
5. Demo with seeded data.
6. Review with Douglas.
