import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Search, BookImage, Users, Layers, Package, SlidersHorizontal, ChevronRight } from 'lucide-react'
import { assetGenerationApi } from '@/api/assetGeneration'
import type { AssetResponse } from '@/api/assetGeneration'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'

type LibraryTab = 'search' | 'characters' | 'backgrounds' | 'props'

const ASSET_TYPES = ['character', 'background', 'prop', 'scene_layout', 'audio', 'animation']
const STATUSES = ['completed', 'pending', 'failed', 'generating']

function AssetCard({ asset, onSelect }: { asset: AssetResponse; onSelect?: (a: AssetResponse) => void }) {
  const qualityColor =
    asset.quality_score >= 80
      ? 'text-green-400'
      : asset.quality_score >= 60
      ? 'text-yellow-400'
      : 'text-red-400'

  return (
    <div
      className="card p-3 space-y-2 cursor-pointer hover:border-gray-600 transition-colors"
      onClick={() => onSelect?.(asset)}
    >
      <div className="w-full aspect-video rounded bg-gray-800 flex items-center justify-center">
          <BookImage className="w-8 h-8 text-gray-600" />
        </div>
      <div>
        <p className="text-sm font-medium text-gray-100 truncate">{asset.name}</p>
        <div className="flex items-center justify-between mt-1">
          <span className="text-xs text-gray-500 capitalize">{asset.asset_type}</span>
          <span className={`text-xs font-semibold ${qualityColor}`}>
            {asset.quality_score.toFixed(0)}
          </span>
        </div>
      </div>
      {asset.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {asset.tags.slice(0, 3).map((tag) => (
            <span key={tag} className="text-xs bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded">
              {tag}
            </span>
          ))}
          {asset.tags.length > 3 && (
            <span className="text-xs text-gray-600">+{asset.tags.length - 3}</span>
          )}
        </div>
      )}
    </div>
  )
}

