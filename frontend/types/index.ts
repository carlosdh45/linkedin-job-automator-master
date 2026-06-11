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
