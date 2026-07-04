import apiClient from './client'
import type { Plugin } from '@/types'

export const pluginsApi = {
  list: () => apiClient.get<Plugin[]>('/plugins').then((r) => r.data),
  get: (id: string) => apiClient.get<Plugin & Record<string, unknown>>(`/plugins/${id}`).then((r) => r.data),
}
