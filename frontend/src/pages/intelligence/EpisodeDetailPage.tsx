import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Film, ChevronRight, CheckCircle2, History } from 'lucide-react'
import { storyIntelligenceApi } from '@/api/storyIntelligence'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Modal } from '@/components/ui/Modal'

export function EpisodeDetailPage() {
  const { projectId, episodeId } = useParams<{ projectId: string; episodeId: string }>()
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [showVersions, setShowVersions] = useState(false)
  const [sceneGoal, setSceneGoal] = useState('')
  const [location, setLocation] = useState('')
  const [narration, setNarration] = useState('')

  const { data: episode, isLoading: episodeLoading } = useQuery({
    queryKey: ['si-episode', episodeId],
    queryFn: () => storyIntelligenceApi.getEpisode(episodeId!),
    enabled: !!episodeId,
  })

  const { data: scenes, isLoading: scenesLoading } = useQuery({
    queryKey: ['si-scenes', episodeId],
    queryFn: () => storyIntelligenceApi.listScenes(episodeId!),
    enabled: !!episodeId,
  })

  const { data: versions } = useQuery({
    queryKey: ['si-episode-versions', episodeId],
    queryFn: () => storyIntelligenceApi.listEpisodeVersions(episodeId!),
    enabled: !!episodeId && showVersions,
  })

  const evaluateMutation = useMutation({
    mutationFn: () => storyIntelligenceApi.evaluateEpisode(episodeId!),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['si-episode', episodeId] }),
  })

  const createSceneMutation = useMutation({
    mutationFn: () =>
      storyIntelligenceApi.createScene(episodeId!, {
        scene_number: (scenes?.items.length ?? 0) + 1,
        scene_goal: sceneGoal,
        location,
        narration,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['si-scenes', episodeId] })
      setShowCreate(false)
      setSceneGoal('')
      setLocation('')
      setNarration('')
    },
  })

  if (episodeLoading) {
    return <div className="flex justify-center py-20"><Spinner size="lg" /></div>
  }

  if (!episode) {
    return <div className="p-6 text-gray-400">Episode not found</div>
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/projects" className="hover:text-gray-300">Projects</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}`} className="hover:text-gray-300">Project</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}/intelligence/seasons/${episode.season_id}`} className="hover:text-gray-300">Season</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300">Ep {episode.episode_number}</span>
      </div>

      <div className="card p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white mb-1">Ep {episode.episode_number}: {episode.title}</h1>
            {episode.summary && <p className="text-gray-400 text-sm">{episode.summary}</p>}
          </div>
          <div className="flex items-center gap-2">
            {episode.story_score > 0 && <span className="badge-blue">score {episode.story_score.toFixed(0)}</span>}
            <span className="badge-gray">{episode.status}</span>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4 pt-4 border-t border-gray-800 text-xs">
          {episode.opening && <div><p className="text-gray-500 mb-1">Opening</p><p className="text-gray-300">{episode.opening}</p></div>}
          {episode.middle && <div><p className="text-gray-500 mb-1">Middle</p><p className="text-gray-300">{episode.middle}</p></div>}
          {episode.ending && <div><p className="text-gray-500 mb-1">Ending</p><p className="text-gray-300">{episode.ending}</p></div>}
        </div>
        {episode.moral && (
          <p className="text-xs text-gray-500 mt-4 pt-4 border-t border-gray-800">Moral: {episode.moral}</p>
        )}
        <div className="flex gap-2 mt-4 pt-4 border-t border-gray-800">
          <button onClick={() => evaluateMutation.mutate()} className="btn-secondary" disabled={evaluateMutation.isPending}>
            {evaluateMutation.isPending ? <Spinner size="sm" /> : <CheckCircle2 className="w-4 h-4" />} Evaluate
          </button>
          <button onClick={() => setShowVersions(true)} className="btn-secondary">
            <History className="w-4 h-4" /> Version History
          </button>
        </div>
        {evaluateMutation.data && (
          <p className="text-xs text-green-400 mt-2">
            Evaluated — overall score {evaluateMutation.data.overall_score.toFixed(1)}, {evaluateMutation.data.approved ? 'approved' : 'needs revision'}
          </p>
        )}
      </div>

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">Scenes</h2>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <Plus className="w-4 h-4" /> New Scene
        </button>
      </div>

      {scenesLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : scenes?.items.length === 0 ? (
        <EmptyState icon={Film} title="No scenes yet" description="Break this episode down into scenes." action={<button onClick={() => setShowCreate(true)} className="btn-primary"><Plus className="w-4 h-4" />Add Scene</button>} />
      ) : (
        <div className="space-y-3">
          {scenes?.items.map((scene) => (
            <div key={scene.id} className="card p-4">
              <div className="flex items-center justify-between mb-1">
                <p className="text-sm font-semibold text-gray-100">Scene {scene.scene_number}{scene.location ? ` — ${scene.location}` : ''}</p>
                <span className="badge-gray">{scene.status}</span>
              </div>
              {scene.scene_goal && <p className="text-xs text-gray-400 mb-1">Goal: {scene.scene_goal}</p>}
              {scene.narration && <p className="text-xs text-gray-500">{scene.narration}</p>}
              {scene.character_names.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {scene.character_names.map((c) => <span key={c} className="badge-gray text-xs">{c}</span>)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <Modal title="New Scene" open={showCreate} onClose={() => setShowCreate(false)}>
        <form onSubmit={(e) => { e.preventDefault(); createSceneMutation.mutate() }} className="space-y-4">
          <div>
            <label className="label">Scene Goal</label>
            <input className="input" placeholder="What should this scene achieve?" value={sceneGoal} onChange={(e) => setSceneGoal(e.target.value)} />
          </div>
          <div>
            <label className="label">Location</label>
            <input className="input" placeholder="Where does this scene take place?" value={location} onChange={(e) => setLocation(e.target.value)} />
          </div>
          <div>
            <label className="label">Narration</label>
            <textarea className="input resize-none" rows={3} placeholder="Narration / description" value={narration} onChange={(e) => setNarration(e.target.value)} />
          </div>
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={createSceneMutation.isPending}>
              {createSceneMutation.isPending ? <Spinner size="sm" /> : 'Add Scene'}
            </button>
          </div>
        </form>
      </Modal>

      <Modal title="Version History" open={showVersions} onClose={() => setShowVersions(false)}>
        {!versions ? (
          <div className="flex justify-center py-8"><Spinner /></div>
        ) : versions.length === 0 ? (
          <p className="text-sm text-gray-500">No versions recorded yet.</p>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {versions.map((v) => (
              <div key={v.id} className="border border-gray-800 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-200">Version {v.version_number}</p>
                  <p className="text-xs text-gray-500">{new Date(v.created_at).toLocaleString()}</p>
                </div>
                {v.change_summary && <p className="text-xs text-gray-500 mt-1">{v.change_summary}</p>}
              </div>
            ))}
          </div>
        )}
      </Modal>
    </div>
  )
}
