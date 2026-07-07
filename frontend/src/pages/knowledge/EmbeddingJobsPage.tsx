import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ChevronRight, Cpu, Loader2, CheckCircle2, XCircle, Clock, AlertCircle } from 'lucide-react'
import { knowledgeApi, type EmbeddingJob } from '@/api/knowledge'
import { Spinner } from '@/components/ui/Spinner'

function JobStatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'completed': return <CheckCircle2 className="w-4 h-4 text-green-400" />
    case 'failed': return <XCircle className="w-4 h-4 text-red-400" />
    case 'running': return <Loader2 className="w-4 h-4 text-yellow-400 animate-spin" />
    case 'pending': case 'queued': return <Clock className="w-4 h-4 text-blue-400" />
    default: return <AlertCircle className="w-4 h-4 text-gray-500" />
  }
}

function statusColor(status: string) {
  switch (status) {
    case 'completed': return 'text-green-400'
    case 'failed': return 'text-red-400'
    case 'running': return 'text-yellow-400'
    case 'pending': case 'queued': return 'text-blue-400'
    default: return 'text-gray-400'
  }
}

function JobRow({ job }: { job: EmbeddingJob }) {
  return (
    <div className="card p-4 flex items-start gap-4">
      <div className="flex-shrink-0 mt-0.5">
        <JobStatusIcon status={job.status} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-gray-100">{job.job_type}</span>
          <span className={`text-xs font-medium capitalize ${statusColor(job.status)}`}>{job.status}</span>
          <span className="text-xs text-gray-600">{job.execution_mode}</span>
          {job.retry_count > 0 && (
            <span className="text-xs text-orange-400">retry #{job.retry_count}</span>
          )}
        </div>

        {job.current_step && (
          <p className="text-xs text-gray-400 mt-0.5">{job.current_step}</p>
        )}

        {(job.chunks_total > 0) && (
          <div className="mt-2">
            <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
              <span>{job.chunks_processed} / {job.chunks_total} chunks</span>
              <span>{job.progress_percent}%</span>
            </div>
            <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-brand-500 rounded-full transition-all"
                style={{ width: `${job.progress_percent}%` }}
              />
            </div>
          </div>
        )}

        {job.error_message && (
          <p className="text-xs text-red-400 mt-1">{job.error_message}</p>
        )}

        <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-600">
          <span>Job: {job.id.slice(0, 8)}…</span>
          {job.document_id && <span>Doc: {job.document_id.slice(0, 8)}…</span>}
          <span>{new Date(job.created_at).toLocaleString()}</span>
        </div>
      </div>
    </div>
  )
}

export function EmbeddingJobsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [activeTab, setActiveTab] = useState<'all' | 'retry'>('all')

  const { data, isLoading } = useQuery({
    queryKey: ['kn-jobs', projectId, page, statusFilter],
    queryFn: () => knowledgeApi.listJobs(projectId!, page, 20, statusFilter || undefined),
    enabled: !!projectId && activeTab === 'all',
    refetchInterval: 5000,
  })

  const { data: retryQueue, isLoading: loadingRetry } = useQuery({
    queryKey: ['kn-retry-queue'],
    queryFn: () => knowledgeApi.getRetryQueue(),
    enabled: activeTab === 'retry',
    refetchInterval: 10000,
  })

  const jobs = data?.items ?? []
  const meta = data?.meta

  const STATUS_FILTERS = ['', 'pending', 'running', 'completed', 'failed']

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/projects" className="hover:text-gray-300">Projects</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}`} className="hover:text-gray-300">Project</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}/knowledge`} className="hover:text-gray-300">Knowledge</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300">Embedding Jobs</span>
      </div>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Embedding Jobs</h1>
          <p className="text-gray-400 text-sm mt-1">Monitor document processing and embedding pipeline</p>
        </div>
      </div>

      <div className="flex gap-1 mb-6 border-b border-gray-800">
        <button
          onClick={() => setActiveTab('all')}
          className={`px-4 py-2 text-sm border-b-2 transition-colors ${
            activeTab === 'all' ? 'border-brand-500 text-white' : 'border-transparent text-gray-500 hover:text-gray-300'
          }`}
        >All Jobs</button>
        <button
          onClick={() => setActiveTab('retry')}
          className={`px-4 py-2 text-sm border-b-2 transition-colors ${
            activeTab === 'retry' ? 'border-brand-500 text-white' : 'border-transparent text-gray-500 hover:text-gray-300'
          }`}
        >Retry Queue</button>
      </div>

      {activeTab === 'all' && (
        <>
          <div className="flex items-center gap-2 mb-4 flex-wrap">
            <span className="text-xs text-gray-500">Status:</span>
            {STATUS_FILTERS.map((s) => (
              <button
                key={s || 'all'}
                onClick={() => { setStatusFilter(s); setPage(1) }}
                className={`px-2.5 py-1 rounded text-xs font-medium capitalize transition-colors ${
                  statusFilter === s ? 'bg-brand-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >{s || 'All'}</button>
            ))}
          </div>

          {isLoading ? (
            <div className="flex justify-center py-20"><Spinner size="lg" /></div>
          ) : jobs.length === 0 ? (
            <div className="card p-12 text-center">
              <Cpu className="w-12 h-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400 font-medium">No jobs found</p>
              <p className="text-gray-600 text-sm mt-1">Upload documents to see embedding jobs here.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {jobs.map((job) => <JobRow key={job.id} job={job} />)}
            </div>
          )}

          {meta && meta.total_pages > 1 && (
            <div className="flex items-center justify-center gap-3 mt-6">
              <button className="btn-secondary text-xs" disabled={page <= 1} onClick={() => setPage(page - 1)}>← Prev</button>
              <span className="text-xs text-gray-500">Page {meta.page} of {meta.total_pages}</span>
              <button className="btn-secondary text-xs" disabled={page >= meta.total_pages} onClick={() => setPage(page + 1)}>Next →</button>
            </div>
          )}
        </>
      )}

      {activeTab === 'retry' && (
        <>
          {loadingRetry ? (
            <div className="flex justify-center py-20"><Spinner size="lg" /></div>
          ) : !retryQueue || retryQueue.length === 0 ? (
            <div className="card p-12 text-center">
              <CheckCircle2 className="w-12 h-12 text-green-600 mx-auto mb-3" />
              <p className="text-gray-400 font-medium">Retry queue is empty</p>
              <p className="text-gray-600 text-sm mt-1">No pending jobs waiting for retry.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {retryQueue.map((job) => <JobRow key={job.id} job={job} />)}
            </div>
          )}
        </>
      )}
    </div>
  )
}
