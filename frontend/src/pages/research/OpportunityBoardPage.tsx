import { useQuery } from '@tanstack/react-query'
import { Star } from 'lucide-react'
import { researchApi, ResearchScore } from '@/api/research'
import { Spinner } from '@/components/ui/Spinner'

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
  const { data: scores, isLoading } = useQuery({
    queryKey: ['research-opportunities'],
    queryFn: () => researchApi.getOpportunities(20),
  })

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

              <div className={`text-center text-xs font-medium py-1 rounded ${score.overall_score >= 60 ? 'bg-green-900/40 text-green-300' : 'bg-red-900/40 text-red-300'}`}>
                {score.overall_score >= 60 ? '✓ Queued for Story Intelligence' : '✗ Below quality threshold'}
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
    </div>
  )
}
