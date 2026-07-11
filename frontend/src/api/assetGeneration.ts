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

// ─── AssetProject ─────────────────────────────────────────────────────────────

export interface AssetProjectCreate {
  project_id: string
  name?: string
  description?: string
  quality_threshold?: number
  max_retries?: number
  target_resolution?: string
  config?: Record<string, unknown>
}

export interface AssetProjectResponse {
  id: string
  project_id: string
  name: string
  description: string
  quality_threshold: number
  max_retries: number
  target_resolution: string
  is_active: boolean
  total_assets_generated: number
  total_retries: number
  avg_quality_score: number
  storage_bytes_used: number
  config: Record<string, unknown>
  created_at: string
  updated_at: string
}

// ─── AssetStyle ───────────────────────────────────────────────────────────────

export interface AssetStyleCreate {
  name: string
  slug: string
  description?: string
  style_prompt?: string
  negative_prompt?: string
  keywords?: string[]
  color_palette?: string[]
  reference_artists?: string[]
  style_type?: string
}

export interface AssetStyleResponse {
  id: string
  name: string
  slug: string
  description: string
  style_prompt: string
  negative_prompt: string
  keywords: string[]
  color_palette: string[]
  reference_artists: string[]
  style_type: string
  is_default: boolean
  is_active: boolean
  usage_count: number
  avg_quality_score: number
  created_at: string
  updated_at: string
}

// ─── AssetCollection ──────────────────────────────────────────────────────────

export interface AssetCollectionCreate {
  project_id: string
  name: string
  description?: string
  collection_type?: string
  tags?: string[]
}

export interface AssetCollectionResponse {
  id: string
  project_id: string
  name: string
  description: string
  collection_type: string
  asset_count: number
  is_active: boolean
  tags: string[]
  created_at: string
  updated_at: string
}

// ─── Asset ────────────────────────────────────────────────────────────────────

export interface AssetCreate {
  project_id: string
  name: string
  description?: string
  asset_type: string
  collection_id?: string | null
  style_id?: string | null
  character_id?: string | null
  episode_id?: string | null
  scene_id?: string | null
  tags?: string[]
  generation_params?: Record<string, unknown>
}

export interface AssetResponse {
  id: string
  project_id: string
  collection_id: string | null
  style_id: string | null
  character_id: string | null
  episode_id: string | null
  scene_id: string | null
  name: string
  description: string
  asset_type: string
  status: string
  version_count: number
  retry_count: number
  max_retries: number
  quality_score: number
  quality_threshold: number
  storage_key: string
  width: number
  height: number
  file_size_bytes: number
  mime_type: string
  tags: string[]
  generation_params: Record<string, unknown>
  generated_at: string | null
  is_deleted: boolean
  created_at: string
  updated_at: string
}

// ─── AssetVersion ─────────────────────────────────────────────────────────────

export interface AssetVersionResponse {
  id: string
  asset_id: string
  version_number: number
  version_label: string
  storage_key: string
  width: number
  height: number
  file_size_bytes: number
  quality_score: number
  is_approved: boolean
  is_rejected: boolean
  rejection_reason: string
  generation_seed: number
  generation_steps: number
  cfg_scale: number
  sampler: string
  generation_params: Record<string, unknown>
  evaluation_scores: Record<string, unknown>
  created_at: string
  updated_at: string
}

// ─── AssetPrompt ──────────────────────────────────────────────────────────────

export interface AssetPromptResponse {
  id: string
  asset_id: string | null
  positive_prompt: string
  negative_prompt: string
  style_prompt: string
  camera_prompt: string
  composition_prompt: string
  lighting_prompt: string
  color_prompt: string
  consistency_prompt: string
  full_prompt: string
  full_negative_prompt: string
  prompt_type: string
  quality_score: number
  was_successful: boolean
  use_count: number
  created_at: string
  updated_at: string
}

// ─── AssetEvaluation ─────────────────────────────────────────────────────────

export interface AssetEvaluationResponse {
  id: string
  asset_id: string
  version_id: string | null
  overall_score: number
  prompt_quality: number
  image_quality: number
  character_consistency: number
  background_consistency: number
  composition_score: number
  lighting_score: number
  style_match: number
  scene_match: number
  resolution_score: number
  artifact_score: number
  hands_score: number
  face_score: number
  text_error_score: number
  passed_threshold: boolean
  failure_reasons: string[]
  notes: string
  evaluated_by: string
  created_at: string
  updated_at: string
}

