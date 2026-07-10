import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Clapperboard, ChevronRight, Sparkles, Pencil, Trash2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { storyIntelligenceApi } from '@/api/storyIntelligence'
import type { Season } from '@/types'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Modal } from '@/components/ui/Modal'

export function SeasonDetailPage() {
  const { projectId, seasonId } = useParams<{ projectId: string; seasonId: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()

  // Create episode
  const [showCreate, setShowCreate] = useState(false)
  const [title, setTitle] = useState('')
  const [summary, setSummary] = useState('')

  // Edit season
  const [showEdit, setShowEdit] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [editStoryArc, setEditStoryArc] = useState('')

  // Delete season
  const [showDelete, setShowDelete] = useState(false)

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

  const editMutation = useMutation({
    mutationFn: () => storyIntelligenceApi.updateSeason(seasonId!, { title: editTitle, story_arc: editStoryArc }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['si-season', seasonId] })
      setShowEdit(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => storyIntelligenceApi.deleteSeason(seasonId!),
    onSuccess: () => {
      navigate(`/projects/${projectId}/intelligence/worlds/${season?.world_id}`)
    },
  })

  function openEdit(s: Season) {
    setEditTitle(s.title)
    setEditStoryArc((s as any).story_arc ?? '')
    setShowEdit(true)
  }

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
        {(season as any).story_arc && (
          <p className="text-xs text-gray-500 mt-4 pt-4 border-t border-gray-800">{(season as any).story_arc}</p>
        )}
        <div className="flex gap-2 mt-4 pt-4 border-t border-gray-800">
          <button onClick={() => openEdit(season)} className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200 transition-colors">
            <Pencil className="w-3 h-3" /> Edit Season
          </button>
          <button onClick={() => setShowDelete(true)} className="flex items-center gap-1 text-xs text-red-500 hover:text-red-400 transition-colors ml-auto">
            <Trash2 className="w-3 h-3" /> Delete Season
          </button>
        </div>
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

      {/* Create Episode Modal */}
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

      {/* Edit Season Modal */}
      <Modal title="Edit Season" open={showEdit} onClose={() => setShowEdit(false)}>
        <form onSubmit={(e) => { e.preventDefault(); editMutation.mutate() }} className="space-y-4">
          <div>
            <label className="label">Title</label>
            <input className="input" value={editTitle} onChange={(e) => setEditTitle(e.target.value)} required />
          </div>
          <div>
            <label className="label">Story Arc</label>
            <textarea className="input resize-none" rows={2} value={editStoryArc} onChange={(e) => setEditStoryArc(e.target.value)} />
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

      {/* Delete Season Confirmation */}
      <Modal title="Delete Season" open={showDelete} onClose={() => setShowDelete(false)}>
        <div className="space-y-4">
          <p className="text-sm text-gray-300">
            Are you sure you want to delete <strong className="text-white">Season {season.season_number}: {season.title}</strong>? All episodes and scenes will be removed. This cannot be undone.
          </p>
          {deleteMutation.isError && <p className="text-xs text-red-400">Failed to delete season.</p>}
          <div className="flex gap-3 justify-end pt-2">
            <button className="btn-secondary" onClick={() => setShowDelete(false)}>Cancel</button>
            <button className="btn-danger" disabled={deleteMutation.isPending} onClick={() => deleteMutation.mutate()}>
              {deleteMutation.isPending ? <Spinner size="sm" /> : 'Delete Season'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
