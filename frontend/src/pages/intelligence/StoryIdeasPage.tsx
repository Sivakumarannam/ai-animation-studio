import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Lightbulb, ChevronRight, Sparkles } from 'lucide-react'
import { storyIntelligenceApi } from '@/api/storyIntelligence'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Modal } from '@/components/ui/Modal'

export function StoryIdeasPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [showGenerate, setShowGenerate] = useState(false)
  const [title, setTitle] = useState('')
  const [premise, setPremise] = useState('')
  const [genre, setGenre] = useState('comedy')
  const [count, setCount] = useState(3)

  const { data, isLoading } = useQuery({
    queryKey: ['si-ideas', projectId],
    queryFn: () => storyIntelligenceApi.listIdeas(projectId!),
    enabled: !!projectId,
  })

  const createMutation = useMutation({
    mutationFn: () => storyIntelligenceApi.createIdea(projectId!, { title, premise, genre }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['si-ideas', projectId] })
      setShowCreate(false)
      setTitle('')
      setPremise('')
    },
  })

  const generateMutation = useMutation({
    mutationFn: () => storyIntelligenceApi.generateIdeas(projectId!, { genre, count }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['si-ideas', projectId] })
      setShowGenerate(false)
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
        <span className="text-gray-300">Story Library</span>
      </div>

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Story Library</h1>
        <div className="flex gap-2">
          <button onClick={() => setShowGenerate(true)} className="btn-secondary">
            <Sparkles className="w-4 h-4" /> Generate Ideas
          </button>
          <button onClick={() => setShowCreate(true)} className="btn-primary">
            <Plus className="w-4 h-4" /> New Idea
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : data?.items.length === 0 ? (
        <EmptyState
          icon={Lightbulb}
          title="No story ideas yet"
          description="Write your own idea or let AI generate some for you."
          action={<button onClick={() => setShowGenerate(true)} className="btn-primary"><Sparkles className="w-4 h-4" />Generate Ideas</button>}
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {data?.items.map((idea) => (
            <div key={idea.id} className="card p-4">
              <div className="w-12 h-12 bg-yellow-900/30 rounded-xl flex items-center justify-center mb-3">
                <Lightbulb className="w-6 h-6 text-yellow-400" />
              </div>
              <p className="text-sm font-semibold text-gray-100 mb-0.5">{idea.title}</p>
              <p className="text-xs text-gray-500 mb-2 line-clamp-3">{idea.premise || 'No premise'}</p>
              <div className="flex flex-wrap gap-1.5">
                <span className="badge-gray">{idea.genre}</span>
                <span className="badge-gray">{idea.status}</span>
                <span className="badge-gray">{idea.estimated_episodes} eps</span>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal title="New Story Idea" open={showCreate} onClose={() => setShowCreate(false)}>
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate() }} className="space-y-4">
          <div>
            <label className="label">Title</label>
            <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} required />
          </div>
          <div>
            <label className="label">Premise</label>
            <textarea className="input resize-none" rows={3} value={premise} onChange={(e) => setPremise(e.target.value)} />
          </div>
          <div>
            <label className="label">Genre</label>
            <input className="input" value={genre} onChange={(e) => setGenre(e.target.value)} />
          </div>
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? <Spinner size="sm" /> : 'Create Idea'}
            </button>
          </div>
        </form>
      </Modal>

      <Modal title="Generate Story Ideas" open={showGenerate} onClose={() => setShowGenerate(false)}>
        <form onSubmit={(e) => { e.preventDefault(); generateMutation.mutate() }} className="space-y-4">
          <div>
            <label className="label">Genre</label>
            <input className="input" value={genre} onChange={(e) => setGenre(e.target.value)} />
          </div>
          <div>
            <label className="label">How many ideas?</label>
            <input type="number" min={1} max={10} className="input" value={count} onChange={(e) => setCount(Number(e.target.value))} />
          </div>
          {generateMutation.isError && <p className="text-xs text-red-400">Failed to generate ideas. Please try again.</p>}
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowGenerate(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={generateMutation.isPending}>
              {generateMutation.isPending ? <Spinner size="sm" /> : 'Generate'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
