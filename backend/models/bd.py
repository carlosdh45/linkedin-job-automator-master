from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid


def _now() -> str:
    return datetime.utcnow().isoformat()


def _uid() -> str:
    return str(uuid.uuid4())


# ── Company ───────────────────────────────────────────────────────────────────

class BDCompany(BaseModel):
    id: str = Field(default_factory=_uid)
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    size_estimate: Optional[str] = None
    tech_signals: List[str] = Field(default_factory=list)
    pain_points: List[str] = Field(default_factory=list)
    opportunity_score: int = 0
    score_label: str = "cold"
    icp_match: bool = False
    status: str = "identified"
    notes: str = ""
    created_at: str = Field(default_factory=_now)
    updated_at: str = Field(default_factory=_now)


class BDCompanyCreate(BaseModel):
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    size_estimate: Optional[str] = None
    tech_signals: List[str] = Field(default_factory=list)
    pain_points: List[str] = Field(default_factory=list)
    icp_match: bool = False
    status: str = "identified"
    notes: str = ""


class BDCompanyUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None
    size_estimate: Optional[str] = None
    tech_signals: Optional[List[str]] = None
    pain_points: Optional[List[str]] = None
    icp_match: Optional[bool] = None
    status: Optional[str] = None
    notes: Optional[str] = None


# ── Prospect ──────────────────────────────────────────────────────────────────

class BDProspect(BaseModel):
    id: str = Field(default_factory=_uid)
    company_id: str
    company_name: str
    name: str
    title: Optional[str] = None
    seniority: Optional[str] = None
    linkedin_url: Optional[str] = None
    pain_point_count: int = 0
    signal_count: int = 0
    opportunity_score: int = 0
    score_label: str = "cold"
    recommended_angle: Optional[str] = None
    status: str = "identified"
    notes: str = ""
    created_at: str = Field(default_factory=_now)
    updated_at: str = Field(default_factory=_now)


class BDProspectCreate(BaseModel):
    company_id: str
    company_name: str
    name: str
    title: Optional[str] = None
    seniority: Optional[str] = None
    linkedin_url: Optional[str] = None
    pain_point_count: int = 0
    signal_count: int = 0
    recommended_angle: Optional[str] = None
    status: str = "identified"
    notes: str = ""


class BDProspectUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    seniority: Optional[str] = None
    linkedin_url: Optional[str] = None
    pain_point_count: Optional[int] = None
    signal_count: Optional[int] = None
    recommended_angle: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


# ── Signal ────────────────────────────────────────────────────────────────────

class BDSignal(BaseModel):
    id: str = Field(default_factory=_uid)
    company_id: Optional[str] = None
    company_name: str
    prospect_id: Optional[str] = None
    signal_type: str = "other"
    summary: str
    source: Optional[str] = None
    relevance_score: int = 50
    detected_at: str = Field(default_factory=lambda: datetime.utcnow().date().isoformat())
    reviewed: bool = False
    review_action: Optional[str] = None
    created_at: str = Field(default_factory=_now)
    # Phase 11: Signal Intelligence
    evaluated: bool = False
    evaluated_at: Optional[str] = None
    signal_strength: str = "medium"  # low | medium | high | critical


class BDSignalCreate(BaseModel):
    company_id: Optional[str] = None
    company_name: str
    prospect_id: Optional[str] = None
    signal_type: str = "other"
    summary: str
    source: Optional[str] = None
    relevance_score: int = 50
    detected_at: Optional[str] = None


# ── Pain Point ────────────────────────────────────────────────────────────────

class BDPainPoint(BaseModel):
    id: str = Field(default_factory=_uid)
    company_id: str
    company_name: str
    description: str
    category: Optional[str] = None
    signal_source: Optional[str] = None
    confidence: int = 70
    recommended_angle: Optional[str] = None
    created_at: str = Field(default_factory=_now)


class BDPainPointCreate(BaseModel):
    company_id: str
    company_name: str
    description: str
    category: Optional[str] = None
    signal_source: Optional[str] = None
    confidence: int = 70
    recommended_angle: Optional[str] = None


# ── Opportunity ───────────────────────────────────────────────────────────────

class BDOpportunity(BaseModel):
    id: str = Field(default_factory=_uid)
    company_id: str
    company_name: str
    contact_name: Optional[str] = None
    score: int = 0
    score_label: str = "cold"
    stage: str = "identified"
    pain_points: List[str] = Field(default_factory=list)
    value_proposition: Optional[str] = None
    recommended_action: Optional[str] = None
    deal_packet_id: Optional[str] = None
    notes: str = ""
    created_at: str = Field(default_factory=_now)
    updated_at: str = Field(default_factory=_now)
    # Phase 11: Recalculation tracking
    last_recalculated_at: Optional[str] = None
    score_change: Optional[int] = None
    score_reason: Optional[str] = None
    signal_contribution: int = 0


