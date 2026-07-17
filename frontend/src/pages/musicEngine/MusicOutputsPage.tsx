import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Music, RefreshCw, Inbox } from 'lucide-react'
import { musicEngineApi } from '@/api/musicEngine'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'

function moodColor(mood: string) {
  const map: Record<string, string> = {
    comedy: 'text-yellow-400',
    happy: 'text-green-400',
    adventure: 'text-blue-400',
    victory: 'text-purple-400',
    tension: 'text-red-400',
    sad: 'text-cyan-400',
    neutral: 'text-gray-400',
  }
  return map[mood] ?? 'text-gray-400'
}

export function MusicOutputsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const [page, setPage] = useState(1)
  const [moodFilter, setMoodFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['mu-outputs', projectId, page, moodFilter, typeFilter],
    queryFn: () =>
      musicEngineApi.listOutputs(projectId!, {
        page,
        mood: moodFilter || undefined,
        output_type: typeFilter || undefined,
      }),
    enabled: !!projectId,
    refetchInterval: 20_000,
  })

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Music className="w-5 h-5 text-brand-400" />
          Music Outputs
        </h1>
        <div className="flex items-center gap-2">
          <select
            className="input text-sm"
            value={moodFilter}
            onChange={(e) => { setMoodFilter(e.target.value); setPage(1) }}
          >
            <option value="">All Moods</option>
            {['neutral', 'comedy', 'adventure', 'happy', 'sad', 'tension', 'victory'].map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
          <select
            className="input text-sm"
            value={typeFilter}
            onChange={(e) => { setTypeFilter(e.target.value); setPage(1) }}
          >
            <option value="">All Types</option>
            <option value="background_music">Background Music</option>
            <option value="sfx_mix">SFX Mix</option>
            <option value="scene_audio">Scene Audio</option>
          </select>
          <button className="btn-secondary p-2" onClick={() => refetch()} title="Refresh">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : !data?.items.length ? (
        <EmptyState
          icon={Inbox}
          title="No music outputs yet"
          description="Generated music tracks will appear here."
        />
      ) : (
        <>
          <div className="card divide-y divide-gray-800">
            {data.items.map((output) => (
              <div key={output.id} className="p-4 flex items-center gap-4">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center bg-gray-800 flex-shrink-0`}>
                  <Music className={`w-4 h-4 ${moodColor(output.mood)}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`text-xs font-semibold ${moodColor(output.mood)}`}>{output.mood}</span>
                    <span className="text-xs text-gray-500">{output.output_type}</span>
                    <span className="text-xs text-gray-600">{output.loop_type}</span>
                    {output.copyright_safe && (
                      <span className="text-xs text-green-500 bg-green-500/10 px-1.5 py-0.5 rounded">©-safe</span>
                    )}
                  </div>
                  <p className="text-xs text-gray-600 mt-0.5 truncate">
                    {output.duration_seconds}s · {output.format.toUpperCase()} · {output.provider}
                  </p>
                  <p className="text-xs text-gray-700 mt-0.5 font-mono truncate">{output.storage_key}</p>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="text-xs text-gray-500">{new Date(output.created_at).toLocaleString()}</p>
                  <p className="text-xs text-gray-600 mt-0.5">{(output.file_size_bytes / 1024).toFixed(1)} KB</p>
                </div>
              </div>
            ))}
          </div>

          {data.meta.total_pages > 1 && (
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>Page {page} of {data.meta.total_pages} ({data.meta.total} total)</span>
              <div className="flex gap-2">
                <button className="btn-secondary py-1 px-3" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>Prev</button>
                <button className="btn-secondary py-1 px-3" onClick={() => setPage(p => p + 1)} disabled={page >= data.meta.total_pages}>Next</button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
