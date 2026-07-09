import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listJobs, listAssetProjects, triggerEpisodeGeneration, type GenerationJob, type AssetProject } from '@/api/assets'

const STATUS_STYLES: Record<string, string> = {
  pending: 'bg-yellow-900/40 text-yellow-300 border-yellow-700',
  running: 'bg-blue-900/40 text-blue-300 border-blue-700',
  completed: 'bg-green-900/40 text-green-300 border-green-700',
  failed: 'bg-red-900/40 text-red-300 border-red-700',
  dispatched: 'bg-indigo-900/40 text-indigo-300 border-indigo-700',
}

function JobRow({ job }: { job: GenerationJob }) {
  const dur = job.duration_ms > 0 ? `${(job.duration_ms / 1000).toFixed(1)}s` : '—'
  return (
    <div className="flex items-center gap-4 py-3 border-b border-gray-800 last:border-0">
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white font-medium truncate">{job.job_type.replace(/_/g, ' ')}</p>
        <p className="text-xs text-gray-400 truncate">{job.id}</p>
      </div>
      <div className="text-xs text-gray-400 hidden sm:block w-32 shrink-0">
        {new Date(job.created_at).toLocaleTimeString()}
      </div>
      <div className="text-xs text-gray-400 w-16 shrink-0 text-right">{dur}</div>
      <span className={`text-xs px-2 py-0.5 rounded-full border shrink-0 ${STATUS_STYLES[job.status] ?? 'bg-gray-700 text-gray-300 border-gray-600'}`}>
        {job.status}
      </span>
    </div>
  )
}

export default function GenerationQueue() {
  const [projects, setProjects] = useState<AssetProject[]>([])
  const [projectId, setProjectId] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [jobs, setJobs] = useState<GenerationJob[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)

  // Trigger form state
  const [episodeId, setEpisodeId] = useState('')
  const [dispatching, setDispatching] = useState(false)
  const [dispatchMsg, setDispatchMsg] = useState<string | null>(null)

  useEffect(() => {
    listAssetProjects().then(r => {
      setProjects(r.data.items)
      if (r.data.items.length > 0) setProjectId(r.data.items[0].id)
    })
  }, [])

  const loadJobs = () => {
    if (!projectId) return
    setLoading(true)
    listJobs(projectId, statusFilter || undefined, page, 20)
      .then(r => { setJobs(r.data.items); setTotal(r.data.meta.total) })
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadJobs() }, [projectId, statusFilter, page])

  const handleTrigger = async () => {
    if (!projectId || !episodeId.trim()) return
    setDispatching(true)
    setDispatchMsg(null)
    try {
      const r = await triggerEpisodeGeneration({
        project_id: projects.find(p => p.id === projectId)?.project_id ?? projectId,
        episode_id: episodeId.trim(),
        quality_threshold: 90,
        force_regenerate: false,
      })
      setDispatchMsg(`✓ Dispatched — Job ${r.data.job_id.slice(0, 8)}… (${r.data.dispatch_mode})`)
      setTimeout(loadJobs, 2000)
    } catch {
      setDispatchMsg('✗ Dispatch failed — check logs')
    } finally {
      setDispatching(false)
    }
  }

  const totalPages = Math.ceil(total / 20)

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <div className="flex items-center gap-4 mb-6">
        <Link to="/assets" className="text-gray-400 hover:text-white text-sm">← Dashboard</Link>
        <h1 className="text-2xl font-bold">Generation Queue</h1>
        <span className="text-gray-400 text-sm ml-auto">{total} jobs</span>
      </div>

      {/* Trigger panel */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 p-5 mb-6">
        <h3 className="text-sm font-medium text-gray-300 mb-3">Trigger Episode Generation</h3>
        <div className="flex flex-wrap gap-3">
          <select
            value={projectId}
            onChange={e => setProjectId(e.target.value)}
            className="bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
          >
            {projects.map(p => <option key={p.id} value={p.id}>{p.name || p.project_id}</option>)}
          </select>
          <input
            type="text"
            placeholder="Episode UUID"
            value={episodeId}
            onChange={e => setEpisodeId(e.target.value)}
            className="bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 flex-1 min-w-[200px]"
          />
          <button
            onClick={handleTrigger}
            disabled={dispatching || !episodeId.trim()}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors"
          >
            {dispatching ? 'Dispatching…' : 'Generate Assets'}
          </button>
        </div>
        {dispatchMsg && (
          <p className={`mt-2 text-sm ${dispatchMsg.startsWith('✓') ? 'text-green-400' : 'text-red-400'}`}>{dispatchMsg}</p>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <select
          value={statusFilter}
          onChange={e => { setStatusFilter(e.target.value); setPage(1) }}
          className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
        >
          <option value="">All Statuses</option>
          {['pending', 'running', 'completed', 'failed'].map(s => (
            <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
          ))}
        </select>
        <button onClick={loadJobs} className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors">
          ↻ Refresh
        </button>
      </div>

      {/* Jobs list */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 p-4">
        {loading ? (
          <p className="text-gray-400 text-sm">Loading jobs…</p>
        ) : jobs.length === 0 ? (
          <p className="text-gray-400 text-sm py-4 text-center">No jobs found.</p>
        ) : (
          jobs.map(j => <JobRow key={j.id} job={j} />)
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-4">
          <button
            disabled={page <= 1}
            onClick={() => setPage(p => p - 1)}
            className="px-3 py-1.5 bg-gray-800 rounded-lg text-sm disabled:opacity-50 hover:bg-gray-700"
          >
            ← Prev
          </button>
          <span className="text-sm text-gray-400">Page {page} of {totalPages}</span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage(p => p + 1)}
            className="px-3 py-1.5 bg-gray-800 rounded-lg text-sm disabled:opacity-50 hover:bg-gray-700"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  )
}
