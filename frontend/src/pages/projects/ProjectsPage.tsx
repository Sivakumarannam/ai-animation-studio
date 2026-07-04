import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Plus, Film, FolderKanban, Trash2 } from 'lucide-react'
import { projectsApi } from '@/api/projects'
import { pluginsApi } from '@/api/plugins'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Modal } from '@/components/ui/Modal'

export function ProjectsPage() {
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [pluginId, setPluginId] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(),
  })

  const { data: plugins } = useQuery({
    queryKey: ['plugins'],
    queryFn: pluginsApi.list,
  })

  const createMutation = useMutation({
    mutationFn: () => projectsApi.create({ title, description, plugin_id: pluginId }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['projects'] })
      setShowCreate(false)
      setTitle('')
      setDescription('')
      setPluginId('')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => projectsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  })

  const statusBadge = (s: string) => {
    const map: Record<string, string> = { draft: 'badge-gray', active: 'badge-green', archived: 'badge-yellow' }
    return map[s] || 'badge-gray'
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Projects</h1>
          <p className="text-gray-400 text-sm mt-1">{data?.total ?? 0} projects total</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <Plus className="w-4 h-4" /> New Project
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : data?.items.length === 0 ? (
        <EmptyState
          icon={FolderKanban}
          title="No projects yet"
          description="Create your first animation project to get started."
          action={
            <button onClick={() => setShowCreate(true)} className="btn-primary">
              <Plus className="w-4 h-4" /> Create Project
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data?.items.map((project) => (
            <div key={project.id} className="card p-5 hover:border-gray-700 transition-colors group">
              <div className="flex items-start justify-between mb-3">
                <div className="w-10 h-10 bg-brand-900/50 rounded-lg flex items-center justify-center">
                  <Film className="w-5 h-5 text-brand-400" />
                </div>
                <span className={statusBadge(project.status)}>{project.status}</span>
              </div>
              <Link to={`/projects/${project.id}`}>
                <h3 className="text-sm font-semibold text-gray-100 mb-1 hover:text-brand-400 transition-colors line-clamp-1">
                  {project.title}
                </h3>
              </Link>
              {project.description && (
                <p className="text-xs text-gray-500 mb-3 line-clamp-2">{project.description}</p>
              )}
              <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-800">
                <span className="text-xs text-gray-600">{project.plugin_id}</span>
                <button
                  onClick={() => deleteMutation.mutate(project.id)}
                  className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-900/30 rounded text-gray-600 hover:text-red-400 transition-all"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal title="New Project" open={showCreate} onClose={() => setShowCreate(false)}>
        <form
          onSubmit={(e) => { e.preventDefault(); createMutation.mutate() }}
          className="space-y-4"
        >
          <div>
            <label className="label">Project Title</label>
            <input
              className="input"
              placeholder="My Animation Project"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="label">Description</label>
            <textarea
              className="input resize-none"
              rows={3}
              placeholder="What is this project about?"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          <div>
            <label className="label">Studio Plugin</label>
            <select
              className="input"
              value={pluginId}
              onChange={(e) => setPluginId(e.target.value)}
              required
            >
              <option value="">Select a plugin...</option>
              {plugins?.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? <Spinner size="sm" /> : 'Create Project'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
