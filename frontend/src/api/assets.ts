import apiClient from '@/api/client'

// ─── Types ────────────────────────────────────────────────────────────────────

export interface PaginationMeta {
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface AssetProject {
  id: string
  project_id: string
  name: string
  description: string
  default_style_id: string | null
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

export interface AssetStyle {
  id: string
  name: string
  slug: string
  description: string
  style_type: string
  is_default: boolean
  is_active: boolean
  usage_count: number
  avg_quality_score: number
  created_at: string
  updated_at: string
}

export interface AssetCollection {
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

export interface Asset {
  id: string
  project_id: string
  collection_id: string | null
  character_id: string | null
  episode_id: string | null
  scene_id: string | null
  name: string
  description: string
  asset_type: string
  status: string
  current_version_id: string | null
  best_version_id: string | null
  version_count: number
  retry_count: number
  quality_score: number
  quality_threshold: number
  storage_key: string
  width: number
  height: number
  tags: string[]
  generation_params: Record<string, unknown>
  generated_at: string | null
  is_deleted: boolean
  created_at: string
  updated_at: string
}

export interface AssetVersion {
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
  evaluation_scores: Record<string, number>
  created_at: string
  updated_at: string
}

export interface AssetEvaluation {
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
}

export interface GenerationJob {
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
  params: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface RetryQueueEntry {
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
  retry_params: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface AssetPrompt {
  id: string
  asset_id: string | null
  full_prompt: string
  full_negative_prompt: string
  prompt_type: string
  quality_score: number
  was_successful: boolean
  use_count: number
  created_at: string
}

export interface LightingPreset {
  id: string
  name: string
  slug: string
  lighting_type: string
  lighting_prompt: string
  time_of_day: string
  weather: string
  intensity: number
  color_temperature: string
  is_active: boolean
  use_count: number
  avg_quality_score: number
}

export interface PosePreset {
  id: string
  name: string
  slug: string
  pose_type: string
  pose_prompt: string
  body_orientation: string
  is_active: boolean
  use_count: number
}

export interface ExpressionPreset {
  id: string
  name: string
  slug: string
  expression_type: string
  expression_prompt: string
  intensity: number
  is_active: boolean
  use_count: number
}

export interface DashboardStats {
  total_assets: number
  assets_completed: number
  assets_pending: number
  assets_failed: number
  assets_generating: number
  total_retries: number
  avg_quality_score: number
  assets_by_type: Record<string, number>
  recent_jobs: GenerationJob[]
  storage_bytes_used: number
  generation_history_7d: unknown[]
}

export interface DispatchResponse {
  job_id: string
  status: string
  message: string
  dispatch_mode: string
}

export interface TriggerEpisodeGenerationRequest {
  project_id: string
  episode_id: string
  asset_types?: string[]
  quality_threshold?: number
  max_retries?: number
  force_regenerate?: boolean
}

export interface AssetSearchRequest {
  query?: string
  project_id?: string
  asset_type?: string
  character_id?: string
  episode_id?: string
  tags?: string[]
  min_quality?: number
  status?: string
  limit?: number
  offset?: number
}

// ─── API calls ────────────────────────────────────────────────────────────────

const BASE = '/ag'

// Dashboard
export const getDashboard = (projectId: string) =>
  apiClient.get<DashboardStats>(`${BASE}/dashboard/${projectId}`)

// Projects
export const listAssetProjects = (page = 1, pageSize = 20) =>
  apiClient.get<{ items: AssetProject[]; meta: PaginationMeta }>(`${BASE}/projects`, {
    params: { page, page_size: pageSize },
  })

export const getAssetProject = (id: string) =>
  apiClient.get<AssetProject>(`${BASE}/projects/${id}`)

export const createAssetProject = (data: { project_id: string; name: string; description?: string; quality_threshold?: number }) =>
  apiClient.post<AssetProject>(`${BASE}/projects`, data)

// Styles
export const listStyles = (page = 1, pageSize = 20, styleType?: string) =>
  apiClient.get<{ items: AssetStyle[]; meta: PaginationMeta }>(`${BASE}/styles`, {
    params: { page, page_size: pageSize, ...(styleType && { style_type: styleType }) },
  })

// Collections
export const listCollections = (projectId: string, page = 1, pageSize = 20) =>
  apiClient.get<{ items: AssetCollection[]; meta: PaginationMeta }>(`${BASE}/collections`, {
    params: { project_id: projectId, page, page_size: pageSize },
  })

// Assets
export const listAssets = (
  projectId: string,
  opts: { assetType?: string; status?: string; characterId?: string; episodeId?: string; page?: number; pageSize?: number } = {}
) =>
  apiClient.get<{ items: Asset[]; meta: PaginationMeta }>(`${BASE}/assets`, {
    params: {
      project_id: projectId,
      ...(opts.assetType && { asset_type: opts.assetType }),
      ...(opts.status && { status: opts.status }),
      ...(opts.characterId && { character_id: opts.characterId }),
      ...(opts.episodeId && { episode_id: opts.episodeId }),
      page: opts.page ?? 1,
      page_size: opts.pageSize ?? 20,
    },
  })

export const getAsset = (id: string) =>
  apiClient.get<Asset>(`${BASE}/assets/${id}`)

export const deleteAsset = (id: string) =>
  apiClient.delete(`${BASE}/assets/${id}`)

// Versions
export const listAssetVersions = (assetId: string, page = 1, pageSize = 20) =>
  apiClient.get<{ items: AssetVersion[]; meta: PaginationMeta }>(`${BASE}/assets/${assetId}/versions`, {
    params: { page, page_size: pageSize },
  })

export const promoteVersion = (assetId: string, versionId: string) =>
  apiClient.post<Asset>(`${BASE}/assets/${assetId}/versions/${versionId}/promote`)

// Generation
export const triggerEpisodeGeneration = (data: TriggerEpisodeGenerationRequest) =>
  apiClient.post<DispatchResponse>(`${BASE}/generate/episode`, data)

export const triggerAssetGeneration = (assetId: string, forceRegenerate = false, customParams: Record<string, unknown> = {}) =>
  apiClient.post<DispatchResponse>(`${BASE}/generate/asset`, {
    asset_id: assetId,
    force_regenerate: forceRegenerate,
    custom_params: customParams,
  })

// Jobs
export const listJobs = (projectId: string, status?: string, page = 1, pageSize = 20) =>
  apiClient.get<{ items: GenerationJob[]; meta: PaginationMeta }>(`${BASE}/jobs`, {
    params: { project_id: projectId, ...(status && { status }), page, page_size: pageSize },
  })

export const getJob = (id: string) =>
  apiClient.get<GenerationJob>(`${BASE}/jobs/${id}`)

// Retry Queue
export const listRetryQueue = (projectId: string, status?: string, page = 1, pageSize = 20) =>
  apiClient.get<{ items: RetryQueueEntry[]; meta: PaginationMeta }>(`${BASE}/retry-queue`, {
    params: { project_id: projectId, ...(status && { status }), page, page_size: pageSize },
  })

export const retryEntry = (entryId: string) =>
  apiClient.post<DispatchResponse>(`${BASE}/retry-queue/${entryId}/retry`)

// Evaluations
export const listEvaluations = (assetId: string, page = 1, pageSize = 20) =>
  apiClient.get<{ items: AssetEvaluation[]; meta: PaginationMeta }>(`${BASE}/evaluations/${assetId}`, {
    params: { page, page_size: pageSize },
  })

// Prompts
export const listPrompts = (opts: { promptType?: string; successfulOnly?: boolean; page?: number; pageSize?: number } = {}) =>
  apiClient.get<{ items: AssetPrompt[]; meta: PaginationMeta }>(`${BASE}/prompts`, {
    params: {
      ...(opts.promptType && { prompt_type: opts.promptType }),
      ...(opts.successfulOnly !== undefined && { successful_only: opts.successfulOnly }),
      page: opts.page ?? 1,
      page_size: opts.pageSize ?? 20,
    },
  })

// Library
export const searchLibrary = (data: AssetSearchRequest) =>
  apiClient.post<{ items: Asset[]; total: number; query: string | null }>(`${BASE}/library/search`, data)

export const getCharacterLibrary = (projectId: string, page = 1, pageSize = 20) =>
  apiClient.get<{ items: Asset[]; meta: PaginationMeta }>(`${BASE}/library/characters`, {
    params: { project_id: projectId, page, page_size: pageSize },
  })

export const getBackgroundLibrary = (projectId: string, page = 1, pageSize = 20) =>
  apiClient.get<{ items: Asset[]; meta: PaginationMeta }>(`${BASE}/library/backgrounds`, {
    params: { project_id: projectId, page, page_size: pageSize },
  })

export const getPropLibrary = (projectId: string, page = 1, pageSize = 20) =>
  apiClient.get<{ items: Asset[]; meta: PaginationMeta }>(`${BASE}/library/props`, {
    params: { project_id: projectId, page, page_size: pageSize },
  })

// Presets
export const listLightingPresets = (page = 1, pageSize = 50) =>
  apiClient.get<{ items: LightingPreset[]; meta: PaginationMeta }>(`${BASE}/presets/lighting`, {
    params: { page, page_size: pageSize },
  })

export const listPosePresets = (page = 1, pageSize = 50) =>
  apiClient.get<{ items: PosePreset[]; meta: PaginationMeta }>(`${BASE}/presets/poses`, {
    params: { page, page_size: pageSize },
  })

export const listExpressionPresets = (page = 1, pageSize = 50) =>
  apiClient.get<{ items: ExpressionPreset[]; meta: PaginationMeta }>(`${BASE}/presets/expressions`, {
    params: { page, page_size: pageSize },
  })

// History
export const listGenerationHistory = (projectId: string, page = 1, pageSize = 20) =>
  apiClient.get(`${BASE}/history`, { params: { project_id: projectId, page, page_size: pageSize } })

// Embeddings
export const triggerEmbeddingUpdate = (projectId: string) =>
  apiClient.post<DispatchResponse>(`${BASE}/embeddings/update`, null, {
    params: { project_id: projectId },
  })
