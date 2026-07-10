import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Package, Search, Sparkles, Plus, Pencil, Trash2 } from 'lucide-react'
import { libraryApi, type Prop } from '@/api/library'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Modal } from '@/components/ui/Modal'

const CATEGORY_META: Record<string, { icon: string; color: string }> = {
  furniture:   { icon: '🛋️', color: 'bg-amber-900/20 text-amber-300 border-amber-800/40' },
  vehicles:    { icon: '🚗', color: 'bg-blue-900/20 text-blue-300 border-blue-800/40' },
  kitchen:     { icon: '🍳', color: 'bg-orange-900/20 text-orange-300 border-orange-800/40' },
  school:      { icon: '📚', color: 'bg-green-900/20 text-green-300 border-green-800/40' },
  electronics: { icon: '💻', color: 'bg-cyan-900/20 text-cyan-300 border-cyan-800/40' },
  food:        { icon: '🍚', color: 'bg-yellow-900/20 text-yellow-300 border-yellow-800/40' },
  money:       { icon: '💰', color: 'bg-emerald-900/20 text-emerald-300 border-emerald-800/40' },
  nature:      { icon: '🌿', color: 'bg-lime-900/20 text-lime-300 border-lime-800/40' },
  medical:     { icon: '🏥', color: 'bg-red-900/20 text-red-300 border-red-800/40' },
  office:      { icon: '💼', color: 'bg-gray-900/20 text-gray-300 border-gray-700' },
}

function PropCard({
  prop,
  onEdit,
  onDelete,
}: {
  prop: Prop
  onEdit: (prop: Prop) => void
  onDelete: (prop: Prop) => void
}) {
  const meta = CATEGORY_META[prop.category] ?? { icon: '📦', color: 'bg-gray-800 text-gray-300 border-gray-700' }

  return (
    <div
      className="card p-3 border hover:border-brand-600/40 transition-colors group cursor-grab active:cursor-grabbing relative"
      draggable
      onDragStart={(e) => {
        e.dataTransfer.setData('application/json', JSON.stringify({
          type: 'prop', id: prop.id, name: prop.name,
          category: prop.category, file_url: prop.file_url, thumbnail_url: prop.thumbnail_url,
        }))
      }}
    >
      {/* Action buttons overlay */}
      <div className="absolute top-1 right-1 z-10 opacity-0 group-hover:opacity-100 flex gap-1 transition-opacity">
        <button
          onClick={(e) => { e.stopPropagation(); onEdit(prop) }}
          className="p-1 rounded bg-gray-800/90 hover:bg-gray-700 text-gray-200"
        >
          <Pencil className="w-3 h-3" />
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(prop) }}
          className="p-1 rounded bg-red-900/80 hover:bg-red-800 text-red-200"
        >
          <Trash2 className="w-3 h-3" />
        </button>
      </div>
      <div className="aspect-square rounded-lg bg-gray-800 mb-2 flex items-center justify-center overflow-hidden">
        {prop.thumbnail_url ? (
          <img src={prop.thumbnail_url} alt={prop.name} className="w-full h-full object-contain" />
        ) : (
          <span className="text-3xl">{meta.icon}</span>
        )}
      </div>
      <p className="text-xs font-medium text-gray-200 text-center truncate">{prop.name}</p>
      <div className="flex justify-center mt-1">
        <span className={`text-xs px-2 py-0.5 rounded-full border ${meta.color}`}>
          {meta.icon} {prop.category}
        </span>
      </div>
    </div>
  )
}

