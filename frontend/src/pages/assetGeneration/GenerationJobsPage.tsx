import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ListChecks, RefreshCw, ChevronRight, Plus, Loader2, Wand2 } from 'lucide-react'
import apiClient from '@/api/client'
import { assetGenerationApi } from '@/api/assetGeneration'
import type { PaginatedResponse } from '@/types'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Modal } from '@/components/ui/Modal'

// ─── Constants ────────────────────────────────────────────────────────────────

const ASSET_TYPES = [
  { value: 'character_reference', label: 'Character Reference' },
  { value: 'background',          label: 'Background' },
  { value: 'prop',                label: 'Prop' },
  { value: 'scene_asset',         label: 'Scene Asset' },
  { value: 'voice_clip',          label: 'Voice Clip' },
]

// ─── Helpers ──────────────────────────────────────────────────────────────────

function statusColor(status: string) {
  switch (status) {
    case 'completed': return 'text-green-400'
    case 'failed':    return 'text-red-400'
    case 'exhausted': return 'text-red-400'
    case 'running':   return 'text-blue-400'
    case 'retrying':  return 'text-orange-400'
    case 'pending':   return 'text-yellow-400'
    default:          return 'text-gray-400'
  }
}

interface Character { id: string; name: string }

// ─── New Generation Modal ─────────────────────────────────────────────────────

interface NewGenerationModalProps {
  projectId: string
  open: boolean
  onClose: () => void
  onSuccess: () => void
}

