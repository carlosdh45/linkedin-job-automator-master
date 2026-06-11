# DobryBot Frontend

Nuxt 3 + Vue 3 + TypeScript + Tailwind CSS dashboard for DobryBot.  
Human-in-the-loop design — never sends or applies automatically.

## Stack

- **Nuxt 3** (SPA mode, SSR disabled)
- **Vue 3** Composition API
- **TypeScript** (strict mode)
- **Tailwind CSS** via `@nuxtjs/tailwindcss`

## Prerequisites

- Node.js 18+
- npm 9+
- DobryBot FastAPI backend running on port 8000

## Install

```bash
cd frontend
npm install
```

## Run backend

```bash
# From project root
uvicorn backend.main:app --reload --port 8000
```

Swagger docs: http://localhost:8000/docs

## Run frontend

```bash
cd frontend
npm run dev
```

Frontend: http://localhost:3000

## Configure API URL

Copy `.env.example` to `.env` and set the backend URL:

```bash
cp .env.example .env
# Edit .env — default is http://localhost:8000
```

Environment variable:

```
NUXT_PUBLIC_API_BASE=http://localhost:8000
```

Do **not** commit `.env` to version control.

## Build for production

```bash
npm run build
npm run preview
```

## Type check

```bash
npm run typecheck
```

## Pages

| Route | Description |
|---|---|
| `/` | Dashboard overview, stats, top opportunities |
| `/daily-brief` | Daily opportunity brief |
| `/jobs` | Jobs list with status filters |
| `/leads` | Leads list with status filters |
| `/review-queue` | Human review with approve / skip / needs-research |
| `/safety` | Safety Center — rules and guarantees |
| `/settings` | Settings placeholder |

## Safety rules (enforced by backend, visible in UI)

- **No send button exists.** The Review Queue has Approve, Skip, and Needs Research — no Send.
- **No apply button exists.** LinkedIn application paths are permanently removed.
- **Approve ≠ Send.** Approving a draft marks it as human-reviewed locally. Nothing is transmitted.
- **Quality Guard is mandatory.** Approving a draft that has not passed Quality Guard returns HTTP 422.
- **Human approval required** for every action in the Review Queue.
- Confirmation dialogs appear before any Review Queue action.

## API endpoints used

| Method | Path | Purpose |
|---|---|---|
| GET | /health | Backend health check |
| GET | /api/stats | Database statistics |
| GET | /api/daily-brief | Daily opportunity summary |
| GET | /api/jobs | All jobs (optional `?status=`) |
| GET | /api/leads | All leads (optional `?status=`) |
| GET | /api/review-queue | Drafts pending review |
| POST | /api/drafts/{id}/approve | Approve a draft (Quality Guard enforced) |
| POST | /api/drafts/{id}/skip | Skip a draft |
| POST | /api/drafts/{id}/needs-research | Flag for research |
| POST | /api/demo/seed | Seed safe demo data |
| POST | /api/demo/clear | Clear demo records |
