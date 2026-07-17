import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { RefreshCw, RotateCcw, Loader2, Inbox, Music } from 'lucide-react'
import { musicEngineApi } from '@/api/musicEngine'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'

function statusColor(status: string) {
  switch (status) {
    case 'resolved': return 'text-green-400'
    case 'exhausted': return 'text-red-400'
    case 'retrying': return 'text-blue-400'
    case 'pending': return 'text-yellow-400'
    default: return 'text-gray-400'
  }
}

export function MusicRetryQueuePage() {
  const { projectId } = useParams<{ projectId: string }>()
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('pending')

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['mu-retry-queue', projectId, page, statusFilter],
    queryFn: () =>
      musicEngineApi.listRetryQueue(projectId!, {
        page,
        status: statusFilter || undefined,
      }),
    enabled: !!projectId,
    refetchInterval: 20_000,
  })

  const sweepMutation = useMutation({
    mutationFn: () => musicEngineApi.processRetryQueue(projectId!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['mu-retry-queue', projectId] })
      qc.invalidateQueries({ queryKey: ['mu-jobs', projectId] })
    },
  })

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <RefreshCw className="w-5 h-5 text-brand-400" />
          Music Retry Queue
        </h1>
        <div className="flex items-center gap-2">
          <select
            className="input text-sm"
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="retrying">Retrying</option>
            <option value="resolved">Resolved</option>
            <option value="exhausted">Exhausted</option>
          </select>
          <button className="btn-secondary p-2" onClick={() => refetch()} title="Refresh">
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            className="btn-secondary flex items-center gap-1 text-sm"
            onClick={() => sweepMutation.mutate()}
            disabled={sweepMutation.isPending}
          >
            {sweepMutation.isPending ? <Loader2 className="w-3 h-3 animate-spin" /> : <RotateCcw className="w-3 h-3" />}
            Sweep Queue
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : !data?.items.length ? (
        <EmptyState
          icon={Inbox}
          title="Retry queue is empty"
          description="Failed music generation jobs will appear here automatically."
        />
      ) : (
        <>
          <div className="card divide-y divide-gray-800">
            {data.items.map((entry) => (
              <div key={entry.id} className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-xs font-semibold ${statusColor(entry.status)}`}>
                        {entry.status}
                      </span>
                      <span className="text-xs text-gray-600">
                        {entry.retry_count}/{entry.max_retries} retries
                      </span>
                      {entry.params?.mood && (
                        <span className="text-xs text-gray-500">mood: {String(entry.params.mood)}</span>
                      )}
                    </div>
                    {entry.reason && (
                      <p className="text-xs text-red-400 mt-1 bg-red-400/10 rounded p-1.5">
                        {entry.reason}
                      </p>
                    )}
                    <p className="text-xs text-gray-600 mt-1">
                      {new Date(entry.created_at).toLocaleString()}
                    </p>
                  </div>
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