function NewGenerationModal({ projectId, open, onClose, onSuccess }: NewGenerationModalProps) {
  const [name, setName]           = useState('')
  const [assetType, setAssetType] = useState(ASSET_TYPES[0].value)
  const [characterId, setCharacterId] = useState('')
  const [prompt, setPrompt]       = useState('')
  const [error, setError]         = useState<string | null>(null)

  // Fetch characters for optional selector
  const { data: chars } = useQuery<PaginatedResponse<Character>>({
    queryKey: ['characters', projectId],
    queryFn: () =>
      apiClient
        .get<PaginatedResponse<Character>>(`/projects/${projectId}/characters`)
        .then((r) => r.data),
    enabled: open && !!projectId,
  })

  const mutation = useMutation({
    mutationFn: async () => {
      // Step 1: create the asset record
      const asset = await assetGenerationApi.createAsset({
        project_id: projectId,
        name: name.trim(),
        asset_type: assetType,
        character_id: characterId || null,
        ...(prompt.trim() ? { generation_params: { prompt: prompt.trim() } } : {}),
      })
      // Step 2: trigger generation for the new asset
      return assetGenerationApi.triggerAssetGeneration({
        asset_id: asset.id,
        custom_params: prompt.trim() ? { prompt: prompt.trim() } : undefined,
      })
    },
    onSuccess: () => {
      setName(''); setAssetType(ASSET_TYPES[0].value); setCharacterId(''); setPrompt(''); setError(null)
      onClose()
      onSuccess()
    },
    onError: (err: Error) => setError(err.message ?? 'Generation failed'),
  })

  function handleClose() {
    if (mutation.isPending) return
    setName(''); setAssetType(ASSET_TYPES[0].value); setCharacterId(''); setPrompt(''); setError(null)
    onClose()
  }

  return (
    <Modal title="New Generation Job" open={open} onClose={handleClose}>
      <form
        data-testid="new-generation-form"
        onSubmit={(e) => { e.preventDefault(); mutation.mutate() }}
        className="space-y-4"
      >
        {/* Name */}
        <div>
          <label className="label">Asset Name <span className="text-red-400">*</span></label>
          <input
            className="input"
            placeholder="e.g. Hero character front view"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            disabled={mutation.isPending}
          />
        </div>

        {/* Asset type */}
        <div>
          <label className="label">Asset Type <span className="text-red-400">*</span></label>
          <select
            className="input"
            value={assetType}
            onChange={(e) => setAssetType(e.target.value)}
            disabled={mutation.isPending}
          >
            {ASSET_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        {/* Character (optional) */}
        <div>
          <label className="label">Character <span className="text-gray-500">(optional)</span></label>
          {chars && chars.items.length > 0 ? (
            <select
              className="input"
              value={characterId}
              onChange={(e) => setCharacterId(e.target.value)}
              disabled={mutation.isPending}
              data-testid="character-select"
            >
              <option value="">— None —</option>
              {chars.items.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          ) : (
            <input
              className="input"
              placeholder="Character ID (UUID)"
              value={characterId}
              onChange={(e) => setCharacterId(e.target.value)}
              disabled={mutation.isPending}
              data-testid="character-id-input"
            />
          )}
        </div>

        {/* Prompt / style override */}
        <div>
          <label className="label">Prompt / Style Override <span className="text-gray-500">(optional)</span></label>
          <textarea
            className="input resize-none"
            rows={3}
            placeholder="Custom generation instructions, style notes, etc."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={mutation.isPending}
          />
        </div>

        {error && <p className="text-xs text-red-400">{error}</p>}

        <div className="flex gap-3 justify-end pt-2">
          <button
            type="button"
            className="btn-secondary"
            onClick={handleClose}
            disabled={mutation.isPending}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn-primary flex items-center gap-1.5"
            disabled={mutation.isPending || !name.trim()}
            data-testid="submit-generation"
          >
            {mutation.isPending
              ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Queuing…</>
              : <><Wand2 className="w-3.5 h-3.5" /> Generate</>
            }
          </button>
        </div>
      </form>
    </Modal>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function GenerationJobsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const qc = useQueryClient()
  const [tab, setTab]           = useState<'jobs' | 'retry'>('jobs')
  const [jobPage, setJobPage]   = useState(1)
  const [retryPage, setRetryPage] = useState(1)
  const [jobStatus, setJobStatus] = useState('')
  const [showNewGen, setShowNewGen] = useState(false)

  const { data: jobs, isLoading: jobsLoading } = useQuery({
    queryKey: ['ag-jobs', projectId, jobPage, jobStatus],
    queryFn: () => assetGenerationApi.listJobs(projectId!, { page: jobPage, page_size: 20, status: jobStatus || undefined }),
    enabled: !!projectId && tab === 'jobs',
  })

  const { data: retryQueue, isLoading: retryLoading } = useQuery({
    queryKey: ['ag-retry-queue', projectId, retryPage],
    queryFn: () => assetGenerationApi.listRetryQueue(projectId!, { page: retryPage, page_size: 20 }),
    enabled: !!projectId && tab === 'retry',
  })

  const retryMutation = useMutation({
    mutationFn: (entryId: string) => assetGenerationApi.retryEntry(entryId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ag-retry-queue', projectId] }),
  })

  function handleGenerationSuccess() {
    qc.invalidateQueries({ queryKey: ['ag-jobs', projectId] })
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
        <span>Asset Generation</span>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300">Generation Jobs</span>
      </div>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <ListChecks className="w-6 h-6 text-blue-400" />
          Generation Jobs
        </h1>
        <button
          onClick={() => setShowNewGen(true)}
          className="btn-primary flex items-center gap-1.5 text-sm"
          data-testid="new-generation-btn"
        >
          <Plus className="w-4 h-4" />
          New Generation
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-gray-900 rounded-lg w-fit">
        <button
          onClick={() => setTab('jobs')}
          className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${tab === 'jobs' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-gray-200'}`}
        >
          Jobs
        </button>
        <button
          onClick={() => setTab('retry')}
          className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${tab === 'retry' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-gray-200'}`}
        >
          Retry Queue
        </button>
      </div>

      {tab === 'jobs' && (
        <>
          <div className="flex gap-3">
            <select
              value={jobStatus}
              onChange={(e) => { setJobStatus(e.target.value); setJobPage(1) }}
              className="input text-sm py-1.5"
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="running">Running</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
          </div>

          {jobsLoading ? (
            <div className="flex justify-center py-20"><Spinner size="lg" /></div>
          ) : jobs?.items.length === 0 ? (
            <EmptyState
              icon={ListChecks}
              title="No jobs found"
              description="Use New Generation above to queue your first asset."
              action={
                <button onClick={() => setShowNewGen(true)} className="btn-primary">
                  <Plus className="w-4 h-4" /> New Generation
                </button>
              }
            />
          ) : (
            <>
              <div className="space-y-2">
                {jobs?.items.map((job) => (
                  <div key={job.id} className="card p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium text-white">{job.job_type}</span>
                          <span className={`text-xs font-semibold ${statusColor(job.status)}`}>{job.status}</span>
                        </div>
                        <p className="text-xs text-gray-500">ID: {job.id.slice(0, 16)}…</p>
                        {job.error_message && (
                          <p className="text-xs text-red-400 mt-1 truncate">{job.error_message}</p>
                        )}
                      </div>
                      <div className="text-right flex-shrink-0 text-xs text-gray-400">
                        {job.duration_ms > 0 && <p>{(job.duration_ms / 1000).toFixed(1)}s</p>}
                        <p>{new Date(job.created_at).toLocaleString()}</p>
                        <p className="text-gray-600">{job.dispatch_mode}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              {jobs && jobs.meta.total_pages > 1 && (
                <div className="flex justify-center gap-2">
                  <button disabled={jobPage <= 1} onClick={() => setJobPage(p => p - 1)} className="btn-secondary text-sm px-3 py-1">Prev</button>
                  <span className="text-sm text-gray-400 self-center">Page {jobPage} / {jobs.meta.total_pages}</span>
                  <button disabled={jobPage >= jobs.meta.total_pages} onClick={() => setJobPage(p => p + 1)} className="btn-secondary text-sm px-3 py-1">Next</button>
                </div>
              )}
            </>
          )}
        </>
      )}

      {tab === 'retry' && (
        <>
          {retryLoading ? (
            <div className="flex justify-center py-20"><Spinner size="lg" /></div>
          ) : retryQueue?.items.length === 0 ? (
            <EmptyState icon={RefreshCw} title="Retry queue is empty" description="Failed assets that need retrying appear here." />
          ) : (
            <>
              <div className="space-y-2">
                {retryQueue?.items.map((entry) => (
                  <div key={entry.id} className="card p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`text-xs font-semibold ${statusColor(entry.status)}`}>{entry.status}</span>
                          <span className="text-xs text-gray-500">priority {entry.priority}</span>
                        </div>
                        <p className="text-xs text-gray-400">{entry.failure_reason}</p>
                        {entry.failure_details && (
                          <p className="text-xs text-gray-500 truncate mt-1">{entry.failure_details}</p>
                        )}
                        <p className="text-xs text-gray-600 mt-1">
                          Retried {entry.retry_count}/{entry.max_retries} times
                        </p>
                      </div>
                      <div className="flex-shrink-0 flex flex-col items-end gap-1">
                        <button
                          onClick={() => retryMutation.mutate(entry.id)}
                          disabled={retryMutation.isPending || entry.status === 'exhausted'}
                          title={entry.status === 'exhausted' ? 'Max retries reached' : undefined}
                          className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1 disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                          {retryMutation.isPending ? <Spinner size="sm" /> : <RefreshCw className="w-3 h-3" />}
                          Retry
                        </button>
                        {entry.status === 'exhausted' && (
                          <span className="text-[10px] text-red-400">Max retries reached</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              {retryQueue && retryQueue.meta.total_pages > 1 && (
                <div className="flex justify-center gap-2">
                  <button disabled={retryPage <= 1} onClick={() => setRetryPage(p => p - 1)} className="btn-secondary text-sm px-3 py-1">Prev</button>
                  <span className="text-sm text-gray-400 self-center">Page {retryPage} / {retryQueue.meta.total_pages}</span>
                  <button disabled={retryPage >= retryQueue.meta.total_pages} onClick={() => setRetryPage(p => p + 1)} className="btn-secondary text-sm px-3 py-1">Next</button>
                </div>
              )}
            </>
          )}
        </>
      )}

      {/* New Generation modal */}
      {projectId && (
        <NewGenerationModal
          projectId={projectId}
          open={showNewGen}
          onClose={() => setShowNewGen(false)}
          onSuccess={handleGenerationSuccess}
        />
      )}
    </div>
  )
}
