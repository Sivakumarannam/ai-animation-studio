import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ImageIcon, Search, Sparkles, Plus, Pencil, Trash2 } from 'lucide-react'
import { libraryApi, type Background } from '@/api/library'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Modal } from '@/components/ui/Modal'

const CATEGORY_ICONS: Record<string, string> = {
  indoor: '🏠', outdoor: '🌳', educational: '🏫', medical: '🏥',
  commercial: '🏪', workplace: '💼', religious: '🛕',
}

function BackgroundCard({
  bg,
  onEdit,
  onDelete,
}: {
  bg: Background
  onEdit: (bg: Background) => void
  onDelete: (bg: Background) => void
}) {
  return (
    <div className="card overflow-hidden hover:border-brand-600/40 transition-colors group">
      <div className="aspect-video bg-gray-800 relative overflow-hidden">
        {bg.thumbnail_url ? (
          <img
            src={bg.thumbnail_url}
            alt={bg.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center gap-2">
            <span className="text-3xl">{CATEGORY_ICONS[bg.category] ?? '🖼️'}</span>
            <span className="text-xs text-gray-500">{bg.name}</span>
          </div>
        )}
        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
          <button
            onClick={() => onEdit(bg)}
            className="p-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200"
          >
            <Pencil className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => onDelete(bg)}
            className="p-1.5 rounded-lg bg-red-900/80 hover:bg-red-800 text-red-200"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
        {bg.category && (
          <div className="absolute top-2 left-2">
            <span className="text-xs px-2 py-0.5 rounded-full bg-black/60 text-gray-200 backdrop-blur-sm">
              {CATEGORY_ICONS[bg.category]} {bg.category}
            </span>
          </div>
        )}
      </div>
      <div className="p-3">
        <p className="text-sm font-medium text-gray-100 truncate">{bg.name}</p>
        {bg.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1.5">
            {bg.tags.slice(0, 3).map((tag) => (
              <span key={tag} className="text-xs text-gray-500">#{tag}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export function BackgroundLibraryPage() {
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const qc = useQueryClient()

  // Create
  const [showCreate, setShowCreate] = useState(false)
  const [createName, setCreateName] = useState('')
  const [createCategory, setCreateCategory] = useState('indoor')
  const [createThumbnail, setCreateThumbnail] = useState('')
  const [createTags, setCreateTags] = useState('')

  // Edit
  const [showEdit, setShowEdit] = useState(false)
  const [editBg, setEditBg] = useState<Background | null>(null)
  const [editName, setEditName] = useState('')
  const [editCategory, setEditCategory] = useState('')
  const [editThumbnail, setEditThumbnail] = useState('')
  const [editTags, setEditTags] = useState('')

  // Delete
  const [showDelete, setShowDelete] = useState(false)
  const [bgToDelete, setBgToDelete] = useState<Background | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['backgrounds', search, category],
    queryFn: () => libraryApi.getBackgrounds({
      search: search || undefined,
      category: category || undefined,
      page_size: 48,
    }),
  })

  const { data: categories } = useQuery({
    queryKey: ['bg-categories'],
    queryFn: libraryApi.getBgCategories,
  })

  const seedMutation = useMutation({
    mutationFn: libraryApi.seedBackgrounds,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['backgrounds'] }),
  })

  const createMutation = useMutation({
    mutationFn: () => libraryApi.createBackground({
      name: createName,
      category: createCategory,
      thumbnail_url: createThumbnail || undefined,
      tags: createTags ? createTags.split(',').map(t => t.trim()).filter(Boolean) : [],
    } as Partial<Background>),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['backgrounds'] })
      setShowCreate(false)
      setCreateName(''); setCreateThumbnail(''); setCreateTags('')
    },
  })

  const editMutation = useMutation({
    mutationFn: () => libraryApi.updateBackground(editBg!.id, {
      name: editName,
      category: editCategory,
      thumbnail_url: editThumbnail || undefined,
      tags: editTags ? editTags.split(',').map(t => t.trim()).filter(Boolean) : [],
    } as Partial<Background>),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['backgrounds'] })
      setShowEdit(false); setEditBg(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => libraryApi.deleteBackground(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['backgrounds'] })
      setShowDelete(false); setBgToDelete(null)
    },
  })

  function openEdit(bg: Background) {
    setEditBg(bg)
    setEditName(bg.name)
    setEditCategory(bg.category)
    setEditThumbnail(bg.thumbnail_url ?? '')
    setEditTags(bg.tags.join(', '))
    setShowEdit(true)
  }

  const backgrounds = data?.items ?? []

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <ImageIcon className="w-6 h-6 text-brand-400" />
            Background Library
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Reusable scene backgrounds — villages, homes, schools, markets and more
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => seedMutation.mutate()}
            disabled={seedMutation.isPending}
            className="btn-secondary flex items-center gap-2"
          >
            {seedMutation.isPending ? <Spinner size="sm" /> : <Sparkles className="w-4 h-4" />}
            Seed Defaults
          </button>
          <button onClick={() => setShowCreate(true)} className="btn-primary">
            <Plus className="w-4 h-4" /> Add Background
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4 flex-wrap">
        <div className="relative flex-1 min-w-48 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            className="input pl-9"
            placeholder="Search backgrounds..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setCategory('')}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
              category === '' ? 'bg-brand-600 border-brand-500 text-white' : 'border-gray-700 text-gray-400 hover:border-gray-500'
            }`}
          >
            All
          </button>
          {(categories ?? []).map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat === category ? '' : cat)}
              className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                category === cat ? 'bg-brand-600 border-brand-500 text-white' : 'border-gray-700 text-gray-400 hover:border-gray-500'
              }`}
            >
              {CATEGORY_ICONS[cat]} {cat}
            </button>
          ))}
        </div>
      </div>

      {data && (
        <p className="text-xs text-gray-500 mb-4">{data.total} background{data.total !== 1 ? 's' : ''}</p>
      )}

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : backgrounds.length === 0 ? (
        <EmptyState
          icon={ImageIcon}
          title="No backgrounds yet"
          description="Seed the default background library or add one manually."
          action={
            <div className="flex gap-2">
              <button onClick={() => seedMutation.mutate()} className="btn-secondary">
                <Sparkles className="w-4 h-4" /> Seed Backgrounds
              </button>
              <button onClick={() => setShowCreate(true)} className="btn-primary">
                <Plus className="w-4 h-4" /> Add Background
              </button>
            </div>
          }
        />
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {backgrounds.map((bg) => (
            <BackgroundCard key={bg.id} bg={bg} onEdit={openEdit} onDelete={(b) => { setBgToDelete(b); setShowDelete(true) }} />
          ))}
        </div>
      )}

      {/* Create */}
      <Modal title="Add Background" open={showCreate} onClose={() => setShowCreate(false)}>
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate() }} className="space-y-4">
          <div>
            <label className="label">Name</label>
            <input className="input" value={createName} onChange={(e) => setCreateName(e.target.value)} required />
          </div>
          <div>
            <label className="label">Category</label>
            <input className="input" value={createCategory} onChange={(e) => setCreateCategory(e.target.value)} />
          </div>
          <div>
            <label className="label">Thumbnail URL</label>
            <input className="input" placeholder="https://..." value={createThumbnail} onChange={(e) => setCreateThumbnail(e.target.value)} />
          </div>
          <div>
            <label className="label">Tags (comma-separated)</label>
            <input className="input" placeholder="nature, green, forest" value={createTags} onChange={(e) => setCreateTags(e.target.value)} />
          </div>
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? <Spinner size="sm" /> : 'Add Background'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit */}
      <Modal title="Edit Background" open={showEdit} onClose={() => setShowEdit(false)}>
        <form onSubmit={(e) => { e.preventDefault(); editMutation.mutate() }} className="space-y-4">
          <div>
            <label className="label">Name</label>
            <input className="input" value={editName} onChange={(e) => setEditName(e.target.value)} required />
          </div>
          <div>
            <label className="label">Category</label>
            <input className="input" value={editCategory} onChange={(e) => setEditCategory(e.target.value)} />
          </div>
          <div>
            <label className="label">Thumbnail URL</label>
            <input className="input" value={editThumbnail} onChange={(e) => setEditThumbnail(e.target.value)} />
          </div>
          <div>
            <label className="label">Tags (comma-separated)</label>
            <input className="input" value={editTags} onChange={(e) => setEditTags(e.target.value)} />
          </div>
          {editMutation.isError && <p className="text-xs text-red-400">Failed to save changes.</p>}
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowEdit(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={editMutation.isPending}>
              {editMutation.isPending ? <Spinner size="sm" /> : 'Save Changes'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete */}
      <Modal title="Delete Background" open={showDelete} onClose={() => setShowDelete(false)}>
        <div className="space-y-4">
          <p className="text-sm text-gray-300">
            Delete <strong className="text-white">{bgToDelete?.name}</strong>? This cannot be undone.
          </p>
          {deleteMutation.isError && <p className="text-xs text-red-400">Failed to delete background.</p>}
          <div className="flex gap-3 justify-end pt-2">
            <button className="btn-secondary" onClick={() => setShowDelete(false)}>Cancel</button>
            <button className="btn-danger" disabled={deleteMutation.isPending} onClick={() => bgToDelete && deleteMutation.mutate(bgToDelete.id)}>
              {deleteMutation.isPending ? <Spinner size="sm" /> : 'Delete'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
