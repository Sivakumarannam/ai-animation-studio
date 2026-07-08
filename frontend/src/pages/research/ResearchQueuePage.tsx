import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Clock, Pause, Trash2 } from 'lucide-react'
import { researchApi } from '@/api/research'
import { Spinner } from '@/components/ui/Spinner'

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-900 text-yellow-300',
  processing: 'bg-blue-900 text-blue-300',
  completed: 'bg-green-900 text-green-300',
  failed: 'bg-red-900 text-red-300',
  paused: 'bg-gray-700 text-gray-300',
}

export function ResearchQueuePage() {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['research-queue', page, statusFilter],
    queryFn: () => researchApi.getQueue(page, 20, statusFilter),
    refetchInterval: 10_000,
  })

  const pause = useMutation({
    mutationFn: (id: string) => researchApi.pauseQueueItem(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['research-queue'] }),
  })

  const remove = useMutation({
    mutationFn: (id: string) => researchApi.deleteQueueItem(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['research-queue'] }),
  })

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Clock className="w-6 h-6 text-yellow-400" /> Research Queue
        </h1>
        <p className="text-gray-400 text-sm mt-1">Topics queued for Story Intelligence generation</p>
      </div>

      <div className="flex gap-2 flex-wrap">
        {[undefined, 'pending', 'processing', 'completed', 'failed', 'paused'].map(s => (
          <button
            key={s || 'all'}
            onClick={() => { setStatusFilter(s); setPage(1) }}
            className={`text-xs px-3 py-1 rounded-full transition-colors ${statusFilter === s ? 'bg-brand-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
          >
            {s || 'All'}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : (
        <div className="space-y-3">
          {data?.items.map(item => (
            <div key={item.id} className="card p-4 flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-white">Priority {item.priority}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[item.status] || 'bg-gray-700 text-gray-300'}`}>
                    {item.status}
                  </span>
                  <span className="text-xs text-green-400 font-medium">Score: {item.overall_score.toFixed(0)}</span>
                </div>
                <p className="text-xs text-gray-400 mt-1 truncate">
                  Topic: {(item.research_summary as any)?.topic || item.topic_id}
                </p>
                {item.queued_at && (
                  <p className="text-xs text-gray-500 mt-0.5">Queued: {new Date(item.queued_at).toLocaleString()}</p>
                )}
              </div>
              <div className="flex gap-2 ml-4">
                {item.status === 'pending' && (
                  <button
                    onClick={() => pause.mutate(item.id)}
                    disabled={pause.isPending}
                    title="Pause"
                    className="p-2 text-gray-400 hover:text-yellow-400 hover:bg-yellow-900/20 rounded transition-colors"
                  >
                    <Pause className="w-4 h-4" />
                  </button>
                )}
                <button
                  onClick={() => remove.mutate(item.id)}
                  disabled={remove.isPending}
                  title="Delete"
                  className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-900/20 rounded transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
          {data?.items.length === 0 && (
            <div className="text-center py-16 text-gray-500">
              Queue is empty. Run the opportunity scoring pipeline to populate it.
            </div>
          )}
          {data && data.meta.total_pages > 1 && (
            <div className="flex justify-center gap-2 pt-2">
              <button className="btn-secondary text-sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Previous</button>
              <span className="text-gray-400 text-sm self-center">Page {page} of {data.meta.total_pages}</span>
              <button className="btn-secondary text-sm" disabled={page >= data.meta.total_pages} onClick={() => setPage(p => p + 1)}>Next</button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
