import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Activity } from 'lucide-react'
import { researchApi, ResearchJob } from '@/api/research'
import { Spinner } from '@/components/ui/Spinner'

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-900 text-yellow-300',
  running: 'bg-blue-900 text-blue-300',
  completed: 'bg-green-900 text-green-300',
  failed: 'bg-red-900 text-red-300',
}

const JOB_TYPES = [
  'discover_trends', 'research_topic', 'verify_facts',
  'score_opportunities', 'scheduler_tick',
]

export function ResearchJobsPage() {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [typeFilter, setTypeFilter] = useState<string | undefined>()

  const { data, isLoading } = useQuery({
    queryKey: ['research-jobs', page, statusFilter, typeFilter],
    queryFn: () => researchApi.getJobs(page, 20, statusFilter, typeFilter),
    refetchInterval: 5_000,
  })

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Activity className="w-6 h-6 text-blue-400" /> Research Jobs
        </h1>
        <p className="text-gray-400 text-sm mt-1">Async pipeline job execution log</p>
      </div>

      <div className="card p-4 flex flex-wrap gap-3">
        <select
          value={statusFilter || ''}
          onChange={e => { setStatusFilter(e.target.value || undefined); setPage(1) }}
          className="input text-sm py-1 px-2"
        >
          <option value="">All statuses</option>
          {['pending', 'running', 'completed', 'failed'].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select
          value={typeFilter || ''}
          onChange={e => { setTypeFilter(e.target.value || undefined); setPage(1) }}
          className="input text-sm py-1 px-2"
        >
          <option value="">All types</option>
          {JOB_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : (
        <div className="space-y-3">
          {data?.items.map((job: ResearchJob) => (
            <div key={job.id} className="card p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs text-gray-400">{job.job_type}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[job.status] || 'bg-gray-700 text-gray-300'}`}>
                    {job.status}
                  </span>
                  <span className="text-xs text-gray-500">{job.execution_mode}</span>
                </div>
                <span className="text-xs text-gray-500">{new Date(job.created_at).toLocaleString()}</span>
              </div>
              {job.status === 'running' && (
                <div className="mt-2">
                  <div className="flex justify-between text-xs text-gray-400 mb-1">
                    <span>{job.current_step}</span>
                    <span>{job.progress_percent}%</span>
                  </div>
                  <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                    <div className="h-full bg-brand-600 rounded-full transition-all" style={{ width: `${job.progress_percent}%` }} />
                  </div>
                </div>
              )}
              {job.error_message && (
                <p className="mt-2 text-xs text-red-400 font-mono">{job.error_message}</p>
              )}
              {job.completed_at && (
                <p className="mt-1 text-xs text-gray-500">
                  Completed: {new Date(job.completed_at).toLocaleString()}
                  {job.started_at && ` · ${((new Date(job.completed_at).getTime() - new Date(job.started_at).getTime()) / 1000).toFixed(1)}s`}
                </p>
              )}
            </div>
          ))}
          {data?.items.length === 0 && (
            <div className="text-center py-16 text-gray-500">No research jobs found</div>
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
