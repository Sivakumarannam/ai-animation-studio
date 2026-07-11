import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  LayoutDashboard, Image, CheckCircle, Clock, AlertCircle, Zap,
  RefreshCw, Database, MessageSquare, ListChecks, Layers, ShieldCheck, Search,
} from 'lucide-react'
import { assetGenerationApi } from '@/api/assetGeneration'
import { Spinner } from '@/components/ui/Spinner'

function StatCard({ label, value, icon: Icon, color }: {
  label: string; value: number | string; icon: React.ElementType; color: string
}) {
  return (
    <div className="card p-4 flex items-center gap-4">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{value}</p>
        <p className="text-xs text-gray-400">{label}</p>
      </div>
    </div>
  )
}

function statusColor(status: string) {
  switch (status) {
    case 'completed': return 'text-green-400'
    case 'failed': return 'text-red-400'
    case 'running': return 'text-blue-400'
    default: return 'text-gray-400'
  }
}

export function AssetGenerationDashboardPage() {
  const { projectId } = useParams<{ projectId: string }>()

  const { data, isLoading, isError } = useQuery({
    queryKey: ['ag-dashboard', projectId],
    queryFn: () => assetGenerationApi.getDashboard(projectId!),
    enabled: !!projectId,
    refetchInterval: 30_000,
  })

  const links = [
    { to: 'prompts', label: 'Prompt Monitoring', Icon: MessageSquare, color: 'bg-purple-600' },
    { to: 'jobs', label: 'Generation Jobs', Icon: ListChecks, color: 'bg-blue-600' },
    { to: 'consistency', label: 'Consistency Engine', Icon: Layers, color: 'bg-teal-600' },
    { to: 'quality', label: 'Quality Evaluation', Icon: ShieldCheck, color: 'bg-green-600' },
    { to: 'library', label: 'Asset Library', Icon: Search, color: 'bg-orange-600' },
  ]

  if (isLoading) return <div className="p-8 flex justify-center"><Spinner size="lg" /></div>
  if (isError || !data) return (
    <div className="p-8 text-center text-red-400">Failed to load dashboard. Check project ID.</div>
  )

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <LayoutDashboard className="w-6 h-6 text-brand-400" />
            Asset Generation Engine
          </h1>
          <p className="text-gray-400 text-sm mt-1">Phase 6 — AI-powered asset generation pipeline</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Assets" value={data.total_assets} icon={Image} color="bg-brand-600" />
        <StatCard label="Completed" value={data.assets_completed} icon={CheckCircle} color="bg-green-600" />
        <StatCard label="Pending" value={data.assets_pending} icon={Clock} color="bg-yellow-600" />
        <StatCard label="Generating" value={data.assets_generating} icon={Zap} color="bg-blue-600" />
        <StatCard label="Failed" value={data.assets_failed} icon={AlertCircle} color="bg-red-600" />
        <StatCard label="Total Retries" value={data.total_retries} icon={RefreshCw} color="bg-orange-600" />
        <StatCard label="Avg Quality" value={data.avg_quality_score.toFixed(1)} icon={ShieldCheck} color="bg-teal-600" />
        <StatCard label="Storage (MB)" value={(data.storage_bytes_used / 1_048_576).toFixed(1)} icon={Database} color="bg-indigo-600" />
      </div>

      {/* Quick links */}
      <div>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Sub-pages</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {links.map(({ to, label, Icon, color }) => (
            <Link
              key={to}
              to={`/projects/${projectId}/asset-generation/${to}`}
              className="card p-4 flex flex-col items-center gap-2 hover:bg-gray-800 transition-colors text-center"
            >
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
                <Icon className="w-5 h-5 text-white" />
              </div>
              <span className="text-xs text-gray-300 font-medium">{label}</span>
            </Link>
          ))}
        </div>
      </div>

      {/* Assets by type */}
      {Object.keys(data.assets_by_type).length > 0 && (
        <div className="card p-4">
          <h2 className="font-semibold text-white mb-3">Assets by Type</h2>
          <div className="flex flex-wrap gap-2">
            {Object.entries(data.assets_by_type).map(([type, count]) => (
              <span key={type} className="px-3 py-1 rounded-full text-xs bg-gray-800 text-gray-300">
                {type}: <span className="font-bold text-white">{count}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Recent Jobs */}
      <div className="card p-4">
        <h2 className="font-semibold text-white mb-3">Recent Jobs</h2>
        {data.recent_jobs.length === 0 ? (
          <p className="text-gray-500 text-sm text-center py-4">No jobs yet</p>
        ) : (
          <div className="space-y-2">
            {data.recent_jobs.map((job) => (
              <div key={job.id} className="flex items-center justify-between p-2 rounded bg-gray-800">
                <div>
                  <p className="text-sm text-white font-medium">{job.job_type}</p>
                  <p className="text-xs text-gray-500">{job.id.slice(0, 8)}</p>
                </div>
                <span className={`text-xs font-medium ${statusColor(job.status)}`}>{job.status}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 7-day history */}
      {data.generation_history_7d.length > 0 && (
        <div className="card p-4">
          <h2 className="font-semibold text-white mb-3">7-Day Generation History</h2>
          <div className="space-y-1">
            {data.generation_history_7d.map((entry, i) => (
              <div key={i} className="flex items-center justify-between text-xs text-gray-400 py-1 border-b border-gray-800 last:border-0">
                <span>{String(entry.date ?? entry.day ?? i)}</span>
                <span className="text-white">{String(entry.count ?? entry.total ?? '')}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
