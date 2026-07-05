import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ChevronRight, ListChecks } from 'lucide-react'
import { storyIntelligenceApi } from '@/api/storyIntelligence'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'

const STATUS_COLORS: Record<string, string> = {
  queued: 'badge-gray',
  pending: 'badge-gray',
  running: 'badge-blue',
  completed: 'badge-green',
  failed: 'badge-yellow',
}

export function RetryQueuePage() {
  const { projectId } = useParams<{ projectId: string }>()
  const [statusFilter, setStatusFilter] = useState<string>('')

  const { data, isLoading } = useQuery({
    queryKey: ['si-jobs', projectId, statusFilter],
    queryFn: () => storyIntelligenceApi.listJobs(projectId!, 1, 50, statusFilter || undefined),
    enabled: !!projectId,
    refetchInterval: 5000,
  })

  const statuses = ['', 'queued', 'running', 'completed', 'failed']

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/projects" className="hover:text-gray-300">Projects</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}`} className="hover:text-gray-300">Project</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}/intelligence`} className="hover:text-gray-300">Story Intelligence</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300">Retry Queue</span>
      </div>

      <h1 className="text-2xl font-bold text-white mb-6">Generation Jobs</h1>

      <div className="flex gap-2 mb-4">
        {statuses.map((s) => (
          <button
            key={s || 'all'}
            onClick={() => setStatusFilter(s)}
            className={`px-3 py-1.5 rounded-lg text-xs capitalize transition-colors ${
              statusFilter === s ? 'bg-brand-600/20 text-brand-400' : 'text-gray-400 hover:bg-gray-800'
            }`}
          >
            {s || 'All'}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : data?.items.length === 0 ? (
        <EmptyState icon={ListChecks} title="No jobs found" description="Generation jobs will appear here once you start the AI pipeline." />
      ) : (
        <div className="space-y-2">
          {data?.items.map((job) => (
            <div key={job.id} className="card p-4">
              <div className="flex items-center justify-between mb-1">
                <p className="text-sm font-semibold text-gray-100">{job.job_type} — {job.entity_type}</p>
                <span className={STATUS_COLORS[job.status] ?? 'badge-gray'}>{job.status}</span>
              </div>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>Mode: {job.execution_mode}</span>
                <span>Progress: {job.progress_percent}%</span>
                {job.retry_count > 0 && <span>Retries: {job.retry_count}/{job.max_retries}</span>}
              </div>
              {job.current_step && <p className="text-xs text-gray-500 mt-1">{job.current_step}</p>}
              {job.error_message && <p className="text-xs text-red-400 mt-1">{job.error_message}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
