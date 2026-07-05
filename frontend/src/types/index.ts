export interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  is_superuser: boolean
  plan: string
  language: string
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface Project {
  id: string
  user_id: string
  title: string
  description: string
  status: 'draft' | 'active' | 'archived'
  plugin_id: string
  animation_style: string
  metadata: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface Story {
  id: string
  project_id: string
  title: string
  premise: string
  full_script: string
  genre: string
  tone: string
  duration_target: number
  language: string
  status: 'draft' | 'generating' | 'ready' | 'failed'
  ai_metadata: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface Scene {
  id: string
  story_id: string
  scene_number: number
  title: string
  description: string
  dialogue: string
  action_notes: string
  duration_seconds: number
  background_id: string | null
  status: string
  ordering: number
  created_at: string
  updated_at: string
}

export interface Character {
  id: string
  project_id: string
  name: string
  description: string
  personality: string
  voice_profile: string
  age_range: string
  gender: string
  is_library: boolean
  thumbnail_url: string
  asset_data: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface Plugin {
  id: string
  name: string
  version: string
  description: string
  language: string
  animation_style: string
  tags: string[]
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

export interface ApiError {
  code: string
  message: string
  detail?: unknown
}

// ─────────────────────────────────────────────────────────────────────────
// Phase 3 — Story Intelligence
// ─────────────────────────────────────────────────────────────────────────

export interface World {
  id: string
  project_id: string
  name: string
  description: string
  rules: unknown[]
  locations: Record<string, unknown>
  timeline_data: unknown[]
  factions: unknown[]
  objects: unknown[]
  lore: string
  status: string
  created_at: string
  updated_at: string
}

export interface Season {
  id: string
  world_id: string
  project_id: string
  season_number: number
  title: string
  description: string
  story_arc: string
  status: string
  episode_count: number
  created_at: string
  updated_at: string
}

export interface Episode {
  id: string
  season_id: string
  world_id: string
  project_id: string
  episode_number: number
  title: string
  summary: string
  opening: string
  middle: string
  ending: string
  moral: string
  duration_target_seconds: number
  story_score: number
  status: string
  generation_metadata: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface StoryScene {
  id: string
  episode_id: string
  scene_number: number
  scene_goal: string
  location: string
  character_names: string[]
  dialogue: unknown[]
  narration: string
  image_prompt: string
  animation_prompt: string
  camera_direction: string
  duration_seconds: number
  status: string
  created_at: string
  updated_at: string
}

export interface StoryIdea {
  id: string
  project_id: string
  world_id: string | null
  title: string
  premise: string
  genre: string
  tone: string
  story_type: string
  target_audience: string
  estimated_episodes: number
  status: string
  created_at: string
  updated_at: string
}

export interface StoryMemory {
  id: string
  world_id: string
  memory_type: string
  key: string
  value: Record<string, unknown>
  episode_id: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface StoryEvaluation {
  id: string
  episode_id: string
  evaluator_version: string
  originality_score: number
  consistency_score: number
  creativity_score: number
  grammar_score: number
  flow_score: number
  entertainment_score: number
  educational_value_score: number
  story_arc_score: number
  dialogue_score: number
  overall_score: number
  feedback: Record<string, unknown>
  approved: boolean
  evaluated_at: string
  created_at: string
}

export interface GenerationJob {
  id: string
  project_id: string | null
  job_type: string
  entity_type: string
  entity_id: string | null
  status: string
  celery_task_id: string
  execution_mode: string
  progress_percent: number
  current_step: string
  result: Record<string, unknown>
  error_message: string
  retry_count: number
  max_retries: number
  started_at: string | null
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface DispatchResult {
  job_id: string
  task_id: string
  mode: string
  status: string
  result?: Record<string, unknown> | null
}

export interface StoryIntelligenceStats {
  worlds: number
  seasons: number
  episodes: number
  scenes: number
  ideas: number
  memories: number
  jobs_by_status: Record<string, number>
  avg_story_score: number
}

export interface StoryVersion {
  id: string
  entity_type: string
  entity_id: string
  version_number: number
  snapshot: Record<string, unknown>
  change_summary: string
  created_by: string
  created_at: string
}
