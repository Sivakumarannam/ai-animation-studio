import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Rss, Plus, Pencil, Trash2, ToggleLeft, ToggleRight } from 'lucide-react'
import { researchApi, ResearchSource } from '@/api/research'
import { Spinner } from '@/components/ui/Spinner'
import { Modal } from '@/components/ui/Modal'

const SOURCE_TYPES = ['rss', 'web', 'api', 'youtube', 'wikipedia', 'wikidata', 'reddit', 'news', 'other']

interface SourceFormData {
  name: string
  source_type: string
  url: string
  description: string
  is_active: boolean
  fetch_interval_seconds: number
}

const EMPTY_FORM: SourceFormData = {
  name: '',
  source_type: 'rss',
  url: '',
  description: '',
  is_active: true,
  fetch_interval_seconds: 3600,
}

export function ResearchSourcesPage() {
  const [page, setPage] = useState(1)
  const qc = useQueryClient()

  // Create modal
  const [showCreate, setShowCreate] = useState(false)
  const [createForm, setCreateForm] = useState<SourceFormData>(EMPTY_FORM)

  // Edit modal
  const [showEdit, setShowEdit] = useState(false)
  const [editSource, setEditSource] = useState<ResearchSource | null>(null)
  const [editForm, setEditForm] = useState<SourceFormData>(EMPTY_FORM)

  // Delete modal
  const [showDelete, setShowDelete] = useState(false)
  const [sourceToDelete, setSourceToDelete] = useState<ResearchSource | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['research-sources', page],
    queryFn: () => researchApi.getSources(page, 20),
  })

  const createMutation = useMutation({
    mutationFn: () => researchApi.createSource(createForm),
    onSuccess: () => {
      setShowCreate(false)
      setCreateForm(EMPTY_FORM)
      qc.invalidateQueries({ queryKey: ['research-sources'] })
    },
  })

  const updateMutation = useMutation({
    mutationFn: () => researchApi.updateSource(editSource!.id, editForm),
    onSuccess: () => {
      setShowEdit(false)
      setEditSource(null)
      qc.invalidateQueries({ queryKey: ['research-sources'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => researchApi.deleteSource(id),
    onSuccess: () => {
      setShowDelete(false)
      setSourceToDelete(null)
      qc.invalidateQueries({ queryKey: ['research-sources'] })
    },
  })

  function openEdit(source: ResearchSource) {
    setEditSource(source)
    setEditForm({
      name: source.name,
      source_type: source.source_type,
      url: source.url,
      description: source.description,
      is_active: source.is_active,
      fetch_interval_seconds: source.fetch_interval_seconds,
    })
    setShowEdit(true)
  }

  function openDelete(source: ResearchSource) {
    setSourceToDelete(source)
    setShowDelete(true)
  }

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Rss className="w-6 h-6 text-orange-400" /> Research Sources
          </h1>
          <p className="text-gray-400 text-sm mt-1">Configure RSS feeds, URLs, and APIs for the research pipeline</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary text-sm flex items-center gap-2">
          <Plus className="w-4 h-4" /> Add Source
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : (
        <div className="space-y-3">
          {data?.items.map((source: ResearchSource) => (
            <div key={source.id} className="card p-4 flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="font-medium text-white truncate">{source.name}</p>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-gray-700 text-gray-300 capitalize">
                    {source.source_type}
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${source.is_active ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`}>
                    {source.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                {source.url && (
                  <p className="text-xs text-gray-500 mt-1 truncate">{source.url}</p>
                )}
                <div className="flex items-center gap-4 mt-1 text-xs text-gray-400">
                  <span>Fetched: {source.fetch_count}x</span>
                  <span>Errors: {source.error_count}</span>
                  <span>Interval: {source.fetch_interval_seconds}s</span>
                  {source.last_fetched_at && (
                    <span>Last: {new Date(source.last_fetched_at).toLocaleDateString()}</span>
                  )}
                </div>
              </div>
              <div className="flex gap-2 ml-4">
                <button
                  onClick={() => openEdit(source)}
                  className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200 transition-colors px-2 py-1"
                >
                  <Pencil className="w-3 h-3" /> Edit
                </button>
                <button
                  onClick={() => openDelete(source)}
                  className="flex items-center gap-1 text-xs text-red-500 hover:text-red-400 transition-colors px-2 py-1"
                >
                  <Trash2 className="w-3 h-3" /> Delete
                </button>
              </div>
            </div>
          ))}
          {data?.items.length === 0 && (
            <div className="text-center py-16 text-gray-500">
              No sources configured. Add RSS feeds or URLs to drive the research pipeline.
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

      {/* Create Modal */}
      <Modal title="Add Research Source" open={showCreate} onClose={() => setShowCreate(false)}>
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate() }} className="space-y-4">
          <SourceForm form={createForm} setForm={setCreateForm} />
          {createMutation.isError && <p className="text-xs text-red-400">Failed to create source.</p>}
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? <Spinner size="sm" /> : 'Add Source'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Modal */}
      <Modal title="Edit Research Source" open={showEdit} onClose={() => setShowEdit(false)}>
        <form onSubmit={(e) => { e.preventDefault(); updateMutation.mutate() }} className="space-y-4">
          <SourceForm form={editForm} setForm={setEditForm} />
          {updateMutation.isError && <p className="text-xs text-red-400">Failed to save changes.</p>}
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowEdit(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? <Spinner size="sm" /> : 'Save Changes'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Modal */}
      <Modal title="Delete Source" open={showDelete} onClose={() => setShowDelete(false)}>
        <div className="space-y-4">
          <p className="text-sm text-gray-300">
            Are you sure you want to delete <strong className="text-white">{sourceToDelete?.name}</strong>? This cannot be undone.
          </p>
          {deleteMutation.isError && <p className="text-xs text-red-400">Failed to delete source.</p>}
          <div className="flex gap-3 justify-end pt-2">
            <button className="btn-secondary" onClick={() => setShowDelete(false)}>Cancel</button>
            <button
              className="btn-danger"
              disabled={deleteMutation.isPending}
              onClick={() => sourceToDelete && deleteMutation.mutate(sourceToDelete.id)}
            >
              {deleteMutation.isPending ? <Spinner size="sm" /> : 'Delete Source'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

function SourceForm({ form, setForm }: { form: SourceFormData; setForm: (f: SourceFormData) => void }) {
  const update = (patch: Partial<SourceFormData>) => setForm({ ...form, ...patch })
  return (
    <>
      <div>
        <label className="label">Name <span className="text-red-400">*</span></label>
        <input className="input" value={form.name} onChange={e => update({ name: e.target.value })} required placeholder="e.g. TechCrunch RSS" />
      </div>
      <div>
        <label className="label">Source Type <span className="text-red-400">*</span></label>
        <select className="input" value={form.source_type} onChange={e => update({ source_type: e.target.value })}>
          {SOURCE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>
      <div>
        <label className="label">URL</label>
        <input className="input" type="url" value={form.url} onChange={e => update({ url: e.target.value })} placeholder="https://example.com/feed.rss" />
      </div>
      <div>
        <label className="label">Description</label>
        <textarea className="input resize-none" rows={2} value={form.description} onChange={e => update({ description: e.target.value })} />
      </div>
      <div>
        <label className="label">Fetch Interval (seconds)</label>
        <input className="input" type="number" min={60} value={form.fetch_interval_seconds} onChange={e => update({ fetch_interval_seconds: Number(e.target.value) })} />
      </div>
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => update({ is_active: !form.is_active })}
          className="text-gray-400 hover:text-gray-200 transition-colors"
        >
          {form.is_active ? <ToggleRight className="w-6 h-6 text-green-400" /> : <ToggleLeft className="w-6 h-6" />}
        </button>
        <span className="text-sm text-gray-300">{form.is_active ? 'Active' : 'Inactive'}</span>
      </div>
    </>
  )
}
