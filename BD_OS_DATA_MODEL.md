# DobryBot BD OS — Data Model Proposal

## Design Principles

1. All entities have `id`, `created_at`, `updated_at` fields.
2. Foreign keys are stored as string IDs (UUID or slug) — no hard database joins in Phase 1.
3. All stores start as JSON files (consistent with existing pattern) and migrate to a database in Phase 3.
4. Enum values use snake_case strings for portability.
5. No real PII stored in demo seed data.

---

## Entities

### Company

The primary target entity — a business you want to engage.

```python
class Company:
    id: str                          # UUID
    name: str                        # "Acme Corp"
    domain: str | None               # "acme.com"
    industry: str | None             # "SaaS / DevTools"
    size_estimate: str | None        # "50-200", "1000+"
    headquarters: str | None         # "San Francisco, CA"
    tech_signals: list[str]          # ["AWS", "Kubernetes", "Python"]
    description: str | None
    linkedin_url: str | None
    website_url: str | None
    opportunity_score: int           # 0-100
    score_label: str                 # "hot" | "warm" | "cold" | "disqualified"
    icp_match: bool                  # Is this in our ICP?
    status: str                      # "identified" | "researched" | "qualified" | "engaged" | "active" | "closed"
    source: str | None               # How we found them: "manual" | "signal" | "import"
    notes: str                       # Free-text notes
    created_at: str                  # ISO datetime
    updated_at: str                  # ISO datetime
```

---

### Prospect

An individual decision maker or contact at a target company.

```python
class Prospect:
    id: str                          # UUID
    company_id: str                  # FK → Company.id
    company_name: str                # Denormalized for display
    name: str                        # "Jane Smith"
    title: str | None                # "VP of Engineering"
    seniority: str | None            # "C-suite" | "VP" | "Director" | "Manager" | "IC"
    linkedin_url: str | None
    email: str | None                # Only if known and consented
    pain_point_count: int            # Derived: how many pain points linked
    signal_count: int                # Derived: how many signals linked
    opportunity_score: int           # 0-100
    score_label: str                 # "hot" | "warm" | "cold"
    recommended_angle: str | None    # "Cost reduction via X", "Risk Y resolution"
    status: str                      # "identified" | "researched" | "engaged" | "active" | "closed"
    notes: str
    created_at: str
    updated_at: str
```

---

### DecisionMaker

Extended profile for a prospect who is a confirmed decision maker.

```python
class DecisionMaker:
    prospect_id: str                 # FK → Prospect.id (1:1)
    company_id: str                  # FK → Company.id
    budget_authority: bool | None
    technical_buyer: bool | None
    economic_buyer: bool | None
    champion: bool | None            # Internal advocate
    inferred_priorities: list[str]   # ["Reduce cloud costs", "Hire faster"]
    best_outreach_channel: str | None  # "email" | "linkedin" | "intro"
    best_angle: str | None
    context_notes: str               # Research notes, observations
    updated_at: str
```

---

### Signal

A market event or trigger that indicates potential buying intent or receptivity.

```python
class Signal:
    id: str                          # UUID
    company_id: str | None           # FK → Company.id (may be unlinked initially)
    company_name: str                # Denormalized
    prospect_id: str | None          # FK → Prospect.id (if person-specific)
    signal_type: str                 # "hiring" | "funding" | "leadership_change" |
                                     # "tech_change" | "competitive" | "pain_point" | "growth" | "other"
    summary: str                     # "Hiring 5 ML engineers — signals AI initiative"
    raw_content: str | None          # Original source text
    source: str | None               # "linkedin_job", "techcrunch", "manual", "csv_import"
    source_url: str | None
    relevance_score: int             # 0-100 — how relevant is this signal
    detected_at: str                 # When the signal event occurred (may differ from created_at)
    reviewed: bool                   # Has a human reviewed this signal?
    review_action: str | None        # "relevant" | "irrelevant" | "pending"
    created_at: str
    updated_at: str
```

---

### PainPoint

A specific pain point detected for a company or prospect.

