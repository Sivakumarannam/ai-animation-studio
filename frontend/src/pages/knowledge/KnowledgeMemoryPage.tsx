import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ChevronRight, Brain, Plus, Trash2 } from 'lucide-react'
import { knowledgeApi } from '@/api/knowledge'
import { Spinner } from '@/components/ui/Spinner'
import { Modal } from '@/components/ui/Modal'

const MEMORY_TYPES = ['fact', 'rule', 'lore', 'preference', 'constraint']

export function KnowledgeMemoryPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [memoryType, setMemoryType] = useState('fact')
  const [key, setKey] = useState('')
  const [valueText, setValueText] = useState('')
  const [filterType, setFilterType] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['kn-memory', projectId, page, filterType],
    queryFn: () => knowledgeApi.listMemory(projectId!, page, 20, filterType || undefined),
    enabled: !!projectId,
  })

  const createMutation = useMutation({
    mutationFn: () => {
      let parsed: Record<string, unknown> = {}
      try { parsed = JSON.parse(valueText || '{}') } catch { parsed = { text: valueText } }
      return knowledgeApi.createMemory(projectId!, { memory_type: memoryType, key, value: parsed })
    },
    onSuccess: () => {
      setShowCreate(false)
      setKey('')
      setValueText('')
      qc.invalidateQueries({ queryKey: ['kn-memory', projectId] })
      qc.invalidateQueries({ queryKey: ['kn-stats', projectId] })
    },
  })

  const deactivateMutation = useMutation({
    mutationFn: (id: string) => knowledgeApi.deactivateMemory(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['kn-memory', projectId] }),
  })

  const memories = data?.items ?? []
  const meta = data?.meta

  const typeColor: Record<string, string> = {
    fact: 'text-blue-400 bg-blue-900/30',
    rule: 'text-red-400 bg-red-900/30',
    lore: 'text-purple-400 bg-purple-900/30',
    preference: 'text-green-400 bg-green-900/30',
    constraint: 'text-orange-400 bg-orange-900/30',
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/projects" className="hover:text-gray-300">Projects</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}`} className="hover:text-gray-300">Project</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}/knowledge`} className="hover:text-gray-300">Knowledge</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300">Memory</span>
      </div>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Knowledge Memory</h1>
          <p className="text-gray-400 text-sm mt-1">Facts, rules, lore, and constraints for AI story generation</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <Plus className="w-4 h-4" /> Add Memory
        </button>
      </div>

      <div className="flex items-center gap-2 mb-6 flex-wrap">
        <span className="text-xs text-gray-500">Filter:</span>
        <button
          onClick={() => { setFilterType(''); setPage(1) }}
          className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
            filterType === '' ? 'bg-brand-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
          }`}
        >All</button>
        {MEMORY_TYPES.map((t) => (
          <button
            key={t}
            onClick={() => { setFilterType(t); setPage(1) }}
            className={`px-2.5 py-1 rounded text-xs font-medium capitalize transition-colors ${
              filterType === t ? 'bg-brand-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >{t}</button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : memories.length === 0 ? (
        <div className="card p-12 text-center">
          <Brain className="w-12 h-12 text-gray-600 mx-auto mb-3" />
          <p className="text-gray-400 font-medium">No memory entries</p>
          <p className="text-gray-600 text-sm mt-1 mb-4">Add facts, rules, and lore to guide AI generation.</p>
          <button onClick={() => setShowCreate(true)} className="btn-primary">
            <Plus className="w-4 h-4" /> Add Memory
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {memories.map((m) => (
            <div key={m.id} className={`card p-4 flex items-start gap-4 ${!m.is_active ? 'opacity-50' : ''}`}>
              <span className={`text-xs font-medium px-2 py-0.5 rounded capitalize flex-shrink-0 mt-0.5 ${typeColor[m.memory_type] ?? 'text-gray-400 bg-gray-800'}`}>
                {m.memory_type}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-100">{m.key}</p>
                <p className="text-xs text-gray-400 mt-1 font-mono break-all">
                  {typeof m.value === 'object' ? JSON.stringify(m.value) : String(m.value)}
                </p>
                <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-600">
                  <span>Confidence: {Math.round(m.confidence * 100)}%</span>
                  {m.world_id && <span>World scoped</span>}
                  {m.collection_id && <span>Collection scoped</span>}
                  <span>{new Date(m.created_at).toLocaleDateString()}</span>
                </div>
              </div>
              {m.is_active && (
                <button
                  onClick={() => deactivateMutation.mutate(m.id)}
                  className="text-gray-600 hover:text-red-400 flex-shrink-0"
                  title="Deactivate"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {meta && meta.total_pages > 1 && (
        <div className="flex items-center justify-center gap-3 mt-6">
          <button className="btn-secondary text-xs" disabled={page <= 1} onClick={() => setPage(page - 1)}>← Prev</button>
          <span className="text-xs text-gray-500">Page {meta.page} of {meta.total_pages}</span>
          <button className="btn-secondary text-xs" disabled={page >= meta.total_pages} onClick={() => setPage(page + 1)}>Next →</button>
        </div>
      )}

      <Modal title="Add Knowledge Memory" open={showCreate} onClose={() => setShowCreate(false)}>
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate() }} className="space-y-4">
          <div>
            <label className="label">Type</label>
            <select className="input" value={memoryType} onChange={(e) => setMemoryType(e.target.value)}>
              {MEMORY_TYPES.map((t) => <option key={t} value={t} className="capitalize">{t}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Key *</label>
            <input className="input" value={key} onChange={(e) => setKey(e.target.value)} required placeholder="e.g. hero_name, no_magic_rule" />
          </div>
          <div>
            <label className="label">Value</label>
            <textarea
              className="input resize-none font-mono text-xs"
              rows={3}
              value={valueText}
              onChange={(e) => setValueText(e.target.value)}
              placeholder='{"text": "value"} or plain text'
            />
            <p className="text-xs text-gray-600 mt-1">JSON object or plain text. Plain text will be wrapped automatically.</p>
          </div>
          {createMutation.isError && (
            <p className="text-xs text-red-400">Failed to add memory entry.</p>
          )}
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending || !key.trim()}>
              {createMutation.isPending ? <Spinner size="sm" /> : 'Add Memory'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