// ─── GenerationJob ────────────────────────────────────────────────────────────

export interface GenerationJobResponse {
  id: string
  project_id: string | null
  asset_id: string | null
  episode_id: string | null
  job_type: string
  status: string
  dispatch_mode: string
  celery_task_id: string
  result: Record<string, unknown>
  error_message: string
  started_at: string | null
  completed_at: string | null
  duration_ms: number
  retry_count: number
  max_retries: number
  params: Record<string, unknown>
  created_at: string
  updated_at: string
}

// ─── RetryQueue ───────────────────────────────────────────────────────────────

export interface RetryQueueResponse {
  id: string
  asset_id: string
  project_id: string
  failure_reason: string
  failure_details: string
  quality_score: number
  retry_count: number
  max_retries: number
  status: string
  priority: number
  last_retry_at: string | null
  resolved_at: string | null
  created_at: string
  updated_at: string
}

// ─── SceneComposition ─────────────────────────────────────────────────────────

export interface SceneCompositionResponse {
  id: string
  project_id: string
  scene_id: string | null
  episode_id: string | null
  name: string
  description: string
  composition_type: string
  foreground_elements: string[]
  midground_elements: string[]
  background_elements: string[]
  focus_point: string
  lighting_direction: string
  color_harmony: string
  negative_space: number
  composition_prompt: string
  layout_data: Record<string, unknown>
  created_at: string
  updated_at: string
}

// ─── CameraShot ───────────────────────────────────────────────────────────────

export interface CameraShotResponse {
  id: string
  composition_id: string | null
  scene_id: string | null
  episode_id: string | null
  shot_type: string
  shot_order: number
  description: string
  camera_movement: string
  focal_length: string
  depth_of_field: string
  camera_prompt: string
  asset_id: string | null
  quality_score: number
  shot_data: Record<string, unknown>
  created_at: string
  updated_at: string
}

// ─── Presets ──────────────────────────────────────────────────────────────────

export interface LightingPresetResponse {
  id: string
  name: string
  slug: string
  description: string
  lighting_type: string
  lighting_prompt: string
  time_of_day: string
  weather: string
  intensity: number
  color_temperature: string
  is_active: boolean
  use_count: number
  avg_quality_score: number
  created_at: string
  updated_at: string
}

export interface PosePresetResponse {
  id: string
  name: string
  slug: string
  description: string
  pose_type: string
  pose_prompt: string
  body_orientation: string
  is_active: boolean
  use_count: number
  avg_quality_score: number
  created_at: string
  updated_at: string
}

export interface ExpressionPresetResponse {
  id: string
  name: string
  slug: string
  description: string
  expression_type: string
  expression_prompt: string
  intensity: number
  is_active: boolean
  use_count: number
  avg_quality_score: number
  created_at: string
  updated_at: string
}

// ─── GenerationHistory ────────────────────────────────────────────────────────

export interface GenerationHistoryResponse {
  id: string
  project_id: string
  episode_id: string | null
  run_type: string
  triggered_by: string
  assets_planned: number
  assets_generated: number
  assets_accepted: number
  assets_rejected: number
  retries_count: number
  avg_quality_score: number
  duration_seconds: number
  run_status: string
  error_summary: string
  started_at: string | null
  finished_at: string | null
  created_at: string
  updated_at: string
}

// ─── AssetMemory ──────────────────────────────────────────────────────────────

