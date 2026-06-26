import type {
  Stats, Job, Lead, Draft, DailyBrief,
  CandidateProfile, ProfileUpdate,
  ResumeInfo, ResumeProfile, ResumeProfileUpdate,
  CVImportPreview, CVImportApplyRequest,
  ApplicationPacket, ApplicationPacketUpdate,
  ResumeQualityReport,
  BDCompany, BDProspect, BDSignal, BDOpportunity, BDDealPacket,
  BDPipelineResponse,
} from '~/types'

export const useApi = () => {
  const config = useRuntimeConfig()
  const base = config.public.apiBase as string

  function get<T>(path: string): Promise<T> {
    return $fetch<T>(`${base}${path}`)
  }

  function post<T>(path: string, body?: unknown): Promise<T> {
    return $fetch<T>(`${base}${path}`, { method: 'POST', body: body ?? {} })
  }

  function put<T>(path: string, body?: unknown): Promise<T> {
    return $fetch<T>(`${base}${path}`, { method: 'PUT', body: body ?? {} })
  }

  return {
    getHealth: () => get<{ status: string }>('/health'),
    getStats: () => get<Stats>('/api/stats'),
    getDailyBrief: () => get<DailyBrief>('/api/daily-brief'),
    getJobs: (status?: string) =>
      get<{ jobs: Job[]; total: number }>(
        status ? `/api/jobs?status=${encodeURIComponent(status)}` : '/api/jobs'
      ),
    getLeads: (status?: string) =>
      get<{ leads: Lead[]; total: number }>(
        status ? `/api/leads?status=${encodeURIComponent(status)}` : '/api/leads'
      ),
    getReviewQueue: () => get<{ drafts: Draft[]; total: number }>('/api/review-queue'),
    approveDraft: (id: number) =>
      post<{ approved: boolean; reason?: string }>(`/api/drafts/${id}/approve`),
    skipDraft: (id: number, reason?: string) =>
      post<{ skipped: boolean }>(`/api/drafts/${id}/skip`, reason ? { reason } : undefined),
    markNeedsResearch: (id: number, note?: string) =>
      post<{ updated: boolean }>(`/api/drafts/${id}/needs-research`, note ? { note } : undefined),
    seedDemo: () => post<{ seeded: boolean; stats: Record<string, number> }>('/api/demo/seed'),
    clearDemo: () => post<{ cleared: boolean }>('/api/demo/clear'),
    // Profile
    getProfile: () => get<CandidateProfile>('/api/profile'),
    updateProfile: (updates: ProfileUpdate) => put<CandidateProfile>('/api/profile', updates),
    getResumeInfo: () => get<ResumeInfo>('/api/profile/resume'),
    uploadResume: (file: File) => {
      const form = new FormData()
      form.append('file', file)
      return $fetch<{ uploaded: boolean; filename: string; original_filename: string }>(
        `${base}/api/profile/resume`,
        { method: 'POST', body: form }
      )
    },
    // Resume Studio
    getResumeProfile: () => get<ResumeProfile>('/api/resume/profile'),
    updateResumeProfile: (updates: ResumeProfileUpdate) => put<ResumeProfile>('/api/resume/profile', updates),
    generateResumeDraft: (tone?: string) =>
      post<{ generated: boolean; preview: string; tone: string }>(
        tone ? `/api/resume/generate?tone=${encodeURIComponent(tone)}` : '/api/resume/generate'
      ),
    getResumePreview: () => get<{ preview: string; has_content: boolean }>('/api/resume/preview'),
    getResumeQuality: () => get<ResumeQualityReport>('/api/resume/quality'),
    // CV Import
    extractCvText: () => post<{ extracted: boolean; text: string; reason?: string }>('/api/resume/extract-cv'),
    importCvText: (text: string) => post<CVImportPreview>('/api/resume/import-text', { text }),
    getImportPreview: () => get<CVImportPreview>('/api/resume/import-preview'),
    applyImport: (opts: CVImportApplyRequest) => post<{ applied: boolean; fields_updated: string[] }>('/api/resume/apply-import', opts),
    // Application Packet
    getApplicationPacket: () => get<ApplicationPacket>('/api/application-packet'),
    updateApplicationPacket: (updates: ApplicationPacketUpdate) => put<ApplicationPacket>('/api/application-packet', updates),
    generateApplicationPacket: () => post<ApplicationPacket>('/api/application-packet/generate'),
    // BD OS — Companies
    getBDCompanies: () => get<BDCompany[]>('/api/bd/companies'),
    getBDCompany: (id: string) => get<BDCompany>(`/api/bd/companies/${id}`),
    createBDCompany: (data: Partial<BDCompany>) => post<BDCompany>('/api/bd/companies', data),
    updateBDCompany: (id: string, data: Partial<BDCompany>) => put<BDCompany>(`/api/bd/companies/${id}`, data),
    // BD OS — Prospects
    getBDProspects: () => get<BDProspect[]>('/api/bd/prospects'),
    getBDProspect: (id: string) => get<BDProspect>(`/api/bd/prospects/${id}`),
    createBDProspect: (data: Partial<BDProspect>) => post<BDProspect>('/api/bd/prospects', data),
    updateBDProspect: (id: string, data: Partial<BDProspect>) => put<BDProspect>(`/api/bd/prospects/${id}`, data),
    // BD OS — Signals
    getBDSignals: () => get<BDSignal[]>('/api/bd/signals'),
    createBDSignal: (data: Partial<BDSignal>) => post<BDSignal>('/api/bd/signals', data),
    // BD OS — Opportunities
    getBDOpportunities: () => get<BDOpportunity[]>('/api/bd/opportunities'),
    scoreBDOpportunity: (req: {
      icp_match?: boolean
      pain_point_count?: number
      signal_count?: number
      prospect_seniority?: string
      days_since_last_signal?: number
      existing_relationship?: boolean
    }) => post<{ score: number; score_label: string; breakdown: Record<string, number> }>('/api/bd/opportunities/score', req),
    // BD OS — Deal Packets
    getBDDealPackets: () => get<BDDealPacket[]>('/api/bd/deal-packets'),
    getBDDealPacket: (id: string) => get<BDDealPacket>(`/api/bd/deal-packets/${id}`),
    generateBDDealPacket: (req: {
      company_name: string
      company_id?: string
      contact_name?: string
      contact_role?: string
      engagement_type?: string
      pain_points?: string[]
      notes?: string
    }) => post<BDDealPacket>('/api/bd/deal-packets/generate', req),
    // BD OS — Pipeline
    getBDPipeline: () => get<BDPipelineResponse>('/api/bd/pipeline'),
    // BD OS — Message Studio
    generateBDDraft: (req: {
      company_name: string
      contact_name: string
      contact_role?: string
      pain_point?: string
      angle?: string
      message_type?: string
      tone?: string
    }) => post<{ draft: string; subject: string | null; safety_notice: string; message_type: string; tone: string }>('/api/bd/message-studio/draft', req),
    // BD OS — Demo
    seedBDDemo: () => post<{ seeded: boolean; stats: Record<string, number> }>('/api/bd/demo/seed'),
    clearBDDemo: () => post<{ cleared: boolean }>('/api/bd/demo/clear'),
  }
}