```python
class PainPoint:
    id: str                          # UUID
    company_id: str                  # FK → Company.id
    prospect_id: str | None          # FK → Prospect.id (if person-specific)
    company_name: str                # Denormalized
    description: str                 # "Manual compliance reporting wastes 20+ hrs/week"
    category: str | None             # "operational" | "technical" | "financial" | "strategic"
    signal_source: str | None        # Which signal revealed this pain
    confidence: int                  # 0-100 — how confident we are this is real
    recommended_angle: str | None    # Suggested value prop angle to address this pain
    created_at: str
    updated_at: str
```

---

### Opportunity

A qualified prospect engagement with scoring and lifecycle tracking.

```python
class Opportunity:
    id: str                          # UUID
    company_id: str                  # FK → Company.id
    prospect_id: str | None          # FK → Prospect.id
    company_name: str                # Denormalized
    contact_name: str | None         # Denormalized
    score: int                       # 0-100
    score_label: str                 # "hot" | "warm" | "cold" | "disqualified"
    score_breakdown: dict            # {"icp_fit": 30, "signal_strength": 25, ...}
    stage: str                       # "identified" | "researched" | "qualified" |
                                     # "engaged" | "deal_packet" | "active" | "won" | "lost"
    pain_points: list[str]           # Top pain point descriptions
    value_proposition: str | None    # Why we're uniquely positioned to help
    recommended_action: str | None   # "Send intro via mutual connection", "Follow up on signal"
    deal_packet_id: str | None       # FK → DealPacket.id
    lost_reason: str | None
    won_notes: str | None
    notes: str
    created_at: str
    updated_at: str
```

---

### DealPacket

A comprehensive briefing document assembled for a specific deal or engagement.

```python
class DealPacket:
    id: str                          # UUID
    opportunity_id: str | None       # FK → Opportunity.id
    company_id: str | None           # FK → Company.id
    company_name: str
    contact_name: str | None
    contact_role: str | None
    engagement_type: str | None      # "new_business" | "expansion" | "partnership" | "intro"
    company_summary: str             # Brief company context
    pain_points: list[str]           # Key pain points addressed
    value_proposition: str           # Why us, why now
    talking_points: list[str]        # Key points for the conversation
    objection_handlers: list[str]    # Anticipated objections + responses
    outreach_draft: str              # Primary outreach message draft
    checklist: list[ChecklistItem]   # Execution steps
    status: str                      # "draft" | "review" | "approved" | "executed"
    notes: str
    created_at: str
    updated_at: str | None
```

---

### OutreachDraft

A personalized outreach message prepared for human review.

```python
class OutreachDraft:
    id: str                          # UUID
    deal_packet_id: str | None       # FK → DealPacket.id
    opportunity_id: str | None       # FK → Opportunity.id
    company_name: str
    contact_name: str
    contact_role: str
    message_type: str                # "email" | "linkedin" | "intro_request"
    subject: str | None              # For emails
    body: str                        # The message draft
    tone: str                        # "warm" | "direct" | "executive" | "technical"
    angle: str | None                # The pain point angle used
    personalization_score: int       # 0-100
    spam_risk_score: int             # 0-100 (lower is better)
    ai_sounding_score: int           # 0-100 (lower is better)
    quality_status: str              # "pass" | "review" | "blocked"
    quality_reasons: list[str]       # Reasons for quality flags
    status: str                      # "draft" | "review" | "approved" | "skipped"
    approved_at: str | None
    skip_reason: str | None
    generated_at: str
    updated_at: str
```

---

### ReviewItem

An item in the human review queue (wraps any reviewable output).

```python
class ReviewItem:
    id: str                          # UUID
    item_type: str                   # "outreach_draft" | "deal_packet" | "signal" | "opportunity"
    item_id: str                     # FK to the referenced item
    company_name: str                # Denormalized for display
    title: str                       # Display title for the review queue
    summary: str                     # One-line summary for reviewers
    quality_status: str              # "pass" | "review" | "blocked"
    quality_reasons: list[str]
    status: str                      # "pending" | "approved" | "skipped" | "needs_research"
    created_at: str
    reviewed_at: str | None
    review_note: str | None
```

---

### PipelineStage

Defines pipeline stage configuration (system-level, not per-record).