export function AssetLibraryPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const [tab, setTab] = useState<LibraryTab>('search')
  const [query, setQuery] = useState('')
  const [assetType, setAssetType] = useState('')
  const [status, setStatus] = useState('')
  const [minQuality, setMinQuality] = useState('')
  const [searchPage, setSearchPage] = useState(0)
  const [libPage, setLibPage] = useState(1)
  const [selected, setSelected] = useState<AssetResponse | null>(null)

  const searchEnabled = tab === 'search'
  const { data: searchData, isLoading: searchLoading } = useQuery({
    queryKey: ['ag-library-search', projectId, query, assetType, status, minQuality, searchPage],
    queryFn: () =>
      assetGenerationApi.searchLibrary({
        query: query || undefined,
        project_id: projectId,
        asset_type: assetType || undefined,
        status: status || undefined,
        min_quality: minQuality ? Number(minQuality) : undefined,
        limit: 20,
        offset: searchPage * 20,
      }),
    enabled: searchEnabled && !!projectId,
  })

  const { data: charData, isLoading: charLoading } = useQuery({
    queryKey: ['ag-char-library', projectId, libPage],
    queryFn: () => assetGenerationApi.getCharacterLibrary(projectId!, libPage),
    enabled: tab === 'characters' && !!projectId,
  })

  const { data: bgData, isLoading: bgLoading } = useQuery({
    queryKey: ['ag-bg-library', projectId, libPage],
    queryFn: () => assetGenerationApi.getBackgroundLibrary(projectId!, libPage),
    enabled: tab === 'backgrounds' && !!projectId,
  })

  const { data: propData, isLoading: propLoading } = useQuery({
    queryKey: ['ag-prop-library', projectId, libPage],
    queryFn: () => assetGenerationApi.getPropLibrary(projectId!, libPage),
    enabled: tab === 'props' && !!projectId,
  })

  const tabs: { id: LibraryTab; label: string; Icon: React.ElementType }[] = [
    { id: 'search', label: 'Search All', Icon: Search },
    { id: 'characters', label: 'Characters', Icon: Users },
    { id: 'backgrounds', label: 'Backgrounds', Icon: Layers },
    { id: 'props', label: 'Props', Icon: Package },
  ]

  const currentPagedData = tab === 'characters' ? charData : tab === 'backgrounds' ? bgData : propData
  const currentLoading =
    tab === 'search' ? searchLoading :
    tab === 'characters' ? charLoading :
    tab === 'backgrounds' ? bgLoading : propLoading

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
        <span>Asset Generation</span>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300">Asset Library</span>
      </div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <BookImage className="w-6 h-6 text-cyan-400" />
            Asset Library
          </h1>
          <p className="text-gray-400 text-sm mt-1">Browse, search, and reuse generated assets</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-800">
        {tabs.map(({ id, label, Icon }) => (
          <button
            key={id}
            onClick={() => { setTab(id); setLibPage(1); setSearchPage(0) }}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === id
                ? 'border-brand-500 text-brand-400'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Search filters (only on Search tab) */}
      {tab === 'search' && (
        <div className="card p-4 space-y-3">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-300">
            <SlidersHorizontal className="w-4 h-4" /> Filters
          </div>
          <div className="flex flex-wrap gap-3">
            <input
              className="input text-sm py-1.5 flex-1 min-w-48"
              placeholder="Search by name, description, tags…"
              value={query}
              onChange={(e) => { setQuery(e.target.value); setSearchPage(0) }}
            />
            <select
              className="input text-sm py-1.5"
              value={assetType}
              onChange={(e) => { setAssetType(e.target.value); setSearchPage(0) }}
            >
              <option value="">All types</option>
              {ASSET_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
            <select
              className="input text-sm py-1.5"
              value={status}
              onChange={(e) => { setStatus(e.target.value); setSearchPage(0) }}
            >
              <option value="">Any status</option>
              {STATUSES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <input
              className="input text-sm py-1.5 w-32"
              type="number"
              placeholder="Min quality"
              value={minQuality}
              min={0}
              max={100}
              onChange={(e) => { setMinQuality(e.target.value); setSearchPage(0) }}
            />
          </div>
        </div>
      )}

      {/* Results grid */}
      {currentLoading ? (
        <div className="flex justify-center py-16"><Spinner size="lg" /></div>
      ) : tab === 'search' ? (
        <>
          {searchData?.items.length === 0 ? (
            <EmptyState icon={BookImage} title="No assets found" description="Try adjusting your search filters." />
          ) : (
            <>
              <p className="text-sm text-gray-500">{searchData?.total ?? 0} assets found</p>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                {searchData?.items.map((asset) => (
                  <AssetCard key={asset.id} asset={asset} onSelect={setSelected} />
                ))}
              </div>
              {(searchData?.total ?? 0) > 20 && (
                <div className="flex justify-center gap-2">
                  <button
                    className="btn-secondary text-sm px-3 py-1"
                    disabled={searchPage <= 0}
                    onClick={() => setSearchPage((p) => p - 1)}
                  >
                    Prev
                  </button>
                  <span className="text-sm text-gray-400 self-center">
                    Page {searchPage + 1} of {Math.ceil((searchData?.total ?? 1) / 20)}
                  </span>
                  <button
                    className="btn-secondary text-sm px-3 py-1"
                    disabled={(searchPage + 1) * 20 >= (searchData?.total ?? 0)}
                    onClick={() => setSearchPage((p) => p + 1)}
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </>
      ) : (
        <>
          {currentPagedData?.items.length === 0 ? (
            <EmptyState icon={BookImage} title="No assets yet" description="Generate assets to populate this library." />
          ) : (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                {currentPagedData?.items.map((asset) => (
                  <AssetCard key={asset.id} asset={asset} onSelect={setSelected} />
                ))}
              </div>
              {currentPagedData && currentPagedData.meta.total_pages > 1 && (
                <div className="flex justify-center gap-2">
                  <button
                    className="btn-secondary text-sm px-3 py-1"
                    disabled={libPage <= 1}
                    onClick={() => setLibPage((p) => p - 1)}
                  >
                    Prev
                  </button>
                  <span className="text-sm text-gray-400 self-center">
                    Page {libPage} of {currentPagedData.meta.total_pages}
                  </span>
                  <button
                    className="btn-secondary text-sm px-3 py-1"
                    disabled={libPage >= currentPagedData.meta.total_pages}
                    onClick={() => setLibPage((p) => p + 1)}
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </>
      )}

      {/* Detail modal */}
      {selected && (
        <div
          className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4"
          onClick={() => setSelected(null)}
        >
          <div
            className="card p-6 max-w-lg w-full space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-lg font-semibold text-white">{selected.name}</h2>
                <p className="text-xs text-gray-500 capitalize">{selected.asset_type} · {selected.status}</p>
              </div>
              <button onClick={() => setSelected(null)} className="text-gray-500 hover:text-gray-300 text-xl leading-none">×</button>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div><span className="text-gray-400">Quality:</span> <span className="text-white">{selected.quality_score.toFixed(1)}</span></div>
              <div><span className="text-gray-400">Versions:</span> <span className="text-white">{selected.version_count}</span></div>
              <div><span className="text-gray-400">Retries:</span> <span className="text-white">{selected.retry_count}</span></div>
              <div><span className="text-gray-400">Created:</span> <span className="text-white">{new Date(selected.created_at).toLocaleDateString()}</span></div>
              {selected.width > 0 && <div><span className="text-gray-400">Size:</span> <span className="text-white">{selected.width}×{selected.height}</span></div>}
            </div>
            {selected.description && (
              <p className="text-sm text-gray-300">{selected.description}</p>
            )}
            {selected.tags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {selected.tags.map((tag) => (
                  <span key={tag} className="text-xs bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded">{tag}</span>
                ))}
              </div>
            )}
            {selected.storage_key && (
              <p className="text-xs text-gray-500 font-mono truncate">Key: {selected.storage_key}</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
