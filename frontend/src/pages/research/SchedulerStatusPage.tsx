import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Calendar, Play, RefreshCw } from 'lucide-react'
import { researchApi } from '@/api/research'
import { Spinner } from '@/components/ui/Spinner'

const PHASES = [
  { key: 'trend_discovery', label: 'Trend Discovery', description: 'Discover trending topics from RSS, Wikipedia, YouTube, and other open sources', interval: 'Every hour' },
  { key: 'research_refresh', label: 'Research Refresh', description: 'Research pending topics, extract facts, entities, and verify claims', interval: 'Every 6 hours' },
  { key: 'opportunity_report', label: 'Opportunity Report', description: 'Score opportunities and queue top topics for Story Intelligence', interval: 'Every day' },
]

export function SchedulerStatusPage() {
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['scheduler-status'],
    queryFn: researchApi.getSchedulerStatus,
    refetchInterval: 30_000,
  })

  const trigger = useMutation({
    mutationFn: (phase: string) => researchApi.triggerScheduler(phase),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['scheduler-status'] })
      qc.invalidateQueries({ queryKey: ['research-history'] })
    },
  })

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Calendar className="w-6 h-6 text-indigo-400" /> Scheduler Status
          </h1>
          <p className="text-gray-400 text-sm mt-1">Automated research pipeline schedule and controls</p>
        </div>
        <button
          onClick={() => trigger.mutate('full')}
          disabled={trigger.isPending}
          className="btn-primary text-sm flex items-center gap-2"
        >
          {trigger.isPending ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          Run Full Pipeline
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : (
        <div className="space-y-4">
          {PHASES.map(phase => {
            const info = data?.phases?.[phase.key]
            const status = info?.last_status || 'never_run'
            const statusColor = status === 'completed' ? 'text-green-400' : status === 'failed' ? 'text-red-400' : 'text-gray-500'

            return (
              <div key={phase.key} className="card p-5 space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="font-semibold text-white">{phase.label}</h2>
                    <p className="text-sm text-gray-400 mt-1">{phase.description}</p>
                    <p className="text-xs text-gray-500 mt-1">Schedule: {phase.interval}</p>
                  </div>
                  <button
                    onClick={() => trigger.mutate(phase.key)}
                    disabled={trigger.isPending}
                    className="btn-secondary text-xs flex items-center gap-1 flex-shrink-0"
                  >
                    <Play className="w-3 h-3" /> Run Now
                  </button>
                </div>

                <div className="flex items-center gap-6 text-sm border-t border-gray-800 pt-3">
                  <div>
                    <p className="text-xs text-gray-500">Last Status</p>
                    <p className={`font-medium ${statusColor}`}>{status.replace(/_/g, ' ')}</p>
                  </div>
                  {info?.last_run_at && (
                    <div>
                      <p className="text-xs text-gray-500">Last Run</p>
                      <p className="text-gray-300">{new Date(info.last_run_at).toLocaleString()}</p>
                    </div>
                  )}
                  {info?.last_duration_seconds != null && (
                    <div>
                      <p className="text-xs text-gray-500">Duration</p>
                      <p className="text-gray-300">{info.last_duration_seconds.toFixed(1)}s</p>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      <div className="card p-4 text-sm text-gray-400">
        <p className="font-medium text-gray-300 mb-2">How the scheduler works</p>
        <ul className="space-y-1 list-disc list-inside text-xs">
          <li>The scheduler runs autonomously — no manual intervention required</li>
          <li>All data sources are free and open (Wikipedia, RSS, YouTube, Wikidata, etc.)</li>
          <li>Verified topics with high opportunity scores are automatically queued for Story Intelligence</li>
          <li>Story Intelligence receives trending topics, verified facts, research summaries, and knowledge chunks</li>
          <li>Use "Run Now" to trigger any phase immediately for testing or manual refresh</li>
        </ul>
      </div>
    </div>
  )
}
