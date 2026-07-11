import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { BookOpen, Play, Plus, Pencil, Trash2 } from 'lucide-react'
import { researchApi, ResearchTopic } from '@/api/research'
import { Spinner } from '@/components/ui/Spinner'
import { Modal } from '@/components/ui/Modal'

const STATUS_COLORS: Record<string, string> = {
  discovered: 'bg-blue-900 text-blue-300',
  researching: 'bg-yellow-900 text-yellow-300',
  researched: 'bg-green-900 text-green-300',
  verified: 'bg-emerald-900 text-emerald-300',
  queued: 'bg-purple-900 text-purple-300',
  completed: 'bg-gray-700 text-gray-300',
  rejected: 'bg-red-900 text-red-300',
}

export function TopicExplorerPage() {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [showCreate, setShowCreate] = useState(false)
  const [newTopic, setNewTopic] = useState('')

  // Edit modal state
  const [showEdit, setShowEdit] = useState(false)
  const [editTopic, setEditTopic] = useState<ResearchTopic | null>(null)
  const [editName, setEditName] = useState('')
  const [editDescription, setEditDescription] = useState('')

  // Delete modal state
  const [showDelete, setShowDelete] = useState(false)
  const [topicToDelete, setTopicToDelete] = useState<ResearchTopic | null>(null)

  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['research-topics', page, statusFilter],
    queryFn: () => researchApi.getTopics(page, 20, statusFilter),
  })

  const createTopic = useMutation({
    mutationFn: () => researchApi.createTopic({ canonical_name: newTopic }),
    onSuccess: () => {
      setNewTopic('')
      setShowCreate(false)
      qc.invalidateQueries({ queryKey: ['research-topics'] })
    },
  })

  const updateTopic = useMutation({
    mutationFn: () => researchApi.updateTopic(editTopic!.id, { canonical_name: editName, description: editDescription }),
    onSuccess: () => {
      setShowEdit(false)
      setEditTopic(null)
      qc.invalidateQueries({ queryKey: ['research-topics'] })
    },
  })

  const deleteTopic = useMutation({
    mutationFn: (id: string) => researchApi.deleteTopic(id),
    onSuccess: () => {
      setShowDelete(false)
      setTopicToDelete(null)
      qc.invalidateQueries({ queryKey: ['research-topics'] })
    },
  })

  const researchTopic = useMutation({
    mutationFn: (id: string) => researchApi.researchTopic(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['research-topics'] }),
  })

  function openEdit(topic: ResearchTopic) {
    setEditTopic(topic)
    setEditName(topic.canonical_name)
    setEditDescription(topic.description)
    setShowEdit(true)
  }

  function openDelete(topic: ResearchTopic) {
    setTopicToDelete(topic)
    setShowDelete(true)
  }

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-indigo-400" /> Topic Explorer
          </h1>
          <p className="text-gray-400 text-sm mt-1">Normalised research topics ready for investigation</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary text-sm flex items-center gap-2">
          <Plus className="w-4 h-4" /> Add Topic
        </button>
      </div>

      {showCreate && (
        <div className="card p-4 flex gap-3">
          <input
            className="input flex-1"
            placeholder="Topic name (e.g. Quantum Computing)"
            value={newTopic}
            onChange={e => setNewTopic(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && newTopic && createTopic.mutate()}
          />
          <button onClick={() => createTopic.mutate()} disabled={!newTopic || createTopic.isPending} className="btn-primary text-sm">
            {createTopic.isPending ? 'Creating…' : 'Create'}
          </button>
          <button onClick={() => setShowCreate(false)} className="btn-secondary text-sm">Cancel</button>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        {[undefined, 'discovered', 'researching', 'researched', 'queued', 'completed'].map(s => (
          <button
            key={s || 'all'}
            onClick={() => { setStatusFilter(s); setPage(1) }}
            className={`text-xs px-3 py-1 rounded-full transition-colors ${statusFilter === s ? 'bg-brand-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
          >
            {s || 'All'}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : (
        <div className="space-y-3">
          {data?.items.map((topic: ResearchTopic) => (
            <div key={topic.id} className="card p-4 flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="font-medium text-white truncate">{topic.canonical_name}</p>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[topic.status] || 'bg-gray-700 text-gray-300'}`}>
                    {topic.status}
                  </span>
                </div>
                <div className="flex items-center gap-4 mt-1 text-xs text-gray-400">
                  <span>{topic.categories.join(', ')}</span>
                  <span>{topic.article_count} articles</span>
                  <span>{topic.fact_count} facts</span>
                  <span>Score: <span className="text-brand-400 font-medium">{topic.opportunity_score.toFixed(0)}</span></span>
                </div>
              </div>
              <div className="flex gap-2 ml-4">
                {topic.research_status === 'pending' && (
                  <button
                    onClick={() => researchTopic.mutate(topic.id)}
                    disabled={researchTopic.isPending}
                    className="btn-primary text-xs flex items-center gap-1"
                  >
                    <Play className="w-3 h-3" /> Research
                  </button>
                )}
                <button
                  onClick={() => openEdit(topic)}
                  className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200 transition-colors px-2 py-1"
                >
                  <Pencil className="w-3 h-3" /> Edit
                </button>
                <button
                  onClick={() => openDelete(topic)}
                  className="flex items-center gap-1 text-xs text-red-500 hover:text-red-400 transition-colors px-2 py-1"
                >
                  <Trash2 className="w-3 h-3" /> Delete
                </button>
              </div>
            </div>
          ))}
          {data?.items.length === 0 && (
            <div className="text-center py-16 text-gray-500">
              No topics found. Run trend discovery to populate topics automatically.
            </div>
          )}

          {data && (
            <div className="flex justify-center gap-2 pt-2">
              <button className="btn-secondary text-sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Previous</button>
              <span className="text-gray-400 text-sm self-center">Page {page} of {data.meta.total_pages}</span>
              <button className="btn-secondary text-sm" disabled={page >= data.meta.total_pages} onClick={() => setPage(p => p + 1)}>Next</button>
            </div>
          )}
        </div>
      )}

      {/* Edit Modal */}
      <Modal title="Edit Topic" open={showEdit} onClose={() => setShowEdit(false)}>
        <form onSubmit={(e) => { e.preventDefault(); updateTopic.mutate() }} className="space-y-4">
          <div>
            <label className="label">Topic Name</label>
            <input
              className="input"
              value={editName}
              onChange={e => setEditName(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="label">Description</label>
            <textarea
              className="input resize-none"
              rows={3}
              value={editDescription}
              onChange={e => setEditDescription(e.target.value)}
            />
          </div>
          {updateTopic.isError && <p className="text-xs text-red-400">Failed to save changes.</p>}
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowEdit(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={updateTopic.isPending}>
              {updateTopic.isPending ? <Spinner size="sm" /> : 'Save Changes'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal title="Delete Topic" open={showDelete} onClose={() => setShowDelete(false)}>
        <div className="space-y-4">
          <p className="text-sm text-gray-300">
            Are you sure you want to delete <strong className="text-white">{topicToDelete?.canonical_name}</strong>? All associated articles and facts will also be removed. This cannot be undone.
          </p>
          {deleteTopic.isError && <p className="text-xs text-red-400">Failed to delete topic.</p>}
          <div className="flex gap-3 justify-end pt-2">
            <button className="btn-secondary" onClick={() => setShowDelete(false)}>Cancel</button>
            <button
              className="btn-danger"
              disabled={deleteTopic.isPending}
              onClick={() => topicToDelete && deleteTopic.mutate(topicToDelete.id)}
            >
              {deleteTopic.isPending ? <Spinner size="sm" /> : 'Delete Topic'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
