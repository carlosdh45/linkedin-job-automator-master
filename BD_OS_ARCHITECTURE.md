# DobryBot BD OS — Architecture

## System Overview

DobryBot BD OS is organized into three layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    Intelligence Layer                        │
│   Signal Ingestion → Company Research → Pain Point Detection│
│   Prospect Mapping → Decision Maker Profiles                │
├─────────────────────────────────────────────────────────────┤
│                   Qualification Layer                        │
│   Opportunity Scoring → ICP Fit → Prioritization           │
│   Recommended Actions → Next Best Move                      │
├─────────────────────────────────────────────────────────────┤
│                    Execution Layer                           │
│   Message Studio → Deal Packets → Review Queue             │
│   Pipeline Tracking → Activity Logging                      │
└─────────────────────────────────────────────────────────────┘
```

All AI-generated content flows through the Review Queue before any human action is taken. Nothing auto-sends.

---

## Core Modules

### 1. Dashboard — Command Center

**Purpose**: Real-time overview of BD activity, top priorities, and recommended actions.

**Key sections**:
- Qualified opportunities (count + top items)
- High signal prospects list
- Companies with detected pain points
- Recommended next actions
- Drafts for review queue
- Pipeline snapshot

**Frontend**: `pages/index.vue`
**Backend (Phase 1)**: Reuses `/api/daily-brief` and `/api/stats`
**Backend (Phase 2)**: New `/api/bd-brief` endpoint with BD-specific aggregates

---

### 2. Prospect Intelligence

**Purpose**: Decision maker profiles with full research context.

**Data shown**: Name, company, role, signal count, pain point count, opportunity score, recommended angle, engagement history.

**Actions**: Add note, create outreach draft (→ Review Queue), link to opportunity, move pipeline stage.

**Frontend**: `pages/prospects.vue`
**Backend (Phase 2)**:
```
GET  /api/prospects
POST /api/prospects
GET  /api/prospects/:id
PUT  /api/prospects/:id
```

---

### 3. Company Profiles

**Purpose**: Aggregated intelligence for each target company.

**Data shown**: Company name, domain, industry, size estimate, detected tech signals, key contacts, pain points, recent signals, opportunity score.

**Actions**: Add to pipeline, assign prospect, create deal packet, mark as ICP match.

**Frontend**: `pages/companies.vue`
**Backend (Phase 2)**:
```
GET  /api/companies
POST /api/companies
GET  /api/companies/:id
PUT  /api/companies/:id
GET  /api/companies/:id/contacts
GET  /api/companies/:id/signals
```

---

### 4. Decision Maker Profiles

**Purpose**: Rich individual contact profiles within target companies.

**Data shown**: Name, title, company, inferred seniority, estimated priorities, best outreach angle, LinkedIn context.

**Linked to**: Prospect Intelligence module, Company Profiles.

**Backend (Phase 3)**: Nested under `GET /api/companies/:id/contacts` and `/api/prospects/:id`.

---

### 5. Signals

**Purpose**: Detect and surface events that indicate buying intent or receptivity.

**Signal types**:
- `hiring` — key role postings (e.g., hiring a Head of Security → security pain)
- `funding` — new funding round (growth, new budget)
- `leadership_change` — new CXO, new VP (new agenda, new budget)
- `tech_change` — technology adoption or retirement signals
- `competitive` — competitor loss, contract expiry signals
- `pain_point` — public content, reviews, job descriptions revealing pain
- `growth` — headcount growth, new office, product launch

**Phase 1**: Manual signal entry, placeholder feed UI.
**Phase 2**: Configurable signal sources (RSS, CSV import, manual).
**Phase 3**: Automated signal detection from configured sources.

**Frontend**: `pages/signals.vue`
**Backend (Phase 2)**:
```
GET  /api/signals
POST /api/signals
PUT  /api/signals/:id/review
```

---

### 6. Pain Points

**Purpose**: Catalog and link detected pain points to companies and prospects.

**Data**: Company, pain point description, signal source, confidence score, recommended angle.

**Linked to**: Company Profiles, Opportunity Scoring, Message Studio context.

**Backend (Phase 3)**:
```
GET  /api/pain-points
POST /api/pain-points
GET  /api/pain-points?company_id=:id
```

---

### 7. Opportunity Scoring

**Purpose**: Qualify and rank opportunities by fit, signal, and readiness.

**Scoring dimensions**:
- ICP fit (industry, company size, stage)
- Signal strength (recency, type, volume)
- Pain point match (count, confidence, alignment)
- Decision maker access (known contact vs. cold)
- Timing indicators (funding date, hiring surge, leadership change recency)

**Output**: Opportunity score (0–100), score label (hot / warm / cold / disqualified), recommended action.

**Frontend**: `pages/opportunities.vue`
**Backend (Phase 2)**:
```
GET  /api/opportunities
POST /api/opportunities
GET  /api/opportunities/:id
PUT  /api/opportunities/:id/stage
POST /api/opportunities/:id/score
```

---

### 8. Deal Origination

**Purpose**: Manage the lifecycle from first signal to active deal.

**Stages**:
```
Identified → Researched → Qualified → Engaged → Deal Packet Sent → Active → Won / Lost
```

**Linked to**: Pipeline, Deal Packets, Prospect Intelligence.
**Backend (Phase 2)**: Opportunity records with stage field, linked to company and prospect.

---

### 9. Message Studio

**Purpose**: Generate, refine, and prepare personalized outreach for human review.

**Features**:
- Context-aware draft generation (company + pain point + angle)
- Multi-format: email, LinkedIn message, warm intro request
- Tone controls: warm, direct, executive, technical, concise
- Quality scoring: personalization score, spam risk score, AI-sounding check
- All output → Review Queue (never direct send)

**Phase 1**: Placeholder workspace with mock draft preview.
**Phase 2**: Connected to Company + Prospect context from backend.
**Phase 3**: AI generation using configured local LLM or API.

**Frontend**: `pages/message-studio.vue`
**Backend (Phase 2)**:
```
POST /api/message-studio/draft
GET  /api/message-studio/drafts
GET  /api/message-studio/drafts/:id
```

---

### 10. Deal Packet

**Purpose**: Comprehensive briefing document for each deal or prospect engagement.

**Contains**:
- Company profile summary
- Key contacts and roles
- Detected pain points with confidence
- Tailored value proposition
- Message angle rationale
- Talking points
- Outreach draft(s)
- Execution checklist
- Notes

**Evolution from**: Application Packet (same human-in-the-loop model, BD context).

**Migration path**: `/api/application-packet` → `/api/deal-packets` with extended BD fields. Both endpoints coexist during transition.

**Frontend**: `pages/deal-packets.vue`
**Backend (Phase 2)**:
```
GET  /api/deal-packets
POST /api/deal-packets
GET  /api/deal-packets/:id
PUT  /api/deal-packets/:id
POST /api/deal-packets/generate
```

---

### 11. Review Queue

**Purpose**: Human-in-the-loop approval gate for all AI-generated output.

**Items reviewed**: outreach drafts, deal packets, generated analyses.
**Actions**: Approve, Skip, Needs Research.
**Approval is always explicit — nothing sends or executes automatically.**

**Frontend**: `pages/review-queue.vue` (existing, unchanged)
**Backend**: `GET /api/review-queue` (existing, unchanged)

---

### 12. Pipeline

**Purpose**: Visual and tabular view of active deals across lifecycle stages.

**Stages**: Prospect → Qualified → Engaged → Deal Packet → Active → Won / Lost

**Metrics**: Deals per stage, average stage velocity, win rate.

**Frontend**: `pages/pipeline.vue`
**Backend (Phase 3)**:
```
GET /api/pipeline
GET /api/pipeline/summary
PUT /api/pipeline/:opportunity_id/stage
```

---

### 13. Execution Plan (Future)

**Purpose**: Daily and weekly prioritized action list.

**Drives**: Recommended Actions widget on Command Center dashboard.
**Backend (Phase 3)**: Derived from opportunity scores + signal recency + pipeline stage.

---

### 14. Settings

**Purpose**: Configure DobryBot behavior, data sources (future), safety rules.

**Phase 1**: Existing settings page, unchanged.
**Frontend**: `pages/settings.vue` (existing)

---

## Frontend Structure

```
frontend/
  pages/
    index.vue              # BD Command Center (dashboard)        ← Updated Phase 1
    prospects.vue          # Prospect Intelligence                ← New Phase 1
    companies.vue          # Company Profiles                     ← New Phase 1
    signals.vue            # Signals Feed                         ← New Phase 1
    opportunities.vue      # Opportunity Scoring                  ← New Phase 1
    pipeline.vue           # Pipeline View                        ← New Phase 1
    message-studio.vue     # Message Studio                       ← New Phase 1
    deal-packets.vue       # Deal Packets                         ← New Phase 1
    review-queue.vue       # Review Queue                         existing
    daily-brief.vue        # Intelligence Brief                   existing
    jobs.vue               # Target Roles (legacy)                existing
    leads.vue              # Leads feed (legacy)                  existing
    profile.vue            # Candidate Profile (legacy)           existing
    resume.vue             # Resume Studio (legacy)               existing
    application-packet.vue # Application Packet (legacy)         existing
    safety.vue             # Safety Center                        existing
    settings.vue           # Settings                             existing
    account.vue            # Account                              existing
  layouts/
    default.vue            # Navigation sidebar                   ← Updated Phase 1
  types/
    index.ts               # Type definitions                     ← Extended Phase 1
  composables/
    useApi.ts              # API layer                            existing
