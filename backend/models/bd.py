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
    created_at: str = Field(default_factory=_now)


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
