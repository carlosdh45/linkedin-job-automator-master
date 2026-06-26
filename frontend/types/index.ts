// Stats keys are dynamic: job_{status}, lead_{status}, outreach_*, contacts_found
export type Stats = Record<string, number>

export function statJobTotal(s: Stats): number {
  return Object.entries(s).filter(([k]) => k.startsWith('job_')).reduce((n, [, v]) => n + v, 0)
}
export function statJobScored(s: Stats): number {
  return (s.job_scored || 0) + (s.job_draft_ready || 0) + (s.job_approved || 0)
}
export function statLeadTotal(s: Stats): number {
  return Object.entries(s).filter(([k]) => k.startsWith('lead_')).reduce((n, [, v]) => n + v, 0)
}
export function statLeadScored(s: Stats): number {
  return (s.lead_scored || 0) + (s.lead_draft_ready || 0)
}

export interface Job {
  id: number
  job_url: string
  company: string
  title: string
  location: string | null
  domain: string | null
  status: string
  external_url: string | null
  applied_at: string
  notes: string | null
  job_score: number
  skill_match_score: number
  score_label: string
  skip_reason: string
  approved_at: string | null
  context_data: Record<string, unknown>
}

export interface Lead {
  id: number
  domain: string
  company: string
  contact_name: string
  contact_email: string
  contact_role: string
  industry: string
  pain_points: string[]
  context_data: Record<string, unknown>
  lead_score: number
  score_label: string
  status: string
  skip_reason: string
  created_at: string
  updated_at: string
}

export interface Draft {
  id: number
  job_url: string
  company: string
  job_title: string
  to_email: string
  to_name: string
  to_role: string
  subject: string
  body: string
  outreach_type: string
  style: string
  status: string
  personalization_score: number
  spam_risk_score: number
  ai_sounding_score: number
  quality_status: string
  quality_reasons: string[]
  send_recommendation: string
  context_used: Record<string, unknown>
  generated_at: string
  approved_at: string | null
  sent_at: string | null
  skip_reason: string
  failure_reason: string
}

export interface CandidateProfile {
  id: string
  full_name: string
  email: string
  target_roles: string[]
  seniority: string
  preferred_locations: string[]
  remote_preference: string
  salary_expectation: string
  linkedin_url: string
  portfolio_url: string
  github_url: string
  key_skills: string[]
  industries_of_interest: string[]
  resume_filename: string | null
  resume_original_filename: string | null
  resume_uploaded_at: string | null
  created_at: string
  updated_at: string
}

export interface ProfileUpdate {
  full_name?: string
  email?: string
  target_roles?: string[]
  seniority?: string
  preferred_locations?: string[]
  remote_preference?: string
  salary_expectation?: string
  linkedin_url?: string
  portfolio_url?: string
  github_url?: string
  key_skills?: string[]
  industries_of_interest?: string[]
}

export interface ResumeInfo {
  filename: string
  original_filename: string
  uploaded_at: string | null
}

// ── Resume Studio structured profile ─────────────────────────────────────────

export interface ResumeExperienceItem {
  company: string
  title: string
  location: string
  start_date: string
  end_date: string
  currently_working: boolean
  bullets: string[]
}

export interface ResumeProjectItem {
  name: string
  description: string
  technologies: string[]
  bullets: string[]
}

export interface ResumeEducationItem {
  institution: string
  degree: string
  dates: string
}

export interface ResumeProfile {
  headline: string
  professional_summary: string
  target_role: string
  location: string
  email: string
  phone: string
  linkedin_url: string
  portfolio_url: string
  github_url: string
  skills: string[]
  experience_items: ResumeExperienceItem[]
  project_items: ResumeProjectItem[]
  education_items: ResumeEducationItem[]
  certifications: string[]
  languages: string[]
  achievements: string[]
  raw_cv_notes: string
  updated_at: string
}

export type ResumeProfileUpdate = Partial<Omit<ResumeProfile, 'updated_at'>>

// ── CV Import ─────────────────────────────────────────────────────────────────

export interface CVImportPreview {
  raw_text: string
  detected_email: string
  detected_phone: string
  detected_linkedin: string
  detected_github: string
  detected_portfolio: string
  detected_skills: string[]
  detected_experience_headings: string[]
  detected_education_entries: string[]
  detected_certifications: string[]
  raw_notes: string
  has_content: boolean
}

export interface CVImportApplyRequest {
  apply_email: boolean
  apply_phone: boolean
  apply_linkedin: boolean
  apply_github: boolean
  apply_portfolio: boolean
  apply_skills: boolean
  apply_certifications: boolean
  apply_raw_notes: boolean
}

