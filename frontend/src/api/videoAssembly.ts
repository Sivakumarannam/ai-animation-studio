/**
 * Phase 10 — Video Assembly Engine API client.
 * Mirrors musicEngine.ts structure exactly.
 */

const BASE = "/api/v1/va";

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

// ─── helpers ───────────────────────────────────────────────────────────────

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...init?.headers },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.message ?? res.statusText);
  }
  return res.json();
}

// ─── API ───────────────────────────────────────────────────────────────────

export const videoAssemblyApi = {
  getDashboard: (projectId: string) =>
    apiFetch<VideoAssemblyDashboardStats>(`${BASE}/dashboard/${projectId}`),

  listJobs: (projectId: string, params?: { page?: number; page_size?: number; status?: string }) => {
    const q = new URLSearchParams({ project_id: projectId, ...params } as Record<string, string>);
    return apiFetch<{ items: VideoAssemblyJob[]; meta: PaginationMeta }>(`${BASE}/jobs?${q}`);
  },

  getJob: (jobId: string) =>
    apiFetch<VideoAssemblyJob>(`${BASE}/jobs/${jobId}`),

  listOutputs: (projectId: string, params?: { page?: number; page_size?: number; output_type?: string }) => {
    const q = new URLSearchParams({ project_id: projectId, ...params } as Record<string, string>);
    return apiFetch<{ items: VideoOutput[]; meta: PaginationMeta }>(`${BASE}/outputs?${q}`);
  },

  getOutput: (outputId: string) =>
    apiFetch<VideoOutput>(`${BASE}/outputs/${outputId}`),

  listRetryQueue: (projectId: string, params?: { page?: number; page_size?: number }) => {
    const q = new URLSearchParams({ project_id: projectId, ...params } as Record<string, string>);
    return apiFetch<{ items: VideoRetryEntry[]; meta: PaginationMeta }>(`${BASE}/retry-queue?${q}`);
  },

  triggerAssembleEpisode: (req: TriggerAssembleEpisodeRequest) =>
    apiFetch<DispatchResponse>(`${BASE}/generate/assemble-episode`, {
      method: "POST",
      body: JSON.stringify(req),
    }),

  sweepRetryQueue: (projectId: string, limit = 10) =>
    apiFetch<DispatchResponse>(`${BASE}/retry-queue/sweep`, {
      method: "POST",
      body: JSON.stringify({ project_id: projectId, limit }),
    }),
};
