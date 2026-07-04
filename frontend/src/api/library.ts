import apiClient from './client'

export interface Expression {
  id: string
  name: string
  slug: string
  description: string
  category: string
  rig_data: Record<string, unknown>
  thumbnail_url: string
  preview_url: string
  tags: string[]
  intensity: number
  is_library: boolean
  sort_order: number
  created_at: string
  updated_at: string
}

export interface Pose {
  id: string
  name: string
  slug: string
  description: string
  category: string
  rig_data: Record<string, unknown>
  thumbnail_url: string
  preview_url: string
  tags: string[]
  duration_frames: number
  is_loopable: boolean
  is_library: boolean
  sort_order: number
  created_at: string
  updated_at: string
}

export interface CharacterTemplate {
  id: string
  name: string
  name_local: string
  slug: string
  archetype: string
  plugin_id: string
  description: string
  personality: string
  age_range: string
  gender: string
  language: string
  voice_profile: Record<string, unknown>
  animation_rig: Record<string, unknown>
  clothing_variants: Record<string, unknown>[]
  accessories: Record<string, unknown>[]
  thumbnail_url: string
  preview_url: string
  tags: string[]
  typical_expressions: string[]
  is_library: boolean
  version: number
  sort_order: number
  created_at: string
  updated_at: string
}

export interface Background {
  id: string
  name: string
  category: string
  tags: string[]
  file_url: string
  thumbnail_url: string
  is_library: boolean
  project_id: string | null
  created_at: string
}

export interface Prop {
  id: string
  name: string
  category: string
  tags: string[]
  file_url: string
  thumbnail_url: string
  is_library: boolean
  project_id: string | null
  created_at: string
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

// Expressions
export const libraryApi = {
  getExpressions: (params?: { page?: number; page_size?: number; category?: string; search?: string }) =>
    apiClient.get<PaginatedResponse<Expression>>('/library/expressions', { params }).then(r => r.data),

  getAllExpressions: () =>
    apiClient.get<Expression[]>('/library/expressions/all').then(r => r.data),

  seedExpressions: () =>
    apiClient.post('/library/expressions/seed').then(r => r.data),

  // Poses
  getPoses: (params?: { page?: number; page_size?: number; category?: string; search?: string }) =>
    apiClient.get<PaginatedResponse<Pose>>('/library/poses', { params }).then(r => r.data),

  getAllPoses: () =>
    apiClient.get<Pose[]>('/library/poses/all').then(r => r.data),

  seedPoses: () =>
    apiClient.post('/library/poses/seed').then(r => r.data),

  // Character Templates
  getCharacterTemplates: (params?: { page?: number; page_size?: number; plugin_id?: string; search?: string }) =>
    apiClient.get<PaginatedResponse<CharacterTemplate>>('/library/character-templates', { params }).then(r => r.data),

  getCharacterTemplatesByPlugin: (pluginId: string) =>
    apiClient.get<CharacterTemplate[]>(`/library/character-templates/by-plugin/${pluginId}`).then(r => r.data),

  seedCharacterTemplates: (pluginId: string) =>
    apiClient.post(`/library/character-templates/seed/${pluginId}`).then(r => r.data),

  // Backgrounds
  getBackgrounds: (params?: { page?: number; page_size?: number; category?: string; search?: string }) =>
    apiClient.get<PaginatedResponse<Background>>('/library/backgrounds', { params }).then(r => r.data),

  getBgCategories: () =>
    apiClient.get<string[]>('/library/backgrounds/categories').then(r => r.data),

  seedBackgrounds: () =>
    apiClient.post('/library/backgrounds/seed').then(r => r.data),

  // Props
  getProps: (params?: { page?: number; page_size?: number; category?: string; search?: string }) =>
    apiClient.get<PaginatedResponse<Prop>>('/library/props', { params }).then(r => r.data),

  getPropCategories: () =>
    apiClient.get<string[]>('/library/props/categories').then(r => r.data),

  seedProps: () =>
    apiClient.post('/library/props/seed').then(r => r.data),

  // Unified Asset Manager REST Client
  getAssets: (type: string, params?: { page?: number; page_size?: number; category?: string; search?: string; tags?: string; deleted?: boolean }) =>
    apiClient.get<PaginatedResponse<any>>(`/asset-manager/${type}`, { params }).then(r => r.data),

  createAsset: (type: string, data: any) =>
    apiClient.post<any>(`/asset-manager/${type}`, data).then(r => r.data),

  updateAsset: (type: string, id: string, data: any) =>
    apiClient.patch<any>(`/asset-manager/${type}/${id}`, data).then(r => r.data),

  deleteAsset: (type: string, id: string) =>
    apiClient.delete(`/asset-manager/${type}/${id}`).then(r => r.data),

  restoreAsset: (type: string, id: string) =>
    apiClient.post(`/asset-manager/${type}/${id}/restore`).then(r => r.data),

  bulkDelete: (type: string, ids: string[]) =>
    apiClient.post(`/asset-manager/${type}/bulk-delete`, { ids }).then(r => r.data),

  bulkRestore: (type: string, ids: string[]) =>
    apiClient.post(`/asset-manager/${type}/bulk-restore`, { ids }).then(r => r.data),

  bulkUpdate: (type: string, ids: string[], category?: string, tags?: string[], metadata_?: Record<string, any>) =>
    apiClient.post(`/asset-manager/${type}/bulk-update`, { ids, category, tags, metadata_ }).then(r => r.data),

  uploadAssetFile: (file: File, assetType: string) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post('/asset-manager/upload', formData, {
      params: { asset_type: assetType },
      headers: { 'Content-Type': 'multipart/form-data' }
    }).then(r => r.data)
  },

  getAssetVersions: (type: string, id: string, params?: { page?: number; page_size?: number }) =>
    apiClient.get<PaginatedResponse<any>>(`/asset-manager/versions/${type}/${id}`, { params }).then(r => r.data),

  createAssetVersion: (type: string, id: string, snapshot: any, changeSummary: string) =>
    apiClient.post(`/asset-manager/versions/${type}/${id}`, { snapshot, change_summary: changeSummary }).then(r => r.data),

  restoreAssetVersion: (type: string, id: string, versionNumber: number) =>
    apiClient.post(`/asset-manager/versions/${type}/${id}/${versionNumber}/restore`).then(r => r.data),

  getAssetStats: () =>
    apiClient.get<Record<string, number>>('/asset-manager/stats').then(r => r.data),

  seedAssets: (type: string) =>
    apiClient.post(`/asset-manager/${type}/seed`).then(r => r.data),
}
