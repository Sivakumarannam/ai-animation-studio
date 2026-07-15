import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Mic, RefreshCw, Plus, Loader2, Inbox } from 'lucide-react'
import { voiceEngineApi, TriggerVoiceLineRequest } from '@/api/voiceEngine'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'

function statusBadge(status: string) {
  const map: Record<string, string> = {
    completed: 'bg-green-500/20 text-green-400',
    running: 'bg-blue-500/20 text-blue-400',
    pending: 'bg-yellow-500/20 text-yellow-400',
    failed: 'bg-red-500/20 text-red-400',
  }
  return map[status] ?? 'bg-gray-500/20 text-gray-400'
}

export function VoiceJobsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [dialogueLine, setDialogueLine] = useState('')
  const [characterName, setCharacterName] = useState('')
  const [language, setLanguage] = useState('en')
  const [emotion, setEmotion] = useState('neutral')
  const [formError, setFormError] = useState('')

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['vo-jobs', projectId, page, statusFilter],
    queryFn: () =>
      voiceEngineApi.listJobs(projectId!, {
        page,
        status: statusFilter || undefined,
      }),
    enabled: !!projectId,
    refetchInterval: 15_000,
  })

  const generateMutation = useMutation({
    mutationFn: (body: TriggerVoiceLineRequest) => voiceEngineApi.generateLine(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['vo-jobs', projectId] })
      setShowModal(false)
      setDialogueLine('')
      setCharacterName('')
      setFormError('')
    },
    onError: (e: Error) => setFormError(e.message),
  })

  const handleGenerate = () => {
    if (!dialogueLine.trim()) { setFormError('Dialogue line is required'); return }
    generateMutation.mutate({
      project_id: projectId!,
      dialogue_line: dialogueLine,
      character_name: characterName,
      language,
      emotion,
    })
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Mic className="w-5 h-5 text-brand-400" />
          Voice Jobs
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
            New Voice Job
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : !data?.items.length ? (
        <EmptyState
          icon={Inbox}
          title="No voice jobs yet"
          description="Trigger a voice generation to see jobs here."
          action={
            <button className="btn-primary text-sm" onClick={() => setShowModal(true)}>
              Generate Voice
            </button>
          }
        />
      ) : (
        <>
          <div className="card divide-y divide-gray-800">
            {data.items.map((job) => (
              <div key={job.id} className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${statusBadge(job.status)}`}>
                        {job.status}
                      </span>
                      <span className="text-xs text-gray-500">{job.job_type}</span>
                    </div>
                    <p className="text-xs font-mono text-gray-500 mt-1">{job.id}</p>
                    {job.character_id && (
                      <p className="text-xs text-gray-400 mt-0.5">char: {job.character_id}</p>
                    )}
                    {job.error_message && (
                      <p className="text-xs text-red-400 mt-1 bg-red-400/10 rounded p-1.5">
                        {job.error_message}
                      </p>
                    )}
                  </div>
                  <p className="text-xs text-gray-600 flex-shrink-0">
                    {new Date(job.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {data.meta.total_pages > 1 && (
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>Page {page} of {data.meta.total_pages}</span>
              <div className="flex gap-2">
                <button className="btn-secondary py-1 px-3" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>Prev</button>
                <button className="btn-secondary py-1 px-3" onClick={() => setPage(p => p + 1)} disabled={page >= data.meta.total_pages}>Next</button>
              </div>
            </div>
          )}
        </>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="card w-full max-w-md p-6 space-y-4">
            <h2 className="text-lg font-bold text-white">New Voice Job</h2>
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
                <input className="input w-full text-sm" value={characterName} onChange={(e) => setCharacterName(e.target.value)} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Language</label>
                  <select className="input w-full text-sm" value={language} onChange={(e) => setLanguage(e.target.value)}>
                    <option value="en">English</option>
                    <option value="te">Telugu</option>
                    <option value="hi">Hindi</option>
                    <option value="ta">Tamil</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Emotion</label>
                  <select className="input w-full text-sm" value={emotion} onChange={(e) => setEmotion(e.target.value)}>
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
            {formError && <p className="text-xs text-red-400 bg-red-400/10 rounded p-2">{formError}</p>}
            <div className="flex gap-3">
              <button className="btn-secondary flex-1" onClick={() => { setShowModal(false); setFormError('') }}>Cancel</button>
              <button className="btn-primary flex-1 flex items-center justify-center gap-2" onClick={handleGenerate} disabled={generateMutation.isPending}>
                {generateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                Generate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
