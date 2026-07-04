import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Play, Pause, SkipBack, SkipForward, Plus, Trash2,
  Clock, Music, Subtitles, Camera, Zap,
} from 'lucide-react'
import { compositionApi } from '@/api/composition'
import { Spinner } from '@/components/ui/Spinner'
import { clsx } from 'clsx'

type TrackType = 'clips' | 'audio_events' | 'subtitle_events' | 'camera_events'

const TRACK_CONFIG: { type: TrackType; label: string; Icon: any; color: string }[] = [
  { type: 'clips', label: 'Animation', Icon: Zap, color: 'bg-brand-600' },
  { type: 'camera_events', label: 'Camera', Icon: Camera, color: 'bg-blue-600' },
  { type: 'audio_events', label: 'Audio', Icon: Music, color: 'bg-green-600' },
  { type: 'subtitle_events', label: 'Subtitles', Icon: Subtitles, color: 'bg-yellow-600' },
]

function TimelineTrack({
  label, Icon, color, events, onAdd, onRemove, pixelsPerFrame,
}: {
  label: string; Icon: any; color: string; events: any[];
  onAdd: () => void; onRemove: (id: string) => void; pixelsPerFrame: number;
}) {
  return (
    <div className="flex h-10 border-b border-gray-800">
      {/* Label */}
      <div className="w-28 flex-shrink-0 flex items-center gap-1.5 px-2 border-r border-gray-800 bg-gray-900">
        <Icon className="w-3 h-3 text-gray-400" />
        <span className="text-xs text-gray-400 truncate">{label}</span>
        <button onClick={onAdd} className="ml-auto text-gray-600 hover:text-gray-300">
          <Plus className="w-3 h-3" />
        </button>
      </div>
      {/* Track area */}
      <div className="flex-1 relative overflow-hidden bg-gray-950">
        {events.map((event) => {
          const startFrame = event.start_frame ?? event.frame ?? 0
          const endFrame = event.end_frame ?? (startFrame + (event.duration_frames ?? 24))
          return (
            <div
              key={event.id}
              className={clsx('absolute top-1 bottom-1 rounded flex items-center px-1 cursor-pointer group', color, 'opacity-80 hover:opacity-100')}
              style={{ left: startFrame * pixelsPerFrame, width: Math.max((endFrame - startFrame) * pixelsPerFrame, 8) }}
              title={event.text || event.type || 'event'}
            >
              <span className="text-xs text-white truncate select-none">{event.text || event.type || label}</span>
              <button
                onClick={(e) => { e.stopPropagation(); onRemove(event.id) }}
                className="absolute right-0.5 top-0.5 opacity-0 group-hover:opacity-100 text-white/70 hover:text-white"
              >
                <Trash2 className="w-2.5 h-2.5" />
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function TimelineEditorPage() {
  const { sceneId } = useParams<{ sceneId: string }>()
  const [isPlaying, setIsPlaying] = useState(false)
  const [pixelsPerFrame, setPixelsPerFrame] = useState(4)
  const qc = useQueryClient()

  const { data: comp, isLoading: compLoading } = useQuery({
    queryKey: ['composition', sceneId],
    queryFn: () => compositionApi.getByScene(sceneId!),
    enabled: !!sceneId,
  })

  const { data: timeline, isLoading: tlLoading } = useQuery({
    queryKey: ['timeline', comp?.id],
    queryFn: () => compositionApi.getTimeline(comp!.id),
    enabled: !!comp?.id,
  })

  const addClipMutation = useMutation({
    mutationFn: ({ id, clip }: { id: string; clip: any }) => compositionApi.addClip(id, clip),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['timeline', comp?.id] }),
  })

  const removeClipMutation = useMutation({
    mutationFn: ({ id, clipId }: { id: string; clipId: string }) => compositionApi.removeClip(id, clipId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['timeline', comp?.id] }),
  })

  const setPlayhead = useMutation({
    mutationFn: ({ id, frame }: { id: string; frame: number }) => compositionApi.setPlayhead(id, frame),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['timeline', comp?.id] }),
  })

  if (compLoading || tlLoading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>
  if (!timeline || !comp) return null

  const fps = timeline.fps
  const totalFrames = Math.max(timeline.total_frames, 120)
  const totalWidth = totalFrames * pixelsPerFrame
  const currentFrame = timeline.playhead_frame

  const frameToTime = (frame: number) => {
    const secs = frame / fps
    const m = Math.floor(secs / 60)
    const s = Math.floor(secs % 60)
    const f = frame % fps
    return `${m}:${s.toString().padStart(2, '0')}.${f.toString().padStart(2, '0')}`
  }

  const handleAddClip = () => {
    addClipMutation.mutate({
      id: timeline.id,
      clip: {
        id: crypto.randomUUID(),
        type: 'pose',
        start_frame: currentFrame,
        end_frame: currentFrame + 24,
        layer_id: 'default',
        data: {},
      },
    })
  }

  return (
    <div className="flex flex-col h-full bg-gray-950">
      {/* Transport controls */}
      <div className="h-12 bg-gray-900 border-b border-gray-800 flex items-center gap-3 px-4">
        <button onClick={() => setPlayhead.mutate({ id: timeline.id, frame: 0 })} className="p-1.5 rounded hover:bg-gray-800 text-gray-400">
          <SkipBack className="w-4 h-4" />
        </button>
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="p-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white"
        >
          {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
        </button>
        <button onClick={() => setPlayhead.mutate({ id: timeline.id, frame: totalFrames })} className="p-1.5 rounded hover:bg-gray-800 text-gray-400">
          <SkipForward className="w-4 h-4" />
        </button>

        <div className="w-px h-4 bg-gray-700 mx-1" />

        <div className="flex items-center gap-1.5 text-xs text-gray-300">
          <Clock className="w-3.5 h-3.5 text-gray-500" />
          <span className="font-mono">{frameToTime(currentFrame)}</span>
          <span className="text-gray-600">/</span>
          <span className="font-mono text-gray-500">{frameToTime(totalFrames)}</span>
        </div>

        <div className="flex-1" />

        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">Zoom:</span>
          <input
            type="range" min={1} max={12} step={1} value={pixelsPerFrame}
            onChange={(e) => setPixelsPerFrame(parseInt(e.target.value))}
            className="w-20 accent-brand-500"
          />
          <span className="text-xs text-gray-500">{pixelsPerFrame}px/f</span>
        </div>

        <div className="w-px h-4 bg-gray-700 mx-1" />
        <span className="text-xs text-gray-500">{fps} fps</span>
        <span className="text-xs text-gray-500">{totalFrames} frames</span>
      </div>

      {/* Timeline tracks */}
      <div className="flex-1 overflow-auto">
        <div className="min-w-max">
          {/* Ruler */}
          <div className="flex h-6 border-b border-gray-800 bg-gray-900">
            <div className="w-28 flex-shrink-0 border-r border-gray-800" />
            <div className="flex-1 relative overflow-hidden" style={{ width: totalWidth }}>
              {Array.from({ length: Math.floor(totalFrames / fps) + 1 }, (_, i) => i).map((sec) => (
                <div
                  key={sec}
                  className="absolute top-0 flex flex-col items-start"
                  style={{ left: sec * fps * pixelsPerFrame }}
                >
                  <div className="h-2 w-px bg-gray-600" />
                  <span className="text-xs text-gray-600 ml-1">{sec}s</span>
                </div>
              ))}
              {/* Playhead */}
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-brand-400 z-10"
                style={{ left: currentFrame * pixelsPerFrame }}
              />
            </div>
          </div>

          {/* Tracks */}
          {TRACK_CONFIG.map(({ type, label, Icon, color }) => {
            const events = (timeline[type] as any[]) ?? []
            return (
              <TimelineTrack
                key={type}
                label={label}
                Icon={Icon}
                color={color}
                events={events}
                pixelsPerFrame={pixelsPerFrame}
                onAdd={type === 'clips' ? handleAddClip : () => {}}
                onRemove={(id) => {
                  if (type === 'clips') {
                    removeClipMutation.mutate({ id: timeline.id, clipId: id })
                  }
                }}
              />
            )
          })}
        </div>
      </div>

      {/* Bottom info bar */}
      <div className="h-6 bg-gray-900 border-t border-gray-800 flex items-center px-4 gap-4 text-xs text-gray-600">
        <span>{timeline.clips.length} clip{timeline.clips.length !== 1 ? 's' : ''}</span>
        <span>{timeline.keyframes.length} keyframe{timeline.keyframes.length !== 1 ? 's' : ''}</span>
        <span>{timeline.subtitle_events.length} subtitle event{timeline.subtitle_events.length !== 1 ? 's' : ''}</span>
      </div>
    </div>
  )
}
