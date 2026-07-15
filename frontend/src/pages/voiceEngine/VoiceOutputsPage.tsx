import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { AudioWaveform, RefreshCw, Inbox } from 'lucide-react'
import { voiceEngineApi } from '@/api/voiceEngine'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'

function emotionColor(emotion: string) {
  const map: Record<string, string> = {
    happy: 'text-green-400',
    sad: 'text-blue-400',
    angry: 'text-red-400',
    fearful: 'text-orange-400',
    surprised: 'text-yellow-400',
    neutral: 'text-gray-400',
  }
  return map[emotion] ?? 'text-gray-400'
}

export function VoiceOutputsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const [page, setPage] = useState(1)
  const [languageFilter, setLanguageFilter] = useState('')

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['vo-outputs', projectId, page, languageFilter],
    queryFn: () =>
      voiceEngineApi.listOutputs(projectId!, {
        page,
        language: languageFilter || undefined,
      }),
    enabled: !!projectId,
    refetchInterval: 20_000,
  })

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <AudioWaveform className="w-5 h-5 text-brand-400" />
          Voice Outputs
        </h1>
        <div className="flex items-center gap-2">
          <select
            className="input text-sm"
            value={languageFilter}
            onChange={(e) => { setLanguageFilter(e.target.value); setPage(1) }}
          >
            <option value="">All Languages</option>
            <option value="en">English</option>
            <option value="te">Telugu</option>
            <option value="hi">Hindi</option>
            <option value="ta">Tamil</option>
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
          title="No voice outputs yet"
          description="Generated audio clips will appear here."
        />
      ) : (
        <>
          <div className="card divide-y divide-gray-800">
            {data.items.map((output) => (
              <div key={output.id} className="p-4">
                <div className="flex items-start gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      {output.character_name && (
                        <span className="text-xs font-semibold text-brand-400">
                          {output.character_name}
                        </span>
                      )}
                      <span className={`text-xs font-semibold ${emotionColor(output.emotion)}`}>
                        {output.emotion}
                      </span>
                      <span className="text-xs text-gray-600 uppercase">{output.language}</span>
                      <span className="text-xs text-gray-600">{output.provider}</span>
                    </div>
                    <p className="text-sm text-gray-200 mt-1 line-clamp-2">
                      "{output.dialogue_line}"
                    </p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                      <span>{output.duration_seconds.toFixed(2)}s</span>
                      <span>{output.sample_rate}Hz</span>
                      <span className="uppercase">{output.format}</span>
                      <span className="font-mono truncate max-w-xs">{output.storage_key}</span>
                    </div>
                  </div>
                  <p className="text-xs text-gray-600 flex-shrink-0">
                    {new Date(output.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {data.meta.total_pages > 1 && (
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>Page {page} of {data.meta.total_pages}</span>
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
