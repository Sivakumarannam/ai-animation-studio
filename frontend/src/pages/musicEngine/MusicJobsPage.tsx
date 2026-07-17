import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Music, RefreshCw, Plus, Loader2, Inbox, Play } from 'lucide-react'
import { musicEngineApi, TriggerMusicTrackRequest } from '@/api/musicEngine'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'

const MOODS = ['neutral', 'comedy', 'adventure', 'happy', 'sad', 'tension', 'victory']

function statusBadge(status: string) {
  const map: Record<string, string> = {
    completed: 'bg-green-500/20 text-green-400',
    running: 'bg-blue-500/20 text-blue-400',
    pending: 'bg-yellow-500/20 text-yellow-400',
    failed: 'bg-red-500/20 text-red-400',
  }
  return map[status] ?? 'bg-gray-500/20 text-gray-400'
}

function moodBadge(mood: string) {
  const map: Record<string, string> = {
    comedy: 'bg-yellow-500/20 text-yellow-400',
    happy: 'bg-green-500/20 text-green-400',
    adventure: 'bg-blue-500/20 text-blue-400',
    victory: 'bg-purple-500/20 text-purple-400',
    tension: 'bg-red-500/20 text-red-400',
    sad: 'bg-cyan-500/20 text-cyan-400',
    neutral: 'bg-gray-500/20 text-gray-400',
  }
  return map[mood] ?? 'bg-gray-500/20 text-gray-400'
}

export function MusicJobsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [mood, setMood] = useState('neutral')
  const [duration, setDuration] = useState(30)
  const [loopType, setLoopType] = useState('looping')
  const [prompt, setPrompt] = useState('')
  const [formError, setFormError] = useState('')

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['mu-jobs', projectId, page, statusFilter],
    queryFn: () =>
      musicEngineApi.listJobs(projectId!, {
        page,
        status: statusFilter || undefined,
      }),
    enabled: !!projectId,
    refetchInterval: 15_000,
  })

  const generateMutation = useMutation({
    mutationFn: (body: TriggerMusicTrackRequest) => musicEngineApi.generateTrack(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['mu-jobs', projectId] })
      setShowModal(false)
      setPrompt('')
      setFormError('')
    },
    onError: (e: Error) => setFormError(e.message),
  })

  const handleGenerate = () => {
    generateMutation.mutate({
      project_id: projectId!,
      mood,
      duration_seconds: duration,
      loop_type: loopType,
      prompt,
    })
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Music className="w-5 h-5 text-brand-400" />
          Music Jobs
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
          <button className="btn-secondary p-2" onClick={() => refetch()} title="Refresh">
            <RefreshCw className="w-4 h-4" />
          </button>
          <button className="btn-primary flex items-center gap-1 text-sm" onClick={() => setShowModal(true)}>
            <Plus className="w-4 h-4" />
            New Music Job
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : !data?.items.length ? (
        <EmptyState
          icon={Inbox}
          title="No music jobs yet"
          description="Trigger a music generation to see jobs here."
          action={
            <button className="btn-primary text-sm" onClick={() => setShowModal(true)}>
              Generate Music
            </button>
          }
        />
      ) : (
        <>
          <div className="card divide-y divide-gray-800">
            {data.items.map((job) => (
              <div key={job.id} className="p-4">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${statusBadge(job.status)}`}>
                        {job.status}
                      </span>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${moodBadge(job.mood)}`}>
                        {job.mood}
                      </span>
                      <span className="text-xs text-gray-500">{job.job_type}</span>
                    </div>
                    <p className="text-xs text-gray-600 mt-1 truncate font-mono">{job.id}</p>
                    {job.error_message && (
                      <p className="text-xs text-red-400 mt-1 bg-red-400/10 rounded p-1.5">
                        {job.error_message}
                      </p>
                    )}
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-xs text-gray-500">{new Date(job.created_at).toLocaleString()}</p>
                    {job.result && typeof job.result === 'object' && 'duration_seconds' in job.result && (
                      <p className="text-xs text-gray-600 mt-0.5">
                        {String(job.result.duration_seconds)}s
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {data.meta.total_pages > 1 && (
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>Page {page} of {data.meta.total_pages} ({data.meta.total} total)</span>
              <div className="flex gap-2">
                <button className="btn-secondary py-1 px-3" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>Prev</button>
                <button className="btn-secondary py-1 px-3" onClick={() => setPage(p => p + 1)} disabled={page >= data.meta.total_pages}>Next</button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Generate Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-md p-6 space-y-4">
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <Music className="w-4 h-4 text-brand-400" />
              Generate Music Track
            </h2>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Mood</label>
                <div className="flex flex-wrap gap-2">
                  {MOODS.map((m) => (
                    <button
                      key={m}
                      onClick={() => setMood(m)}
                      className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                        mood === m
                          ? 'bg-brand-600 border-brand-500 text-white'
                          : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-500'
                      }`}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Duration (s)</label>
                  <input type="number" className="input w-full text-sm" min={5} max={300} value={duration} onChange={(e) => setDuration(Number(e.target.value))} />
                </div>
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Loop Type</label>
                  <select className="input w-full text-sm" value={loopType} onChange={(e) => setLoopType(e.target.value)}>
                    <option value="looping">Looping</option>
                    <option value="one_shot">One Shot</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Prompt (optional)</label>
                <textarea className="input w-full text-sm resize-none" rows={2} placeholder="e.g. upbeat comedy background" value={prompt} onChange={(e) => setPrompt(e.target.value)} />
              </div>
            </div>

            {formError && <p className="text-xs text-red-400 bg-red-400/10 rounded p-2">{formError}</p>}
            <div className="flex gap-3 pt-2">
              <button className="btn-secondary flex-1" onClick={() => { setShowModal(false); setFormError('') }}>Cancel</button>
              <button className="btn-primary flex-1 flex items-center justify-center gap-2" onClick={handleGenerate} disabled={generateMutation.isPending}>
                {generateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                Generate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
