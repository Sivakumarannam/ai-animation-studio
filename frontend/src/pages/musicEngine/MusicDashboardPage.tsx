import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Music, Play, CheckCircle, XCircle, Clock, Loader2, BarChart3, Volume2 } from 'lucide-react'
import { musicEngineApi, TriggerMusicTrackRequest } from '@/api/musicEngine'
import { Spinner } from '@/components/ui/Spinner'

const MOODS = ['neutral', 'comedy', 'adventure', 'happy', 'sad', 'tension', 'victory']

function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string
  value: number
  icon: React.ElementType
  color: string
}) {
  return (
    <div className="card p-5 flex items-center gap-4">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{value}</p>
        <p className="text-xs text-gray-500">{label}</p>
      </div>
    </div>
  )
}

function moodColor(mood: string) {
  const map: Record<string, string> = {
    comedy: 'text-yellow-400',
    happy: 'text-green-400',
    adventure: 'text-blue-400',
    victory: 'text-purple-400',
    tension: 'text-red-400',
    sad: 'text-cyan-400',
    neutral: 'text-gray-400',
  }
  return map[mood] ?? 'text-gray-400'
}

function statusColor(status: string) {
  switch (status) {
    case 'completed': return 'text-green-400'
    case 'failed': return 'text-red-400'
    case 'running': return 'text-blue-400'
    case 'pending': return 'text-yellow-400'
    default: return 'text-gray-400'
  }
}

export function MusicDashboardPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const qc = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [mood, setMood] = useState('neutral')
  const [duration, setDuration] = useState(30)
  const [loopType, setLoopType] = useState('looping')
  const [prompt, setPrompt] = useState('')
  const [error, setError] = useState('')

  const { data: stats, isLoading } = useQuery({
    queryKey: ['mu-dashboard', projectId],
    queryFn: () => musicEngineApi.getDashboard(projectId!),
    enabled: !!projectId,
    refetchInterval: 30_000,
  })

  const generateMutation = useMutation({
    mutationFn: (body: TriggerMusicTrackRequest) => musicEngineApi.generateTrack(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['mu-dashboard', projectId] })
      qc.invalidateQueries({ queryKey: ['mu-jobs', projectId] })
      setShowModal(false)
      setPrompt('')
      setError('')
    },
    onError: (e: Error) => setError(e.message),
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

  if (isLoading) {
    return <div className="flex justify-center py-20"><Spinner size="lg" /></div>
  }

  const s = stats!

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Music className="w-5 h-5 text-brand-400" />
          Music & Sound Engine
        </h1>
        <button
          className="btn-primary flex items-center gap-2"
          onClick={() => setShowModal(true)}
        >
          <Play className="w-4 h-4" />
          Generate Music
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        <StatCard label="Total Jobs" value={s.total_jobs} icon={BarChart3} color="bg-brand-600" />
        <StatCard label="Completed" value={s.jobs_completed} icon={CheckCircle} color="bg-green-700" />
        <StatCard label="Running" value={s.jobs_running} icon={Loader2} color="bg-blue-700" />
        <StatCard label="Pending" value={s.jobs_pending} icon={Clock} color="bg-yellow-700" />
        <StatCard label="Failed" value={s.jobs_failed} icon={XCircle} color="bg-red-700" />
        <StatCard label="Music Outputs" value={s.total_music_outputs} icon={Music} color="bg-purple-700" />
        <StatCard label="SFX Library" value={s.total_sfx_assets} icon={Volume2} color="bg-cyan-700" />
        <StatCard label="Retry Queue" value={s.total_retry_queue} icon={Clock} color="bg-orange-700" />
      </div>

      {/* Recent Jobs */}
      <div className="card p-5 space-y-3">
        <h2 className="text-sm font-semibold text-gray-300">Recent Jobs</h2>
        {s.recent_jobs.length === 0 ? (
          <p className="text-sm text-gray-500">No jobs yet — generate your first music track above.</p>
        ) : (
          <div className="divide-y divide-gray-800">
            {s.recent_jobs.map((job) => (
              <div key={job.id} className="py-3 flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-semibold ${statusColor(job.status)}`}>{job.status}</span>
                    <span className={`text-xs font-medium ${moodColor(job.mood)}`}>{job.mood}</span>
                    <span className="text-xs text-gray-600">{job.job_type}</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5 truncate">{job.id}</p>
                </div>
                <span className="text-xs text-gray-600 flex-shrink-0">
                  {new Date(job.created_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Generate Music Modal */}
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
                  <input
                    type="number"
                    className="input w-full text-sm"
                    min={5}
                    max={300}
                    value={duration}
                    onChange={(e) => setDuration(Number(e.target.value))}
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Loop Type</label>
                  <select
                    className="input w-full text-sm"
                    value={loopType}
                    onChange={(e) => setLoopType(e.target.value)}
                  >
                    <option value="looping">Looping</option>
                    <option value="one_shot">One Shot</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs text-gray-400 mb-1 block">Prompt (optional)</label>
                <textarea
                  className="input w-full text-sm resize-none"
                  rows={2}
                  placeholder="e.g. upbeat comedy background with light piano"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                />
              </div>
            </div>

            {error && <p className="text-xs text-red-400 bg-red-400/10 rounded p-2">{error}</p>}

            <div className="flex gap-3 pt-2">
              <button className="btn-secondary flex-1" onClick={() => { setShowModal(false); setError('') }}>
                Cancel
              </button>
              <button
                className="btn-primary flex-1 flex items-center justify-center gap-2"
                onClick={handleGenerate}
                disabled={generateMutation.isPending}
              >
                {generateMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                Generate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
