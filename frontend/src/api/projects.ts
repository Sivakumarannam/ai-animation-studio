import apiClient from './client'
import type { PaginatedResponse, Project } from '@/types'

export const projectsApi = {
  list: (page = 1, pageSize = 20, status?: string) =>
    apiClient
      .get<PaginatedResponse<Project>>('/projects', {
        params: { page, page_size: pageSize, status },
      })
      .then((r) => r.data),

  create: (data: { title: string; description?: string; plugin_id: string; animation_style?: string }) =>
    apiClient.post<Project>('/projects', data).then((r) => r.data),

  get: (id: string) => apiClient.get<Project>(`/projects/${id}`).then((r) => r.data),

  update: (id: string, data: Partial<Project>) =>
    apiClient.patch<Project>(`/projects/${id}`, data).then((r) => r.data),

  delete: (id: string) => apiClient.delete(`/projects/${id}`),
}
