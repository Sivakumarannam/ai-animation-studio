import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Globe2, ChevronRight, Pencil, Trash2 } from 'lucide-react'
import { storyIntelligenceApi } from '@/api/storyIntelligence'
import type { World } from '@/types'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Modal } from '@/components/ui/Modal'

export function WorldsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const qc = useQueryClient()

  // Create
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [lore, setLore] = useState('')

  // Edit
  const [showEdit, setShowEdit] = useState(false)
  const [editWorld, setEditWorld] = useState<World | null>(null)
  const [editName, setEditName] = useState('')
  const [editDescription, setEditDescription] = useState('')
  const [editLore, setEditLore] = useState('')

  // Delete
  const [showDelete, setShowDelete] = useState(false)
  const [worldToDelete, setWorldToDelete] = useState<World | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['si-worlds', projectId],
    queryFn: () => storyIntelligenceApi.listWorlds(projectId!),
    enabled: !!projectId,
  })

  const createMutation = useMutation({
    mutationFn: () => storyIntelligenceApi.createWorld(projectId!, { name, description, lore }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['si-worlds', projectId] })
      setShowCreate(false)
      setName(''); setDescription(''); setLore('')
    },
  })

  const editMutation = useMutation({
    mutationFn: () => storyIntelligenceApi.updateWorld(editWorld!.id, { name: editName, description: editDescription, lore: editLore }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['si-worlds', projectId] })
      setShowEdit(false)
      setEditWorld(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => storyIntelligenceApi.deleteWorld(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['si-worlds', projectId] })
      setShowDelete(false)
      setWorldToDelete(null)
    },
  })

  function openEdit(world: World, e: React.MouseEvent) {
    e.preventDefault()
    setEditWorld(world)
    setEditName(world.name)
    setEditDescription(world.description ?? '')
    setEditLore((world as any).lore ?? '')
    setShowEdit(true)
  }

  function openDelete(world: World, e: React.MouseEvent) {
    e.preventDefault()
    setWorldToDelete(world)
    setShowDelete(true)
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/projects" className="hover:text-gray-300">Projects</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}`} className="hover:text-gray-300">Project</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}/intelligence`} className="hover:text-gray-300">Story Intelligence</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300">Worlds</span>
      </div>

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">World Builder</h1>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <Plus className="w-4 h-4" /> New World
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : data?.items.length === 0 ? (
        <EmptyState
          icon={Globe2}
          title="No worlds yet"
          description="Create a world to define the setting, lore, and rules for your stories."
          action={<button onClick={() => setShowCreate(true)} className="btn-primary"><Plus className="w-4 h-4" />Create World</button>}
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {data?.items.map((world) => (
            <div key={world.id} className="card p-4 relative group">
              <Link to={`/projects/${projectId}/intelligence/worlds/${world.id}`} className="block">
                <div className="w-12 h-12 bg-blue-900/30 rounded-xl flex items-center justify-center mb-3">
                  <Globe2 className="w-6 h-6 text-blue-400" />
                </div>
                <p className="text-sm font-semibold text-gray-100 mb-0.5">{world.name}</p>
                <p className="text-xs text-gray-500 mb-2 line-clamp-2">{world.description || 'No description'}</p>
                <span className="badge-gray">{world.status}</span>
              </Link>
              <div className="flex gap-2 mt-3 pt-3 border-t border-gray-800">
                <button
                  onClick={(e) => openEdit(world, e)}
                  className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200 transition-colors"
                >
                  <Pencil className="w-3 h-3" /> Edit
                </button>
                <button
                  onClick={(e) => openDelete(world, e)}
                  className="flex items-center gap-1 text-xs text-red-500 hover:text-red-400 transition-colors ml-auto"
                >
                  <Trash2 className="w-3 h-3" /> Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal title="New World" open={showCreate} onClose={() => setShowCreate(false)}>
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate() }} className="space-y-4">
          <div>
            <label className="label">Name</label>
            <input className="input" placeholder="World name" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div>
            <label className="label">Description</label>
            <textarea className="input resize-none" rows={2} placeholder="What is this world about?" value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div>
            <label className="label">Lore</label>
            <textarea className="input resize-none" rows={3} placeholder="Backstory, history, mythology..." value={lore} onChange={(e) => setLore(e.target.value)} />
          </div>
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? <Spinner size="sm" /> : 'Create World'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Modal */}
      <Modal title="Edit World" open={showEdit} onClose={() => setShowEdit(false)}>
        <form onSubmit={(e) => { e.preventDefault(); editMutation.mutate() }} className="space-y-4">
          <div>
            <label className="label">Name</label>
            <input className="input" value={editName} onChange={(e) => setEditName(e.target.value)} required />
          </div>
          <div>
            <label className="label">Description</label>
            <textarea className="input resize-none" rows={2} value={editDescription} onChange={(e) => setEditDescription(e.target.value)} />
          </div>
          <div>
            <label className="label">Lore</label>
            <textarea className="input resize-none" rows={3} value={editLore} onChange={(e) => setEditLore(e.target.value)} />
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

      {/* Delete Confirmation */}
      <Modal title="Delete World" open={showDelete} onClose={() => setShowDelete(false)}>
        <div className="space-y-4">
          <p className="text-sm text-gray-300">
            Are you sure you want to delete <strong className="text-white">{worldToDelete?.name}</strong>? All seasons, episodes, and story memory will be removed. This cannot be undone.
          </p>
          {deleteMutation.isError && <p className="text-xs text-red-400">Failed to delete world.</p>}
          <div className="flex gap-3 justify-end pt-2">
            <button className="btn-secondary" onClick={() => setShowDelete(false)}>Cancel</button>
            <button
              className="btn-danger"
              disabled={deleteMutation.isPending}
              onClick={() => worldToDelete && deleteMutation.mutate(worldToDelete.id)}
            >
              {deleteMutation.isPending ? <Spinner size="sm" /> : 'Delete World'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
