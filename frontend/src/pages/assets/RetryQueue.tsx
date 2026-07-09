import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listRetryQueue, retryEntry, listAssetProjects, type RetryQueueEntry, type AssetProject } from '@/api/assets'

const STATUS_STYLES: Record<string, string> = {
  pending: 'bg-yellow-900/40 text-yellow-300 border-yellow-700',
  retrying: 'bg-blue-900/40 text-blue-300 border-blue-700',
  resolved: 'bg-green-900/40 text-green-300 border-green-700',
  exhausted: 'bg-red-900/40 text-red-300 border-red-700',
}

export default function RetryQueue() {
  const [projects, setProjects] = useState<AssetProject[]>([])
  const [projectId, setProjectId] = useState('')
  const [status, setStatus] = useState('')
  const [entries, setEntries] = useState<RetryQueueEntry[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [retrying, setRetrying] = useState<string | null>(null)

  useEffect(() => {
    listAssetProjects().then(r => {
      setProjects(r.data.items)
      if (r.data.items.length > 0) setProjectId(r.data.items[0].id)
    })
  }, [])

  const loadEntries = () => {
    if (!projectId) return
    setLoading(true)
    listRetryQueue(projectId, status || undefined, page, 20)
      .then(r => { setEntries(r.data.items); setTotal(r.data.meta.total) })
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadEntries() }, [projectId, status, page])

  const handleRetry = async (id: string) => {
    setRetrying(id)
    try {
      await retryEntry(id)
      setTimeout(loadEntries, 2000)
    } finally {
      setRetrying(null)
    }
  }

  const totalPages = Math.ceil(total / 20)

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <div className="flex items-center gap-4 mb-6">
        <Link to="/assets" className="text-gray-400 hover:text-white text-sm">← Dashboard</Link>
        <h1 className="text-2xl font-bold">Retry Queue</h1>
        <span className="text-gray-400 text-sm ml-auto">{total} entries</span>
      </div>

      <div className="flex flex-wrap gap-3 mb-4">
        <select
          value={projectId}
          onChange={e => { setProjectId(e.target.value); setPage(1) }}
          className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
        >
          {projects.map(p => <option key={p.id} value={p.id}>{p.name || p.project_id}</option>)}
        </select>
        <select
          value={status}
          onChange={e => { setStatus(e.target.value); setPage(1) }}
          className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
        >
          <option value="">All Statuses</option>
          {['pending', 'retrying', 'resolved', 'exhausted'].map(s => (
            <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
          ))}
        </select>
        <button onClick={loadEntries} className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors">
          ↻ Refresh
        </button>
      </div>

      <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
        {loading ? (
          <p className="p-4 text-gray-400 text-sm">Loading…</p>
        ) : entries.length === 0 ? (
          <p className="p-8 text-gray-400 text-sm text-center">No retry queue entries found.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700 text-xs text-gray-400 uppercase">
                <th className="px-4 py-3 text-left">Asset</th>
                <th className="px-4 py-3 text-left">Failure Reason</th>
                <th className="px-4 py-3 text-center">Attempts</th>
                <th className="px-4 py-3 text-center">Quality</th>
                <th className="px-4 py-3 text-center">Status</th>
                <th className="px-4 py-3 text-center">Priority</th>
                <th className="px-4 py-3 text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {entries.map(e => (
                <tr key={e.id} className="border-b border-gray-700/50 last:border-0 hover:bg-gray-700/30 transition-colors">
                  <td className="px-4 py-3">
                    <Link to={`/assets/viewer/${e.asset_id}`} className="text-indigo-400 hover:text-indigo-300 text-xs truncate block max-w-[120px]">
                      {e.asset_id.slice(0, 8)}…
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-gray-300">{e.failure_reason.replace(/_/g, ' ')}</td>
                  <td className="px-4 py-3 text-center text-gray-300">{e.retry_count} / {e.max_retries}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={e.quality_score >= 90 ? 'text-green-400' : e.quality_score >= 70 ? 'text-yellow-400' : 'text-red-400'}>
                      {e.quality_score.toFixed(0)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${STATUS_STYLES[e.status] ?? 'bg-gray-700 text-gray-300 border-gray-600'}`}>
                      {e.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center text-gray-400">{e.priority}</td>
                  <td className="px-4 py-3 text-center">
                    {e.status === 'pending' && (
                      <button
                        disabled={retrying === e.id}
                        onClick={() => handleRetry(e.id)}
                        className="text-xs text-indigo-400 hover:text-indigo-300 disabled:opacity-50"
                      >
                        {retrying === e.id ? 'Retrying…' : 'Retry'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-4">
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
            className="px-3 py-1.5 bg-gray-800 rounded-lg text-sm disabled:opacity-50 hover:bg-gray-700">
            ← Prev
          </button>
          <span className="text-sm text-gray-400">Page {page} of {totalPages}</span>
          <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}
            className="px-3 py-1.5 bg-gray-800 rounded-lg text-sm disabled:opacity-50 hover:bg-gray-700">
            Next →
          </button>
        </div>
      )}
    </div>
  )
}
