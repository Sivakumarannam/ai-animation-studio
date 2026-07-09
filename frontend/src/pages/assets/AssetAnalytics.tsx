import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getDashboard, listGenerationHistory, listAssetProjects, type DashboardStats, type AssetProject } from '@/api/assets'

function BarChart({ data, label }: { data: Record<string, number>; label: string }) {
  const max = Math.max(...Object.values(data), 1)
  return (
    <div>
      <p className="text-xs text-gray-400 mb-3">{label}</p>
      <div className="space-y-2">
        {Object.entries(data).map(([key, val]) => (
          <div key={key} className="flex items-center gap-3">
            <span className="text-xs text-gray-400 w-28 shrink-0 capitalize">{key.replace('_', ' ')}</span>
            <div className="flex-1 h-4 bg-gray-700 rounded overflow-hidden">
              <div
                className="h-full bg-indigo-500 rounded"
                style={{ width: `${(val / max) * 100}%` }}
              />
            </div>
            <span className="text-xs text-gray-300 w-8 text-right">{val}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function AssetAnalytics() {
  const [projects, setProjects] = useState<AssetProject[]>([])
  const [projectId, setProjectId] = useState('')
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [history, setHistory] = useState<unknown[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    listAssetProjects().then(r => {
      setProjects(r.data.items)
      if (r.data.items.length > 0) setProjectId(r.data.items[0].id)
    })
  }, [])

  useEffect(() => {
    if (!projectId) return
    setLoading(true)
    Promise.all([
      getDashboard(projectId),
      listGenerationHistory(projectId, 1, 10),
    ])
      .then(([statsRes, histRes]) => {
        setStats(statsRes.data)
        setHistory((histRes.data as { items: unknown[] }).items)
      })
      .finally(() => setLoading(false))
  }, [projectId])

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <div className="flex items-center gap-4 mb-6">
        <Link to="/assets" className="text-gray-400 hover:text-white text-sm">← Dashboard</Link>
        <h1 className="text-2xl font-bold">Asset Analytics</h1>
      </div>

      <div className="mb-4">
        <select
          value={projectId}
          onChange={e => setProjectId(e.target.value)}
          className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
        >
          {projects.map(p => <option key={p.id} value={p.id}>{p.name || p.project_id}</option>)}
        </select>
      </div>

      {loading ? (
        <p className="text-gray-400 text-sm">Loading analytics…</p>
      ) : stats ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Asset type distribution */}
          {Object.keys(stats.assets_by_type).length > 0 && (
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
              <BarChart data={stats.assets_by_type} label="Assets by Type" />
            </div>
          )}

          {/* Status distribution */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
            <BarChart
              data={{
                completed: stats.assets_completed,
                pending: stats.assets_pending,
                generating: stats.assets_generating,
                failed: stats.assets_failed,
              }}
              label="Assets by Status"
            />
          </div>

          {/* Quality overview */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
            <p className="text-xs text-gray-400 mb-3">Quality Metrics</p>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-300">Average Quality Score</span>
                <span className={`text-sm font-bold ${stats.avg_quality_score >= 90 ? 'text-green-400' : stats.avg_quality_score >= 70 ? 'text-yellow-400' : 'text-red-400'}`}>
                  {stats.avg_quality_score.toFixed(1)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-300">Pass Rate</span>
                <span className="text-sm font-bold text-white">
                  {stats.total_assets > 0
                    ? `${((stats.assets_completed / stats.total_assets) * 100).toFixed(0)}%`
                    : '—'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-300">Total Retries</span>
                <span className="text-sm font-bold text-orange-400">{stats.total_retries}</span>
              </div>
            </div>
          </div>

          {/* Generation history */}
          {history.length > 0 && (
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-5">
              <p className="text-xs text-gray-400 mb-3">Recent Generation Runs</p>
              <div className="space-y-2">
                {(history as Record<string, unknown>[]).map((h, i) => (
                  <div key={i} className="flex items-center justify-between py-1.5 border-b border-gray-700/50 last:border-0">
                    <div>
                      <p className="text-xs text-white">{String(h.run_type ?? '').replace('_', ' ')}</p>
                      <p className="text-xs text-gray-500">{String(h.assets_accepted ?? 0)}/{String(h.assets_generated ?? 0)} accepted</p>
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${
                      h.run_status === 'completed'
                        ? 'bg-green-900/40 text-green-300 border-green-700'
                        : 'bg-yellow-900/40 text-yellow-300 border-yellow-700'
                    }`}>
                      {String(h.run_status ?? '')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : null}
    </div>
  )
}