class BDOpportunityCreate(BaseModel):
    company_id: str
    company_name: str
    contact_name: Optional[str] = None
    stage: str = "identified"
    pain_points: List[str] = Field(default_factory=list)
    value_proposition: Optional[str] = None
    recommended_action: Optional[str] = None
    notes: str = ""


class OpportunityScoreRequest(BaseModel):
    icp_match: bool = False
    pain_point_count: int = 0
    signal_count: int = 0
    company_size: Optional[str] = None
    prospect_seniority: Optional[str] = None
    days_since_last_signal: Optional[int] = None
    existing_relationship: bool = False


class OpportunityScoreResponse(BaseModel):
    score: int
    score_label: str
    breakdown: dict


# ── Deal Packet ───────────────────────────────────────────────────────────────

class BDChecklistItem(BaseModel):
    text: str
    done: bool = False


class BDDealPacket(BaseModel):
    id: str = Field(default_factory=_uid)
    company_id: Optional[str] = None
    company_name: str
    contact_name: Optional[str] = None
    contact_role: Optional[str] = None
    engagement_type: Optional[str] = "New Business"
    company_summary: str = ""
    pain_points: List[str] = Field(default_factory=list)
    value_proposition: str = ""
    talking_points: List[str] = Field(default_factory=list)
    outreach_draft: str = ""
    checklist: List[BDChecklistItem] = Field(default_factory=list)
    status: str = "draft"
    notes: str = ""
    created_at: str = Field(default_factory=_now)
    updated_at: Optional[str] = None


class BDDealPacketGenerateRequest(BaseModel):
    company_id: Optional[str] = None
    company_name: str
    contact_name: Optional[str] = None
    contact_role: Optional[str] = None
    engagement_type: Optional[str] = "New Business"
    pain_points: List[str] = Field(default_factory=list)
    notes: str = ""


# ── Outreach Draft ────────────────────────────────────────────────────────────

class BDOutreachDraft(BaseModel):
    id: str = Field(default_factory=_uid)
    company_name: str
    contact_name: str
    contact_role: str
    message_type: str = "email"
    subject: Optional[str] = None
    body: str
    tone: str = "warm"
    angle: Optional[str] = None
    personalization_score: int = 0
    spam_risk_score: int = 0
    ai_sounding_score: int = 0
    quality_status: str = "draft"
    status: str = "draft"
    notes: str = ""
    created_at: str = Field(default_factory=_now)
    updated_at: Optional[str] = None


class BDMessageDraftRequest(BaseModel):
    company_name: str
    contact_name: str
    contact_role: str = ""
    pain_point: str = ""
    angle: str = ""
    message_type: str = "email"
    tone: str = "warm"


class BDMessageDraftResponse(BaseModel):
    draft: str
    subject: Optional[str] = None
    safety_notice: str
    message_type: str
    tone: str


# ── Outreach Draft (extended) ─────────────────────────────────────────────────

class BDOutreachDraftCreate(BaseModel):
    company_name: str
    contact_name: str
    contact_role: str = ""
    message_type: str = "email"
    subject: Optional[str] = None
    body: str
    tone: str = "warm"
    angle: Optional[str] = None
    personalization_score: int = 0
    spam_risk_score: int = 0
    ai_sounding_score: int = 0
    notes: str = ""


