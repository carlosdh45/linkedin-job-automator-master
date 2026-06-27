import type {
  Stats, Job, Lead, Draft, DailyBrief,
  BDImportResult,
  CandidateProfile, ProfileUpdate,
  ResumeInfo, ResumeProfile, ResumeProfileUpdate,
  CVImportPreview, CVImportApplyRequest,
  ApplicationPacket, ApplicationPacketUpdate,
  ResumeQualityReport,
  BDCompany, BDProspect, BDSignal, BDOpportunity, BDDealPacket,
  BDPipelineResponse,
  BDOutreachDraft, BDOutreachDraftCreate,
  BDActivity, BDICPConfig, BDICPConfigUpdate,
  BDDashboardStats, BDMoveStageResponse,
  BDRecommendation,
  BDSignalEvaluationResult,
  BDCompanyEvaluationResult,
  BDOpportunityRecalculateResult,
  BDRecommendationRefreshResult,
  BDEvaluateAllResult,
  BDImportHistoryEntry,
  BDWorkspaceStatus,
  BDRestorePreviewResult,
  BDClearResult,
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
    // BD OS — Outreach Drafts
    getOutreachDrafts: () => get<BDOutreachDraft[]>('/api/bd/outreach-drafts'),
    getOutreachDraft: (id: string) => get<BDOutreachDraft>(`/api/bd/outreach-drafts/${id}`),
    createOutreachDraft: (data: BDOutreachDraftCreate) => post<BDOutreachDraft>('/api/bd/outreach-drafts', data),
    updateOutreachDraft: (id: string, data: Partial<BDOutreachDraftCreate> & { status?: string }) =>
      put<BDOutreachDraft>(`/api/bd/outreach-drafts/${id}`, data),
    approveOutreachDraft: (id: string) =>
      post<BDOutreachDraft>(`/api/bd/outreach-drafts/${id}/approve`),
    rejectOutreachDraft: (id: string) =>
      post<BDOutreachDraft>(`/api/bd/outreach-drafts/${id}/reject`),
    markOutreachDraftNeedsResearch: (id: string) =>
      post<BDOutreachDraft>(`/api/bd/outreach-drafts/${id}/needs-research`),
    // BD OS — Activity
    getBDActivity: (params?: { entity_type?: string; entity_id?: string; limit?: number }) => {
      const q = new URLSearchParams()
      if (params?.entity_type) q.set('entity_type', params.entity_type)
      if (params?.entity_id) q.set('entity_id', params.entity_id)
      if (params?.limit) q.set('limit', String(params.limit))
      const qs = q.toString()
      return get<BDActivity[]>(qs ? `/api/bd/activity?${qs}` : '/api/bd/activity')
    },
    // BD OS — ICP Config
    getICPConfig: () => get<BDICPConfig>('/api/bd/icp-config'),
    updateICPConfig: (data: BDICPConfigUpdate) => put<BDICPConfig>('/api/bd/icp-config', data),
    resetICPToDemo: () => put<BDICPConfig>('/api/bd/icp-config', {
      target_industries: ['SaaS', 'Financial Services', 'Private Equity', 'Logistics', 'Healthcare Operations', 'Professional Services', 'Mid-market Technology'],
      company_size_min: 50,
      company_size_max: 2000,
      target_roles: ['CEO', 'Founder', 'COO', 'CTO', 'VP Operations', 'VP Sales', 'Managing Partner', 'Head of Business Development'],
      pain_point_priorities: ['manual prospecting', 'low outbound conversion', 'poor lead qualification', 'disconnected CRM data', 'slow deal origination', 'lack of market signal tracking', 'offshore execution bottlenecks'],
      signal_priorities: ['hiring', 'leadership_change', 'pain_point', 'funding', 'growth'],
      scoring_weights: { icp_match: 30, pain_points: 25, signals: 20, seniority: 15, urgency: 7, existing_relationship: 3 },
    }),
    // BD OS — Dashboard Stats
    getBDDashboard: () => get<BDDashboardStats>('/api/bd/dashboard'),
    // BD OS — Move Stage
    moveBDOpportunityStage: (id: string, stage: string) =>
      post<BDMoveStageResponse>(`/api/bd/opportunities/${id}/move-stage`, { stage }),
    // BD OS — Signal Intelligence (Phase 11)
    evaluateBDSignal: (id: string) =>
      post<BDSignalEvaluationResult>(`/api/bd/signals/${id}/evaluate`),
    evaluateBDCompany: (id: string) =>
      post<BDCompanyEvaluationResult>(`/api/bd/companies/${id}/evaluate`),
    recalculateBDOpportunity: (id: string) =>
      post<BDOpportunityRecalculateResult>(`/api/bd/opportunities/${id}/recalculate`),
    getBDRecommendations: (params?: {
      status?: string
      entity_type?: string
      priority?: string
      limit?: number
    }) => {
      const q = new URLSearchParams()
      if (params?.status) q.set('status', params.status)
      if (params?.entity_type) q.set('entity_type', params.entity_type)
      if (params?.priority) q.set('priority', params.priority)
      if (params?.limit) q.set('limit', String(params.limit))
      const qs = q.toString()
      return get<BDRecommendation[]>(qs ? `/api/bd/recommendations?${qs}` : '/api/bd/recommendations')
    },
    refreshBDRecommendations: () =>
      post<BDRecommendationRefreshResult>('/api/bd/recommendations/refresh'),
    dismissBDRecommendation: (id: string) =>
      post<BDRecommendation>(`/api/bd/recommendations/${id}/dismiss`),
    actionBDRecommendation: (id: string) =>
      post<BDRecommendation>(`/api/bd/recommendations/${id}/action`),
    reviewBDRecommendation: (id: string) =>
      post<BDRecommendation>(`/api/bd/recommendations/${id}/review`),
    createOpportunityFromRec: (id: string) =>
      post<BDOpportunity>(`/api/bd/recommendations/${id}/create-opportunity`),
    // BD OS — Evaluate All Signals (Phase 15)
    evaluateAllBDSignals: () =>
      post<BDEvaluateAllResult>('/api/bd/signals/evaluate-all'),
    // BD OS — Create Opportunity
    createBDOpportunity: (data: Partial<BDOpportunity>) =>
      post<BDOpportunity>('/api/bd/opportunities', data),
    // BD OS — CSV Import
    importCSV: (type: 'companies' | 'prospects' | 'signals', file: File, dryRun = true) => {
      const form = new FormData()
      form.append('file', file)
      return $fetch<BDImportResult>(
        `${base}/api/bd/import/${type}-csv?dry_run=${dryRun}`,
        { method: 'POST', body: form },
      )
    },
    downloadTemplate: (type: 'companies' | 'prospects' | 'signals') =>
      `${base}/api/bd/import/templates?type=${type}`,
    // BD OS — Import History (Phase 16)
    getImportHistory: () => get<BDImportHistoryEntry[]>('/api/bd/import/history'),
    // BD OS — Workspace (Phase 16)
    getWorkspaceStatus: () => get<BDWorkspaceStatus>('/api/bd/workspace/status'),
    backupWorkspace: () => `${base}/api/bd/workspace/backup`,
    restorePreview: (backup: Record<string, unknown>) =>
      post<BDRestorePreviewResult>('/api/bd/workspace/restore-preview', backup),
    clearAllWorkspace: (confirmText: string) =>
      post<BDClearResult>('/api/bd/workspace/clear-all', { confirm_text: confirmText }),
    // BD OS — Exports (Phase 16)
    exportUrl: (type: 'companies' | 'prospects' | 'signals' | 'opportunities' | 'workspace') => {
      if (type === 'workspace') return `${base}/api/bd/export/workspace.json`
      return `${base}/api/bd/export/${type}.csv`
    },
  }
}
