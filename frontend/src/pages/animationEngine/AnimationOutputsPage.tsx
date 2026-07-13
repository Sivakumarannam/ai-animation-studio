import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Film, RefreshCw, Inbox } from 'lucide-react'
import { animationEngineApi } from '@/api/animationEngine'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'

function statusColor(status: string) {
  switch (status) {
    case 'completed': return 'text-green-400'
    case 'failed': return 'text-red-400'
    case 'processing': return 'text-blue-400'
    default: return 'text-gray-400'
  }
}

export function AnimationOutputsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const [page, setPage] = useState(1)
  const [outputType, setOutputType] = useState('')

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['an-outputs', projectId, page, outputType],
    queryFn: () =>
      animationEngineApi.listOutputs(projectId!, {
        page,
        output_type: outputType || undefined,
      }),
    enabled: !!projectId,
  })

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Film className="w-5 h-5 text-brand-400" />
          Render Outputs
        </h1>
        <div className="flex items-center gap-2">
          <select
            className="input text-sm"
            value={outputType}
            onChange={(e) => { setOutputType(e.target.value); setPage(1) }}
          >
            <option value="">All Types</option>
            <option value="scene_clip">Scene Clip</option>
            <option value="episode_video">Episode Video</option>
            <option value="preview">Preview</option>
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
          title="No render outputs yet"
          description="Generate an animation from the dashboard or Jobs page."
        />
      ) : (
        <>
          <div className="card divide-y divide-gray-800">
            {data.items.map((output) => (
              <div key={output.id} className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium text-white">{output.output_type}</p>
                    <p className="text-xs text-gray-500 mt-0.5 font-mono truncate max-w-xs" title={output.storage_key}>
                      {output.storage_key || '(no storage key)'}
                    </p>
                  </div>
                  <span className={`text-xs font-semibold ${statusColor(output.status)}`}>
                    {output.status}
                  </span>
                </div>
                <div className="mt-2 flex gap-4 text-xs text-gray-500 flex-wrap">
                  <span>{output.width}×{output.height} @ {output.fps}fps</span>
                  <span>{output.duration_seconds.toFixed(2)}s</span>
                  <span>{output.format.toUpperCase()}</span>
                  <span>Provider: {output.provider}</span>
                  <span>{new Date(output.created_at).toLocaleString()}</span>
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
