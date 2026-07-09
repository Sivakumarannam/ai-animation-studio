import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { searchLibrary, listAssetProjects, type Asset, type AssetProject } from '@/api/assets'

const ASSET_TYPES = ['character', 'background', 'prop', 'thumbnail', 'expression', 'pose', 'object', 'effect']
const STATUSES = ['completed', 'pending', 'generating', 'evaluating', 'retrying', 'failed']

const STATUS_COLOR: Record<string, string> = {
  completed: 'bg-green-900/50 text-green-300 border-green-700',
  pending: 'bg-yellow-900/50 text-yellow-300 border-yellow-700',
  generating: 'bg-blue-900/50 text-blue-300 border-blue-700',
  evaluating: 'bg-purple-900/50 text-purple-300 border-purple-700',
  retrying: 'bg-orange-900/50 text-orange-300 border-orange-700',
  failed: 'bg-red-900/50 text-red-300 border-red-700',
}

function AssetCard({ asset }: { asset: Asset }) {
  return (
    <Link to={`/assets/viewer/${asset.id}`} className="block">
      <div className="bg-gray-800 rounded-xl border border-gray-700 hover:border-indigo-500/50 transition-colors overflow-hidden">
        {/* Placeholder image */}
        <div className="aspect-square bg-gradient-to-br from-gray-700 to-gray-900 flex items-center justify-center">
          {asset.storage_key ? (
            <img
              src={`/api/v1/assets/file/${asset.storage_key}`}
              alt={asset.name}
              className="w-full h-full object-cover"
              onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
            />
          ) : (
            <div className="text-4xl opacity-20">🎨</div>
          )}
        </div>
        <div className="p-3">
          <p className="text-sm font-medium text-white truncate">{asset.name}</p>
          <div className="flex items-center justify-between mt-2">
            <span className="text-xs text-gray-400 capitalize">{asset.asset_type.replace('_', ' ')}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full border ${STATUS_COLOR[asset.status] ?? 'bg-gray-700 text-gray-300 border-gray-600'}`}>
              {asset.status}
            </span>
          </div>
          {asset.quality_score > 0 && (
            <div className="mt-2">
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>Quality</span>
                <span className={asset.quality_score >= 90 ? 'text-green-400' : asset.quality_score >= 70 ? 'text-yellow-400' : 'text-red-400'}>
                  {asset.quality_score.toFixed(1)}
                </span>
              </div>
              <div className="h-1 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${asset.quality_score >= 90 ? 'bg-green-500' : asset.quality_score >= 70 ? 'bg-yellow-500' : 'bg-red-500'}`}
                  style={{ width: `${asset.quality_score}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </Link>
  )
}

export default function AssetLibrary() {
  const [projects, setProjects] = useState<AssetProject[]>([])
  const [projectId, setProjectId] = useState('')
  const [assets, setAssets] = useState<Asset[]>([])
  const [total, setTotal] = useState(0)
  const [query, setQuery] = useState('')
  const [assetType, setAssetType] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    listAssetProjects().then(r => {
      setProjects(r.data.items)
      if (r.data.items.length > 0) setProjectId(r.data.items[0].id)
    })
  }, [])

  const search = useCallback(() => {
    if (!projectId) return
    setLoading(true)
    searchLibrary({
      project_id: projectId,
      query: query || undefined,
      asset_type: assetType || undefined,
      status: status || undefined,
      limit: 24,
      offset: (page - 1) * 24,
    })
      .then(r => {
        setAssets(r.data.items)
        setTotal(r.data.total)
      })
      .finally(() => setLoading(false))
  }, [projectId, query, assetType, status, page])

  useEffect(() => { search() }, [search])

  const totalPages = Math.ceil(total / 24)

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <div className="flex items-center gap-4 mb-6">
        <Link to="/assets" className="text-gray-400 hover:text-white text-sm">← Dashboard</Link>
        <h1 className="text-2xl font-bold">Asset Library</h1>
        <span className="text-gray-400 text-sm ml-auto">{total} assets</span>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <select
          value={projectId}
          onChange={e => { setProjectId(e.target.value); setPage(1) }}
          className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
        >
          {projects.map(p => <option key={p.id} value={p.id}>{p.name || p.project_id}</option>)}
        </select>
        <input
          type="text"
          placeholder="Search assets…"
          value={query}
          onChange={e => { setQuery(e.target.value); setPage(1) }}
          className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 w-48"
        />
        <select
          value={assetType}
          onChange={e => { setAssetType(e.target.value); setPage(1) }}
          className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
        >
          <option value="">All Types</option>
          {ASSET_TYPES.map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1).replace('_', ' ')}</option>)}
        </select>
        <select
          value={status}
          onChange={e => { setStatus(e.target.value); setPage(1) }}
          className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
        >
          <option value="">All Statuses</option>
          {STATUSES.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
        </select>
      </div>

      {loading ? (
        <div className="text-gray-400 text-sm">Loading assets…</div>
      ) : assets.length === 0 ? (
        <div className="bg-gray-800 rounded-xl p-12 text-center border border-gray-700">
          <p className="text-4xl mb-4">🖼️</p>
          <p className="text-gray-300 font-medium">No assets found</p>
          <p className="text-gray-400 text-sm mt-2">Try adjusting your filters or generate assets for an episode.</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-6">
            {assets.map(a => <AssetCard key={a.id} asset={a} />)}
          </div>
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
                className="px-3 py-1.5 bg-gray-800 rounded-lg text-sm disabled:opacity-50 hover:bg-gray-700 transition-colors"
              >
                ← Prev
              </button>
              <span className="text-sm text-gray-400">Page {page} of {totalPages}</span>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage(p => p + 1)}
                className="px-3 py-1.5 bg-gray-800 rounded-lg text-sm disabled:opacity-50 hover:bg-gray-700 transition-colors"
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
