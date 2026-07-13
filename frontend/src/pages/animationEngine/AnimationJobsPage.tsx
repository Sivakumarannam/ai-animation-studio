import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Video, RefreshCw, Play, Loader2, Inbox } from 'lucide-react'
import { animationEngineApi, type TriggerSceneAnimationRequest } from '@/api/animationEngine'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Modal } from '@/components/ui/Modal'

function statusColor(status: string) {
  switch (status) {
    case 'completed': return 'text-green-400'
    case 'failed': return 'text-red-400'
    case 'running': return 'text-blue-400'
    case 'pending': return 'text-yellow-400'
    default: return 'text-gray-400'
  }
}

// ─── Generate Modal ───────────────────────────────────────────────────────────

interface NewJobModalProps {
  projectId: string
  open: boolean
  onClose: () => void
  onSuccess: () => void
}

function NewJobModal({ projectId, open, onClose, onSuccess }: NewJobModalProps) {
  const [sceneId, setSceneId] = useState('')
  const [duration, setDuration] = useState('5')
  const [cameraMotion, setCameraMotion] = useState('static')
  const [backgroundKey, setBackgroundKey] = useState('')
  const [error, setError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: () =>
      animationEngineApi.triggerSceneAnimation({
        project_id: projectId,
        scene_id: sceneId.trim(),
        duration_seconds: parseFloat(duration) || 5,
        camera_motion: cameraMotion,
        background_storage_key: backgroundKey.trim(),
      } as TriggerSceneAnimationRequest),
    onSuccess: () => {
      setSceneId(''); setDuration('5'); setCameraMotion('static'); setBackgroundKey(''); setError(null)
      onClose()
      onSuccess()
    },
    onError: (err: Error) => setError(err.message ?? 'Generation failed'),
  })

  function handleClose() {
    if (mutation.isPending) return
    setSceneId(''); setDuration('5'); setCameraMotion('static'); setBackgroundKey(''); setError(null)
    onClose()
  }

  return (
    <Modal title="New Animation Render Job" open={open} onClose={handleClose}>
      <form
        data-testid="new-animation-job-form"
        onSubmit={(e) => { e.preventDefault(); mutation.mutate() }}
        className="space-y-4"
      >
        <div>
          <label className="label">Scene ID <span className="text-red-400">*</span></label>
          <input
            className="input"
            placeholder="UUID of the scene to animate"
            value={sceneId}
            onChange={(e) => setSceneId(e.target.value)}
            required
            disabled={mutation.isPending}
          />
        </div>

        <div>
          <label className="label">Background Storage Key</label>
          <input
            className="input"
            placeholder="Phase 6 generated background image key"
            value={backgroundKey}
            onChange={(e) => setBackgroundKey(e.target.value)}
            disabled={mutation.isPending}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Duration (s)</label>
            <input
              className="input" type="number" min="1" max="60"
              value={duration} onChange={(e) => setDuration(e.target.value)}
              disabled={mutation.isPending}
            />
          </div>
          <div>
            <label className="label">Camera Motion</label>
            <select className="input" value={cameraMotion} onChange={(e) => setCameraMotion(e.target.value)} disabled={mutation.isPending}>
              <option value="static">Static</option>
              <option value="pan_left">Pan Left</option>
              <option value="pan_right">Pan Right</option>
              <option value="zoom_in">Zoom In</option>
              <option value="zoom_out">Zoom Out</option>
            </select>
          </div>
        </div>

        {error && <p className="text-sm text-red-400 bg-red-400/10 rounded p-2">{error}</p>}

        <div className="flex gap-3 pt-2">
          <button type="button" className="btn-secondary flex-1" onClick={handleClose} disabled={mutation.isPending}>
            Cancel
          </button>
          <button
            type="submit"
            className="btn-primary flex-1 flex items-center justify-center gap-2"
            disabled={mutation.isPending || !sceneId.trim()}
            data-testid="submit-new-animation-job"
          >
            {mutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {mutation.isPending ? 'Dispatching…' : 'Start Render'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export function AnimationJobsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [showModal, setShowModal] = useState(false)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['an-jobs', projectId, page, statusFilter],
    queryFn: () =>
      animationEngineApi.listJobs(projectId!, {
        page,
        status: statusFilter || undefined,
      }),
    enabled: !!projectId,
    refetchInterval: 15_000,
  })

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Video className="w-5 h-5 text-brand-400" />
          Render Jobs
        </h1>
        <div className="flex items-center gap-2">
          <select
            className="input text-sm"
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
          <button
            className="btn-secondary p-2"
            onClick={() => refetch()}
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            className="btn-primary flex items-center gap-2"
            onClick={() => setShowModal(true)}
            data-testid="new-animation-job-button"
          >
            <Play className="w-4 h-4" />
            New Render Job
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : !data?.items.length ? (
        <EmptyState
          icon={Inbox}
          title="No render jobs yet"
          description='Click "New Render Job" to start animating a scene.'
          action={
            <button className="btn-primary" onClick={() => setShowModal(true)}>
              New Render Job
            </button>
          }
        />
      ) : (
        <>
          <div className="card divide-y divide-gray-800">
            {data.items.map((job) => (
              <div key={job.id} className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium text-white">{job.job_type}</p>
                    <p className="text-xs text-gray-500 mt-0.5 font-mono">
                      job: {job.id.slice(0, 8)}…
                      {job.scene_id && ` · scene: ${job.scene_id.slice(0, 8)}…`}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className={`text-xs font-semibold ${statusColor(job.status)}`}>
                      {job.status}
                    </span>
                    <span className="text-xs text-gray-600">{job.mode}</span>
                  </div>
                </div>
                {job.error_message && (
                  <p className="text-xs text-red-400 mt-2 bg-red-400/10 rounded p-2 font-mono">
                    {job.error_message}
                  </p>
                )}
                <div className="mt-2 flex gap-4 text-xs text-gray-500">
                  <span>Created: {new Date(job.created_at).toLocaleString()}</span>
                  {job.duration_seconds != null && (
                    <span>Duration: {job.duration_seconds.toFixed(2)}s</span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {data.meta.total_pages > 1 && (
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>Page {page} of {data.meta.total_pages} ({data.meta.total} total)</span>
              <div className="flex gap-2">
                <button className="btn-secondary py-1 px-3" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
                  Prev
                </button>
                <button className="btn-secondary py-1 px-3" onClick={() => setPage(p => p + 1)} disabled={page >= data.meta.total_pages}>
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}

      <NewJobModal
        projectId={projectId!}
        open={showModal}
        onClose={() => setShowModal(false)}
        onSuccess={() => { qc.invalidateQueries({ queryKey: ['an-jobs', projectId] }); qc.invalidateQueries({ queryKey: ['an-dashboard', projectId] }) }}
      />
    </div>
  )
}
