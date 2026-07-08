import apiClient from '@/api/client'

// ─── Types ────────────────────────────────────────────────────────────────────

export interface PaginationMeta {
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface ResearchSource {
  id: string
  name: string
  source_type: string
  url: string
  description: string
  is_active: boolean
  fetch_interval_seconds: number
  fetch_count: number
  error_count: number
  last_fetched_at: string | null
  created_at: string
  updated_at: string
}

export interface ResearchTrend {
  id: string
  keyword: string
  normalized_keyword: string
  category: string
  region: string
  language: string
  trend_score: number
  velocity: number
  growth_rate: number
  popularity_index: number
  is_emerging: boolean
  is_declining: boolean
  status: string
  discovered_at: string | null
  created_at: string
}

export interface ResearchTopic {
  id: string
  canonical_name: string
  slug: string
  description: string
  keywords: string[]
  categories: string[]
  language: string
  status: string
  research_status: string
  trend_score: number
  research_quality: number
  fact_confidence: number
  opportunity_score: number
  article_count: number
  fact_count: number
  researched_at: string | null
  created_at: string
  updated_at: string
}

export interface ResearchCluster {
  id: string
  canonical_name: string
  description: string
  keywords: string[]
  categories: string[]
  topic_ids: string[]
  topic_count: number
  confidence: number
  avg_opportunity_score: number
  status: string
  created_at: string
}

export interface ResearchArticle {
  id: string
  topic_id: string
  title: string
  url: string
  summary: string
  author: string
  published_at: string | null
  source_type: string
  language: string
  quality_score: number
  relevance_score: number
  status: string
  created_at: string
}

export interface ResearchFact {
  id: string
  topic_id: string
  fact_type: string
  statement: string
  confidence: number
  supporting_sources: string[]
  conflicting_sources: string[]
  citations: Record<string, unknown>[]
  is_verified: boolean
  is_rejected: boolean
  rejection_reason: string
  verification_count: number
  created_at: string
}

export interface ResearchEntity {
  id: string
  topic_id: string
  entity_type: string
  name: string
  normalized_name: string
  description: string
  attributes: Record<string, unknown>
  confidence: number
  wikidata_id: string
  wikipedia_url: string
  occurrence_count: number
  created_at: string
}

export interface ResearchScore {
  id: string
  topic_id: string
  trend_score: number
  research_quality: number
  fact_confidence: number
  competition_score: number
  novelty_score: number
  audience_fit: number
  seasonality_score: number
  educational_value: number
  entertainment_value: number
  overall_score: number
  breakdown: Record<string, unknown>
  scored_at: string | null
  created_at: string
}

export interface ResearchQueueItem {
  id: string
  topic_id: string
  project_id: string | null
  priority: number
  status: string
  overall_score: number
  research_summary: Record<string, unknown>
  queued_at: string | null
  processed_at: string | null
  error_message: string
  retry_count: number
  created_at: string
}

export interface ResearchJob {
  id: string
  job_type: string
  status: string
  topic_id: string | null
  execution_mode: string
  progress_percent: number
  current_step: string
  result: Record<string, unknown>
  error_message: string
  retry_count: number
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface ResearchHistory {
  id: string
  run_type: string
  status: string
  trends_discovered: number
  topics_researched: number
  facts_verified: number
  opportunities_scored: number
  knowledge_docs_created: number
  duration_seconds: number
  error_message: string
  triggered_by: string
  created_at: string
}

export interface SchedulerPhaseStatus {
  last_run_at: string | null
  last_status: string
  last_duration_seconds: number | null
}

export interface SchedulerStatus {
  phases: Record<string, SchedulerPhaseStatus>
}

export interface ResearchDashboardStats {
  active_trends: number
  emerging_trends: number
  total_topics: number
  topics_by_status: Record<string, number>
  researched_topics: number
  verified_facts: number
  knowledge_docs_created: number
  queue_pending: number
  jobs_by_status: Record<string, number>
  scheduler_status: SchedulerStatus
  top_trends: ResearchTrend[]
  top_opportunities: ResearchTopic[]
}

export interface DispatchResponse {
  job_id: string
  task_id: string
  mode: string
  status: string
  result?: Record<string, unknown>
}

export interface Paginated<T> {
  items: T[]
  meta: PaginationMeta
}

// ─── API Functions ────────────────────────────────────────────────────────────

const BASE = '/rs'

export const researchApi = {
  // Dashboard
  getDashboard: () =>
    apiClient.get<ResearchDashboardStats>(`${BASE}/dashboard`).then(r => r.data),

  // Sources
  getSources: (page = 1, pageSize = 20) =>
    apiClient.get<Paginated<ResearchSource>>(`${BASE}/sources`, { params: { page, page_size: pageSize } }).then(r => r.data),
  createSource: (data: { name: string; source_type: string; url?: string; description?: string }) =>
    apiClient.post<ResearchSource>(`${BASE}/sources`, data).then(r => r.data),
  deleteSource: (id: string) =>
    apiClient.delete(`${BASE}/sources/${id}`),

  // Trends
  getTrends: (page = 1, pageSize = 20, category?: string, emergingOnly?: boolean) =>
    apiClient.get<Paginated<ResearchTrend>>(`${BASE}/trends`, {
      params: { page, page_size: pageSize, category, emerging_only: emergingOnly },
    }).then(r => r.data),
  getTrend: (id: string) =>
    apiClient.get<ResearchTrend>(`${BASE}/trends/${id}`).then(r => r.data),

  // Topics
  getTopics: (page = 1, pageSize = 20, status?: string, researchStatus?: string) =>
    apiClient.get<Paginated<ResearchTopic>>(`${BASE}/topics`, {
      params: { page, page_size: pageSize, status, research_status: researchStatus },
    }).then(r => r.data),
  getTopic: (id: string) =>
    apiClient.get<ResearchTopic>(`${BASE}/topics/${id}`).then(r => r.data),
  createTopic: (data: { canonical_name: string; description?: string; keywords?: string[]; categories?: string[] }) =>
    apiClient.post<ResearchTopic>(`${BASE}/topics`, data).then(r => r.data),
  researchTopic: (id: string) =>
    apiClient.post<DispatchResponse>(`${BASE}/topics/${id}/research`).then(r => r.data),
  deleteTopic: (id: string) =>
    apiClient.delete(`${BASE}/topics/${id}`),

  // Clusters
  getClusters: (page = 1, pageSize = 20) =>
    apiClient.get<Paginated<ResearchCluster>>(`${BASE}/clusters`, { params: { page, page_size: pageSize } }).then(r => r.data),

  // Articles
  getArticles: (topicId: string, page = 1, pageSize = 20) =>
    apiClient.get<Paginated<ResearchArticle>>(`${BASE}/topics/${topicId}/articles`, {
      params: { page, page_size: pageSize },
    }).then(r => r.data),

  // Facts
  getFacts: (topicId: string, page = 1, pageSize = 20, verifiedOnly?: boolean) =>
    apiClient.get<Paginated<ResearchFact>>(`${BASE}/topics/${topicId}/facts`, {
      params: { page, page_size: pageSize, verified_only: verifiedOnly },
    }).then(r => r.data),

  // Entities
  getEntities: (topicId: string) =>
    apiClient.get<ResearchEntity[]>(`${BASE}/topics/${topicId}/entities`).then(r => r.data),

  // Scores / Opportunities
  getOpportunities: (limit = 20) =>
    apiClient.get<ResearchScore[]>(`${BASE}/opportunities`, { params: { limit } }).then(r => r.data),

  // Queue
  getQueue: (page = 1, pageSize = 20, status?: string) =>
    apiClient.get<Paginated<ResearchQueueItem>>(`${BASE}/queue`, {
      params: { page, page_size: pageSize, status },
    }).then(r => r.data),
  pauseQueueItem: (id: string) =>
    apiClient.patch<ResearchQueueItem>(`${BASE}/queue/${id}/pause`).then(r => r.data),
  deleteQueueItem: (id: string) =>
    apiClient.delete(`${BASE}/queue/${id}`),

  // Jobs
  getJobs: (page = 1, pageSize = 20, status?: string, jobType?: string) =>
    apiClient.get<Paginated<ResearchJob>>(`${BASE}/jobs`, {
      params: { page, page_size: pageSize, status, job_type: jobType },
    }).then(r => r.data),
  getJob: (id: string) =>
    apiClient.get<ResearchJob>(`${BASE}/jobs/${id}`).then(r => r.data),
  getRetryQueue: () =>
    apiClient.get<ResearchJob[]>(`${BASE}/jobs/retry-queue`).then(r => r.data),

  // History
  getHistory: (page = 1, pageSize = 20, runType?: string) =>
    apiClient.get<Paginated<ResearchHistory>>(`${BASE}/history`, {
      params: { page, page_size: pageSize, run_type: runType },
    }).then(r => r.data),

  // Scheduler
  getSchedulerStatus: () =>
    apiClient.get<SchedulerStatus>(`${BASE}/scheduler/status`).then(r => r.data),
  triggerScheduler: (phase: string) =>
    apiClient.post<DispatchResponse>(`${BASE}/scheduler/trigger`, { phase }).then(r => r.data),

  // Analytics
  getAnalytics: (periodType = 'daily', limit = 30) =>
    apiClient.get<Record<string, unknown>[]>(`${BASE}/analytics`, {
      params: { period_type: periodType, limit },
    }).then(r => r.data),
}
