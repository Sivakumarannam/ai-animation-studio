import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Globe2, ChevronRight } from 'lucide-react'
import { storyIntelligenceApi } from '@/api/storyIntelligence'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Modal } from '@/components/ui/Modal'

export function WorldsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [lore, setLore] = useState('')

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
      setName('')
      setDescription('')
      setLore('')
    },
  })

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
            <Link key={world.id} to={`/projects/${projectId}/intelligence/worlds/${world.id}`} className="card p-4 hover:border-gray-700 transition-colors">
              <div className="w-12 h-12 bg-blue-900/30 rounded-xl flex items-center justify-center mb-3">
                <Globe2 className="w-6 h-6 text-blue-400" />
              </div>
              <p className="text-sm font-semibold text-gray-100 mb-0.5">{world.name}</p>
              <p className="text-xs text-gray-500 mb-2 line-clamp-2">{world.description || 'No description'}</p>
              <span className="badge-gray">{world.status}</span>
            </Link>
          ))}
        </div>
      )}

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
    </div>
  )
}
