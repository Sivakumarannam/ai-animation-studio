import apiClient from './client'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface MusicJob {
  id: string
  project_id: string
  scene_id: string | null
  episode_id: string | null
  job_type: string
  status: string
  mood: string
  triggered_by: string
  params: Record<string, unknown>
  result: Record<string, unknown> | null
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface MusicOutput {
  id: string
  job_id: string
  project_id: string
  scene_id: string | null
  episode_id: string | null
  output_type: string
  mood: string
  loop_type: string
  storage_key: string
  duration_seconds: number
  sample_rate: number
  format: string
  file_size_bytes: number
  provider: string
  copyright_safe: boolean
  status: string
  created_at: string
}

export interface SFXAsset {
  id: string
  sfx_key: string
  name: string
  description: string
  category: string
  tags: string[]
  storage_key: string
  duration_seconds: number
  format: string
  sample_rate: number
  is_builtin: boolean
  is_active: boolean
  created_at: string
}

export interface MusicRetryEntry {
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

export interface MusicJobListResponse {
  items: MusicJob[]
  meta: PaginationMeta
}

export interface MusicOutputListResponse {
  items: MusicOutput[]
  meta: PaginationMeta
}

export interface SFXAssetListResponse {
  items: SFXAsset[]
  meta: PaginationMeta
}

export interface MusicRetryQueueListResponse {
  items: MusicRetryEntry[]
  meta: PaginationMeta
}

export interface MusicDashboardStats {
  total_jobs: number
  jobs_completed: number
  jobs_pending: number
  jobs_failed: number
  jobs_running: number
  total_music_outputs: number
  total_sfx_assets: number
  total_retry_queue: number
  recent_jobs: MusicJob[]
}

export interface DispatchResponse {
  job_id: string
  status: string
  message: string
  dispatch_mode: string
}

export interface TriggerMusicTrackRequest {
  project_id: string
  scene_id?: string
  episode_id?: string
  mood?: string
  duration_seconds?: number
  loop_type?: string
  prompt?: string
  bpm?: number
  instruments?: string[]
  output_format?: string
  extra_params?: Record<string, unknown>
}

export interface TriggerSceneAudioRequest {
  project_id: string
  scene_id: string
  episode_id?: string
  mood?: string
  duration_seconds?: number
  output_format?: string
  include_sfx?: boolean
  sfx_keys?: string[]
  extra_params?: Record<string, unknown>
}

// ---------------------------------------------------------------------------
// API client
// ---------------------------------------------------------------------------

export const musicEngineApi = {
  getDashboard: (projectId: string): Promise<MusicDashboardStats> =>
    apiClient.get(`/mu/dashboard/${projectId}`).then((r) => r.data),

  // Jobs
  listJobs: (
    projectId: string,
    params?: { page?: number; status?: string; job_type?: string }
  ): Promise<MusicJobListResponse> =>
    apiClient
      .get('/mu/jobs', { params: { project_id: projectId, ...params } })
      .then((r) => r.data),

  getJob: (jobId: string): Promise<MusicJob> =>
    apiClient.get(`/mu/jobs/${jobId}`).then((r) => r.data),

  // Outputs
  listOutputs: (
    projectId: string,
    params?: { page?: number; mood?: string; output_type?: string; status?: string }
  ): Promise<MusicOutputListResponse> =>
    apiClient
      .get('/mu/outputs', { params: { project_id: projectId, ...params } })
      .then((r) => r.data),

  getOutput: (outputId: string): Promise<MusicOutput> =>
    apiClient.get(`/mu/outputs/${outputId}`).then((r) => r.data),

  // SFX Library
  listSFX: (params?: {
    page?: number
    category?: string
    search?: string
  }): Promise<SFXAssetListResponse> =>
    apiClient.get('/mu/sfx', { params }).then((r) => r.data),

  getSFX: (sfxKey: string): Promise<SFXAsset> =>
    apiClient.get(`/mu/sfx/${sfxKey}`).then((r) => r.data),

  // Retry queue
  listRetryQueue: (
    projectId: string,
    params?: { page?: number; status?: string }
  ): Promise<MusicRetryQueueListResponse> =>
    apiClient
      .get('/mu/retry-queue', { params: { project_id: projectId, ...params } })
      .then((r) => r.data),

  processRetryQueue: (projectId: string): Promise<DispatchResponse> =>
    apiClient
      .post('/mu/retry-queue/process', null, { params: { project_id: projectId } })
      .then((r) => r.data),

  // Triggers
  generateTrack: (body: TriggerMusicTrackRequest): Promise<DispatchResponse> =>
    apiClient.post('/mu/generate/track', body).then((r) => r.data),

  generateSceneAudio: (body: TriggerSceneAudioRequest): Promise<DispatchResponse> =>
    apiClient.post('/mu/generate/scene-audio', body).then((r) => r.data),
}