```

---

## Backend Structure

```
backend/
  api/
    # Existing — Phase 1 (keep, do not modify)
    health.py
    daily_brief.py
    jobs.py
    leads.py
    review.py
    stats.py
    profile.py
    resume.py
    application_packet.py
    cv_import.py
    auth.py
    demo.py

    # Phase 2 — New BD modules
    prospects.py           # Prospect Intelligence API
    companies.py           # Company Profiles API
    signals.py             # Signals API
    opportunities.py       # Opportunity Scoring + Deal Origination API
    deal_packets.py        # Deal Packets API (extends application_packet)
    message_studio.py      # Message Studio draft API
    pipeline.py            # Pipeline tracking API

  models/
    # Existing (keep)
    application_packet.py
    cv_import.py
    profile.py
    resume_profile.py

    # Phase 2 — New BD models
    prospect.py
    company.py
    signal.py
    opportunity.py
    deal_packet.py
    outreach_draft.py
    pipeline.py

  services/
    # Existing (keep)
    approval.py
    cv_extractor.py
    cv_importer.py
    packet_generator.py
    packet_store.py
    profile_store.py
    resume_generator.py
    resume_store.py

    # Phase 2 — New BD services
    prospect_store.py
    company_store.py
    signal_store.py
    opportunity_scorer.py
    deal_packet_generator.py
    message_studio.py
```

---

## Safety Architecture

All AI-generated content flows through the Review Queue:

```
Signal Detection
       ↓
Company Research + Pain Point Analysis
       ↓
Opportunity Scoring
       ↓
Context Assembly (Company + Pain Points + Angle)
       ↓
Deal Packet Generation
       ↓
Message Draft Generation
       ↓
Quality Scoring (local — personalization, spam risk, AI-sounding)
       ↓
Review Queue (human gate — explicit approval required)
       ↓
Approved Draft (ready to copy/use manually — never auto-sent)
```

**Non-negotiable invariants**:
1. No step bypasses human review
2. No step auto-sends or auto-submits
3. All external API calls require explicit user configuration
4. Quality scoring gates block low-quality output before human review
5. Demo seed data uses only fake/test domains — never real companies or emails
