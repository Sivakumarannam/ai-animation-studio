import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Mic, Play, CheckCircle, XCircle, Clock, Loader2, BarChart3, RefreshCw } from 'lucide-react'
import { voiceEngineApi, TriggerVoiceLineRequest } from '@/api/voiceEngine'
import { Spinner } from '@/components/ui/Spinner'

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

function statusColor(status: string) {
  switch (status) {
    case 'completed': return 'text-green-400'
    case 'failed': return 'text-red-400'
    case 'running': return 'text-blue-400'
    case 'pending': return 'text-yellow-400'
    default: return 'text-gray-400'
  }
}

export function VoiceDashboardPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const qc = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [dialogueLine, setDialogueLine] = useState('')
  const [characterName, setCharacterName] = useState('')
  const [language, setLanguage] = useState('en')
  const [emotion, setEmotion] = useState('neutral')
  const [error, setError] = useState('')

  const { data: stats, isLoading } = useQuery({
    queryKey: ['vo-dashboard', projectId],
    queryFn: () => voiceEngineApi.getDashboard(projectId!),
    enabled: !!projectId,
    refetchInterval: 30_000,
  })

  const generateMutation = useMutation({
    mutationFn: (body: TriggerVoiceLineRequest) => voiceEngineApi.generateLine(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['vo-dashboard', projectId] })
      qc.invalidateQueries({ queryKey: ['vo-jobs', projectId] })
      setShowModal(false)
      setDialogueLine('')
      setCharacterName('')
      setError('')
    },
    onError: (e: Error) => setError(e.message),
  })

  const handleGenerate = () => {
    if (!dialogueLine.trim()) {
      setError('Dialogue line is required')
      return
    }
    generateMutation.mutate({
      project_id: projectId!,
      dialogue_line: dialogueLine,
      character_name: characterName,
      language,
      emotion,
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
          <Mic className="w-5 h-5 text-brand-400" />
          Voice Engine
        </h1>
        <button
          className="btn-primary flex items-center gap-2"
          onClick={() => setShowModal(true)}
        >
          <Play className="w-4 h-4" />
          Generate Voice
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard label="Total Jobs" value={s.total_jobs} icon={BarChart3} color="bg-brand-600" />
        <StatCard label="Completed" value={s.jobs_completed} icon={CheckCircle} color="bg-green-700" />
        <StatCard label="Running" value={s.jobs_running} icon={Loader2} color="bg-blue-700" />
        <StatCard label="Pending" value={s.jobs_pending} icon={Clock} color="bg-yellow-700" />
        <StatCard label="Failed" value={s.jobs_failed} icon={XCircle} color="bg-red-700" />
        <StatCard label="Audio Clips" value={s.total_voice_outputs} icon={Mic} color="bg-purple-700" />
      </div>

      {/* Recent jobs */}
      {s.recent_jobs.length > 0 && (
        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <RefreshCw className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-semibold text-gray-300">Recent Jobs</span>
          </div>
          <div className="divide-y divide-gray-800">
            {s.recent_jobs.map((job) => (
              <div key={job.id} className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-xs font-mono text-gray-400">{job.id.slice(0, 8)}…</p>
                  <p className="text-xs text-gray-600">{job.job_type}</p>
                </div>
                <span className={`text-xs font-semibold ${statusColor(job.status)}`}>
                  {job.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Generate Voice Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="card w-full max-w-md p-6 space-y-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Mic className="w-4 h-4 text-brand-400" />
              Generate Voice
            </h2>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Dialogue Line *</label>
                <textarea
                  className="input w-full h-20 resize-none text-sm"
                  placeholder="Enter the line to be spoken…"
                  value={dialogueLine}
                  onChange={(e) => setDialogueLine(e.target.value)}
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Character Name</label>
                <input
                  className="input w-full text-sm"
                  placeholder="e.g. Narrator, Hero…"
                  value={characterName}
                  onChange={(e) => setCharacterName(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Language</label>
                  <select
                    className="input w-full text-sm"
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                  >
                    <option value="en">English</option>
                    <option value="te">Telugu</option>
                    <option value="hi">Hindi</option>
                    <option value="ta">Tamil</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Emotion</label>
                  <select
                    className="input w-full text-sm"
                    value={emotion}
                    onChange={(e) => setEmotion(e.target.value)}
                  >
                    <option value="neutral">Neutral</option>
                    <option value="happy">Happy</option>
                    <option value="sad">Sad</option>
                    <option value="angry">Angry</option>
                    <option value="fearful">Fearful</option>
                    <option value="surprised">Surprised</option>
                  </select>
                </div>
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
