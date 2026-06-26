# DobryBot — Product Pivot: Business Development Operating System

## Executive Summary

DobryBot is pivoting from a career assistant and resume preparation tool to an AI-powered **Business Development Operating System (BD OS)**. The new direction transforms how teams find, qualify, and engage with prospects — moving from manual CRM hygiene to an intelligence-first deal origination engine.

---

## Old vs. New Positioning

| Dimension | Old Direction | New Direction |
|---|---|---|
| Core persona | Job seeker | Founder, BD team, sales professional |
| Primary job | Prepare resume and apply to jobs | Find, qualify, and engage right-fit prospects |
| Output | Application packets, cover letters | Deal packets, outreach drafts, deal intelligence |
| Value proposition | Make you look great on paper | Surface opportunities others miss |
| Competition | Resume builders, applicant trackers | Apollo, Clay, Salesforce, HubSpot |
| Differentiation | Human-in-the-loop quality control | Signal-driven intelligence + quality gate |
| Data source | Candidate's own profile | Market signals, company research, contact intelligence |

---

## Target Users

1. **Founders** — researching markets, identifying early customers, validating BD hypotheses
2. **Business Development Teams** — sourcing deals, managing prospect pipelines
3. **Sales Teams** — prospecting, qualification, personalized outreach
4. **Advisors and Consultants** — identifying clients, positioning services
5. **Private Equity Firms** — deal sourcing, market mapping
6. **Small Businesses** — replacing manual outreach with systematic BD
7. **Technology Services Companies** — new client acquisition
8. **CorosDev Internal BD Team** — primary initial user group

---

## Core Jobs to Be Done

1. **Find the right prospects** — surface companies and decision makers worth engaging
2. **Research companies and contacts** — build context before reaching out
3. **Detect pain points** — identify signals that indicate buying intent or receptivity
4. **Qualify opportunities** — score and prioritize prospects based on fit and signal strength
5. **Decide who to contact** — determine the right decision maker and timing
6. **Know why to contact them** — identify the most relevant angle for each prospect
7. **Craft the right message** — generate personalized, relevant outreach
8. **Prepare deal packets** — build comprehensive briefings for deal execution
9. **Close better deals** — maintain context across the full deal lifecycle

---

## Main Workflows

### 1. Intelligence → Qualification
- Ingest company and contact data
- Detect signals (hiring, tech changes, funding, pain points)
- Score opportunities automatically
- Surface high-priority prospects in the Command Center

### 2. Research → Preparation
- Build company profiles
- Map decision makers
- Identify pain points and messaging angles
- Prepare deal context for execution

### 3. Message → Review
- Generate personalized outreach drafts using company + pain point + angle context
- Apply quality scoring (personalization, spam risk, AI-sounding check)
- Route to human review queue
- **Never auto-send**

### 4. Deal Execution
- Assemble deal packets with all context in one place
- Track pipeline stages
- Log activities and outcomes
- Learn what works across deals

---

## Product Principles

1. **Signal over noise** — surface what matters, suppress what doesn't
2. **Intelligence before outreach** — research before messaging, always
3. **Quality gate on all output** — human review before any action
4. **Context drives personalization** — use real signals to craft real messages
5. **Human-in-the-loop always** — all drafts require explicit human approval
6. **Local-first** — no external API calls unless explicitly configured by the user
7. **Privacy by design** — no platform scraping, no unauthorized data collection
8. **Premium quality** — every output must meet a high bar for professionalism

---

## Safety Principles

1. No auto-send functionality of any kind
2. No mass outbound automation
3. No aggressive platform scraping
4. No bypass of human review
5. No hidden AI calls
6. No external API calls in Phase 1
7. All outreach drafts go to Review Queue before any action
8. "Drafts prepared for manual review" is the permanent model
9. Every AI-generated output is labeled as such
10. No real company data stored in the demo seed

---

## Why This Is Not a Traditional CRM

Traditional CRMs are databases that store contacts and move deals across columns. They are **reactive tools** — you put data in, and the CRM shows it back to you organized. They require manual hygiene, manual research, and manual judgment.

DobryBot is **proactive**: it surfaces intelligence, detects signals, scores opportunities, and suggests actions. The CRM layer is the *output* of the intelligence layer, not the product itself.

A CRM tells you what you already know. DobryBot tells you what to do next and why.

---

## Why This Is Not Just Lead Generation

Lead generation tools give you lists. DobryBot gives you **understanding**.

The difference:
- Lead gen: "Here are 500 companies in your ICP"
- DobryBot: "These 12 companies are hiring engineers in your stack, had a leadership change last month, and their competitor just raised a round — here's who to talk to, why now, and what angle to use"

Lead generation is a commodity. Deal intelligence is the moat.

---

## Why This Is Not Apollo with AI

Apollo and similar tools bolt AI onto existing lead databases. DobryBot is built **intelligence-first**:

| Apollo/Clay | DobryBot |
|---|---|
| Finds contacts → exports CSV | Contextualizes contacts → builds deal packets |
| Automates sequences | Drafts for human review |
| Relies on database freshness | Derives context from signals |
| Measures email open rates | Measures deal quality and outcomes |
| Optimizes for volume | Optimizes for signal quality |

DobryBot earns trust through output quality, not feature checklists.

---

## How DobryBot Becomes a Business Development Operating System

A Business Development OS is the **single source of truth** for all BD activity. It:

1. **Ingests signals** — market noise, competitive data, trigger events, hiring patterns
2. **Builds intelligence** — company profiles, contact maps, pain point analysis
3. **Scores and prioritizes** — which opportunities to pursue and why, not just who
4. **Prepares for execution** — deal packets, message drafts, talking points, checklists
5. **Routes for review** — human-in-the-loop quality gate, no auto-action
6. **Tracks execution** — pipeline stages, activities, outcomes
7. **Learns and improves** — what worked, what didn't, patterns over time

The "OS" framing means it is not one feature — it is the **operating environment** for all BD activity. Every prospect interaction, every deal, every message starts and ends in DobryBot.

---

## Application Packet → Deal Packet Migration Path

The existing Application Packet module is the closest ancestor to the Deal Packet concept:

| Application Packet | Deal Packet |
|---|---|
| target_job_title | target_role / engagement_type |
| target_company | target_company |
| job_description | pain_points + company_context |
| resume_markdown | value_proposition |
| cover_letter_draft | outreach_draft |
| tailored_summary | company_summary |
| talking_points | talking_points |
| checklist | execution_checklist |

The human-in-the-loop model, quality gate, and draft review pattern carry over unchanged.

**Phase 2 migration**: Create `/api/deal-packets` endpoint that wraps and extends the application packet model with BD-specific fields. The old `/api/application-packet` endpoint remains until migration is complete.

---

## Phase Roadmap

| Phase | Focus | Status |
|---|---|---|
| Phase 1 (current) | Strategic pivot foundation — documents, navigation, placeholder UI | In progress |
| Phase 2 | BD data models in backend — Prospect, Company, Signal, Opportunity, DealPacket | Next |
| Phase 3 | Intelligence engine — scoring, pain point detection, signal analysis | Future |
| Phase 4 | Message Studio — context-aware draft generation | Future |
| Phase 5 | Pipeline tracking and deal lifecycle management | Future |
| Phase 6 | Integrations — configurable signal sources, optional external enrichment | Future |
