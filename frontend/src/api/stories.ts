import apiClient from './client'
import type { PaginatedResponse, Story } from '@/types'

export const storiesApi = {
  list: (projectId: string, page = 1, pageSize = 20) =>
    apiClient
      .get<PaginatedResponse<Story>>(`/projects/${projectId}/stories`, {
        params: { page, page_size: pageSize },
      })
      .then((r) => r.data),

  create: (
    projectId: string,
    data: { title: string; premise?: string; genre?: string; tone?: string; duration_target?: number; language?: string }
  ) => apiClient.post<Story>(`/projects/${projectId}/stories`, data).then((r) => r.data),

  get: (id: string) => apiClient.get<Story>(`/stories/${id}`).then((r) => r.data),

  update: (id: string, data: Partial<Story>) =>
    apiClient.patch<Story>(`/stories/${id}`, data).then((r) => r.data),

  delete: (id: string) => apiClient.delete(`/stories/${id}`),
}
