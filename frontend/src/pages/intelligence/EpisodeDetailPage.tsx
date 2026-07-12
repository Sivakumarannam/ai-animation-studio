import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Film, ChevronRight, CheckCircle2, History, Pencil, Trash2, Wand2 } from 'lucide-react'
import { storyIntelligenceApi } from '@/api/storyIntelligence'
import { assetGenerationApi } from '@/api/assetGeneration'
import type { StoryScene } from '@/types'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Modal } from '@/components/ui/Modal'

export function EpisodeDetailPage() {
  const { projectId, episodeId } = useParams<{ projectId: string; episodeId: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()

  // Create scene
  const [showCreate, setShowCreate] = useState(false)
  const [sceneGoal, setSceneGoal] = useState('')
  const [location, setLocation] = useState('')
  const [narration, setNarration] = useState('')

  // Edit episode
  const [showEditEp, setShowEditEp] = useState(false)
  const [editEpTitle, setEditEpTitle] = useState('')
  const [editEpSummary, setEditEpSummary] = useState('')

  // Delete episode
  const [showDeleteEp, setShowDeleteEp] = useState(false)

  // Generate assets
  const [showGenAssets, setShowGenAssets] = useState(false)
  const [genForceRegen, setGenForceRegen] = useState(false)

  // Edit scene
  const [showEditScene, setShowEditScene] = useState(false)
  const [editScene, setEditScene] = useState<StoryScene | null>(null)
  const [editSceneGoal, setEditSceneGoal] = useState('')
  const [editLocation, setEditLocation] = useState('')
  const [editNarration, setEditNarration] = useState('')

  // Delete scene
  const [showDeleteScene, setShowDeleteScene] = useState(false)
  const [sceneToDelete, setSceneToDelete] = useState<StoryScene | null>(null)

  const [showVersions, setShowVersions] = useState(false)

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

  const generateAssetsMutation = useMutation({
    mutationFn: () =>
      assetGenerationApi.triggerEpisodeGeneration({
        episode_id: episodeId!,
        project_id: projectId!,
        force_regenerate: genForceRegen,
      }),
    onSuccess: () => setShowGenAssets(false),
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
      setSceneGoal(''); setLocation(''); setNarration('')
    },
  })

  const editEpisodeMutation = useMutation({
    mutationFn: () => storyIntelligenceApi.updateEpisode(episodeId!, { title: editEpTitle, summary: editEpSummary }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['si-episode', episodeId] })
      setShowEditEp(false)
    },
  })

  const deleteEpisodeMutation = useMutation({
    mutationFn: () => storyIntelligenceApi.deleteEpisode(episodeId!),
    onSuccess: () => {
      navigate(`/projects/${projectId}/intelligence/seasons/${episode?.season_id}`)
    },
  })

  const editSceneMutation = useMutation({
    mutationFn: () => storyIntelligenceApi.updateScene(editScene!.id, {
      scene_goal: editSceneGoal,
      location: editLocation,
      narration: editNarration,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['si-scenes', episodeId] })
      setShowEditScene(false)
      setEditScene(null)
    },
  })

  const deleteSceneMutation = useMutation({
    mutationFn: (id: string) => storyIntelligenceApi.deleteScene(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['si-scenes', episodeId] })
      setShowDeleteScene(false)
      setSceneToDelete(null)
    },
  })

  function openEditEpisode() {
    if (!episode) return
    setEditEpTitle(episode.title)
    setEditEpSummary(episode.summary ?? '')
    setShowEditEp(true)
  }

  function openEditScene(scene: StoryScene) {
    setEditScene(scene)
    setEditSceneGoal(scene.scene_goal ?? '')
    setEditLocation(scene.location ?? '')
    setEditNarration(scene.narration ?? '')
    setShowEditScene(true)
  }

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
        <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-gray-800">
          <button onClick={() => evaluateMutation.mutate()} className="btn-secondary" disabled={evaluateMutation.isPending}>
            {evaluateMutation.isPending ? <Spinner size="sm" /> : <CheckCircle2 className="w-4 h-4" />} Evaluate
          </button>
          <button
            onClick={() => setShowGenAssets(true)}
            className="btn-primary flex items-center gap-1.5"
            data-testid="generate-assets-btn"
          >
            <Wand2 className="w-4 h-4" /> Generate Assets
          </button>
          <button onClick={() => setShowVersions(true)} className="btn-secondary">
            <History className="w-4 h-4" /> Version History
          </button>
          <button onClick={openEditEpisode} className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200 transition-colors ml-auto">
            <Pencil className="w-3 h-3" /> Edit Episode
          </button>
          <button onClick={() => setShowDeleteEp(true)} className="flex items-center gap-1 text-xs text-red-500 hover:text-red-400 transition-colors">
            <Trash2 className="w-3 h-3" /> Delete Episode
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
              <div className="flex gap-3 mt-3 pt-3 border-t border-gray-800">
                <button onClick={() => openEditScene(scene)} className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200 transition-colors">
                  <Pencil className="w-3 h-3" /> Edit
                </button>
                <button
                  onClick={() => { setSceneToDelete(scene); setShowDeleteScene(true) }}
                  className="flex items-center gap-1 text-xs text-red-500 hover:text-red-400 transition-colors ml-auto"
                >
                  <Trash2 className="w-3 h-3" /> Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Scene */}
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

      {/* Edit Episode */}
      <Modal title="Edit Episode" open={showEditEp} onClose={() => setShowEditEp(false)}>
        <form onSubmit={(e) => { e.preventDefault(); editEpisodeMutation.mutate() }} className="space-y-4">
          <div>
            <label className="label">Title</label>
            <input className="input" value={editEpTitle} onChange={(e) => setEditEpTitle(e.target.value)} required />
          </div>
          <div>
            <label className="label">Summary</label>
            <textarea className="input resize-none" rows={3} value={editEpSummary} onChange={(e) => setEditEpSummary(e.target.value)} />
          </div>
          {editEpisodeMutation.isError && <p className="text-xs text-red-400">Failed to save changes.</p>}
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowEditEp(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={editEpisodeMutation.isPending}>
              {editEpisodeMutation.isPending ? <Spinner size="sm" /> : 'Save Changes'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Episode */}
      <Modal title="Delete Episode" open={showDeleteEp} onClose={() => setShowDeleteEp(false)}>
        <div className="space-y-4">
          <p className="text-sm text-gray-300">
            Delete <strong className="text-white">Ep {episode.episode_number}: {episode.title}</strong>? All scenes will be removed. This cannot be undone.
          </p>
          {deleteEpisodeMutation.isError && <p className="text-xs text-red-400">Failed to delete episode.</p>}
          <div className="flex gap-3 justify-end pt-2">
            <button className="btn-secondary" onClick={() => setShowDeleteEp(false)}>Cancel</button>
            <button className="btn-danger" disabled={deleteEpisodeMutation.isPending} onClick={() => deleteEpisodeMutation.mutate()}>
              {deleteEpisodeMutation.isPending ? <Spinner size="sm" /> : 'Delete Episode'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Edit Scene */}
      <Modal title="Edit Scene" open={showEditScene} onClose={() => setShowEditScene(false)}>
        <form onSubmit={(e) => { e.preventDefault(); editSceneMutation.mutate() }} className="space-y-4">
          <div>
            <label className="label">Scene Goal</label>
            <input className="input" value={editSceneGoal} onChange={(e) => setEditSceneGoal(e.target.value)} />
          </div>
          <div>
            <label className="label">Location</label>
            <input className="input" value={editLocation} onChange={(e) => setEditLocation(e.target.value)} />
          </div>
          <div>
            <label className="label">Narration</label>
            <textarea className="input resize-none" rows={3} value={editNarration} onChange={(e) => setEditNarration(e.target.value)} />
          </div>
          {editSceneMutation.isError && <p className="text-xs text-red-400">Failed to save changes.</p>}
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowEditScene(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={editSceneMutation.isPending}>
              {editSceneMutation.isPending ? <Spinner size="sm" /> : 'Save Changes'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Scene */}
      <Modal title="Delete Scene" open={showDeleteScene} onClose={() => setShowDeleteScene(false)}>
        <div className="space-y-4">
          <p className="text-sm text-gray-300">
            Delete <strong className="text-white">Scene {sceneToDelete?.scene_number}</strong>? This cannot be undone.
          </p>
          {deleteSceneMutation.isError && <p className="text-xs text-red-400">Failed to delete scene.</p>}
          <div className="flex gap-3 justify-end pt-2">
            <button className="btn-secondary" onClick={() => setShowDeleteScene(false)}>Cancel</button>
            <button className="btn-danger" disabled={deleteSceneMutation.isPending} onClick={() => sceneToDelete && deleteSceneMutation.mutate(sceneToDelete.id)}>
              {deleteSceneMutation.isPending ? <Spinner size="sm" /> : 'Delete Scene'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Generate Assets */}
      <Modal title="Generate Assets for Episode" open={showGenAssets} onClose={() => setShowGenAssets(false)}>
        <div className="space-y-4">
          <p className="text-sm text-gray-400">
            Queues an AI generation job for all assets in{' '}
            <strong className="text-white">Ep {episode.episode_number}: {episode.title}</strong>.
          </p>
          <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer select-none">
            <input
              type="checkbox"
              className="rounded border-gray-700"
              checked={genForceRegen}
              onChange={(e) => setGenForceRegen(e.target.checked)}
              disabled={generateAssetsMutation.isPending}
            />
            Force re-generate already-completed assets
          </label>
          {generateAssetsMutation.isError && (
            <p className="text-xs text-red-400">Failed to queue generation job.</p>
          )}
          {generateAssetsMutation.isSuccess && (
            <p className="text-xs text-green-400">Generation job queued successfully.</p>
          )}
          <div className="flex gap-3 justify-end pt-2">
            <button
              className="btn-secondary"
              onClick={() => setShowGenAssets(false)}
              disabled={generateAssetsMutation.isPending}
            >
              Cancel
            </button>
            <button
              className="btn-primary flex items-center gap-1.5"
              onClick={() => generateAssetsMutation.mutate()}
              disabled={generateAssetsMutation.isPending}
              data-testid="confirm-generate-assets"
            >
              {generateAssetsMutation.isPending
                ? <><Spinner size="sm" /> Queuing…</>
                : <><Wand2 className="w-4 h-4" /> Generate</>
              }
            </button>
          </div>
        </div>
      </Modal>

      {/* Version History */}
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
