import { useState, useRef, DragEvent } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Database, Search, Sparkles, RefreshCw,
  Users, ImageIcon, Package, PersonStanding, Volume2, Music, Disc,
  Trash2, Upload, Play, Pause, ChevronLeft, ChevronRight, X, History,
  AlertCircle, Eye, CornerUpLeft, CheckSquare, Square
} from 'lucide-react'
import { libraryApi } from '@/api/library'
import { Spinner } from '@/components/ui/Spinner'
import { clsx } from 'clsx'

const TABS = [
  { id: 'character_template', label: 'Characters', Icon: Users, color: 'text-brand-400 bg-brand-900/20' },
  { id: 'background', label: 'Backgrounds', Icon: ImageIcon, color: 'text-green-400 bg-green-900/20' },
  { id: 'prop', label: 'Props', Icon: Package, color: 'text-orange-400 bg-orange-900/20' },
  { id: 'animation_preset', label: 'Animations', Icon: PersonStanding, color: 'text-purple-400 bg-purple-900/20' },
  { id: 'audio', label: 'Voices / Audio', Icon: Volume2, color: 'text-yellow-400 bg-yellow-900/20' },
  { id: 'music', label: 'Music', Icon: Music, color: 'text-blue-400 bg-blue-900/20' },
  { id: 'sound_effect', label: 'Sound Effects', Icon: Disc, color: 'text-pink-400 bg-pink-900/20' },
]

