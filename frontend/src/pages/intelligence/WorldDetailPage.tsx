import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Layers, ChevronRight, Database } from 'lucide-react'
import { storyIntelligenceApi } from '@/api/storyIntelligence'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Modal } from '@/components/ui/Modal'

export function WorldDetailPage() {
  const { projectId, worldId } = useParams<{ projectId: string; worldId: string }>()
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [title, setTitle] = useState('')
  const [storyArc, setStoryArc] = useState('')
  const [episodeCount, setEpisodeCount] = useState(10)
  const [tab, setTab] = useState<'seasons' | 'memory'>('seasons')

  const { data: world, isLoading: worldLoading } = useQuery({
    queryKey: ['si-world', worldId],
    queryFn: () => storyIntelligenceApi.getWorld(worldId!),
    enabled: !!worldId,
  })

  const { data: seasons, isLoading: seasonsLoading } = useQuery({
    queryKey: ['si-seasons', worldId],
    queryFn: () => storyIntelligenceApi.listSeasons(worldId!),
    enabled: !!worldId,
  })

  const { data: memory, isLoading: memoryLoading } = useQuery({
    queryKey: ['si-memory', worldId],
    queryFn: () => storyIntelligenceApi.listMemory(worldId!),
    enabled: !!worldId && tab === 'memory',
  })

  const createMutation = useMutation({
    mutationFn: () => storyIntelligenceApi.createSeason(worldId!, { title, story_arc: storyArc, episode_count: episodeCount }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['si-seasons', worldId] })
      setShowCreate(false)
      setTitle('')
      setStoryArc('')
    },
  })

  if (worldLoading) {
    return <div className="flex justify-center py-20"><Spinner size="lg" /></div>
  }

  if (!world) {
    return <div className="p-6 text-gray-400">World not found</div>
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/projects" className="hover:text-gray-300">Projects</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}`} className="hover:text-gray-300">Project</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}/intelligence/worlds`} className="hover:text-gray-300">Worlds</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300">{world.name}</span>
      </div>

      <div className="card p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white mb-1">{world.name}</h1>
            {world.description && <p className="text-gray-400 text-sm">{world.description}</p>}
          </div>
          <span className="badge-blue">{world.status}</span>
        </div>
        {world.lore && (
          <p className="text-xs text-gray-500 mt-4 pt-4 border-t border-gray-800 whitespace-pre-wrap">{world.lore}</p>
        )}
      </div>

      <div className="flex gap-2 mb-4 border-b border-gray-800">
        <button
          onClick={() => setTab('seasons')}
          className={`px-3 py-2 text-sm ${tab === 'seasons' ? 'text-brand-400 border-b-2 border-brand-400' : 'text-gray-500'}`}
        >
          Seasons
        </button>
        <button
          onClick={() => setTab('memory')}
          className={`px-3 py-2 text-sm ${tab === 'memory' ? 'text-brand-400 border-b-2 border-brand-400' : 'text-gray-500'}`}
        >
          Story Memory
        </button>
      </div>

      {tab === 'seasons' && (
        <>
          <div className="flex items-center justify-end mb-4">
            <button onClick={() => setShowCreate(true)} className="btn-primary">
              <Plus className="w-4 h-4" /> New Season
            </button>
          </div>
          {seasonsLoading ? (
            <div className="flex justify-center py-20"><Spinner size="lg" /></div>
          ) : seasons?.items.length === 0 ? (
            <EmptyState
              icon={Layers}
              title="No seasons yet"
              description="Create a season to group episodes into a story arc."
              action={<button onClick={() => setShowCreate(true)} className="btn-primary"><Plus className="w-4 h-4" />Create Season</button>}
            />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {seasons?.items.map((season) => (
                <Link
                  key={season.id}
                  to={`/projects/${projectId}/intelligence/seasons/${season.id}`}
                  className="card p-4 hover:border-gray-700 transition-colors"
                >
                  <div className="w-12 h-12 bg-purple-900/30 rounded-xl flex items-center justify-center mb-3">
                    <Layers className="w-6 h-6 text-purple-400" />
                  </div>
                  <p className="text-sm font-semibold text-gray-100 mb-0.5">Season {season.season_number}: {season.title}</p>
                  <p className="text-xs text-gray-500 mb-2 line-clamp-2">{season.description || season.story_arc || 'No description'}</p>
                  <span className="badge-gray">{season.status}</span>
                </Link>
              ))}
            </div>
          )}
        </>
      )}

      {tab === 'memory' && (
        memoryLoading ? (
          <div className="flex justify-center py-20"><Spinner size="lg" /></div>
        ) : memory?.items.length === 0 ? (
          <EmptyState icon={Database} title="No memory entries" description="Story memory (characters, facts, running gags) will appear here as episodes are generated." />
        ) : (
          <div className="space-y-2">
            {memory?.items.map((m) => (
              <div key={m.id} className="card p-4">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-sm font-semibold text-gray-100">{m.key}</p>
                  <span className="badge-gray">{m.memory_type}</span>
                </div>
                <pre className="text-xs text-gray-500 whitespace-pre-wrap break-words">{JSON.stringify(m.value, null, 2)}</pre>
              </div>
            ))}
          </div>
        )
      )}

      <Modal title="New Season" open={showCreate} onClose={() => setShowCreate(false)}>
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate() }} className="space-y-4">
          <div>
            <label className="label">Title</label>
            <input className="input" placeholder="Season title" value={title} onChange={(e) => setTitle(e.target.value)} required />
          </div>
          <div>
            <label className="label">Story Arc</label>
            <textarea className="input resize-none" rows={2} placeholder="The overarching arc for this season" value={storyArc} onChange={(e) => setStoryArc(e.target.value)} />
          </div>
          <div>
            <label className="label">Episode Count</label>
            <input type="number" min={1} max={50} className="input" value={episodeCount} onChange={(e) => setEpisodeCount(Number(e.target.value))} />
          </div>
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? <Spinner size="sm" /> : 'Create Season'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
