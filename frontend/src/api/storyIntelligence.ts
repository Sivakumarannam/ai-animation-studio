import apiClient from './client'
import type {
  World, Season, Episode, StoryScene, StoryIdea, StoryMemory,
  StoryEvaluation, GenerationJob, DispatchResult, StoryIntelligenceStats,
  StoryVersion, GenerationLog,
} from '@/types'

interface ListResponse<T> {
  items: T[]
  meta: { page: number; page_size: number; total: number; total_pages: number }
}

export const storyIntelligenceApi = {
  // Worlds
  listWorlds: (projectId: string, page = 1, pageSize = 20) =>
    apiClient
      .get<ListResponse<World>>(`/si/projects/${projectId}/worlds`, { params: { page, page_size: pageSize } })
      .then((r) => r.data),

  createWorld: (projectId: string, data: Partial<World>) =>
    apiClient.post<World>(`/si/projects/${projectId}/worlds`, data).then((r) => r.data),

  getWorld: (worldId: string) => apiClient.get<World>(`/si/worlds/${worldId}`).then((r) => r.data),

  updateWorld: (worldId: string, data: Partial<World>) =>
    apiClient.patch<World>(`/si/worlds/${worldId}`, data).then((r) => r.data),

  deleteWorld: (worldId: string) => apiClient.delete(`/si/worlds/${worldId}`),

  // Seasons
  listSeasons: (worldId: string, page = 1, pageSize = 20) =>
    apiClient
      .get<ListResponse<Season>>(`/si/worlds/${worldId}/seasons`, { params: { page, page_size: pageSize } })
      .then((r) => r.data),

  createSeason: (worldId: string, data: Partial<Season>) =>
    apiClient.post<Season>(`/si/worlds/${worldId}/seasons`, data).then((r) => r.data),

  getSeason: (seasonId: string) => apiClient.get<Season>(`/si/seasons/${seasonId}`).then((r) => r.data),

  updateSeason: (seasonId: string, data: Partial<Season>) =>
    apiClient.patch<Season>(`/si/seasons/${seasonId}`, data).then((r) => r.data),

  deleteSeason: (seasonId: string) => apiClient.delete(`/si/seasons/${seasonId}`),

  // Episodes
  listEpisodes: (seasonId: string, page = 1, pageSize = 20) =>
    apiClient
      .get<ListResponse<Episode>>(`/si/seasons/${seasonId}/episodes`, { params: { page, page_size: pageSize } })
      .then((r) => r.data),

  createEpisode: (seasonId: string, data: Partial<Episode>) =>
    apiClient.post<Episode>(`/si/seasons/${seasonId}/episodes`, data).then((r) => r.data),

  getEpisode: (episodeId: string) => apiClient.get<Episode>(`/si/episodes/${episodeId}`).then((r) => r.data),

  updateEpisode: (episodeId: string, data: Partial<Episode>) =>
    apiClient.patch<Episode>(`/si/episodes/${episodeId}`, data).then((r) => r.data),

  deleteEpisode: (episodeId: string) => apiClient.delete(`/si/episodes/${episodeId}`),

  evaluateEpisode: (episodeId: string) =>
    apiClient.post<StoryEvaluation>(`/si/episodes/${episodeId}/evaluate`).then((r) => r.data),

  listEpisodeVersions: (episodeId: string) =>
    apiClient.get<StoryVersion[]>(`/si/episodes/${episodeId}/versions`).then((r) => r.data),

  // Scenes
  listScenes: (episodeId: string, page = 1, pageSize = 50) =>
    apiClient
      .get<ListResponse<StoryScene>>(`/si/episodes/${episodeId}/scenes`, { params: { page, page_size: pageSize } })
      .then((r) => r.data),

  createScene: (episodeId: string, data: Partial<StoryScene>) =>
    apiClient.post<StoryScene>(`/si/episodes/${episodeId}/scenes`, data).then((r) => r.data),

  updateScene: (sceneId: string, data: Partial<StoryScene>) =>
    apiClient.patch<StoryScene>(`/si/scenes/${sceneId}`, data).then((r) => r.data),

  deleteScene: (sceneId: string) => apiClient.delete(`/si/scenes/${sceneId}`),

  // Ideas
  listIdeas: (projectId: string, page = 1, pageSize = 20) =>
    apiClient
      .get<ListResponse<StoryIdea>>(`/si/projects/${projectId}/ideas`, { params: { page, page_size: pageSize } })
      .then((r) => r.data),

  createIdea: (projectId: string, data: Partial<StoryIdea>) =>
    apiClient.post<StoryIdea>(`/si/projects/${projectId}/ideas`, data).then((r) => r.data),

  generateIdeas: (projectId: string, data: { genre?: string; story_type?: string; count?: number; world_id?: string | null }) =>
    apiClient.post<StoryIdea[]>(`/si/projects/${projectId}/ideas/generate`, data).then((r) => r.data),

  updateIdea: (ideaId: string, data: Partial<StoryIdea>) =>
    apiClient.patch<StoryIdea>(`/si/ideas/${ideaId}`, data).then((r) => r.data),

  deleteIdea: (ideaId: string) => apiClient.delete(`/si/ideas/${ideaId}`),

  // Memory
  listMemory: (worldId: string, page = 1, pageSize = 50) =>
    apiClient
      .get<ListResponse<StoryMemory>>(`/si/worlds/${worldId}/memory`, { params: { page, page_size: pageSize } })
      .then((r) => r.data),

  createMemory: (worldId: string, data: Partial<StoryMemory>) =>
    apiClient.post<StoryMemory>(`/si/worlds/${worldId}/memory`, data).then((r) => r.data),

  // Jobs
  listJobs: (projectId: string, page = 1, pageSize = 20, status?: string) =>
    apiClient
      .get<ListResponse<GenerationJob>>(`/si/projects/${projectId}/jobs`, { params: { page, page_size: pageSize, status } })
      .then((r) => r.data),

  getJob: (jobId: string) => apiClient.get<GenerationJob>(`/si/jobs/${jobId}`).then((r) => r.data),

  getJobLogs: (jobId: string) => apiClient.get<{ logs: GenerationLog[] }>(`/si/jobs/${jobId}/logs`).then((r) => r.data),

  // Pipeline / generation
  runFullPipeline: (
    projectId: string,
    data: { genre?: string; story_type?: string; episode_count?: number | null; world_id?: string | null; world_data?: Record<string, unknown> }
  ) => apiClient.post<DispatchResult>(`/si/projects/${projectId}/generate`, data).then((r) => r.data),

  generateEpisode: (seasonId: string, data: { season_id: string; world_id: string }) =>
    apiClient.post<DispatchResult>(`/si/seasons/${seasonId}/generate-episode`, data).then((r) => r.data),

  // Analytics
  getStats: (projectId: string) =>
    apiClient.get<StoryIntelligenceStats>(`/si/projects/${projectId}/stats`).then((r) => r.data),
}
