import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Layers, ChevronRight, Database, Pencil, Trash2 } from 'lucide-react'
import { storyIntelligenceApi } from '@/api/storyIntelligence'
import type { World } from '@/types'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Modal } from '@/components/ui/Modal'

export function WorldDetailPage() {
  const { projectId, worldId } = useParams<{ projectId: string; worldId: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()

  // Create season
  const [showCreate, setShowCreate] = useState(false)
  const [title, setTitle] = useState('')
  const [storyArc, setStoryArc] = useState('')
  const [episodeCount, setEpisodeCount] = useState(10)

  // Edit world
  const [showEdit, setShowEdit] = useState(false)
  const [editName, setEditName] = useState('')
  const [editDescription, setEditDescription] = useState('')
  const [editLore, setEditLore] = useState('')

  // Delete world
  const [showDelete, setShowDelete] = useState(false)

  // Add memory
  const [showAddMemory, setShowAddMemory] = useState(false)
  const [memoryKey, setMemoryKey] = useState('')
  const [memoryType, setMemoryType] = useState('character_fact')
  const [memoryValue, setMemoryValue] = useState('')

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
      setTitle(''); setStoryArc('')
    },
  })

  const editMutation = useMutation({
    mutationFn: () => storyIntelligenceApi.updateWorld(worldId!, { name: editName, description: editDescription, lore: editLore }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['si-world', worldId] })
      setShowEdit(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => storyIntelligenceApi.deleteWorld(worldId!),
    onSuccess: () => {
      navigate(`/projects/${projectId}/intelligence/worlds`)
    },
  })

  const addMemoryMutation = useMutation({
    mutationFn: () => {
      let parsedValue: unknown
      try { parsedValue = JSON.parse(memoryValue) } catch { parsedValue = memoryValue }
      return storyIntelligenceApi.createMemory(worldId!, {
        key: memoryKey,
        memory_type: memoryType,
        value: parsedValue,
      })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['si-memory', worldId] })
      setShowAddMemory(false)
      setMemoryKey(''); setMemoryValue('')
    },
  })

  function openEdit(w: World) {
    setEditName(w.name)
    setEditDescription(w.description ?? '')
    setEditLore((w as any).lore ?? '')
    setShowEdit(true)
  }

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
        {(world as any).lore && (
          <p className="text-xs text-gray-500 mt-4 pt-4 border-t border-gray-800 whitespace-pre-wrap">{(world as any).lore}</p>
        )}
        <div className="flex gap-2 mt-4 pt-4 border-t border-gray-800">
          <button onClick={() => openEdit(world)} className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200 transition-colors">
            <Pencil className="w-3 h-3" /> Edit World
          </button>
          <button onClick={() => setShowDelete(true)} className="flex items-center gap-1 text-xs text-red-500 hover:text-red-400 transition-colors ml-auto">
            <Trash2 className="w-3 h-3" /> Delete World
          </button>
        </div>
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
                  <p className="text-xs text-gray-500 mb-2 line-clamp-2">{season.description || (season as any).story_arc || 'No description'}</p>
                  <span className="badge-gray">{season.status}</span>
                </Link>
              ))}
            </div>
          )}
        </>
      )}

      {tab === 'memory' && (
        <>
          <div className="flex items-center justify-end mb-4">
            <button onClick={() => setShowAddMemory(true)} className="btn-primary">
              <Plus className="w-4 h-4" /> Add Memory
            </button>
          </div>
          {memoryLoading ? (
            <div className="flex justify-center py-20"><Spinner size="lg" /></div>
          ) : memory?.items.length === 0 ? (
            <EmptyState
              icon={Database}
              title="No memory entries"
              description="Story memory (characters, facts, running gags) appears here. Add entries manually or generate episodes."
              action={<button onClick={() => setShowAddMemory(true)} className="btn-primary"><Plus className="w-4 h-4" />Add Memory</button>}
            />
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
          )}
        </>
      )}

      {/* Create Season */}
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

      {/* Edit World */}
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

      {/* Delete World */}
      <Modal title="Delete World" open={showDelete} onClose={() => setShowDelete(false)}>
        <div className="space-y-4">
          <p className="text-sm text-gray-300">
            Delete <strong className="text-white">{world.name}</strong>? All seasons, episodes, scenes, and story memory will be removed. This cannot be undone.
          </p>
          {deleteMutation.isError && <p className="text-xs text-red-400">Failed to delete world.</p>}
          <div className="flex gap-3 justify-end pt-2">
            <button className="btn-secondary" onClick={() => setShowDelete(false)}>Cancel</button>
            <button className="btn-danger" disabled={deleteMutation.isPending} onClick={() => deleteMutation.mutate()}>
              {deleteMutation.isPending ? <Spinner size="sm" /> : 'Delete World'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Add Memory */}
      <Modal title="Add Story Memory" open={showAddMemory} onClose={() => setShowAddMemory(false)}>
        <form onSubmit={(e) => { e.preventDefault(); addMemoryMutation.mutate() }} className="space-y-4">
          <div>
            <label className="label">Key</label>
            <input className="input" placeholder="e.g. protagonist_name, running_gag_1" value={memoryKey} onChange={(e) => setMemoryKey(e.target.value)} required />
          </div>
          <div>
            <label className="label">Type</label>
            <select className="input" value={memoryType} onChange={(e) => setMemoryType(e.target.value)}>
              <option value="character_fact">Character Fact</option>
              <option value="plot_point">Plot Point</option>
              <option value="running_gag">Running Gag</option>
              <option value="world_rule">World Rule</option>
              <option value="relationship">Relationship</option>
              <option value="event">Event</option>
            </select>
          </div>
          <div>
            <label className="label">Value</label>
            <textarea
              className="input resize-none font-mono text-xs"
              rows={3}
              placeholder='Text value or JSON, e.g. "Raju always trips on banana peels"'
              value={memoryValue}
              onChange={(e) => setMemoryValue(e.target.value)}
              required
            />
            <p className="text-xs text-gray-500 mt-1">Plain text or valid JSON</p>
          </div>
          {addMemoryMutation.isError && <p className="text-xs text-red-400">Failed to add memory entry.</p>}
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowAddMemory(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={addMemoryMutation.isPending}>
              {addMemoryMutation.isPending ? <Spinner size="sm" /> : 'Add Memory'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
