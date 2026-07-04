import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, BookOpen, ChevronRight, Trash2 } from 'lucide-react'
import { storiesApi } from '@/api/stories'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Modal } from '@/components/ui/Modal'

export function StoriesPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [title, setTitle] = useState('')
  const [premise, setPremise] = useState('')
  const [genre, setGenre] = useState('')
  const [tone, setTone] = useState('')
  const [language, setLanguage] = useState('te')

  const { data, isLoading } = useQuery({
    queryKey: ['stories', projectId],
    queryFn: () => storiesApi.list(projectId!),
    enabled: !!projectId,
  })

  const createMutation = useMutation({
    mutationFn: () => storiesApi.create(projectId!, { title, premise, genre, tone, language }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['stories', projectId] })
      setShowCreate(false)
      setTitle('')
      setPremise('')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => storiesApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['stories', projectId] }),
  })

  const statusColor = (s: string) => {
    const map: Record<string, string> = { draft: 'badge-gray', generating: 'badge-yellow', ready: 'badge-green', failed: 'badge-gray' }
    return map[s] || 'badge-gray'
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/projects" className="hover:text-gray-300">Projects</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}`} className="hover:text-gray-300">Project</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300">Stories</span>
      </div>

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Stories</h1>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <Plus className="w-4 h-4" /> New Story
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : data?.items.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title="No stories yet"
          description="Create your first story script for this project."
          action={<button onClick={() => setShowCreate(true)} className="btn-primary"><Plus className="w-4 h-4" />New Story</button>}
        />
      ) : (
        <div className="space-y-3">
          {data?.items.map((story) => (
            <div key={story.id} className="card p-4 flex items-center gap-4 group hover:border-gray-700 transition-colors">
              <div className="w-9 h-9 bg-blue-900/30 rounded-lg flex items-center justify-center flex-shrink-0">
                <BookOpen className="w-4 h-4 text-blue-400" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <p className="text-sm font-semibold text-gray-100 truncate">{story.title}</p>
                  <span className={statusColor(story.status)}>{story.status}</span>
                </div>
                <p className="text-xs text-gray-500 truncate">{story.premise || 'No premise yet'}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-600">{story.language}</span>
                <button
                  onClick={() => deleteMutation.mutate(story.id)}
                  className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-900/30 rounded text-gray-600 hover:text-red-400 transition-all"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal title="New Story" open={showCreate} onClose={() => setShowCreate(false)}>
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate() }} className="space-y-4">
          <div>
            <label className="label">Title</label>
            <input className="input" placeholder="Episode 1: The Mishap" value={title} onChange={(e) => setTitle(e.target.value)} required />
          </div>
          <div>
            <label className="label">Premise</label>
            <textarea className="input resize-none" rows={3} placeholder="What happens in this episode?" value={premise} onChange={(e) => setPremise(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Genre</label>
              <input className="input" placeholder="family_comedy" value={genre} onChange={(e) => setGenre(e.target.value)} />
            </div>
            <div>
              <label className="label">Tone</label>
              <input className="input" placeholder="lighthearted" value={tone} onChange={(e) => setTone(e.target.value)} />
            </div>
          </div>
          <div>
            <label className="label">Language</label>
            <select className="input" value={language} onChange={(e) => setLanguage(e.target.value)}>
              <option value="te">Telugu</option>
              <option value="en">English</option>
              <option value="hi">Hindi</option>
              <option value="ta">Tamil</option>
            </select>
          </div>
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? <Spinner size="sm" /> : 'Create Story'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