export function AssetManagerPage() {
  const qc = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Page States
  const [activeTab, setActiveTab] = useState('character_template')
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [showDeleted, setShowDeleted] = useState(false)
  const [page, setPage] = useState(1)
  const pageSize = 12

  // Bulk Operations State
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [bulkCategory, setBulkCategory] = useState('')
  const [bulkTags, setBulkTags] = useState('')
  const [showBulkEdit, setShowBulkEdit] = useState(false)

  // Versioning States
  const [versionAsset, setVersionAsset] = useState<{ id: string; type: string; name: string } | null>(null)
  const [versionNotes, setVersionNotes] = useState('')

  // Preview States
  const [previewAsset, setPreviewAsset] = useState<any | null>(null)
  const [playingAudioUrl, setPlayingAudioUrl] = useState<string | null>(null)
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null)

  // Drag and Drop Upload State
  const [isDragging, setIsDragging] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)

  // 1. Stats Query
  const { data: stats, refetch: refetchStats } = useQuery<Record<string, number>>({
    queryKey: ['asset-stats'],
    queryFn: libraryApi.getAssetStats,
  })

  // 2. Main Assets Query
  const { data: assetsData, isLoading, refetch } = useQuery({
    queryKey: ['assets', activeTab, search, category, showDeleted, page],
    queryFn: () => libraryApi.getAssets(activeTab, {
      page,
      page_size: pageSize,
      search: search || undefined,
      category: category || undefined,
      deleted: showDeleted,
    }),
  })

  // 3. Asset Version Query
  const { data: versionsData, refetch: refetchVersions } = useQuery({
    queryKey: ['versions', versionAsset?.type, versionAsset?.id],
    queryFn: () => libraryApi.getAssetVersions(versionAsset!.type, versionAsset!.id),
    enabled: !!versionAsset,
  })

  // Mutations
  const uploadMutation = useMutation({
    mutationFn: ({ file, type }: { file: File; type: string }) => libraryApi.uploadAssetFile(file, type),
    onSuccess: async (data, variables) => {
      // Once uploaded, create record in library
      await libraryApi.createAsset(variables.type, {
        name: data.filename.split('.')[0],
        category: 'uploaded',
        tags: ['user-upload'],
        file_url: data.file_url,
        thumbnail_url: variables.type === 'background' || variables.type === 'prop' ? data.file_url : '',
        preview_url: variables.type === 'animation_preset' || variables.type.includes('audio') || variables.type === 'music' || variables.type === 'sound_effect' ? data.file_url : '',
        duration_seconds: (activeTab.includes('audio') || activeTab === 'music' || activeTab === 'sound_effect')
          ? await new Promise<number>((resolve) => {
              const audio = new Audio()
              const url = URL.createObjectURL(variables.file)
              audio.addEventListener('loadedmetadata', () => { resolve(isFinite(audio.duration) ? audio.duration : 0); URL.revokeObjectURL(url) })
              audio.addEventListener('error', () => { resolve(0); URL.revokeObjectURL(url) })
              audio.src = url
            })
          : 0.0,
      })
      qc.invalidateQueries({ queryKey: ['assets'] })
      refetchStats()
      setIsUploading(false)
    },
    onError: (err: any) => {
      setUploadError(err.message || 'Upload failed')
      setIsUploading(false)
    }
  })

  const softDeleteMutation = useMutation({
    mutationFn: ({ type, id }: { type: string; id: string }) => libraryApi.deleteAsset(type, id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['assets'] })
      refetchStats()
    }
  })

  const restoreMutation = useMutation({
    mutationFn: ({ type, id }: { type: string; id: string }) => libraryApi.restoreAsset(type, id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['assets'] })
      refetchStats()
    }
  })

  const createVersionMutation = useMutation({
    mutationFn: ({ type, id, snapshot, summary }: { type: string; id: string; snapshot: any; summary: string }) =>
      libraryApi.createAssetVersion(type, id, snapshot, summary),
    onSuccess: () => {
      refetchVersions()
      setVersionNotes('')
    }
  })

  const restoreVersionMutation = useMutation({
    mutationFn: ({ type, id, version }: { type: string; id: string; version: number }) =>
      libraryApi.restoreAssetVersion(type, id, version),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['assets'] })
      setVersionAsset(null)
    }
  })

  const bulkDeleteMutation = useMutation({
    mutationFn: ({ type, ids }: { type: string; ids: string[] }) => libraryApi.bulkDelete(type, ids),
    onSuccess: () => {
      setSelectedIds([])
      qc.invalidateQueries({ queryKey: ['assets'] })
      refetchStats()
    }
  })

  const bulkRestoreMutation = useMutation({
    mutationFn: ({ type, ids }: { type: string; ids: string[] }) => libraryApi.bulkRestore(type, ids),
    onSuccess: () => {
      setSelectedIds([])
      qc.invalidateQueries({ queryKey: ['assets'] })
      refetchStats()
    }
  })

  const bulkUpdateMutation = useMutation({
    mutationFn: ({ type, ids, cat, tags }: { type: string; ids: string[]; cat?: string; tags?: string[] }) =>
      libraryApi.bulkUpdate(type, ids, cat, tags),
    onSuccess: () => {
      setSelectedIds([])
      setShowBulkEdit(false)
      setBulkCategory('')
      setBulkTags('')
      qc.invalidateQueries({ queryKey: ['assets'] })
    }
  })

  const seedMutation = useMutation({
    mutationFn: (type: string) => libraryApi.seedAssets(type),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['assets'] })
      refetchStats()
    }
  })

  // Audio preview player logic
  const handlePlayAudio = (url: string) => {
    if (playingAudioUrl === url) {
      audioPlayerRef.current?.pause()
      setPlayingAudioUrl(null)
    } else {
      setPlayingAudioUrl(url)
      if (audioPlayerRef.current) {
        audioPlayerRef.current.src = url
        audioPlayerRef.current.play()
      }
    }
  }

  // Drag over / leave handler
  const handleDragOver = (e: DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    setUploadError(null)

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0]
      // Disallow folders
      if (file.type === '' && file.size % 4096 === 0) return
      uploadFile(file)
    }
  }

  const handleFileSelect = (e: any) => {
    setUploadError(null)
    if (e.target.files && e.target.files.length > 0) {
      uploadFile(e.target.files[0])
    }
  }

  const uploadFile = (file: File) => {
    setIsUploading(true)
    uploadMutation.mutate({ file, type: activeTab })
  }

  // Selection toggle
  const toggleSelect = (id: string) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])
  }

  const toggleSelectAll = () => {
    const items = assetsData?.items ?? []
    if (selectedIds.length === items.length) {
      setSelectedIds([])
    } else {
      setSelectedIds(items.map(x => x.id))
    }
  }

  const items = assetsData?.items ?? []
  const total = assetsData?.total ?? 0
  const totalPages = assetsData?.total_pages ?? 1

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Database className="w-6 h-6 text-brand-400" />
            Asset Manager
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Centrally upload, tag, version, and manage all visual, animation, and audio assets
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => seedMutation.mutate(activeTab)}
            disabled={seedMutation.isPending}
            className="btn-secondary flex items-center gap-2 text-xs"
          >
            {seedMutation.isPending ? <Spinner size="sm" /> : <Sparkles className="w-3.5 h-3.5 text-brand-400" />}
            Seed Tab Defaults
          </button>
          <button
            onClick={() => { refetch(); refetchStats() }}
            className="btn-secondary p-2.5"
          >
            <RefreshCw className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      </div>

      {/* Stats Board */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        {TABS.map(({ id, label, Icon, color }) => (
          <div key={id} className="card p-3 flex items-center gap-3">
            <div className={clsx('w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0', color)}>
              <Icon className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-bold text-white truncate">{stats?.[
                id === 'character_template' ? 'characters' :
                id === 'animation_preset' ? 'presets' :
                id === 'sound_effect' ? 'sound_effects' :
                id
              ] ?? 0}</p>
              <p className="text-[10px] text-gray-400 truncate">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Library Tabs */}
      <div className="flex border-b border-gray-800 overflow-x-auto gap-2">
        {TABS.map(({ id, label, Icon }) => (
          <button
            key={id}
            onClick={() => {
              setActiveTab(id)
              setPage(1)
              setSelectedIds([])
              setCategory('')
            }}
            className={clsx(
              'flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-all whitespace-nowrap',
              activeTab === id
                ? 'border-brand-500 text-brand-400 bg-brand-500/5'
                : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-700'
            )}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Search and Upload */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Upload Zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={clsx(
            'lg:col-span-1 border-2 border-dashed rounded-xl p-5 flex flex-col items-center justify-center gap-2 cursor-pointer transition-all hover:bg-gray-900/40',
            isDragging ? 'border-brand-500 bg-brand-900/10' : 'border-gray-800 bg-gray-900/20'
          )}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            className="hidden"
          />
          {isUploading ? (
            <>
              <Spinner size="lg" />
              <p className="text-xs text-gray-400">Uploading your asset to MinIO...</p>
            </>
          ) : (
            <>
              <Upload className="w-6 h-6 text-brand-400" />
              <p className="text-xs font-medium text-gray-200">Drag & drop files here, or click to upload</p>
              <p className="text-[10px] text-gray-500">Supports PNG, JPG, MP3, WAV up to 50MB</p>
            </>
          )}
          {uploadError && (
            <div className="flex items-center gap-1.5 text-red-400 text-[10px] mt-1">
              <AlertCircle className="w-3.5 h-3.5" />
              {uploadError}
            </div>
          )}
        </div>

        {/* Filters and Controls */}
        <div className="lg:col-span-2 card p-5 flex flex-col justify-between gap-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                className="input pl-9 w-full"
                placeholder={`Search ${activeTab.replace('_', ' ')}s...`}
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1) }}
              />
            </div>
            <input
              className="input sm:w-48"
              placeholder="Filter by category"
              value={category}
              onChange={(e) => { setCategory(e.target.value); setPage(1) }}
            />
          </div>

          <div className="flex items-center justify-between border-t border-gray-800 pt-3">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showDeleted}
                onChange={(e) => { setShowDeleted(e.target.checked); setPage(1); setSelectedIds([]) }}
                className="checkbox"
              />
              <span className="text-xs text-gray-400 flex items-center gap-1">
                <Trash2 className="w-3.5 h-3.5 text-gray-500" />
                Show soft-deleted items (Trash)
              </span>
            </label>

            {selectedIds.length > 0 && (
              <span className="text-xs text-brand-400 font-semibold">
                {selectedIds.length} item{selectedIds.length !== 1 ? 's' : ''} selected
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Bulk Action Toolbar */}
      {selectedIds.length > 0 && (
        <div className="bg-brand-950/40 border border-brand-900/50 rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 backdrop-blur-md animate-in fade-in slide-in-from-bottom-4 duration-300">
          <div className="flex items-center gap-3">
            <button
              onClick={toggleSelectAll}
              className="text-xs text-gray-300 hover:text-white flex items-center gap-1.5"
            >
              {selectedIds.length === items.length ? <CheckSquare className="w-4 h-4" /> : <Square className="w-4 h-4" />}
              Toggle Select All
            </button>
            <div className="h-4 w-px bg-brand-900" />
            <button
              onClick={() => {
                if (showDeleted) {
                  bulkRestoreMutation.mutate({ type: activeTab, ids: selectedIds })
                } else {
                  bulkDeleteMutation.mutate({ type: activeTab, ids: selectedIds })
                }
              }}
              className="btn-danger py-1.5 px-3 text-xs flex items-center gap-1.5"
            >
              {showDeleted ? <CornerUpLeft className="w-3.5 h-3.5" /> : <Trash2 className="w-3.5 h-3.5" />}
              {showDeleted ? 'Restore Selected' : 'Delete Selected'}
            </button>
            {!showDeleted && (
              <button
                onClick={() => setShowBulkEdit(!showBulkEdit)}
                className="btn-secondary py-1.5 px-3 text-xs"
              >
                Bulk Update Metadata
              </button>
            )}
          </div>

          {showBulkEdit && (
            <div className="flex items-center gap-2 flex-wrap bg-gray-900 p-2 rounded-lg border border-gray-800">
              <input
                className="input py-1 text-xs"
                placeholder="Bulk Category"
                value={bulkCategory}
                onChange={(e) => setBulkCategory(e.target.value)}
              />
              <input
                className="input py-1 text-xs"
                placeholder="Bulk Tags (comma separated)"
                value={bulkTags}
                onChange={(e) => setBulkTags(e.target.value)}
              />
              <button
                onClick={() => bulkUpdateMutation.mutate({
                  type: activeTab,
                  ids: selectedIds,
                  cat: bulkCategory || undefined,
                  tags: bulkTags ? bulkTags.split(',').map(x => x.trim()) : undefined
                })}
                className="btn-primary py-1 px-3 text-xs"
              >
                Apply
              </button>
            </div>
          )}
        </div>
      )}

      {/* Assets Grid */}
      {isLoading ? (
        <div className="flex justify-center items-center py-20">
          <Spinner size="lg" />
        </div>
      ) : items.length === 0 ? (
        <div className="card p-12 flex flex-col items-center justify-center text-center gap-3">
          <Database className="w-12 h-12 text-gray-600" />
          <p className="text-sm font-semibold text-gray-300">No assets found</p>
          <p className="text-xs text-gray-500">Try adjusting your filters or upload a new asset to get started.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {items.map((item) => {
            const isSelected = selectedIds.includes(item.id)
            const isAudio = activeTab.includes('audio') || activeTab === 'music' || activeTab === 'sound_effect'
            const isPlaying = playingAudioUrl === item.file_url

            return (
              <div
                key={item.id}
                className={clsx(
                  'card relative flex flex-col justify-between overflow-hidden hover:border-brand-600/40 transition-all duration-300 group',
                  isSelected && 'border-brand-500 bg-brand-950/10'
                )}
              >
                {/* Selection Checkbox */}
                <button
                  onClick={() => toggleSelect(item.id)}
                  className="absolute top-2.5 left-2.5 z-10 w-5 h-5 rounded border border-gray-700 bg-gray-950/80 flex items-center justify-center text-brand-400 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  {isSelected ? <CheckSquare className="w-4 h-4" /> : <Square className="w-4 h-4 text-gray-500" />}
                </button>

                {/* Card Thumbnail / Preview */}
                <div className="aspect-video bg-gray-900 relative overflow-hidden flex items-center justify-center">
                  {item.thumbnail_url ? (
                    <img
                      src={item.thumbnail_url}
                      alt={item.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : isAudio ? (
                    <div className="flex flex-col items-center justify-center gap-2">
                      <button
                        onClick={() => handlePlayAudio(item.file_url)}
                        className="w-10 h-10 rounded-full bg-brand-600 hover:bg-brand-500 text-white flex items-center justify-center transition-colors"
                      >
                        {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
                      </button>
                      <span className="text-[10px] text-gray-500">
                        {item.duration_seconds ? `${item.duration_seconds.toFixed(1)}s` : 'Audio'}
                      </span>
                    </div>
                  ) : (
                    <PersonStanding className="w-10 h-10 text-gray-600" />
                  )}
                  {item.category && (
                    <span className="absolute top-2 right-2 text-[10px] px-2 py-0.5 rounded-full bg-black/60 text-gray-300 backdrop-blur-sm">
                      {item.category}
                    </span>
                  )}
                </div>

                {/* Info & Metadata */}
                <div className="p-3.5 space-y-2">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-gray-200 truncate">{item.name}</p>
                    {item.name_local && (
                      <p className="text-xs text-gray-500 truncate">{item.name_local}</p>
                    )}
                  </div>

                  {item.tags && item.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {item.tags.slice(0, 3).map((tag: string) => (
                        <span key={tag} className="text-[10px] text-gray-500">#{tag}</span>
                      ))}
                    </div>
                  )}

                  {/* Actions Row */}
                  <div className="flex items-center justify-between border-t border-gray-800 pt-2 text-xs text-gray-400">
                    <div className="flex items-center gap-2">
                      {showDeleted ? (
                        <button
                          onClick={() => restoreMutation.mutate({ type: activeTab, id: item.id })}
                          className="text-green-400 hover:text-green-300 flex items-center gap-1 transition-colors"
                        >
                          <CornerUpLeft className="w-3.5 h-3.5" /> Restore
                        </button>
                      ) : (
                        <>
                          <button
                            onClick={() => setPreviewAsset(item)}
                            className="hover:text-white flex items-center gap-1 transition-colors"
                          >
                            <Eye className="w-3.5 h-3.5" /> Details
                          </button>
                          <button
                            onClick={() => setVersionAsset({ id: item.id, type: activeTab, name: item.name })}
                            className="hover:text-white flex items-center gap-1 transition-colors"
                          >
                            <History className="w-3.5 h-3.5 text-gray-500" /> History
                          </button>
                        </>
                      )}
                    </div>
                    {!showDeleted && (
                      <button
                        onClick={() => softDeleteMutation.mutate({ type: activeTab, id: item.id })}
                        className="text-red-500/80 hover:text-red-400 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 pt-6 border-t border-gray-900">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="btn-secondary p-2 disabled:opacity-50"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="text-xs text-gray-400">
            Page {page} of {totalPages} ({total} total assets)
          </span>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="btn-secondary p-2 disabled:opacity-50"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Version Control Slider Modal */}
      {versionAsset && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in duration-250">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 max-w-lg w-full flex flex-col gap-4 shadow-2xl">
            <div className="flex justify-between items-center pb-3 border-b border-gray-800">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <History className="w-5 h-5 text-brand-400" />
                Version History: {versionAsset.name}
              </h3>
              <button onClick={() => setVersionAsset(null)} className="text-gray-500 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* List Versions */}
            <div className="space-y-3 max-h-60 overflow-y-auto pr-1">
              {versionsData?.items && versionsData.items.length > 0 ? (
                versionsData.items.map((v: any) => (
                  <div key={v.id} className="bg-gray-950 p-3 rounded-lg border border-gray-800 flex items-center justify-between gap-4">
                    <div>
                      <p className="text-xs font-semibold text-brand-400">Version #{v.version_number}</p>
                      <p className="text-xs text-gray-300 mt-1">{v.change_summary || 'No summary provided'}</p>
                      <p className="text-[10px] text-gray-500 mt-0.5">{new Date(v.created_at).toLocaleString()}</p>
                    </div>
                    <button
                      onClick={() => restoreVersionMutation.mutate({ type: versionAsset.type, id: versionAsset.id, version: v.version_number })}
                      className="btn-secondary py-1 px-2.5 text-[10px] flex items-center gap-1"
                    >
                      <CornerUpLeft className="w-3 h-3" /> Restore
                    </button>
                  </div>
                ))
              ) : (
                <p className="text-xs text-gray-500 text-center py-4">No version snapshots found for this asset.</p>
              )}
            </div>

            {/* Create Snapshot Form */}
            <div className="border-t border-gray-800 pt-4 flex flex-col gap-2.5">
              <p className="text-xs font-semibold text-gray-300">Create New Version Snapshot</p>
              <textarea
                className="input min-h-16 text-xs"
                placeholder="Describe what changed in this version..."
                value={versionNotes}
                onChange={(e) => setVersionNotes(e.target.value)}
              />
              <button
                onClick={() => createVersionMutation.mutate({
                  type: versionAsset.type,
                  id: versionAsset.id,
                  snapshot: {},
                  summary: versionNotes
                })}
                disabled={!versionNotes}
                className="btn-primary py-2 text-xs w-full"
              >
                Save Snapshot
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Details / Preview Modal */}
      {previewAsset && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in duration-250">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 max-w-2xl w-full flex flex-col gap-4 shadow-2xl">
            <div className="flex justify-between items-center pb-3 border-b border-gray-800">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                Asset Specifications
              </h3>
              <button onClick={() => setPreviewAsset(null)} className="text-gray-500 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-950 aspect-video rounded-xl border border-gray-800 overflow-hidden flex items-center justify-center">
                {previewAsset.thumbnail_url ? (
                  <img src={previewAsset.thumbnail_url} alt={previewAsset.name} className="w-full h-full object-contain" />
                ) : (
                  <div className="text-center p-4">
                    <Volume2 className="w-10 h-10 text-brand-400 mx-auto mb-2" />
                    <p className="text-xs text-gray-400">{previewAsset.name}</p>
                  </div>
                )}
              </div>
              <div className="space-y-3">
                <div>
                  <label className="text-[10px] uppercase font-semibold tracking-wider text-gray-500">Asset ID</label>
                  <p className="text-xs font-mono text-gray-300">{previewAsset.id}</p>
                </div>
                {previewAsset.category && (
                  <div>
                    <label className="text-[10px] uppercase font-semibold tracking-wider text-gray-500">Category</label>
                    <p className="text-xs text-gray-300">{previewAsset.category}</p>
                  </div>
                )}
                {previewAsset.file_url && (
                  <div>
                    <label className="text-[10px] uppercase font-semibold tracking-wider text-gray-500">File Url</label>
                    <a
                      href={previewAsset.file_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-brand-400 hover:underline block truncate"
                    >
                      {previewAsset.file_url}
                    </a>
                  </div>
                )}
                <div>
                  <label className="text-[10px] uppercase font-semibold tracking-wider text-gray-500">Custom Metadata</label>
                  <pre className="bg-gray-950 p-2.5 rounded-lg border border-gray-800 text-[10px] text-gray-400 max-h-36 overflow-y-auto">
                    {JSON.stringify(previewAsset.metadata || {}, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Hidden audio element for preview players */}
      <audio ref={audioPlayerRef} onEnded={() => setPlayingAudioUrl(null)} className="hidden" />
    </div>
  )
}
