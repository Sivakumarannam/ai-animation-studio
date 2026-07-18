/**
 * Phase 10 — Video Assembly Engine API client.
 * Mirrors musicEngine.ts structure exactly.
 */
import apiClient from './client'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface VideoAssemblyJob {
  id: string;
  project_id: string;
  episode_id: string | null;
  job_type: string;
  status: "pending" | "running" | "completed" | "failed";
  mode: string;
  triggered_by: string;
  params: Record<string, unknown>;
  result: Record<string, unknown> | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  created_at: string;
  updated_at: string;
}

export interface VideoOutput {
  id: string;
  job_id: string;
  project_id: string;
  episode_id: string | null;
  output_type: string;
  status: string;
  storage_key: string;
  storage_bucket: string;
  file_size_bytes: number;
  duration_seconds: number;
  width: number;
  height: number;
  fps: number;
  format: string;
  provider: string;
  scene_count: number;
  has_voice: boolean;
  has_music: boolean;
  has_subtitles: boolean;
  quality_passed: boolean;
  quality_score: number;
  output_metadata: Record<string, unknown>;
  created_at: string;
}

export interface VideoRetryEntry {
  id: string;
  project_id: string;
  episode_id: string | null;
  original_job_id: string | null;
  status: string;
  retry_count: number;
  max_retries: number;
  reason: string;
  params: Record<string, unknown>;
  next_retry_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaginationMeta {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface VideoAssemblyDashboardStats {
  total_jobs: number;
  jobs_completed: number;
  jobs_pending: number;
  jobs_failed: number;
  jobs_running: number;
  total_video_outputs: number;
  total_retry_entries: number;
  recent_jobs: VideoAssemblyJob[];
}

export interface DispatchResponse {
  job_id: string;
  task_id: string;
  mode: string;
  status: string;
}

export interface TriggerAssembleEpisodeRequest {
  project_id: string;
  episode_id?: string | null;
  output_type?: "episode_cut" | "short_form_cut";
  width?: number;
  height?: number;
  fps?: number;
  include_subtitles?: boolean;
  triggered_by?: string;
}

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

const BASE = '/va'

export const videoAssemblyApi = {
  getDashboard: (projectId: string) =>
    apiClient
      .get<VideoAssemblyDashboardStats>(`${BASE}/dashboard/${projectId}`)
      .then((r) => r.data),

  listJobs: (
    projectId: string,
    params?: { page?: number; page_size?: number; status?: string }
  ) =>
    apiClient
      .get<{ items: VideoAssemblyJob[]; meta: PaginationMeta }>(`${BASE}/jobs`, {
        params: { project_id: projectId, ...params },
      })
      .then((r) => r.data),

  getJob: (jobId: string) =>
    apiClient.get<VideoAssemblyJob>(`${BASE}/jobs/${jobId}`).then((r) => r.data),

  listOutputs: (
    projectId: string,
    params?: { page?: number; page_size?: number; output_type?: string }
  ) =>
    apiClient
      .get<{ items: VideoOutput[]; meta: PaginationMeta }>(`${BASE}/outputs`, {
        params: { project_id: projectId, ...params },
      })
      .then((r) => r.data),

  getOutput: (outputId: string) =>
    apiClient.get<VideoOutput>(`${BASE}/outputs/${outputId}`).then((r) => r.data),

  listRetryQueue: (projectId: string, params?: { page?: number; page_size?: number }) =>
    apiClient
      .get<{ items: VideoRetryEntry[]; meta: PaginationMeta }>(`${BASE}/retry-queue`, {
        params: { project_id: projectId, ...params },
      })
      .then((r) => r.data),

  triggerAssembleEpisode: (req: TriggerAssembleEpisodeRequest) =>
    apiClient
      .post<DispatchResponse>(`${BASE}/generate/assemble-episode`, req)
      .then((r) => r.data),

  sweepRetryQueue: (projectId: string, limit = 10) =>
    apiClient
      .post<DispatchResponse>(`${BASE}/retry-queue/sweep`, { project_id: projectId, limit })
      .then((r) => r.data),
};