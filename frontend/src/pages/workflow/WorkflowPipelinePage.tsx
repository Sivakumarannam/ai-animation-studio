import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  GitBranch, Play, Pause, RotateCcw, XCircle, Trash2,
  CheckCircle2, AlertCircle, Clock, Loader2, ChevronRight,
} from 'lucide-react'
import {
  workflowApi,
  PIPELINE_STEPS,
  WorkflowRun,
  WorkflowStartRequest,
} from '@/api/workflow'
import { Spinner } from '@/components/ui/Spinner'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function stateColor(state: string) {
  switch (state) {
    case 'running':   return 'text-blue-400'
    case 'paused':    return 'text-yellow-400'
    case 'completed': return 'text-green-400'
    case 'failed':    return 'text-red-400'
    case 'cancelled': return 'text-gray-500'
    default:          return 'text-gray-400'
  }
}

function stateBg(state: string) {
  switch (state) {
    case 'running':   return 'bg-blue-900/30 border-blue-700'
    case 'paused':    return 'bg-yellow-900/20 border-yellow-700'
    case 'completed': return 'bg-green-900/20 border-green-700'
    case 'failed':    return 'bg-red-900/20 border-red-700'
    case 'cancelled': return 'bg-gray-800 border-gray-700'
    default:          return 'bg-gray-800/60 border-gray-700'
  }
}

function stepStatus(run: WorkflowRun, stepName: string): 'done' | 'failed' | 'active' | 'pending' {
  if (run.completed_steps.includes(stepName)) return 'done'
  if (run.failed_steps.includes(stepName)) return 'failed'
  if (run.current_step === stepName && run.state === 'running') return 'active'
  return 'pending'
}

// ─── Step badge ───────────────────────────────────────────────────────────────

function StepBadge({ status, label }: { status: 'done' | 'failed' | 'active' | 'pending'; label: string }) {
  const icon = {
    done:    <CheckCircle2 className="w-4 h-4 text-green-400" />,
    failed:  <AlertCircle className="w-4 h-4 text-red-400" />,
    active:  <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />,
    pending: <Clock className="w-4 h-4 text-gray-600" />,
  }[status]

  const textColor = {
    done:    'text-green-300',
    failed:  'text-red-300',
    active:  'text-blue-300',
    pending: 'text-gray-500',
  }[status]

  return (
    <div className="flex items-center gap-2">
      {icon}
      <span className={`text-xs font-medium ${textColor}`}>{label}</span>
    </div>
  )
}

// ─── Run card ─────────────────────────────────────────────────────────────────

function RunCard({
  run,
  onPause,
  onResume,
  onCancel,
  onDelete,
  busy,
}: {
  run: WorkflowRun
  onPause: () => void
  onResume: () => void
  onCancel: () => void
  onDelete: () => void
  busy: boolean
}) {
  const isActive = run.state === 'running' || run.state === 'paused'
  const isTerminal = ['completed', 'cancelled', 'failed'].includes(run.state)

  return (
    <div className={`card border rounded-lg p-5 space-y-4 ${stateBg(run.state)}`}>
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs font-mono text-gray-500 truncate">{run.run_id}</p>
          <p className="text-sm text-gray-400 mt-0.5">
            Story: <span className="text-gray-300 font-mono text-xs">{run.story_id}</span>
          </p>
        </div>
        <span className={`shrink-0 text-sm font-semibold uppercase tracking-wide ${stateColor(run.state)}`}>
          {run.state}
        </span>
      </div>

      {/* Progress bar */}
      <div>
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>{run.progress_message || 'Waiting…'}</span>
          <span>{Math.round(run.progress_percent)}%</span>
        </div>
        <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-brand-500 rounded-full transition-all duration-500"
            style={{ width: `${run.progress_percent}%` }}
          />
        </div>
      </div>

      {/* Step pipeline */}
      <div className="flex flex-wrap gap-3">
        {PIPELINE_STEPS.map((step, i) => (
          <div key={step.name} className="flex items-center gap-1.5">
            <StepBadge status={stepStatus(run, step.name)} label={step.label} />
            {i < PIPELINE_STEPS.length - 1 && (
              <ChevronRight className="w-3 h-3 text-gray-700 shrink-0" />
            )}
          </div>
        ))}
      </div>

      {/* Error detail */}
      {Object.keys(run.errors).length > 0 && (
        <div className="rounded bg-red-950/40 border border-red-900 p-3 text-xs text-red-300 font-mono space-y-1">
          {Object.entries(run.errors).map(([step, err]) => (
            <div key={step}><span className="font-semibold">{step}:</span> {err}</div>
          ))}
        </div>
      )}

      {/* Timestamps */}
      <div className="flex gap-4 text-xs text-gray-600">
        <span>Started: {new Date(run.created_at).toLocaleString()}</span>
        <span>Updated: {new Date(run.updated_at).toLocaleString()}</span>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 flex-wrap">
        {run.state === 'running' && (
          <button
            onClick={onPause}
            disabled={busy}
            className="btn-secondary flex items-center gap-1.5 text-xs"
          >
            <Pause className="w-3.5 h-3.5" /> Pause
          </button>
        )}
        {(run.state === 'paused' || run.state === 'failed') && (
          <button
            onClick={onResume}
            disabled={busy}
            className="btn-primary flex items-center gap-1.5 text-xs"
          >
            <RotateCcw className="w-3.5 h-3.5" /> Resume
          </button>
        )}
        {isActive && (
          <button
            onClick={onCancel}
            disabled={busy}
            className="btn-secondary flex items-center gap-1.5 text-xs text-red-400 hover:text-red-300"
          >
            <XCircle className="w-3.5 h-3.5" /> Cancel
          </button>
        )}
        {isTerminal && (
          <button
            onClick={onDelete}
            disabled={busy}
            className="btn-secondary flex items-center gap-1.5 text-xs text-gray-400 hover:text-red-400"
          >
            <Trash2 className="w-3.5 h-3.5" /> Delete
          </button>
        )}
      </div>
    </div>
  )
}

