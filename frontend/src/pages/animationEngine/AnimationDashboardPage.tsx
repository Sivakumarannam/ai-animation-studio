import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Film, CheckCircle, Clock, AlertCircle, Zap, RefreshCw, Video, Play, Loader2,
} from 'lucide-react'
import { animationEngineApi, type TriggerSceneAnimationRequest } from '@/api/animationEngine'
import { Spinner } from '@/components/ui/Spinner'
import { Modal } from '@/components/ui/Modal'

function StatCard({ label, value, icon: Icon, color }: {
  label: string; value: number | string; icon: React.ElementType; color: string
}) {
  return (
    <div className="card p-4 flex items-center gap-4">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{value}</p>
        <p className="text-xs text-gray-400">{label}</p>
      </div>
    </div>
  )
}

function statusColor(status: string) {
  switch (status) {
    case 'completed': return 'text-green-400'
    case 'failed': return 'text-red-400'
    case 'running': return 'text-blue-400'
    default: return 'text-gray-400'
  }
}

// ─── Generate Scene Modal ─────────────────────────────────────────────────────

interface GenerateSceneModalProps {
  projectId: string
  open: boolean
  onClose: () => void
  onSuccess: () => void
}

function GenerateSceneModal({ projectId, open, onClose, onSuccess }: GenerateSceneModalProps) {
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
    <Modal title="Generate Animation" open={open} onClose={handleClose}>
      <form
        data-testid="generate-animation-form"
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
          <p className="text-xs text-gray-500 mt-1">
            Use a scene UUID from your project, or leave as-is to test with mock provider
          </p>
        </div>

        <div>
          <label className="label">Background Storage Key</label>
          <input
            className="input"
            placeholder="e.g. assets/project/.../bg.png (from Phase 6)"
            value={backgroundKey}
            onChange={(e) => setBackgroundKey(e.target.value)}
            disabled={mutation.isPending}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Duration (seconds)</label>
            <input
              className="input"
              type="number"
              min="1"
              max="60"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              disabled={mutation.isPending}
            />
          </div>
          <div>
            <label className="label">Camera Motion</label>
            <select
              className="input"
              value={cameraMotion}
              onChange={(e) => setCameraMotion(e.target.value)}
              disabled={mutation.isPending}
            >
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
            data-testid="submit-generate-animation"
          >
            {mutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {mutation.isPending ? 'Dispatching…' : 'Generate Animation'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export function AnimationDashboardPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const qc = useQueryClient()
  const [showModal, setShowModal] = useState(false)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['an-dashboard', projectId],
    queryFn: () => animationEngineApi.getDashboard(projectId!),
    enabled: !!projectId,
    refetchInterval: 30_000,
  })

  const links = [
    { to: 'jobs', label: 'Render Jobs', Icon: Video, color: 'bg-blue-600' },
    { to: 'outputs', label: 'Render Outputs', Icon: Film, color: 'bg-purple-600' },
    { to: 'retry-queue', label: 'Retry Queue', Icon: RefreshCw, color: 'bg-orange-600' },
  ]

  if (isLoading) return <div className="p-8 flex justify-center"><Spinner size="lg" /></div>
  if (isError || !data) return (
    <div className="p-8 text-center text-red-400">Failed to load dashboard.</div>
  )

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Film className="w-6 h-6 text-brand-400" />
            Animation Engine
          </h1>
          <p className="text-gray-400 text-sm mt-1">Phase 7 — Scene compositing and animation rendering</p>
        </div>
        <button
          className="btn-primary flex items-center gap-2"
          onClick={() => setShowModal(true)}
          data-testid="open-generate-animation-modal"
        >
          <Play className="w-4 h-4" />
          Generate Animation
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Jobs" value={data.total_jobs} icon={Video} color="bg-brand-600" />
        <StatCard label="Completed" value={data.jobs_completed} icon={CheckCircle} color="bg-green-600" />
        <StatCard label="Pending" value={data.jobs_pending} icon={Clock} color="bg-yellow-600" />
        <StatCard label="Running" value={data.jobs_running} icon={Zap} color="bg-blue-600" />
        <StatCard label="Failed" value={data.jobs_failed} icon={AlertCircle} color="bg-red-600" />
        <StatCard label="Render Outputs" value={data.total_render_outputs} icon={Film} color="bg-purple-600" />
        <StatCard label="Retry Queue" value={data.total_retry_queue} icon={RefreshCw} color="bg-orange-600" />
      </div>

      {/* Navigation links */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {links.map(({ to, label, Icon, color }) => (
          <Link key={to} to={to} className="card p-4 hover:border-gray-700 transition-colors flex items-center gap-3">
            <div className={`w-8 h-8 ${color} rounded-lg flex items-center justify-center`}>
              <Icon className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm font-medium text-gray-100">{label}</span>
          </Link>
        ))}
      </div>

      {/* Recent Jobs */}
      {data.recent_jobs.length > 0 && (
        <div className="card">
          <div className="p-4 border-b border-gray-800">
            <h2 className="text-sm font-semibold text-gray-200">Recent Jobs</h2>
          </div>
          <div className="divide-y divide-gray-800">
            {data.recent_jobs.map((job) => (
              <div key={job.id} className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-sm text-white font-mono">{job.job_type}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {job.scene_id ? `scene: ${job.scene_id.slice(0, 8)}…` : 'episode'}
                    {' · '}
                    {new Date(job.created_at).toLocaleString()}
                  </p>
                </div>
                <span className={`text-xs font-medium ${statusColor(job.status)}`}>
                  {job.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <GenerateSceneModal
        projectId={projectId!}
        open={showModal}
        onClose={() => setShowModal(false)}
        onSuccess={() => qc.invalidateQueries({ queryKey: ['an-dashboard', projectId] })}
      />
    </div>
  )
}
