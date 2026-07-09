import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getDashboard, listAssetProjects, type DashboardStats, type AssetProject } from '@/api/assets'

function StatCard({ label, value, color }: { label: string; value: number | string; color?: string }) {
  return (
    <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
      <p className="text-sm text-gray-400 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color ?? 'text-white'}`}>{value}</p>
    </div>
  )
}

const JOB_STATUS_COLOR: Record<string, string> = {
  pending: 'text-yellow-400',
  running: 'text-blue-400',
  completed: 'text-green-400',
  failed: 'text-red-400',
}

export default function AssetsDashboard() {
  const [projects, setProjects] = useState<AssetProject[]>([])
  const [selectedProject, setSelectedProject] = useState<string>('')
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loadingProjects, setLoadingProjects] = useState(true)
  const [loadingStats, setLoadingStats] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    listAssetProjects()
      .then(r => {
        setProjects(r.data.items)
        if (r.data.items.length > 0) setSelectedProject(r.data.items[0].id)
      })
      .catch(() => setError('Failed to load asset projects'))
      .finally(() => setLoadingProjects(false))
  }, [])

  useEffect(() => {
    if (!selectedProject) return
    setLoadingStats(true)
    getDashboard(selectedProject)
      .then(r => setStats(r.data))
      .catch(() => setError('Failed to load dashboard stats'))
      .finally(() => setLoadingStats(false))
  }, [selectedProject])

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Asset Generation Engine</h1>
          <p className="text-gray-400 text-sm mt-1">AI-powered visual asset production pipeline</p>
        </div>
        <div className="flex gap-3">
          <Link
            to="/assets/library"
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors"
          >
            Library
          </Link>
          <Link
            to="/assets/queue"
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition-colors"
          >
            Generation Queue
          </Link>
        </div>
      </div>

      {/* Project selector */}
      {loadingProjects ? (
        <div className="text-gray-400 text-sm mb-4">Loading projects…</div>
      ) : projects.length === 0 ? (
        <div className="bg-gray-800 rounded-xl p-8 text-center border border-gray-700 mb-6">
          <p className="text-gray-400 mb-4">No asset projects yet. Create one by triggering generation for an episode.</p>
        </div>
      ) : (
        <div className="mb-6">
          <select
            value={selectedProject}
            onChange={e => setSelectedProject(e.target.value)}
            className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
          >
            {projects.map(p => (
              <option key={p.id} value={p.id}>{p.name || p.project_id}</option>
            ))}
          </select>
        </div>
      )}

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 text-red-300 text-sm mb-4">{error}</div>
      )}

      {loadingStats ? (
        <div className="text-gray-400 text-sm">Loading stats…</div>
      ) : stats ? (
        <>
          {/* Stats grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <StatCard label="Total Assets" value={stats.total_assets} />
            <StatCard label="Completed" value={stats.assets_completed} color="text-green-400" />
            <StatCard label="Generating" value={stats.assets_generating} color="text-blue-400" />
            <StatCard label="Failed" value={stats.assets_failed} color="text-red-400" />
            <StatCard label="Pending" value={stats.assets_pending} color="text-yellow-400" />
            <StatCard label="Avg Quality" value={`${stats.avg_quality_score.toFixed(1)}%`} />
            <StatCard label="Total Retries" value={stats.total_retries} />
            <StatCard label="Storage" value={`${(stats.storage_bytes_used / 1024 / 1024).toFixed(1)} MB`} />
          </div>

          {/* Assets by type */}
          {Object.keys(stats.assets_by_type).length > 0 && (
            <div className="bg-gray-800 rounded-xl p-5 border border-gray-700 mb-6">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Assets by Type</h3>
              <div className="flex flex-wrap gap-3">
                {Object.entries(stats.assets_by_type).map(([type, count]) => (
                  <div key={type} className="flex items-center gap-2 bg-gray-700 rounded-lg px-3 py-1.5">
                    <span className="text-xs text-gray-400 capitalize">{type.replace('_', ' ')}</span>
                    <span className="text-sm font-semibold text-white">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent Jobs */}
          {stats.recent_jobs.length > 0 && (
            <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-gray-300">Recent Jobs</h3>
                <Link to="/assets/queue" className="text-xs text-indigo-400 hover:text-indigo-300">
                  View All →
                </Link>
              </div>
              <div className="space-y-2">
                {stats.recent_jobs.map(job => (
                  <div key={job.id} className="flex items-center justify-between py-2 border-b border-gray-700 last:border-0">
                    <div>
                      <p className="text-sm text-white font-medium">{job.job_type.replace(/_/g, ' ')}</p>
                      <p className="text-xs text-gray-400">{new Date(job.created_at).toLocaleString()}</p>
                    </div>
                    <span className={`text-xs font-medium ${JOB_STATUS_COLOR[job.status] ?? 'text-gray-400'}`}>
                      {job.status.toUpperCase()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      ) : selectedProject ? (
        <div className="text-gray-400 text-sm">No dashboard data available.</div>
      ) : null}
    </div>
  )
}
