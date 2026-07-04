import apiClient from './client'

export interface SceneComposition {
  id: string
  scene_id: string
  background_id: string | null
  background_override: Record<string, unknown>
  camera: Record<string, unknown>
  lighting: Record<string, unknown>
  layers: Record<string, unknown>[]
  characters: Record<string, unknown>[]
  props: Record<string, unknown>[]
  canvas_width: number
  canvas_height: number
  status: string
  version: number
  created_at: string
  updated_at: string
}

export interface Timeline {
  id: string
  composition_id: string
  fps: number
  total_frames: number
  duration_seconds: number
  keyframes: Record<string, unknown>[]
  clips: Record<string, unknown>[]
  transitions: Record<string, unknown>[]
  camera_events: Record<string, unknown>[]
  audio_events: Record<string, unknown>[]
  subtitle_events: Record<string, unknown>[]
  playhead_frame: number
  created_at: string
  updated_at: string
}

export const compositionApi = {
  getByScene: (sceneId: string) =>
    apiClient.get<SceneComposition>(`/scenes/${sceneId}/composition`).then(r => r.data),

  getById: (compId: string) =>
    apiClient.get<SceneComposition>(`/compositions/${compId}`).then(r => r.data),

  update: (compId: string, data: Partial<SceneComposition>) =>
    apiClient.patch<SceneComposition>(`/compositions/${compId}`, data).then(r => r.data),

  addCharacter: (compId: string, charData: Record<string, unknown>) =>
    apiClient.post<SceneComposition>(`/compositions/${compId}/characters`, charData).then(r => r.data),

  removeCharacter: (compId: string, refId: string) =>
    apiClient.delete<SceneComposition>(`/compositions/${compId}/characters/${refId}`).then(r => r.data),

  addProp: (compId: string, propData: Record<string, unknown>) =>
    apiClient.post<SceneComposition>(`/compositions/${compId}/props`, propData).then(r => r.data),

  removeProp: (compId: string, refId: string) =>
    apiClient.delete<SceneComposition>(`/compositions/${compId}/props/${refId}`).then(r => r.data),

  getTimeline: (compId: string) =>
    apiClient.get<Timeline>(`/compositions/${compId}/timeline`).then(r => r.data),

  updateTimeline: (tlId: string, data: Partial<Timeline>) =>
    apiClient.patch<Timeline>(`/timelines/${tlId}`, data).then(r => r.data),

  addKeyframe: (tlId: string, keyframe: Record<string, unknown>) =>
    apiClient.post<Timeline>(`/timelines/${tlId}/keyframes`, keyframe).then(r => r.data),

  addClip: (tlId: string, clip: Record<string, unknown>) =>
    apiClient.post<Timeline>(`/timelines/${tlId}/clips`, clip).then(r => r.data),

  removeClip: (tlId: string, clipId: string) =>
    apiClient.delete<Timeline>(`/timelines/${tlId}/clips/${clipId}`).then(r => r.data),

  setPlayhead: (tlId: string, frame: number) =>
    apiClient.patch<Timeline>(`/timelines/${tlId}/playhead/${frame}`).then(r => r.data),
}