// ── Application Packet ────────────────────────────────────────────────────────

export interface ChecklistItem {
  text: string
  done: boolean
}

export interface ApplicationPacket {
  target_job_title: string
  target_company: string
  job_description: string
  resume_markdown: string
  cover_letter_draft: string
  tailored_summary: string
  skills_emphasis: string[]
  fit_summary: string
  talking_points: string[]
  checklist: ChecklistItem[]
  status: string
  notes: string
  updated_at: string | null
}

export type ApplicationPacketUpdate = Partial<Omit<ApplicationPacket, 'updated_at'>>

// ── BD OS Types ───────────────────────────────────────────────────────────────

export type ProspectStatus = 'identified' | 'researched' | 'engaged' | 'active' | 'closed'
export type CompanyStatus = 'identified' | 'researched' | 'qualified' | 'engaged' | 'active' | 'closed'
export type SignalType = 'hiring' | 'funding' | 'leadership_change' | 'tech_change' | 'competitive' | 'pain_point' | 'growth' | 'other'
export type OpportunityStage = 'identified' | 'researched' | 'qualified' | 'engaged' | 'deal_packet' | 'active' | 'won' | 'lost'
export type DealPacketStatus = 'draft' | 'review' | 'approved' | 'executed'
export type MessageType = 'email' | 'linkedin' | 'intro_request'
export type ScoreLabel = 'hot' | 'warm' | 'cold' | 'disqualified'

export interface BDCompany {
  id: string
  name: string
  domain: string | null
  industry: string | null
  size_estimate: string | null
  tech_signals: string[]
  pain_points: string[]
  opportunity_score: number
  score_label: ScoreLabel
  icp_match: boolean
  status: CompanyStatus
  notes: string
  created_at: string
  updated_at: string
}

export interface BDProspect {
  id: string
  company_id: string
  company_name: string
  name: string
  title: string | null
  seniority: string | null
  linkedin_url: string | null
  pain_point_count: number
  signal_count: number
  opportunity_score: number
  score_label: ScoreLabel
  recommended_angle: string | null
  status: ProspectStatus
  notes: string
  created_at: string
  updated_at: string
}

export interface BDSignal {
  id: string
  company_id: string | null
  company_name: string
  prospect_id: string | null
  signal_type: SignalType
  summary: string
  source: string | null
  relevance_score: number
  detected_at: string
  reviewed: boolean
  review_action: string | null
  created_at: string
}

export interface BDPainPoint {
  id: string
  company_id: string
  company_name: string
  description: string
  category: string | null
  signal_source: string | null
  confidence: number
  recommended_angle: string | null
  created_at: string
}

export interface BDOpportunity {
  id: string
  company_id: string
  company_name: string
  contact_name: string | null
  score: number
  score_label: ScoreLabel
  stage: OpportunityStage
  pain_points: string[]
  value_proposition: string | null
  recommended_action: string | null
  deal_packet_id: string | null
  notes: string
  created_at: string
  updated_at: string
}

export interface BDDealPacket {
  id: string
  company_name: string
  contact_name: string | null
  contact_role: string | null
  engagement_type: string | null
  company_summary: string
  pain_points: string[]
  value_proposition: string
  talking_points: string[]
  outreach_draft: string
  checklist: ChecklistItem[]
  status: DealPacketStatus
  notes: string
  created_at: string
  updated_at: string | null
}

export interface BDOutreachDraft {
  id: string
  company_name: string
  contact_name: string
  contact_role: string
  message_type: MessageType
  subject: string | null
  body: string
  tone: string
  angle: string | null
  personalization_score: number
  spam_risk_score: number
  ai_sounding_score: number
  quality_status: string
  status: string
  created_at: string
}

export interface BDPipelineStage {
  slug: string
  label: string
  order: number
  color: string
  count: number
}

export interface BDPipelineSnapshot {
  stages: BDPipelineStage[]
  total_active: number
}

// ── Resume Editor — Phase 6 ───────────────────────────────────────────────────

export type ResumeTone = 'professional' | 'executive' | 'technical' | 'concise'

export interface ResumeATSCheck {
  label: string
  passed: boolean
}

export interface ResumeQualityReport {
  completeness_score: number
  ats_score: number
  ats_total: number
  sections: Record<string, boolean>
  missing_sections: string[]
  ats_checks: ResumeATSCheck[]
}

export interface DailyBrief {
  date: string
  stats: Stats
  top_jobs: Job[]
  top_leads: Lead[]
  pending_drafts: {
    total: number
    approvable: Draft[]
    blocked: Draft[]
  }
  recommended_actions: string[]
}
