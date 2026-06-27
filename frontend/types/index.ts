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
  // Phase 11
  evaluated: boolean
  evaluated_at: string | null
  signal_strength: string
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
  // Phase 11
  last_recalculated_at: string | null
  score_change: number | null
  score_reason: string | null
  signal_contribution: number
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

export type OutreachDraftStatus = 'draft' | 'pending_review' | 'approved' | 'rejected' | 'needs_research'

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
  status: OutreachDraftStatus
  notes: string
  created_at: string
  updated_at: string | null
}

export interface BDOutreachDraftCreate {
  company_name: string
  contact_name: string
  contact_role?: string
  message_type?: MessageType
  subject?: string | null
  body: string
  tone?: string
  angle?: string | null
  personalization_score?: number
  spam_risk_score?: number
  ai_sounding_score?: number
  notes?: string
}

export interface BDActivity {
  id: string
  entity_type: string
  entity_id: string
  action: string
  description: string
  metadata: Record<string, unknown>
  created_at: string
}

export interface BDICPConfig {
  target_industries: string[]
  company_size_min: number | null
  company_size_max: number | null
  target_roles: string[]
  pain_point_priorities: string[]
  signal_priorities: string[]
  scoring_weights: Record<string, number>
  updated_at: string
}

export interface BDICPConfigUpdate {
  target_industries?: string[]
  company_size_min?: number | null
  company_size_max?: number | null
  target_roles?: string[]
  pain_point_priorities?: string[]
  signal_priorities?: string[]
  scoring_weights?: Record<string, number>
}

export interface BDDashboardStats {
  qualified_opportunities: number
  hot_opportunities: number
  high_signal_prospects: number
  companies_with_pain_points: number
  drafts_for_review: number
  approved_drafts: number
  pipeline_snapshot: Array<{ stage: string; count: number }>
  recommended_actions: string[]
  // Phase 11: Signal Intelligence
  signal_recommendations: number
  companies_needing_research: number
  prospects_ready_for_review: number
}

export interface BDMoveStageResponse {
  id: string
  previous_stage: string
  new_stage: string
  activity_id: string
}

// ── Phase 11: Signal Intelligence ─────────────────────────────────────────────

export type RecommendationStatus = 'new' | 'reviewed' | 'dismissed' | 'actioned'
export type RecommendationPriority = 'critical' | 'high' | 'medium' | 'low'

export interface BDRecommendation {
  id: string
  entity_type: string
  entity_id: string
  entity_name: string
  priority: RecommendationPriority
  reason: string
  recommended_action: string
  confidence_score: number
  status: RecommendationStatus
  created_at: string
  updated_at: string
}

export interface BDSignalEvaluationResult {
  signal_id: string
  signal_strength: string
  priority: RecommendationPriority
  confidence_score: number
  reason: string
  recommended_action: string
  recommendation_created: boolean
}

export interface BDCompanyEvaluationResult {
  company_id: string
  recommendations_created: number
  score_updated: boolean
  new_score: number
  new_score_label: string
  flags: string[]
}

export interface BDOpportunityRecalculateResult {
  opportunity_id: string
  previous_score: number
  new_score: number
  score_change: number
  new_score_label: string
  signal_contribution: number
  score_reason: string
  breakdown: Record<string, number>
  recommendation_created: boolean
}

export interface BDRecommendationRefreshResult {
  signals_evaluated: number
  companies_evaluated: number
  opportunities_recalculated: number
  recommendations_created: number
  safety_notice: string
}

export interface BDPipelineDeal {
  id: string
  company: string
  contact: string | null
  score: number
  score_label: string
  stage: string
  last_action: string
  pain_points: string[]
}

export interface BDPipelineStage {
  slug: string
  label: string
  order: number
  color: string
  count: number
  deals: BDPipelineDeal[]
}

export interface BDPipelineSnapshot {
  stages: BDPipelineStage[]
  total_active: number
}

export type BDPipelineResponse = BDPipelineSnapshot

// ── Phase 16: Workspace Data Management ──────────────────────────────────────

export interface BDImportHistoryEntry {
  id: string
  import_type: 'companies' | 'prospects' | 'signals'
  filename: string
  imported_count: number
  skipped_count: number
  duplicate_count: number
  error_count: number
  committed_at: string
  safety_notice: string
  local_only: boolean
}

export interface BDWorkspaceStatus {
  total_companies: number
  total_prospects: number
  total_signals: number
  total_opportunities: number
  total_deal_packets: number
  total_outreach_drafts: number
  total_recommendations: number
  imported_companies: number
  imported_prospects: number
  imported_signals: number
  last_import_date: string | null
  last_activity_date: string | null
  icp_configured: boolean
  data_health_warnings: string[]
  local_only: boolean
  safety_notice: string
}

export interface BDRestorePreviewResult {
  companies_count: number
  prospects_count: number
  signals_count: number
  opportunities_count: number
  deal_packets_count: number
  outreach_drafts_count: number
  recommendations_count: number
  warnings: string[]
  valid: boolean
  local_only: boolean
  safety_notice: string
}

export interface BDClearResult {
  cleared: string[]
  records_removed: number
  safety_notice: string
}

// ── Phase 15: Evaluate All ────────────────────────────────────────────────────

export interface BDEvaluateAllResult {
  evaluated_count: number
  skipped_count: number
  recommendations_created: number
  safety_notice: string
}

// ── CSV Import — Phase 14 ─────────────────────────────────────────────────────

export interface BDImportPreviewRow {
  row: number
  data: Record<string, string>
  status: 'ok' | 'duplicate' | 'error'
  message: string | null
}

export interface BDImportResult {
  import_type: 'companies' | 'prospects' | 'signals'
  dry_run: boolean
  imported_count: number
  skipped_count: number
  duplicate_count: number
  error_count: number
  errors: string[]
  preview_rows: BDImportPreviewRow[]
  safety_notice: string
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
