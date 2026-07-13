import apiClient from './client'

// ─── Shared ───────────────────────────────────────────────────────────────────

export interface PaginationMeta {
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface Paginated<T> {
  items: T[]
  meta: PaginationMeta
}

// ─── AnimationJob ─────────────────────────────────────────────────────────────

export interface AnimationJobResponse {
  id: string
  project_id: string
  scene_id: string | null
  episode_id: string | null
  job_type: string
  status: string
  mode: string
  triggered_by: string
  params: Record<string, unknown>
  result: Record<string, unknown>
  error_message: string
  started_at: string | null
  completed_at: string | null
  duration_seconds: number | null
  created_at: string
  updated_at: string
}

// ─── AnimationRenderOutput ────────────────────────────────────────────────────

export interface AnimationRenderOutputResponse {
  id: string
  job_id: string
  project_id: string
  scene_id: string | null
  episode_id: string | null
  output_type: string
  status: string
  storage_key: string
  storage_bucket: string
  file_size_bytes: number
  duration_seconds: number
  width: number
  height: number
  fps: number
  format: string
  provider: string
  render_params: Record<string, unknown>
  created_at: string
  updated_at: string
}

// ─── AnimationRetryQueue ──────────────────────────────────────────────────────

export interface AnimationRetryQueueResponse {
  id: string
  project_id: string
  scene_id: string | null
  episode_id: string | null
  original_job_id: string | null
  retry_count: number
  max_retries: number
  status: string
  reason: string
  next_retry_at: string | null
  resolved_at: string | null
  params: Record<string, unknown>
  created_at: string
  updated_at: string
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

export interface AnimationDashboardStats {
  total_jobs: number
  jobs_completed: number
  jobs_pending: number
  jobs_failed: number
  jobs_running: number
  total_render_outputs: number
  total_retry_queue: number
  recent_jobs: AnimationJobResponse[]
}

// ─── Trigger requests ─────────────────────────────────────────────────────────

export interface TriggerSceneAnimationRequest {
  project_id: string
  scene_id: string
  episode_id?: string | null
  duration_seconds?: number
  fps?: number
  width?: number
  height?: number
  camera_motion?: string
  characters?: Record<string, unknown>[]
  background_storage_key?: string
  dialogue_segments?: Record<string, unknown>[]
  extra_params?: Record<string, unknown>
}

export interface TriggerEpisodeAnimationRequest {
  project_id: string
  episode_id: string
  scene_ids?: string[]
  fps?: number
  width?: number
  height?: number
  force_re_render?: boolean
}

export interface DispatchResponse {
  job_id: string
  status: string
  message: string
  dispatch_mode: string
}

// ─── API client ───────────────────────────────────────────────────────────────

const BASE = '/an'

export const animationEngineApi = {
  getDashboard: (projectId: string): Promise<AnimationDashboardStats> =>
    apiClient.get<AnimationDashboardStats>(`${BASE}/dashboard/${projectId}`).then(r => r.data),

  // Jobs
  listJobs: (
    projectId: string,
    params?: { status?: string; job_type?: string; page?: number; page_size?: number }
  ): Promise<Paginated<AnimationJobResponse>> =>
    apiClient
      .get<Paginated<AnimationJobResponse>>(`${BASE}/jobs`, {
        params: { project_id: projectId, ...params },
      })
      .then(r => r.data),

  getJob: (jobId: string): Promise<AnimationJobResponse> =>
    apiClient.get<AnimationJobResponse>(`${BASE}/jobs/${jobId}`).then(r => r.data),

  // Render outputs
  listOutputs: (
    projectId: string,
    params?: { output_type?: string; status?: string; page?: number; page_size?: number }
  ): Promise<Paginated<AnimationRenderOutputResponse>> =>
    apiClient
      .get<Paginated<AnimationRenderOutputResponse>>(`${BASE}/outputs`, {
        params: { project_id: projectId, ...params },
      })
      .then(r => r.data),

  getOutput: (outputId: string): Promise<AnimationRenderOutputResponse> =>
    apiClient.get<AnimationRenderOutputResponse>(`${BASE}/outputs/${outputId}`).then(r => r.data),

  // Retry queue
  listRetryQueue: (
    projectId: string,
    params?: { status?: string; page?: number; page_size?: number }
  ): Promise<Paginated<AnimationRetryQueueResponse>> =>
    apiClient
      .get<Paginated<AnimationRetryQueueResponse>>(`${BASE}/retry-queue`, {
        params: { project_id: projectId, ...params },
      })
      .then(r => r.data),

  retryEntry: (entryId: string): Promise<DispatchResponse> =>
    apiClient.post<DispatchResponse>(`${BASE}/retry-queue/${entryId}/retry`).then(r => r.data),

  // Triggers
  triggerSceneAnimation: (body: TriggerSceneAnimationRequest): Promise<DispatchResponse> =>
    apiClient.post<DispatchResponse>(`${BASE}/generate/scene`, body).then(r => r.data),

  triggerEpisodeAnimation: (body: TriggerEpisodeAnimationRequest): Promise<DispatchResponse> =>
    apiClient.post<DispatchResponse>(`${BASE}/generate/episode`, body).then(r => r.data),
}
