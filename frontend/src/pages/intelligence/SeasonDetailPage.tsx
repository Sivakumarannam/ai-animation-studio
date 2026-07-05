import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Clapperboard, ChevronRight, Sparkles } from 'lucide-react'
import { storyIntelligenceApi } from '@/api/storyIntelligence'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Modal } from '@/components/ui/Modal'

export function SeasonDetailPage() {
  const { projectId, seasonId } = useParams<{ projectId: string; seasonId: string }>()
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [title, setTitle] = useState('')
  const [summary, setSummary] = useState('')

  const { data: season, isLoading: seasonLoading } = useQuery({
    queryKey: ['si-season', seasonId],
    queryFn: () => storyIntelligenceApi.getSeason(seasonId!),
    enabled: !!seasonId,
  })

  const { data: episodes, isLoading: episodesLoading } = useQuery({
    queryKey: ['si-episodes', seasonId],
    queryFn: () => storyIntelligenceApi.listEpisodes(seasonId!),
    enabled: !!seasonId,
  })

  const createMutation = useMutation({
    mutationFn: () => storyIntelligenceApi.createEpisode(seasonId!, { title, summary }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['si-episodes', seasonId] })
      setShowCreate(false)
      setTitle('')
      setSummary('')
    },
  })

  const generateMutation = useMutation({
    mutationFn: () => storyIntelligenceApi.generateEpisode(seasonId!, { season_id: seasonId!, world_id: season!.world_id }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['si-episodes', seasonId] }),
  })

  if (seasonLoading) {
    return <div className="flex justify-center py-20"><Spinner size="lg" /></div>
  }

  if (!season) {
    return <div className="p-6 text-gray-400">Season not found</div>
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/projects" className="hover:text-gray-300">Projects</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}`} className="hover:text-gray-300">Project</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}/intelligence/worlds/${season.world_id}`} className="hover:text-gray-300">World</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300">Season {season.season_number}</span>
      </div>

      <div className="card p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white mb-1">Season {season.season_number}: {season.title}</h1>
            {season.description && <p className="text-gray-400 text-sm">{season.description}</p>}
          </div>
          <span className="badge-blue">{season.status}</span>
        </div>
        {season.story_arc && (
          <p className="text-xs text-gray-500 mt-4 pt-4 border-t border-gray-800">{season.story_arc}</p>
        )}
      </div>

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">Episodes</h2>
        <div className="flex gap-2">
          <button onClick={() => generateMutation.mutate()} className="btn-secondary" disabled={generateMutation.isPending}>
            {generateMutation.isPending ? <Spinner size="sm" /> : <Sparkles className="w-4 h-4" />} Generate Episode
          </button>
          <button onClick={() => setShowCreate(true)} className="btn-primary">
            <Plus className="w-4 h-4" /> New Episode
          </button>
        </div>
      </div>

      {generateMutation.isError && (
        <p className="text-xs text-red-400 mb-4">Failed to start episode generation. Please try again.</p>
      )}

      {episodesLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : episodes?.items.length === 0 ? (
        <EmptyState
          icon={Clapperboard}
          title="No episodes yet"
          description="Create an episode manually or generate one with AI."
          action={<button onClick={() => setShowCreate(true)} className="btn-primary"><Plus className="w-4 h-4" />Add Episode</button>}
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {episodes?.items.map((ep) => (
            <Link
              key={ep.id}
              to={`/projects/${projectId}/intelligence/episodes/${ep.id}`}
              className="card p-4 hover:border-gray-700 transition-colors"
            >
              <div className="w-12 h-12 bg-green-900/30 rounded-xl flex items-center justify-center mb-3">
                <Clapperboard className="w-6 h-6 text-green-400" />
              </div>
              <p className="text-sm font-semibold text-gray-100 mb-0.5">Ep {ep.episode_number}: {ep.title}</p>
              <p className="text-xs text-gray-500 mb-2 line-clamp-2">{ep.summary || 'No summary'}</p>
              <div className="flex items-center gap-2">
                <span className="badge-gray">{ep.status}</span>
                {ep.story_score > 0 && <span className="badge-blue">score {ep.story_score.toFixed(0)}</span>}
              </div>
            </Link>
          ))}
        </div>
      )}

      <Modal title="New Episode" open={showCreate} onClose={() => setShowCreate(false)}>
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate() }} className="space-y-4">
          <div>
            <label className="label">Title</label>
            <input className="input" placeholder="Episode title" value={title} onChange={(e) => setTitle(e.target.value)} required />
          </div>
          <div>
            <label className="label">Summary</label>
            <textarea className="input resize-none" rows={3} placeholder="What happens in this episode?" value={summary} onChange={(e) => setSummary(e.target.value)} />
          </div>
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? <Spinner size="sm" /> : 'Create Episode'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
