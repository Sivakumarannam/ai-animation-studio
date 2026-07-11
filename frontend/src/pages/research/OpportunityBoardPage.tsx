import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Star, Send } from 'lucide-react'
import { researchApi, ResearchScore } from '@/api/research'
import { storyIntelligenceApi } from '@/api/storyIntelligence'
import { projectsApi } from '@/api/projects'
import type { Project } from '@/types'
import { Spinner } from '@/components/ui/Spinner'
import { Modal } from '@/components/ui/Modal'

function ScoreBar({ label, value }: { label: string; value: number }) {
  const color = value >= 80 ? 'bg-green-500' : value >= 60 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-400 w-28 truncate">{label}</span>
      <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${value}%` }} />
      </div>
      <span className="text-xs text-gray-300 w-7 text-right">{value.toFixed(0)}</span>
    </div>
  )
}

export function OpportunityBoardPage() {
  const qc = useQueryClient()
  const [sendModal, setSendModal] = useState<ResearchScore | null>(null)
  const [selectedProjectId, setSelectedProjectId] = useState('')
  const [ideaTitle, setIdeaTitle] = useState('')
  const [sendSuccess, setSendSuccess] = useState(false)

  const { data: scores, isLoading } = useQuery({
    queryKey: ['research-opportunities'],
    queryFn: () => researchApi.getOpportunities(20),
  })

  const { data: projectsData, isLoading: projectsLoading } = useQuery({
    queryKey: ['projects-list'],
    queryFn: () => projectsApi.list(1, 50),
    enabled: !!sendModal,
  })

  const sendMutation = useMutation({
    mutationFn: () =>
      storyIntelligenceApi.createIdea(selectedProjectId, {
        title: ideaTitle,
        premise: `Opportunity from Research Intelligence. Topic ID: ${sendModal?.topic_id}. Overall score: ${sendModal?.overall_score.toFixed(0)}. Trend score: ${sendModal?.trend_score.toFixed(0)}, Research quality: ${sendModal?.research_quality.toFixed(0)}.`,
      }),
    onSuccess: () => {
      setSendSuccess(true)
      qc.invalidateQueries({ queryKey: ['research-opportunities'] })
    },
  })

  function openSend(score: ResearchScore) {
    setSendModal(score)
    setSelectedProjectId('')
    setIdeaTitle(`Research Opportunity — Topic ${score.topic_id.slice(0, 8)}`)
    setSendSuccess(false)
  }

  function closeSend() {
    setSendModal(null)
    setSendSuccess(false)
    sendMutation.reset()
  }

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Star className="w-6 h-6 text-yellow-400" /> Opportunity Board
        </h1>
        <p className="text-gray-400 text-sm mt-1">Top-scored video content opportunities ready for Story Intelligence</p>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {scores?.map((score: ResearchScore) => (
            <div key={score.id} className="card p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-400 font-mono">{score.topic_id.slice(0, 8)}…</p>
                  {score.scored_at && (
                    <p className="text-xs text-gray-500">Scored {new Date(score.scored_at).toLocaleDateString()}</p>
                  )}
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-brand-400">{score.overall_score.toFixed(0)}</p>
                  <p className="text-xs text-gray-400">Overall</p>
                </div>
              </div>

              <div className="space-y-1.5">
                <ScoreBar label="Trend Score" value={score.trend_score} />
                <ScoreBar label="Research Quality" value={score.research_quality} />
                <ScoreBar label="Fact Confidence" value={score.fact_confidence} />
                <ScoreBar label="Audience Fit" value={score.audience_fit} />
                <ScoreBar label="Educational Value" value={score.educational_value} />
                <ScoreBar label="Entertainment" value={score.entertainment_value} />
              </div>

              <div className="flex items-center gap-2">
                <div className={`flex-1 text-center text-xs font-medium py-1 rounded ${score.overall_score >= 60 ? 'bg-green-900/40 text-green-300' : 'bg-red-900/40 text-red-300'}`}>
                  {score.overall_score >= 60 ? '✓ Queued for Story Intelligence' : '✗ Below quality threshold'}
                </div>
                {score.overall_score >= 60 && (
                  <button
                    onClick={() => openSend(score)}
                    className="btn-secondary text-xs flex items-center gap-1 py-1 px-2 flex-shrink-0"
                    title="Send to Story Intelligence"
                  >
                    <Send className="w-3 h-3" /> Send
                  </button>
                )}
              </div>
            </div>
          ))}
          {(!scores || scores.length === 0) && (
            <div className="col-span-2 text-center py-16 text-gray-500">
              No scored opportunities yet. Run the opportunity scoring pipeline from the dashboard.
            </div>
          )}
        </div>
      )}

      <Modal title="Send to Story Intelligence" open={!!sendModal} onClose={closeSend}>
        {sendSuccess ? (
          <div className="py-6 text-center space-y-3">
            <p className="text-green-400 font-medium">✓ Story idea created successfully!</p>
            <p className="text-sm text-gray-400">The idea has been added to your project's Story Intelligence queue.</p>
            <button className="btn-primary" onClick={closeSend}>Done</button>
          </div>
        ) : (
          <form onSubmit={(e) => { e.preventDefault(); sendMutation.mutate() }} className="space-y-4">
            <p className="text-sm text-gray-400">
              This will create a Story Idea in the selected project based on this research opportunity.
            </p>
            <div>
              <label className="label">Idea Title</label>
              <input
                className="input"
                value={ideaTitle}
                onChange={(e) => setIdeaTitle(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="label">Target Project *</label>
              {projectsLoading ? (
                <div className="flex justify-center py-3"><Spinner /></div>
              ) : (
                <select
                  className="input"
                  value={selectedProjectId}
                  onChange={(e) => setSelectedProjectId(e.target.value)}
                  required
                >
                  <option value="">Select a project…</option>
                  {projectsData?.items.map((p: Project) => (
                    <option key={p.id} value={p.id}>{p.title}</option>
                  ))}
                </select>
              )}
            </div>
            {sendMutation.isError && (
              <p className="text-xs text-red-400">Failed to create story idea. Please try again.</p>
            )}
            <div className="flex gap-3 justify-end pt-2">
              <button type="button" className="btn-secondary" onClick={closeSend}>Cancel</button>
              <button
                type="submit"
                className="btn-primary flex items-center gap-2"
                disabled={sendMutation.isPending || !selectedProjectId || !ideaTitle.trim()}
              >
                {sendMutation.isPending ? <Spinner size="sm" /> : <Send className="w-4 h-4" />}
                Send to Story Intelligence
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  )
}
