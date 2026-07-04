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