export interface AssetMemoryResponse {
  id: string
  project_id: string
  memory_type: string
  scope: string
  key: string
  value: Record<string, unknown>
  confidence: number
  use_count: number
  last_used_at: string | null
  created_at: string
  updated_at: string
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

export interface AssetDashboardStats {
  total_assets: number
  assets_completed: number
  assets_pending: number
  assets_failed: number
  assets_generating: number
  total_retries: number
  avg_quality_score: number
  assets_by_type: Record<string, number>
  recent_jobs: GenerationJobResponse[]
  storage_bytes_used: number
  generation_history_7d: Record<string, unknown>[]
}

// ─── Dispatch ─────────────────────────────────────────────────────────────────

export interface DispatchResponse {
  job_id: string
  status: string
  message: string
  dispatch_mode: string
}

export interface TriggerEpisodeGenerationRequest {
  episode_id: string
  project_id: string
  asset_types?: string[]
  quality_threshold?: number
  max_retries?: number
  force_regenerate?: boolean
}

export interface TriggerAssetGenerationRequest {
  asset_id: string
  force_regenerate?: boolean
  custom_params?: Record<string, unknown>
}

// ─── Search ───────────────────────────────────────────────────────────────────

export interface AssetSearchRequest {
  query?: string
  asset_type?: string | null
  project_id?: string | null
  collection_id?: string | null
  character_id?: string | null
  episode_id?: string | null
  tags?: string[]
  min_quality?: number
  status?: string | null
  limit?: number
  offset?: number
}

export interface AssetSearchResponse {
  items: AssetResponse[]
  total: number
  query: string
}

// ─── API Client ───────────────────────────────────────────────────────────────

const BASE = '/ag'

export const assetGenerationApi = {
  // Dashboard
  getDashboard: (projectId: string) =>
    apiClient.get<AssetDashboardStats>(`${BASE}/dashboard/${projectId}`).then((r) => r.data),

  // Asset Projects
  createProject: (data: AssetProjectCreate) =>
    apiClient.post<AssetProjectResponse>(`${BASE}/projects`, data).then((r) => r.data),
  listProjects: (page = 1, pageSize = 20) =>
    apiClient
      .get<Paginated<AssetProjectResponse>>(`${BASE}/projects`, { params: { page, page_size: pageSize } })
      .then((r) => r.data),
  getProject: (apId: string) =>
    apiClient.get<AssetProjectResponse>(`${BASE}/projects/${apId}`).then((r) => r.data),

  // Styles
  createStyle: (data: AssetStyleCreate) =>
    apiClient.post<AssetStyleResponse>(`${BASE}/styles`, data).then((r) => r.data),
  listStyles: (page = 1, pageSize = 20, styleType?: string) =>
    apiClient
      .get<Paginated<AssetStyleResponse>>(`${BASE}/styles`, { params: { page, page_size: pageSize, style_type: styleType } })
      .then((r) => r.data),

  // Collections
  createCollection: (data: AssetCollectionCreate) =>
    apiClient.post<AssetCollectionResponse>(`${BASE}/collections`, data).then((r) => r.data),
  listCollections: (projectId: string, page = 1, pageSize = 20) =>
    apiClient
      .get<Paginated<AssetCollectionResponse>>(`${BASE}/collections`, { params: { project_id: projectId, page, page_size: pageSize } })
      .then((r) => r.data),

  // Assets
  createAsset: (data: AssetCreate) =>
    apiClient.post<AssetResponse>(`${BASE}/assets`, data).then((r) => r.data),
  listAssets: (
    projectId: string,
    options?: { asset_type?: string; status?: string; character_id?: string; episode_id?: string; collection_id?: string; page?: number; page_size?: number }
  ) =>
    apiClient
      .get<Paginated<AssetResponse>>(`${BASE}/assets`, {
        params: { project_id: projectId, ...options },
      })
      .then((r) => r.data),
  getAsset: (assetId: string) =>
    apiClient.get<AssetResponse>(`${BASE}/assets/${assetId}`).then((r) => r.data),
  deleteAsset: (assetId: string) =>
    apiClient.delete(`${BASE}/assets/${assetId}`),

  // Asset Versions
  listAssetVersions: (assetId: string, page = 1, pageSize = 20) =>
    apiClient
      .get<Paginated<AssetVersionResponse>>(`${BASE}/assets/${assetId}/versions`, { params: { page, page_size: pageSize } })
      .then((r) => r.data),
  promoteVersion: (assetId: string, versionId: string) =>
    apiClient.post<AssetResponse>(`${BASE}/assets/${assetId}/versions/${versionId}/promote`).then((r) => r.data),

  // Generation triggers
  triggerEpisodeGeneration: (data: TriggerEpisodeGenerationRequest) =>
    apiClient.post<DispatchResponse>(`${BASE}/generate/episode`, data).then((r) => r.data),
  triggerAssetGeneration: (data: TriggerAssetGenerationRequest) =>
    apiClient.post<DispatchResponse>(`${BASE}/generate/asset`, data).then((r) => r.data),

  // Retry Queue
  listRetryQueue: (projectId: string, options?: { status?: string; page?: number; page_size?: number }) =>
    apiClient
      .get<Paginated<RetryQueueResponse>>(`${BASE}/retry-queue`, { params: { project_id: projectId, ...options } })
      .then((r) => r.data),
  retryEntry: (entryId: string) =>
    apiClient.post<DispatchResponse>(`${BASE}/retry-queue/${entryId}/retry`).then((r) => r.data),

  // Jobs
  listJobs: (projectId: string, options?: { status?: string; page?: number; page_size?: number }) =>
    apiClient
      .get<Paginated<GenerationJobResponse>>(`${BASE}/jobs`, { params: { project_id: projectId, ...options } })
      .then((r) => r.data),
  getJob: (jobId: string) =>
    apiClient.get<GenerationJobResponse>(`${BASE}/jobs/${jobId}`).then((r) => r.data),

  // Evaluations
  listEvaluations: (assetId: string, page = 1, pageSize = 20) =>
    apiClient
      .get<Paginated<AssetEvaluationResponse>>(`${BASE}/evaluations/${assetId}`, { params: { page, page_size: pageSize } })
      .then((r) => r.data),

  // Prompts
  listPrompts: (options?: { prompt_type?: string; successful_only?: boolean; page?: number; page_size?: number }) =>
    apiClient
      .get<Paginated<AssetPromptResponse>>(`${BASE}/prompts`, { params: options })
      .then((r) => r.data),
  getPrompt: (promptId: string) =>
    apiClient.get<AssetPromptResponse>(`${BASE}/prompts/${promptId}`).then((r) => r.data),

  // Library search
  searchLibrary: (data: AssetSearchRequest) =>
    apiClient.post<AssetSearchResponse>(`${BASE}/library/search`, data).then((r) => r.data),
  getCharacterLibrary: (projectId: string, page = 1, pageSize = 20) =>
    apiClient
      .get<Paginated<AssetResponse>>(`${BASE}/library/characters`, { params: { project_id: projectId, page, page_size: pageSize } })
      .then((r) => r.data),
  getBackgroundLibrary: (projectId: string, page = 1, pageSize = 20) =>
    apiClient
      .get<Paginated<AssetResponse>>(`${BASE}/library/backgrounds`, { params: { project_id: projectId, page, page_size: pageSize } })
      .then((r) => r.data),
  getPropLibrary: (projectId: string, page = 1, pageSize = 20) =>
    apiClient
      .get<Paginated<AssetResponse>>(`${BASE}/library/props`, { params: { project_id: projectId, page, page_size: pageSize } })
      .then((r) => r.data),

  // Presets
  listLightingPresets: (page = 1, pageSize = 50) =>
    apiClient
      .get<Paginated<LightingPresetResponse>>(`${BASE}/presets/lighting`, { params: { page, page_size: pageSize } })
      .then((r) => r.data),
  listPosePresets: (page = 1, pageSize = 50) =>
    apiClient
      .get<Paginated<PosePresetResponse>>(`${BASE}/presets/poses`, { params: { page, page_size: pageSize } })
      .then((r) => r.data),
  listExpressionPresets: (page = 1, pageSize = 50) =>
    apiClient
      .get<Paginated<ExpressionPresetResponse>>(`${BASE}/presets/expressions`, { params: { page, page_size: pageSize } })
      .then((r) => r.data),

  // Compositions & Shots
  listCompositions: (projectId: string, page = 1, pageSize = 20) =>
    apiClient
      .get<Paginated<SceneCompositionResponse>>(`${BASE}/compositions`, { params: { project_id: projectId, page, page_size: pageSize } })
      .then((r) => r.data),
  listShots: (episodeId: string, page = 1, pageSize = 50) =>
    apiClient
      .get<Paginated<CameraShotResponse>>(`${BASE}/shots`, { params: { episode_id: episodeId, page, page_size: pageSize } })
      .then((r) => r.data),

  // Generation History
  listHistory: (projectId: string, page = 1, pageSize = 20) =>
    apiClient
      .get<Paginated<GenerationHistoryResponse>>(`${BASE}/history`, { params: { project_id: projectId, page, page_size: pageSize } })
      .then((r) => r.data),

  // Asset Memory
  listMemory: (projectId: string, page = 1, pageSize = 20) =>
    apiClient
      .get<Paginated<AssetMemoryResponse>>(`${BASE}/memory`, { params: { project_id: projectId, page, page_size: pageSize } })
      .then((r) => r.data),

  // Embeddings
  updateEmbeddings: (projectId: string) =>
    apiClient
      .post<DispatchResponse>(`${BASE}/embeddings/update`, null, { params: { project_id: projectId } })
      .then((r) => r.data),
}
