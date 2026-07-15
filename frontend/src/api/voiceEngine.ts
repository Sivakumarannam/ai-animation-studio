import apiClient from './client'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface VoiceJob {
  id: string
  project_id: string
  scene_id: string | null
  episode_id: string | null
  character_id: string | null
  job_type: string
  status: string
  triggered_by: string
  params: Record<string, unknown>
  result: Record<string, unknown> | null
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface VoiceOutput {
  id: string
  job_id: string
  project_id: string
  scene_id: string | null
  character_id: string | null
  character_name: string | null
  dialogue_line: string
  language: string
  emotion: string
  voice_id: string | null
  storage_key: string
  duration_seconds: number
  sample_rate: number
  format: string
  file_size_bytes: number
  provider: string
  status: string
  metadata: Record<string, unknown>
  created_at: string
}

export interface VoiceRetryEntry {
  id: string
  project_id: string
  scene_id: string | null
  episode_id: string | null
  original_job_id: string | null
  status: string
  retry_count: number
  max_retries: number
  reason: string
  params: Record<string, unknown>
  next_retry_at: string | null
  created_at: string
  updated_at: string
}

export interface PaginationMeta {
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface VoiceJobListResponse {
  items: VoiceJob[]
  meta: PaginationMeta
}

export interface VoiceOutputListResponse {
  items: VoiceOutput[]
  meta: PaginationMeta
}

export interface VoiceRetryQueueListResponse {
  items: VoiceRetryEntry[]
  meta: PaginationMeta
}

export interface VoiceDashboardStats {
  total_jobs: number
  jobs_completed: number
  jobs_pending: number
  jobs_failed: number
  jobs_running: number
  total_voice_outputs: number
  total_retry_queue: number
  recent_jobs: VoiceJob[]
}

export interface DispatchResponse {
  job_id: string
  status: string
  message: string
  dispatch_mode: string
}

export interface TriggerVoiceLineRequest {
  project_id: string
  scene_id?: string
  episode_id?: string
  character_id?: string
  character_name?: string
  dialogue_line: string
  language?: string
  voice_id?: string
  emotion?: string
  speed?: number
  pitch?: number
  output_format?: string
  voice_seed?: number
  extra_params?: Record<string, unknown>
}

export interface SceneDialogueLine {
  character_id?: string
  character_name?: string
  dialogue_line: string
  language?: string
  voice_id?: string
  emotion?: string
  speed?: number
  voice_seed?: number
}

export interface TriggerSceneVoiceRequest {
  project_id: string
  scene_id: string
  episode_id?: string
  dialogue_lines: SceneDialogueLine[]
  output_format?: string
  extra_params?: Record<string, unknown>
}

// ---------------------------------------------------------------------------
// API client
// ---------------------------------------------------------------------------

export const voiceEngineApi = {
  getDashboard: (projectId: string): Promise<VoiceDashboardStats> =>
    apiClient.get(`/vo/dashboard/${projectId}`).then((r) => r.data),

  // Jobs
  listJobs: (
    projectId: string,
    params?: { page?: number; status?: string; job_type?: string }
  ): Promise<VoiceJobListResponse> =>
    apiClient
      .get('/vo/jobs', { params: { project_id: projectId, ...params } })
      .then((r) => r.data),

  getJob: (jobId: string): Promise<VoiceJob> =>
    apiClient.get(`/vo/jobs/${jobId}`).then((r) => r.data),

  // Outputs
  listOutputs: (
    projectId: string,
    params?: { page?: number; character_id?: string; language?: string; status?: string }
  ): Promise<VoiceOutputListResponse> =>
    apiClient
      .get('/vo/outputs', { params: { project_id: projectId, ...params } })
      .then((r) => r.data),

  getOutput: (outputId: string): Promise<VoiceOutput> =>
    apiClient.get(`/vo/outputs/${outputId}`).then((r) => r.data),

  // Retry queue
  listRetryQueue: (
    projectId: string,
    params?: { page?: number; status?: string }
  ): Promise<VoiceRetryQueueListResponse> =>
    apiClient
      .get('/vo/retry-queue', { params: { project_id: projectId, ...params } })
      .then((r) => r.data),

  retryEntry: (entryId: string): Promise<DispatchResponse> =>
    apiClient.post(`/vo/retry-queue/${entryId}/retry`).then((r) => r.data),

  // Triggers
  generateLine: (body: TriggerVoiceLineRequest): Promise<DispatchResponse> =>
    apiClient.post('/vo/generate/line', body).then((r) => r.data),

  generateScene: (body: TriggerSceneVoiceRequest): Promise<DispatchResponse> =>
    apiClient.post('/vo/generate/scene', body).then((r) => r.data),
}
