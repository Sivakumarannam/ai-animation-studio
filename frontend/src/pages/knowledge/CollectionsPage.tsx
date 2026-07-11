import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ChevronRight, Library, Plus, Trash2, FileText, Layers, Pencil } from 'lucide-react'
import { knowledgeApi } from '@/api/knowledge'
import type { KnowledgeCollection } from '@/api/knowledge'
import { Spinner } from '@/components/ui/Spinner'
import { Modal } from '@/components/ui/Modal'

export function CollectionsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [collectionType, setCollectionType] = useState('general')
  const [page, setPage] = useState(1)

  // Edit state
  const [showEdit, setShowEdit] = useState(false)
  const [editCollection, setEditCollection] = useState<KnowledgeCollection | null>(null)
  const [editName, setEditName] = useState('')
  const [editDescription, setEditDescription] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['kn-collections', projectId, page],
    queryFn: () => knowledgeApi.listCollections(projectId!, page),
    enabled: !!projectId,
  })

  const createMutation = useMutation({
    mutationFn: () => knowledgeApi.createCollection(projectId!, { name, description, collection_type: collectionType }),
    onSuccess: () => {
      setShowCreate(false)
      setName('')
      setDescription('')
      qc.invalidateQueries({ queryKey: ['kn-collections', projectId] })
      qc.invalidateQueries({ queryKey: ['kn-stats', projectId] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => knowledgeApi.deleteCollection(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['kn-collections', projectId] })
      qc.invalidateQueries({ queryKey: ['kn-stats', projectId] })
    },
  })

  const editMutation = useMutation({
    mutationFn: () => knowledgeApi.updateCollection(editCollection!.id, { name: editName, description: editDescription }),
    onSuccess: () => {
      setShowEdit(false)
      setEditCollection(null)
      qc.invalidateQueries({ queryKey: ['kn-collections', projectId] })
    },
  })

  function openEdit(c: KnowledgeCollection, e: React.MouseEvent) {
    e.preventDefault()
    setEditCollection(c)
    setEditName(c.name)
    setEditDescription(c.description ?? '')
    setShowEdit(true)
  }

  const collections = data?.items ?? []
  const meta = data?.meta

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/projects" className="hover:text-gray-300">Projects</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}`} className="hover:text-gray-300">Project</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}/knowledge`} className="hover:text-gray-300">Knowledge</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300">Collections</span>
      </div>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Knowledge Collections</h1>
          <p className="text-gray-400 text-sm mt-1">Organize documents into searchable knowledge bases</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <Plus className="w-4 h-4" /> New Collection
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : collections.length === 0 ? (
        <div className="card p-12 text-center">
          <Library className="w-12 h-12 text-gray-600 mx-auto mb-3" />
          <p className="text-gray-400 font-medium">No collections yet</p>
          <p className="text-gray-600 text-sm mt-1 mb-4">Create your first knowledge collection to start adding documents.</p>
          <button onClick={() => setShowCreate(true)} className="btn-primary">
            <Plus className="w-4 h-4" /> New Collection
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {collections.map((c) => (
            <div key={c.id} className="card p-5 flex flex-col gap-3">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <Link
                    to={`/projects/${projectId}/knowledge/collections/${c.id}`}
                    className="text-sm font-semibold text-gray-100 hover:text-white truncate block"
                  >
                    {c.name}
                  </Link>
                  {c.description && (
                    <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{c.description}</p>
                  )}
                </div>
                <div className="flex items-center gap-1 ml-2 flex-shrink-0">
                  <button
                    onClick={(e) => openEdit(c, e)}
                    className="text-gray-600 hover:text-gray-300 p-1"
                    title="Edit"
                  >
                    <Pencil className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => { if (confirm(`Delete "${c.name}"?`)) deleteMutation.mutate(c.id) }}
                    className="text-gray-600 hover:text-red-400 p-1"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <FileText className="w-3.5 h-3.5" /> {c.document_count} docs
                </span>
                <span className="flex items-center gap-1">
                  <Layers className="w-3.5 h-3.5" /> {c.chunk_count} chunks
                </span>
                <span className={`ml-auto capitalize px-1.5 py-0.5 rounded text-xs font-medium ${
                  c.status === 'ready' ? 'bg-green-900/40 text-green-400' :
                  c.status === 'indexing' ? 'bg-yellow-900/40 text-yellow-400' :
                  'bg-gray-800 text-gray-400'
                }`}>{c.status}</span>
              </div>

              <div className="flex items-center gap-2 pt-1 border-t border-gray-800">
                <span className="text-xs text-gray-600 capitalize">{c.collection_type}</span>
                <Link
                  to={`/projects/${projectId}/knowledge/collections/${c.id}`}
                  className="ml-auto text-xs text-brand-400 hover:text-brand-300"
                >
                  View documents →
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {meta && meta.total_pages > 1 && (
        <div className="flex items-center justify-center gap-3 mt-6">
          <button className="btn-secondary text-xs" disabled={page <= 1} onClick={() => setPage(page - 1)}>← Prev</button>
          <span className="text-xs text-gray-500">Page {meta.page} of {meta.total_pages}</span>
          <button className="btn-secondary text-xs" disabled={page >= meta.total_pages} onClick={() => setPage(page + 1)}>Next →</button>
        </div>
      )}

      <Modal title="New Knowledge Collection" open={showCreate} onClose={() => setShowCreate(false)}>
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate() }} className="space-y-4">
          <div>
            <label className="label">Name *</label>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g. Character Backstories" />
          </div>
          <div>
            <label className="label">Description</label>
            <textarea className="input resize-none" rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div>
            <label className="label">Type</label>
            <select className="input" value={collectionType} onChange={(e) => setCollectionType(e.target.value)}>
              <option value="general">General</option>
              <option value="character">Character</option>
              <option value="world">World</option>
              <option value="lore">Lore</option>
              <option value="script">Script</option>
            </select>
          </div>
          {createMutation.isError && (
            <p className="text-xs text-red-400">Failed to create collection.</p>
          )}
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending || !name.trim()}>
              {createMutation.isPending ? <Spinner size="sm" /> : 'Create'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
