import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Play, Pause, SkipBack, SkipForward, Volume2, VolumeX,
  Maximize2, Download, Film, Clock,
} from 'lucide-react'
import apiClient from '@/api/client'
import { Spinner } from '@/components/ui/Spinner'
import { clsx } from 'clsx'

interface Story {
  id: string
  title: string
  status: string
  scene_count: number
  duration_seconds: number
  created_at: string
}

interface Scene {
  id: string
  scene_number: number
  title: string
  description: string
  duration_seconds: number
  status: string
}

export function PreviewPlayerPage() {
  const { projectId, storyId } = useParams<{ projectId: string; storyId: string }>()
  const [currentScene, setCurrentScene] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [volume, setVolume] = useState(80)

  const { data: story, isLoading: storyLoading } = useQuery<Story>({
    queryKey: ['story', storyId],
    queryFn: () => apiClient.get<Story>(`/stories/${storyId}`).then(r => r.data),
    enabled: !!storyId,
  })

  const { data: scenes, isLoading: scenesLoading } = useQuery<{ items: Scene[] }>({
    queryKey: ['story-scenes', storyId],
    queryFn: () => apiClient.get<{ items: Scene[] }>(`/stories/${storyId}/scenes`).then(r => r.data),
    enabled: !!storyId,
  })

  const sceneList = scenes?.items ?? []
  const activeScene = sceneList[currentScene]

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60)
    const s = Math.floor(secs % 60)
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  const totalDuration = sceneList.reduce((sum, s) => sum + (s.duration_seconds || 0), 0)

  if (storyLoading || scenesLoading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/projects" className="hover:text-gray-300">Projects</Link>
        <span>/</span>
        <Link to={`/projects/${projectId}`} className="hover:text-gray-300">Project</Link>
        <span>/</span>
        <Link to={`/projects/${projectId}/stories`} className="hover:text-gray-300">Stories</Link>
        <span>/</span>
        <span className="text-gray-300">{story?.title || 'Preview'}</span>
      </div>

      <div className="flex gap-6">
        {/* Main player */}
        <div className="flex-1">
          {/* Video canvas */}
          <div className="aspect-video bg-gray-900 rounded-xl overflow-hidden border border-gray-800 relative">
            {activeScene ? (
              <div className="w-full h-full flex items-center justify-center">
                {/* Placeholder scene viewer */}
                <div className="text-center">
                  <Film className="w-16 h-16 text-gray-700 mx-auto mb-4" />
                  <p className="text-gray-400 text-lg font-medium">{activeScene.title}</p>
                  <p className="text-gray-600 text-sm mt-1">{activeScene.description}</p>
                  <div className="mt-4">
                    <span className={clsx(
                      'text-xs px-3 py-1 rounded-full',
                      activeScene.status === 'done' ? 'bg-green-900/40 text-green-400' :
                      activeScene.status === 'rendering' ? 'bg-yellow-900/40 text-yellow-400' :
                      'bg-gray-800 text-gray-400'
                    )}>
                      {activeScene.status}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <div className="text-center">
                  <Film className="w-16 h-16 text-gray-700 mx-auto mb-3" />
                  <p className="text-gray-500">No scenes available</p>
                </div>
              </div>
            )}

            {/* Scene number overlay */}
            {activeScene && (
              <div className="absolute top-3 left-3 bg-black/60 rounded px-2 py-1">
                <span className="text-xs text-white font-mono">
                  Scene {activeScene.scene_number} / {sceneList.length}
                </span>
              </div>
            )}

            {/* Duration overlay */}
            {activeScene && activeScene.duration_seconds > 0 && (
              <div className="absolute top-3 right-3 bg-black/60 rounded px-2 py-1 flex items-center gap-1">
                <Clock className="w-3 h-3 text-gray-400" />
                <span className="text-xs text-white font-mono">{formatTime(activeScene.duration_seconds)}</span>
              </div>
            )}
          </div>

          {/* Controls */}
          <div className="mt-3 bg-gray-900 rounded-lg border border-gray-800 p-3">
            {/* Progress bar */}
            <div className="h-1 bg-gray-800 rounded-full mb-3 cursor-pointer relative">
              <div
                className="h-full bg-brand-500 rounded-full"
                style={{ width: sceneList.length > 0 ? `${(currentScene / Math.max(sceneList.length - 1, 1)) * 100}%` : '0%' }}
              />
            </div>

            <div className="flex items-center gap-3">
              {/* Transport */}
              <button
                onClick={() => setCurrentScene(0)}
                className="p-1.5 rounded hover:bg-gray-800 text-gray-400"
              >
                <SkipBack className="w-4 h-4" />
              </button>
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="p-2.5 rounded-full bg-brand-600 hover:bg-brand-500 text-white"
              >
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
              </button>
              <button
                onClick={() => setCurrentScene(Math.min(sceneList.length - 1, currentScene + 1))}
                className="p-1.5 rounded hover:bg-gray-800 text-gray-400"
              >
                <SkipForward className="w-4 h-4" />
              </button>

              {/* Time */}
              <span className="text-xs text-gray-500 font-mono ml-2">
                {formatTime(sceneList.slice(0, currentScene).reduce((s, sc) => s + sc.duration_seconds, 0))}
                {' / '}
                {formatTime(totalDuration)}
              </span>

              <div className="flex-1" />

              {/* Volume */}
              <button onClick={() => setIsMuted(!isMuted)} className="p-1.5 rounded hover:bg-gray-800 text-gray-400">
                {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
              </button>
              <input
                type="range" min={0} max={100} value={isMuted ? 0 : volume}
                onChange={(e) => { setVolume(parseInt(e.target.value)); setIsMuted(false) }}
                className="w-20 accent-brand-500"
              />

              <button className="p-1.5 rounded hover:bg-gray-800 text-gray-400">
                <Maximize2 className="w-4 h-4" />
              </button>
              <button className="p-1.5 rounded hover:bg-gray-800 text-gray-400">
                <Download className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Story info */}
          {story && (
            <div className="mt-4 card p-4">
              <h2 className="text-base font-semibold text-white">{story.title}</h2>
              <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <Film className="w-3 h-3" /> {story.scene_count} scene{story.scene_count !== 1 ? 's' : ''}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" /> {formatTime(totalDuration)}
                </span>
                <span className={clsx(
                  'px-2 py-0.5 rounded-full',
                  story.status === 'completed' ? 'bg-green-900/40 text-green-400' :
                  story.status === 'generating' ? 'bg-yellow-900/40 text-yellow-400' :
                  'bg-gray-800 text-gray-400'
                )}>
                  {story.status}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Scene playlist */}
        <div className="w-64 flex-shrink-0">
          <h3 className="text-sm font-semibold text-gray-200 mb-3">Scenes</h3>
          <div className="space-y-2">
            {sceneList.map((scene, idx) => (
              <button
                key={scene.id}
                onClick={() => setCurrentScene(idx)}
                className={clsx(
                  'w-full text-left p-3 rounded-lg border transition-colors',
                  idx === currentScene
                    ? 'border-brand-600 bg-brand-900/20'
                    : 'border-gray-800 hover:border-gray-600 bg-gray-900'
                )}
              >
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-gray-500 w-5">{scene.scene_number}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-gray-200 truncate">{scene.title || `Scene ${scene.scene_number}`}</p>
                    {scene.duration_seconds > 0 && (
                      <p className="text-xs text-gray-500">{formatTime(scene.duration_seconds)}</p>
                    )}
                  </div>
                  {scene.status === 'done' && (
                    <div className="w-1.5 h-1.5 rounded-full bg-green-400 flex-shrink-0" />
                  )}
                </div>
              </button>
            ))}
            {sceneList.length === 0 && (
              <p className="text-xs text-gray-500 text-center py-4">No scenes yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