```python
class PipelineStage:
    slug: str                        # "identified" | "researched" | etc.
    label: str                       # Display label
    order: int                       # Sort order
    color: str                       # UI color hint: "gray" | "blue" | "violet" | "amber" | "green"
    is_terminal: bool                # Won/Lost stages
```

---

### Activity

Log of all actions taken on an opportunity or prospect.

```python
class Activity:
    id: str                          # UUID
    opportunity_id: str | None
    company_id: str | None
    prospect_id: str | None
    activity_type: str               # "note" | "email_sent" | "call" | "meeting" |
                                     # "deal_packet_created" | "stage_change" | "signal_detected"
    description: str
    outcome: str | None              # "positive" | "neutral" | "negative" | "no_response"
    occurred_at: str
    created_at: str
```

---

### Source

Configuration for signal and data sources (future Phase 3).

```python
class Source:
    id: str                          # UUID
    name: str                        # "LinkedIn Jobs RSS", "Crunchbase Export"
    source_type: str                 # "rss" | "csv_import" | "manual" | "webhook"
    config: dict                     # Source-specific configuration
    enabled: bool
    last_synced_at: str | None
    created_at: str
    updated_at: str
```

---

## Entity Relationships

```
Company ─────────────────────── 1:N ─── Prospect
Company ─────────────────────── 1:N ─── Signal
Company ─────────────────────── 1:N ─── PainPoint
Company ─────────────────────── 1:N ─── Opportunity
Company ─────────────────────── 1:N ─── DealPacket
Company ─────────────────────── 1:N ─── Activity

Prospect ────────────────────── 1:1 ─── DecisionMaker
Prospect ────────────────────── 1:N ─── Signal
Prospect ────────────────────── 1:N ─── PainPoint
Prospect ────────────────────── 1:N ─── Activity

Opportunity ─────────────────── 1:1 ─── DealPacket
Opportunity ─────────────────── 1:N ─── OutreachDraft
Opportunity ─────────────────── 1:N ─── Activity

DealPacket ──────────────────── 1:N ─── OutreachDraft

OutreachDraft ───────────────── 1:1 ─── ReviewItem
DealPacket ──────────────────── 1:1 ─── ReviewItem
Signal ──────────────────────── 1:1 ─── ReviewItem (optional)
```

---

## Existing Model Mapping

### Job → Opportunity (Phase 2 migration path)

| Job field | Opportunity field |
|---|---|
| id | id |
| title | contact_name (role pursued) |
| company | company_name |
| job_score | score |
| score_label | score_label |
| status | stage |
| notes | notes |
| context_data | score_breakdown |

### Lead → Company + Prospect (Phase 2 migration path)

| Lead field | Company field | Prospect field |
|---|---|---|
| domain | domain | — |
| company | name | company_name |
| industry | industry | — |
| contact_name | — | name |
| contact_email | — | email |
| contact_role | — | title |
| pain_points | — | (linked PainPoints) |
| lead_score | opportunity_score | opportunity_score |
| score_label | score_label | score_label |
| status | status | status |

### ApplicationPacket → DealPacket (Phase 2 migration path)

| ApplicationPacket field | DealPacket field |
|---|---|
| target_job_title | engagement_type / talking_points context |
| target_company | company_name |
| job_description | → PainPoint descriptions |
| resume_markdown | value_proposition |
| cover_letter_draft | outreach_draft |
| tailored_summary | company_summary |
| skills_emphasis | talking_points |
| fit_summary | value_proposition |
| talking_points | talking_points |
| checklist | checklist |
| status | status |
| notes | notes |

---

## Storage Strategy

### Phase 1 (Current)
- All new BD entities: JSON file stores (matching existing pattern)
- Files: `data/prospects.json`, `data/companies.json`, `data/signals.json`, etc.
- Pattern mirrors `PacketStore`, `ResumeStore`, `ProfileStore`

### Phase 2
- Migrate to SQLite with SQLModel/SQLAlchemy
- Keep JSON stores as migration source
- Maintain backward compatibility on all API endpoints during migration

### Phase 3
- Optional: PostgreSQL for multi-user / production deployments
- JSON stores remain valid for single-user local mode

---

## ChecklistItem (Shared)

```python
class ChecklistItem:
    text: str
    done: bool
```

Used by both `ApplicationPacket` (existing) and `DealPacket` (new).