class BDOutreachDraftUpdate(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None
    tone: Optional[str] = None
    angle: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


# ── Activity Log ──────────────────────────────────────────────────────────────

class BDActivity(BaseModel):
    id: str = Field(default_factory=_uid)
    entity_type: str  # "draft" | "opportunity" | "deal_packet"
    entity_id: str
    action: str
    description: str
    metadata: dict = Field(default_factory=dict)
    created_at: str = Field(default_factory=_now)


class BDActivityCreate(BaseModel):
    entity_type: str
    entity_id: str
    action: str
    description: str
    metadata: dict = Field(default_factory=dict)


# ── ICP Configuration ─────────────────────────────────────────────────────────

class BDICPConfig(BaseModel):
    target_industries: List[str] = Field(default_factory=list)
    company_size_min: Optional[int] = None
    company_size_max: Optional[int] = None
    target_roles: List[str] = Field(default_factory=list)
    pain_point_priorities: List[str] = Field(default_factory=list)
    signal_priorities: List[str] = Field(default_factory=list)
    scoring_weights: dict = Field(default_factory=lambda: {
        "icp_match": 30,
        "pain_points": 20,
        "signals": 20,
        "seniority": 15,
        "urgency": 10,
        "existing_relationship": 5,
    })
    updated_at: str = Field(default_factory=_now)


class BDICPConfigUpdate(BaseModel):
    target_industries: Optional[List[str]] = None
    company_size_min: Optional[int] = None
    company_size_max: Optional[int] = None
    target_roles: Optional[List[str]] = None
    pain_point_priorities: Optional[List[str]] = None
    signal_priorities: Optional[List[str]] = None
    scoring_weights: Optional[dict] = None


# ── Move Stage ────────────────────────────────────────────────────────────────

_VALID_STAGES = frozenset({
    "identified", "researched", "qualified", "outreach_ready",
    "in_conversation", "proposal", "engaged", "deal_packet", "active", "won", "lost",
})


class BDMoveStageRequest(BaseModel):
    stage: str

    def validate_stage(self) -> str:
        if self.stage not in _VALID_STAGES:
            raise ValueError(f"Invalid stage: {self.stage}. Valid: {sorted(_VALID_STAGES)}")
        return self.stage


class BDMoveStageResponse(BaseModel):
    id: str
    previous_stage: str
    new_stage: str
    activity_id: str


# ── Dashboard Stats ───────────────────────────────────────────────────────────

class BDDashboardStats(BaseModel):
    qualified_opportunities: int = 0
    hot_opportunities: int = 0
    high_signal_prospects: int = 0
    companies_with_pain_points: int = 0
    drafts_for_review: int = 0
    approved_drafts: int = 0
    pipeline_snapshot: List[dict] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    # Phase 11: Signal Intelligence
    signal_recommendations: int = 0
    companies_needing_research: int = 0
    prospects_ready_for_review: int = 0


# ── Pipeline ──────────────────────────────────────────────────────────────────

class BDPipelineDeal(BaseModel):
    id: str
    company: str
    contact: Optional[str] = None
    score: int
    score_label: str
    stage: str
    last_action: str
    pain_points: List[str] = Field(default_factory=list)


class BDPipelineStage(BaseModel):
    slug: str
    label: str
    order: int
    color: str
    count: int
    deals: List[BDPipelineDeal] = Field(default_factory=list)


class BDPipelineResponse(BaseModel):
    stages: List[BDPipelineStage]
    total_active: int


# ── Phase 11: Signal Intelligence Recommendations ─────────────────────────────

class BDRecommendation(BaseModel):
    id: str = Field(default_factory=_uid)
    entity_type: str          # "signal" | "company" | "opportunity" | "prospect"
    entity_id: str
    entity_name: str
    priority: str             # "critical" | "high" | "medium" | "low"
    reason: str
    recommended_action: str
    confidence_score: int = 50
    status: str = "new"       # "new" | "reviewed" | "dismissed" | "actioned"
    created_at: str = Field(default_factory=_now)
    updated_at: str = Field(default_factory=_now)


class BDRecommendationCreate(BaseModel):
    entity_type: str
    entity_id: str
    entity_name: str
    priority: str
    reason: str
    recommended_action: str
    confidence_score: int = 50


class BDSignalEvaluationResult(BaseModel):
    signal_id: str
    signal_strength: str
    priority: str
    confidence_score: int
    reason: str
    recommended_action: str
    recommendation_created: bool


class BDCompanyEvaluationResult(BaseModel):
    company_id: str
    recommendations_created: int
    score_updated: bool
    new_score: int
    new_score_label: str
    flags: List[str]


class BDOpportunityRecalculateResult(BaseModel):
    opportunity_id: str
    previous_score: int
    new_score: int
    score_change: int
    new_score_label: str
    signal_contribution: int
    score_reason: str
    breakdown: dict
    recommendation_created: bool


class BDRecommendationRefreshResult(BaseModel):
    signals_evaluated: int
    companies_evaluated: int
    opportunities_recalculated: int
    recommendations_created: int
    safety_notice: str


# ── CSV Import ────────────────────────────────────────────────────────────────

class BDImportPreviewRow(BaseModel):
    row: int
    data: dict
    status: str          # "ok" | "duplicate" | "error"
    message: Optional[str] = None


class BDImportResult(BaseModel):
    import_type: str     # "companies" | "prospects" | "signals"
    dry_run: bool
    imported_count: int
    skipped_count: int
    duplicate_count: int
    error_count: int
    errors: List[str] = Field(default_factory=list)
    preview_rows: List[BDImportPreviewRow] = Field(default_factory=list)
    safety_notice: str = "All data imported locally. No external APIs called."


# ── Phase 15: Evaluate All / Opportunity from Recommendation ──────────────────

class BDEvaluateAllResult(BaseModel):
    evaluated_count: int
    skipped_count: int          # already evaluated
    recommendations_created: int
    safety_notice: str = (
        "Signals evaluated locally using rule-based intelligence. "
        "No external API calls. Recommendations require explicit human review."
    )