export function PropsLibraryPage() {
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const qc = useQueryClient()

  // Create
  const [showCreate, setShowCreate] = useState(false)
  const [createName, setCreateName] = useState('')
  const [createCategory, setCreateCategory] = useState('furniture')
  const [createThumbnail, setCreateThumbnail] = useState('')
  const [createTags, setCreateTags] = useState('')

  // Edit
  const [showEdit, setShowEdit] = useState(false)
  const [editProp, setEditProp] = useState<Prop | null>(null)
  const [editName, setEditName] = useState('')
  const [editCategory, setEditCategory] = useState('')
  const [editThumbnail, setEditThumbnail] = useState('')
  const [editTags, setEditTags] = useState('')

  // Delete
  const [showDelete, setShowDelete] = useState(false)
  const [propToDelete, setPropToDelete] = useState<Prop | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['props', search, category],
    queryFn: () => libraryApi.getProps({
      search: search || undefined,
      category: category || undefined,
      page_size: 60,
    }),
  })

  const { data: categories } = useQuery({
    queryKey: ['prop-categories'],
    queryFn: libraryApi.getPropCategories,
  })

  const seedMutation = useMutation({
    mutationFn: libraryApi.seedProps,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['props'] }),
  })

  const createMutation = useMutation({
    mutationFn: () => libraryApi.createProp({
      name: createName,
      category: createCategory,
      thumbnail_url: createThumbnail || undefined,
      tags: createTags ? createTags.split(',').map(t => t.trim()).filter(Boolean) : [],
    } as Partial<Prop>),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['props'] })
      setShowCreate(false)
      setCreateName(''); setCreateThumbnail(''); setCreateTags('')
    },
  })

  const editMutation = useMutation({
    mutationFn: () => libraryApi.updateProp(editProp!.id, {
      name: editName,
      category: editCategory,
      thumbnail_url: editThumbnail || undefined,
      tags: editTags ? editTags.split(',').map(t => t.trim()).filter(Boolean) : [],
    } as Partial<Prop>),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['props'] })
      setShowEdit(false); setEditProp(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => libraryApi.deleteProp(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['props'] })
      setShowDelete(false); setPropToDelete(null)
    },
  })

  function openEdit(prop: Prop) {
    setEditProp(prop)
    setEditName(prop.name)
    setEditCategory(prop.category)
    setEditThumbnail(prop.thumbnail_url ?? '')
    setEditTags(prop.tags.join(', '))
    setShowEdit(true)
  }

  const props = data?.items ?? []

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Package className="w-6 h-6 text-brand-400" />
            Props Library
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Drag and drop props into your scene — furniture, vehicles, food, electronics and more
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
            <Plus className="w-4 h-4" /> Add Prop
          </button>
        </div>
      </div>

      <div className="flex gap-3 mb-4 flex-wrap">
        <div className="relative flex-1 min-w-48 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            className="input pl-9"
            placeholder="Search props..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setCategory('')}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
              !category ? 'bg-brand-600 border-brand-500 text-white' : 'border-gray-700 text-gray-400 hover:border-gray-500'
            }`}
          >
            All
          </button>
          {(categories ?? []).map((cat) => {
            const m = CATEGORY_META[cat]
            return (
              <button
                key={cat}
                onClick={() => setCategory(cat === category ? '' : cat)}
                className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                  category === cat ? 'bg-brand-600 border-brand-500 text-white' : 'border-gray-700 text-gray-400 hover:border-gray-500'
                }`}
              >
                {m?.icon} {cat}
              </button>
            )
          })}
        </div>
      </div>

      {data && (
        <p className="text-xs text-gray-500 mb-4">{data.total} prop{data.total !== 1 ? 's' : ''} · Drag to place in scene editor</p>
      )}

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : props.length === 0 ? (
        <EmptyState
          icon={Package}
          title="No props yet"
          description="Seed the default props library or add one manually."
          action={
            <div className="flex gap-2">
              <button onClick={() => seedMutation.mutate()} className="btn-secondary">
                <Sparkles className="w-4 h-4" /> Seed Props
              </button>
              <button onClick={() => setShowCreate(true)} className="btn-primary">
                <Plus className="w-4 h-4" /> Add Prop
              </button>
            </div>
          }
        />
      ) : (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-8 gap-3">
          {props.map((prop) => (
            <PropCard
              key={prop.id}
              prop={prop}
              onEdit={openEdit}
              onDelete={(p) => { setPropToDelete(p); setShowDelete(true) }}
            />
          ))}
        </div>
      )}

      {/* Create */}
      <Modal title="Add Prop" open={showCreate} onClose={() => setShowCreate(false)}>
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
            <input className="input" placeholder="wood, antique, rustic" value={createTags} onChange={(e) => setCreateTags(e.target.value)} />
          </div>
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? <Spinner size="sm" /> : 'Add Prop'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit */}
      <Modal title="Edit Prop" open={showEdit} onClose={() => setShowEdit(false)}>
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
      <Modal title="Delete Prop" open={showDelete} onClose={() => setShowDelete(false)}>
        <div className="space-y-4">
          <p className="text-sm text-gray-300">
            Delete <strong className="text-white">{propToDelete?.name}</strong>? This cannot be undone.
          </p>
          {deleteMutation.isError && <p className="text-xs text-red-400">Failed to delete prop.</p>}
          <div className="flex gap-3 justify-end pt-2">
            <button className="btn-secondary" onClick={() => setShowDelete(false)}>Cancel</button>
            <button className="btn-danger" disabled={deleteMutation.isPending} onClick={() => propToDelete && deleteMutation.mutate(propToDelete.id)}>
              {deleteMutation.isPending ? <Spinner size="sm" /> : 'Delete'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
