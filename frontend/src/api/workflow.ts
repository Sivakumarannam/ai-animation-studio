import apiClient from './client'

// ─── Shared ───────────────────────────────────────────────────────────────────

export type WorkflowState =
  | 'pending'
  | 'running'
  | 'paused'
  | 'completed'
  | 'failed'
  | 'cancelled'

export const PIPELINE_STEPS = [
  { name: 'story_generation',    label: 'Story Generation',    order: 1 },
  { name: 'scene_breakdown',     label: 'Scene Breakdown',     order: 2 },
  { name: 'character_resolution',label: 'Character Resolution',order: 3 },
  { name: 'asset_generation',    label: 'Asset Generation',    order: 4 },
  { name: 'voice_generation',    label: 'Voice Generation',    order: 5 },
  { name: 'subtitle_generation', label: 'Subtitle Generation', order: 6 },
  { name: 'video_render',        label: 'Video Render',        order: 7 },
]

// ─── Types ───────────────────────────────────────────────────────────────────

export interface WorkflowRun {
  run_id: string
  story_id: string
  project_id: string
  user_id: string
  plugin_id: string
  state: WorkflowState
  current_step: string
  completed_steps: string[]
  failed_steps: string[]
  errors: Record<string, string>
  progress_percent: number
  progress_message: string
  created_at: string
  updated_at: string
  metadata: Record<string, unknown>
}

export interface WorkflowStartRequest {
  story_id: string
  project_id: string
  plugin_id?: string
  settings?: Record<string, unknown>
}

export interface WorkflowStartResponse {
  run_id: string
  state: WorkflowState
  message: string
}

// ─── API client ───────────────────────────────────────────────────────────────

export const workflowApi = {
  listRuns: (projectId?: string): Promise<WorkflowRun[]> =>
    apiClient.get('/workflow/runs', { params: projectId ? { project_id: projectId } : undefined }),

  getRun: (runId: string): Promise<WorkflowRun> =>
    apiClient.get(`/workflow/runs/${runId}`),

  startRun: (body: WorkflowStartRequest): Promise<WorkflowStartResponse> =>
    apiClient.post('/workflow/runs', body),

  pause: (runId: string): Promise<WorkflowRun> =>
    apiClient.post(`/workflow/runs/${runId}/pause`),

  resume: (runId: string): Promise<{ run_id: string; state: string; message: string }> =>
    apiClient.post(`/workflow/runs/${runId}/resume`),

  cancel: (runId: string): Promise<WorkflowRun> =>
    apiClient.post(`/workflow/runs/${runId}/cancel`),

  deleteRun: (runId: string): Promise<void> =>
    apiClient.delete(`/workflow/runs/${runId}`),
}
