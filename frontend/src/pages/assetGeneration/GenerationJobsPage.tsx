import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ListChecks, RefreshCw, ChevronRight } from 'lucide-react'
import { assetGenerationApi } from '@/api/assetGeneration'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'

function statusColor(status: string) {
  switch (status) {
    case 'completed': return 'text-green-400'
    case 'failed': return 'text-red-400'
    case 'running': return 'text-blue-400'
    case 'pending': return 'text-yellow-400'
    default: return 'text-gray-400'
  }
}

export function GenerationJobsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const qc = useQueryClient()
  const [tab, setTab] = useState<'jobs' | 'retry'>('jobs')
  const [jobPage, setJobPage] = useState(1)
  const [retryPage, setRetryPage] = useState(1)
  const [jobStatus, setJobStatus] = useState('')

  const { data: jobs, isLoading: jobsLoading } = useQuery({
    queryKey: ['ag-jobs', projectId, jobPage, jobStatus],
    queryFn: () => assetGenerationApi.listJobs(projectId!, { page: jobPage, page_size: 20, status: jobStatus || undefined }),
    enabled: !!projectId && tab === 'jobs',
  })

  const { data: retryQueue, isLoading: retryLoading } = useQuery({
    queryKey: ['ag-retry-queue', projectId, retryPage],
    queryFn: () => assetGenerationApi.listRetryQueue(projectId!, { page: retryPage, page_size: 20 }),
    enabled: !!projectId && tab === 'retry',
  })

  const retryMutation = useMutation({
    mutationFn: (entryId: string) => assetGenerationApi.retryEntry(entryId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ag-retry-queue', projectId] }),
  })

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
        <span>Asset Generation</span>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300">Generation Jobs</span>
      </div>

      <h1 className="text-2xl font-bold text-white flex items-center gap-2">
        <ListChecks className="w-6 h-6 text-blue-400" />
        Generation Jobs
      </h1>

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-gray-900 rounded-lg w-fit">
        <button
          onClick={() => setTab('jobs')}
          className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${tab === 'jobs' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-gray-200'}`}
        >
          Jobs
        </button>
        <button
          onClick={() => setTab('retry')}
          className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${tab === 'retry' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-gray-200'}`}
        >
          Retry Queue
        </button>
      </div>

      {tab === 'jobs' && (
        <>
          <div className="flex gap-3">
            <select
              value={jobStatus}
              onChange={(e) => { setJobStatus(e.target.value); setJobPage(1) }}
              className="input text-sm py-1.5"
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="running">Running</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
          </div>

          {jobsLoading ? (
            <div className="flex justify-center py-20"><Spinner size="lg" /></div>
          ) : jobs?.items.length === 0 ? (
            <EmptyState icon={ListChecks} title="No jobs found" description="Generation jobs appear here after triggering generation." />
          ) : (
            <>
              <div className="space-y-2">
                {jobs?.items.map((job) => (
                  <div key={job.id} className="card p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium text-white">{job.job_type}</span>
                          <span className={`text-xs font-semibold ${statusColor(job.status)}`}>{job.status}</span>
                        </div>
                        <p className="text-xs text-gray-500">ID: {job.id.slice(0, 16)}…</p>
                        {job.error_message && (
                          <p className="text-xs text-red-400 mt-1 truncate">{job.error_message}</p>
                        )}
                      </div>
                      <div className="text-right flex-shrink-0 text-xs text-gray-400">
                        {job.duration_ms > 0 && <p>{(job.duration_ms / 1000).toFixed(1)}s</p>}
                        <p>{new Date(job.created_at).toLocaleString()}</p>
                        <p className="text-gray-600">{job.dispatch_mode}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              {jobs && jobs.meta.total_pages > 1 && (
                <div className="flex justify-center gap-2">
                  <button disabled={jobPage <= 1} onClick={() => setJobPage(p => p - 1)} className="btn-secondary text-sm px-3 py-1">Prev</button>
                  <span className="text-sm text-gray-400 self-center">Page {jobPage} / {jobs.meta.total_pages}</span>
                  <button disabled={jobPage >= jobs.meta.total_pages} onClick={() => setJobPage(p => p + 1)} className="btn-secondary text-sm px-3 py-1">Next</button>
                </div>
              )}
            </>
          )}
        </>
      )}

      {tab === 'retry' && (
        <>
          {retryLoading ? (
            <div className="flex justify-center py-20"><Spinner size="lg" /></div>
          ) : retryQueue?.items.length === 0 ? (
            <EmptyState icon={RefreshCw} title="Retry queue is empty" description="Failed assets that need retrying appear here." />
          ) : (
            <>
              <div className="space-y-2">
                {retryQueue?.items.map((entry) => (
                  <div key={entry.id} className="card p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`text-xs font-semibold ${statusColor(entry.status)}`}>{entry.status}</span>
                          <span className="text-xs text-gray-500">priority {entry.priority}</span>
                        </div>
                        <p className="text-xs text-gray-400">{entry.failure_reason}</p>
                        {entry.failure_details && (
                          <p className="text-xs text-gray-500 truncate mt-1">{entry.failure_details}</p>
                        )}
                        <p className="text-xs text-gray-600 mt-1">
                          Retried {entry.retry_count}/{entry.max_retries} times
                        </p>
                      </div>
                      <div className="flex-shrink-0">
                        <button
                          onClick={() => retryMutation.mutate(entry.id)}
                          disabled={retryMutation.isPending}
                          className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1"
                        >
                          {retryMutation.isPending ? <Spinner size="sm" /> : <RefreshCw className="w-3 h-3" />}
                          Retry
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              {retryQueue && retryQueue.meta.total_pages > 1 && (
                <div className="flex justify-center gap-2">
                  <button disabled={retryPage <= 1} onClick={() => setRetryPage(p => p - 1)} className="btn-secondary text-sm px-3 py-1">Prev</button>
                  <span className="text-sm text-gray-400 self-center">Page {retryPage} / {retryQueue.meta.total_pages}</span>
                  <button disabled={retryPage >= retryQueue.meta.total_pages} onClick={() => setRetryPage(p => p + 1)} className="btn-secondary text-sm px-3 py-1">Next</button>
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  )
}