// ─── Start form ───────────────────────────────────────────────────────────────

function StartRunForm({ projectId, onStarted }: { projectId: string; onStarted: () => void }) {
  const [storyId, setStoryId] = useState('')
  const [pluginId, setPluginId] = useState('default')
  const qc = useQueryClient()

  const startMutation = useMutation({
    mutationFn: (body: WorkflowStartRequest) => workflowApi.startRun(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['workflow-runs', projectId] })
      setStoryId('')
      onStarted()
    },
  })

  return (
    <div className="card p-4 space-y-3">
      <h3 className="text-sm font-semibold text-white">Start New Pipeline Run</h3>
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Story ID (UUID)"
          value={storyId}
          onChange={e => setStoryId(e.target.value)}
          className="input flex-1 text-sm"
        />
        <input
          type="text"
          placeholder="Plugin ID"
          value={pluginId}
          onChange={e => setPluginId(e.target.value)}
          className="input w-32 text-sm"
        />
        <button
          onClick={() =>
            startMutation.mutate({ story_id: storyId, project_id: projectId, plugin_id: pluginId })
          }
          disabled={!storyId.trim() || startMutation.isPending}
          className="btn-primary flex items-center gap-1.5 text-sm whitespace-nowrap"
        >
          {startMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4" />
          )}
          Start
        </button>
      </div>
      {startMutation.isError && (
        <p className="text-xs text-red-400">Failed to start run. Check the Story ID.</p>
      )}
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function WorkflowPipelinePage() {
  const { projectId } = useParams<{ projectId: string }>()
  const qc = useQueryClient()
  const [busyRunId, setBusyRunId] = useState<string | null>(null)

  const { data: runs = [], isLoading, isError } = useQuery({
    queryKey: ['workflow-runs', projectId],
    queryFn: () => workflowApi.listRuns(projectId),
    enabled: !!projectId,
    // Poll every 3 s when there are active runs
    refetchInterval: (data) => {
      const active = (data?.state?.data ?? []).some(
        (r: WorkflowRun) => r.state === 'running' || r.state === 'pending'
      )
      return active ? 3000 : 15000
    },
  })

  const makeMutation = (fn: (runId: string) => Promise<unknown>) =>
    useMutation({
      mutationFn: async (runId: string) => {
        setBusyRunId(runId)
        return fn(runId)
      },
      onSettled: () => {
        setBusyRunId(null)
        qc.invalidateQueries({ queryKey: ['workflow-runs', projectId] })
      },
    })

  const pauseMutation  = makeMutation(workflowApi.pause)
  const resumeMutation = makeMutation(workflowApi.resume)
  const cancelMutation = makeMutation(workflowApi.cancel)
  const deleteMutation = makeMutation(workflowApi.deleteRun)

  const activeCount = runs.filter(r => r.state === 'running' || r.state === 'pending').length

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
          <Link to={`/projects/${projectId}`} className="hover:text-gray-300">Project</Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <span className="text-gray-300">Automation Pipeline</span>
        </div>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <GitBranch className="w-6 h-6 text-brand-400" />
            Automation Pipeline
          </h1>
          {activeCount > 0 && (
            <span className="text-xs bg-blue-900/40 border border-blue-700 text-blue-300 px-2 py-0.5 rounded-full">
              {activeCount} active
            </span>
          )}
        </div>
        <p className="text-gray-400 text-sm mt-1">
          7-step generation pipeline: Story → Scenes → Characters → Assets → Voice → Subtitles → Video
        </p>
      </div>

      {/* Pipeline step legend */}
      <div className="card p-4">
        <p className="text-xs text-gray-500 mb-3 font-medium uppercase tracking-wide">Pipeline Stages</p>
        <div className="flex flex-wrap items-center gap-2">
          {PIPELINE_STEPS.map((step, i) => (
            <div key={step.name} className="flex items-center gap-1.5">
              <span className="text-xs text-gray-400 bg-gray-800 px-2 py-0.5 rounded">
                {step.label}
              </span>
              {i < PIPELINE_STEPS.length - 1 && (
                <ChevronRight className="w-3.5 h-3.5 text-gray-600" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Start form */}
      {projectId && (
        <StartRunForm
          projectId={projectId}
          onStarted={() => qc.invalidateQueries({ queryKey: ['workflow-runs', projectId] })}
        />
      )}

      {/* Run list */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      )}

      {isError && (
        <div className="card p-6 text-center text-red-400">
          Failed to load pipeline runs.
        </div>
      )}

      {!isLoading && !isError && runs.length === 0 && (
        <div className="card p-10 text-center text-gray-500">
          <GitBranch className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p className="text-sm">No pipeline runs yet. Start one above.</p>
        </div>
      )}

      {runs.length > 0 && (
        <div className="space-y-4">
          <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">
            {runs.length} run{runs.length !== 1 ? 's' : ''}
          </p>
          {runs.map(run => (
            <RunCard
              key={run.run_id}
              run={run}
              busy={busyRunId === run.run_id}
              onPause={() => pauseMutation.mutate(run.run_id)}
              onResume={() => resumeMutation.mutate(run.run_id)}
              onCancel={() => cancelMutation.mutate(run.run_id)}
              onDelete={() => deleteMutation.mutate(run.run_id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
