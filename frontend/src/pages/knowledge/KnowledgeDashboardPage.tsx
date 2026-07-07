import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ChevronRight, Library, FileText, Layers, Cpu, Brain,
  ListChecks, Sparkles,
} from 'lucide-react'
import { knowledgeApi } from '@/api/knowledge'
import { Spinner } from '@/components/ui/Spinner'
import { Modal } from '@/components/ui/Modal'

export function KnowledgeDashboardPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [collectionType, setCollectionType] = useState('general')

  const { data: stats, isLoading } = useQuery({
    queryKey: ['kn-stats', projectId],
    queryFn: () => knowledgeApi.getStats(projectId!),
    enabled: !!projectId,
    refetchInterval: 10000,
  })

  const createMutation = useMutation({
    mutationFn: () => knowledgeApi.createCollection(projectId!, { name, description, collection_type: collectionType }),
    onSuccess: () => {
      setShowCreate(false)
      setName('')
      setDescription('')
      qc.invalidateQueries({ queryKey: ['kn-stats', projectId] })
      qc.invalidateQueries({ queryKey: ['kn-collections', projectId] })
    },
  })

  if (isLoading) {
    return <div className="flex justify-center py-20"><Spinner size="lg" /></div>
  }

  const jobsByStatus = stats?.jobs_by_status ?? {}
  const runningJobs = jobsByStatus.running ?? 0
  const pendingJobs = jobsByStatus.pending ?? jobsByStatus.queued ?? 0
  const failedJobs = jobsByStatus.failed ?? 0
  const completedJobs = jobsByStatus.completed ?? 0

  const statCards = [
    { label: 'Collections', value: stats?.collections ?? 0, icon: Library, color: 'text-blue-400', to: `/projects/${projectId}/knowledge/collections` },
    { label: 'Documents', value: stats?.documents ?? 0, icon: FileText, color: 'text-green-400', to: `/projects/${projectId}/knowledge/collections` },
    { label: 'Chunks', value: stats?.chunks ?? 0, icon: Layers, color: 'text-purple-400' },
    { label: 'Embedded', value: stats?.embedded_chunks ?? 0, icon: Cpu, color: 'text-cyan-400' },
    { label: 'Memories', value: stats?.memories ?? 0, icon: Brain, color: 'text-yellow-400', to: `/projects/${projectId}/knowledge/memory` },
  ]

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/projects" className="hover:text-gray-300">Projects</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}`} className="hover:text-gray-300">Project</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300">Knowledge</span>
      </div>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Knowledge Intelligence</h1>
          <p className="text-gray-400 text-sm mt-1">RAG-powered knowledge base for AI story generation</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <Library className="w-4 h-4" /> New Collection
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mb-6">
        {statCards.map(({ label, value, icon: Icon, color, to }) => {
          const Card = (
            <div className="card p-4 h-full">
              <Icon className={`w-5 h-5 ${color} mb-2`} />
              <p className="text-2xl font-bold text-white">{value}</p>
              <p className="text-xs text-gray-500">{label}</p>
            </div>
          )
          return to ? <Link key={label} to={to}>{Card}</Link> : <div key={label}>{Card}</div>
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <ListChecks className="w-4 h-4 text-brand-400" />
            <h2 className="text-base font-semibold text-gray-100">Embedding Jobs</h2>
          </div>
          <div className="grid grid-cols-4 gap-3 text-center">
            <div>
              <p className="text-xl font-bold text-blue-400">{pendingJobs}</p>
              <p className="text-xs text-gray-500">Pending</p>
            </div>
            <div>
              <p className="text-xl font-bold text-yellow-400">{runningJobs}</p>
              <p className="text-xs text-gray-500">Running</p>
            </div>
            <div>
              <p className="text-xl font-bold text-green-400">{completedJobs}</p>
              <p className="text-xs text-gray-500">Done</p>
            </div>
            <div>
              <p className="text-xl font-bold text-red-400">{failedJobs}</p>
              <p className="text-xs text-gray-500">Failed</p>
            </div>
          </div>
          <Link to={`/projects/${projectId}/knowledge/jobs`} className="text-xs text-brand-400 hover:text-brand-300 mt-4 inline-block">
            View embedding jobs →
          </Link>
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-4 h-4 text-brand-400" />
            <h2 className="text-base font-semibold text-gray-100">Provider Info</h2>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Embedding Provider</span>
              <span className="text-gray-100 font-mono text-xs bg-gray-800 px-2 py-0.5 rounded">
                {stats?.embedding_provider ?? '—'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Vector Store</span>
              <span className="text-gray-100 font-mono text-xs bg-gray-800 px-2 py-0.5 rounded">
                {stats?.vector_store_provider ?? '—'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Embedding Coverage</span>
              <span className="text-gray-100 text-xs">
                {stats && stats.chunks > 0
                  ? `${Math.round((stats.embedded_chunks / stats.chunks) * 100)}%`
                  : '—'}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Link to={`/projects/${projectId}/knowledge/collections`} className="card p-5 hover:border-gray-700 transition-colors flex items-center gap-4">
          <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center flex-shrink-0">
            <Library className="w-5 h-5 text-brand-400" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-gray-100">Collections</p>
            <p className="text-xs text-gray-500">Manage knowledge collections &amp; documents</p>
          </div>
          <ChevronRight className="w-4 h-4 text-gray-600" />
        </Link>

        <Link to={`/projects/${projectId}/knowledge/memory`} className="card p-5 hover:border-gray-700 transition-colors flex items-center gap-4">
          <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center flex-shrink-0">
            <Brain className="w-5 h-5 text-brand-400" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-gray-100">Knowledge Memory</p>
            <p className="text-xs text-gray-500">Facts, rules &amp; lore for AI context</p>
          </div>
          <ChevronRight className="w-4 h-4 text-gray-600" />
        </Link>

        <Link to={`/projects/${projectId}/knowledge/jobs`} className="card p-5 hover:border-gray-700 transition-colors flex items-center gap-4">
          <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center flex-shrink-0">
            <Cpu className="w-5 h-5 text-brand-400" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-gray-100">Embedding Jobs</p>
            <p className="text-xs text-gray-500">Monitor document processing queue</p>
          </div>
          <ChevronRight className="w-4 h-4 text-gray-600" />
        </Link>
      </div>

      <Modal title="New Knowledge Collection" open={showCreate} onClose={() => setShowCreate(false)}>
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate() }} className="space-y-4">
          <div>
            <label className="label">Name *</label>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g. Story World Lore" />
          </div>
          <div>
            <label className="label">Description</label>
            <textarea className="input resize-none" rows={2} value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What knowledge does this collection contain?" />
          </div>
          <div>
            <label className="label">Type</label>
            <select className="input" value={collectionType} onChange={(e) => setCollectionType(e.target.value)}>
              <option value="general">General</option>
              <option value="character">Character</option>
              <option value="world">World</option>
              <option value="lore">Lore</option>
              <option value="script">Script</option>
            </select>
          </div>
          {createMutation.isError && (
            <p className="text-xs text-red-400">Failed to create collection. Please try again.</p>
          )}
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending || !name.trim()}>
              {createMutation.isPending ? <Spinner size="sm" /> : 'Create'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
