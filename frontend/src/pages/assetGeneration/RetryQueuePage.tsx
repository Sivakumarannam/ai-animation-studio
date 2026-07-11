import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { RefreshCw, AlertCircle, ChevronRight } from 'lucide-react'
import { assetGenerationApi } from '@/api/assetGeneration'
import type { RetryQueueResponse } from '@/api/assetGeneration'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-900/40 text-yellow-400',
  retrying: 'bg-blue-900/40 text-blue-400',
  resolved: 'bg-green-900/40 text-green-400',
  exhausted: 'bg-red-900/40 text-red-400',
}

export function RetryQueuePage() {
  const { projectId } = useParams<{ projectId: string }>()
  const qc = useQueryClient()
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['ag-retry-queue', projectId, statusFilter, page],
    queryFn: () =>
      assetGenerationApi.listRetryQueue(projectId!, {
        status: statusFilter || undefined,
        page,
        page_size: 20,
      }),
    enabled: !!projectId,
    refetchInterval: 15_000,
  })

  const retryMutation = useMutation({
    mutationFn: (entryId: string) => assetGenerationApi.retryEntry(entryId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ag-retry-queue', projectId] }),
  })

  const entries = data?.items ?? []

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <span>Asset Generation</span>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300">Retry Queue</span>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <AlertCircle className="w-6 h-6 text-red-400" /> Retry Queue
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Failed assets eligible for re-generation — auto-refreshes every 15 s
          </p>
        </div>
        <select
          className="input text-sm py-1.5"
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
        >
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="retrying">Retrying</option>
          <option value="resolved">Resolved</option>
          <option value="exhausted">Exhausted</option>
        </select>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16"><Spinner size="lg" /></div>
      ) : entries.length === 0 ? (
        <EmptyState
          icon={AlertCircle}
          title="No retry entries"
          description={statusFilter ? 'No entries match the selected filter.' : 'No failed assets in the retry queue.'}
        />
      ) : (
        <>
          <div className="space-y-3">
            {entries.map((entry: RetryQueueResponse) => (
              <div key={entry.id} className="card p-4 space-y-3">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[entry.status] ?? 'bg-gray-800 text-gray-400'}`}>
                        {entry.status}
                      </span>
                      <span className="text-xs text-gray-500">
                        Priority {entry.priority} · {entry.retry_count}/{entry.max_retries} retries
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 font-mono truncate">Asset: {entry.asset_id}</p>
                    {entry.failure_reason && (
                      <p className="text-sm text-red-300 mt-1">{entry.failure_reason}</p>
                    )}
                    {entry.failure_details && (
                      <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{entry.failure_details}</p>
                    )}
                  </div>
                  <div className="flex-shrink-0 text-right space-y-2">
                    <div>
                      <p className="text-lg font-bold text-white">{entry.quality_score.toFixed(0)}</p>
                      <p className="text-xs text-gray-500">quality</p>
                    </div>
                    <button
                      onClick={() => retryMutation.mutate(entry.id)}
                      disabled={
                        retryMutation.isPending ||
                        entry.status === 'resolved' ||
                        entry.status === 'exhausted'
                      }
                      className="btn-secondary text-xs flex items-center gap-1 py-1 px-2"
                      title="Retry this asset"
                    >
                      {retryMutation.isPending ? (
                        <Spinner size="sm" />
                      ) : (
                        <RefreshCw className="w-3 h-3" />
                      )}
                      Retry
                    </button>
                  </div>
                </div>

                <div className="flex items-center gap-4 text-xs text-gray-500 border-t border-gray-800 pt-2">
                  <span>Added {new Date(entry.created_at).toLocaleString()}</span>
                  {entry.last_retry_at && (
                    <span>Last retry {new Date(entry.last_retry_at).toLocaleString()}</span>
                  )}
                  {entry.resolved_at && (
                    <span className="text-green-400">
                      Resolved {new Date(entry.resolved_at).toLocaleString()}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {data && data.meta.total_pages > 1 && (
            <div className="flex justify-center gap-2">
              <button
                className="btn-secondary text-sm px-3 py-1"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Prev
              </button>
              <span className="text-sm text-gray-400 self-center">
                Page {page} of {data.meta.total_pages}
              </span>
              <button
                className="btn-secondary text-sm px-3 py-1"
                disabled={page >= data.meta.total_pages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
