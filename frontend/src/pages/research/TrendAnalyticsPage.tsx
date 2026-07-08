import { useQuery } from '@tanstack/react-query'
import { BarChart2 } from 'lucide-react'
import { researchApi } from '@/api/research'
import { Spinner } from '@/components/ui/Spinner'

export function TrendAnalyticsPage() {
  const { data: analytics, isLoading } = useQuery({
    queryKey: ['research-analytics'],
    queryFn: () => researchApi.getAnalytics('daily', 30),
  })

  const { data: dashboard } = useQuery({
    queryKey: ['research-dashboard'],
    queryFn: researchApi.getDashboard,
  })

  const topicsByStatus = dashboard?.topics_by_status || {}

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <BarChart2 className="w-6 h-6 text-purple-400" /> Trend Analytics
        </h1>
        <p className="text-gray-400 text-sm mt-1">Aggregated research intelligence metrics over time</p>
      </div>

      {/* Topic Breakdown */}
      <div className="card p-4">
        <h2 className="font-semibold text-white mb-4">Topics by Status</h2>
        <div className="space-y-2">
          {Object.entries(topicsByStatus).map(([status, count]) => {
            const total = Object.values(topicsByStatus).reduce((a, b) => a + b, 0)
            const pct = total > 0 ? ((count as number) / total) * 100 : 0
            const colors: Record<string, string> = {
              discovered: 'bg-blue-500',
              researching: 'bg-yellow-500',
              researched: 'bg-green-500',
              verified: 'bg-emerald-500',
              queued: 'bg-purple-500',
              completed: 'bg-gray-500',
              rejected: 'bg-red-500',
            }
            return (
              <div key={status} className="flex items-center gap-3">
                <span className="text-xs text-gray-400 w-24 capitalize">{status}</span>
                <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${colors[status] || 'bg-gray-500'}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <span className="text-xs text-gray-300 w-8 text-right">{count as number}</span>
              </div>
            )
          })}
          {Object.keys(topicsByStatus).length === 0 && (
            <p className="text-gray-500 text-sm text-center py-4">No topic data available</p>
          )}
        </div>
      </div>

      {/* Analytics history */}
      {isLoading ? (
        <div className="flex justify-center py-8"><Spinner /></div>
      ) : (
        <div className="card p-4">
          <h2 className="font-semibold text-white mb-4">Daily Analytics (last 30 days)</h2>
          {analytics && analytics.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-gray-400">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-2 pr-4 text-gray-300">Date</th>
                    <th className="text-right py-2 pr-4">Trends</th>
                    <th className="text-right py-2 pr-4">Topics</th>
                    <th className="text-right py-2 pr-4">Researched</th>
                    <th className="text-right py-2 pr-4">Verified Facts</th>
                    <th className="text-right py-2">Avg Score</th>
                  </tr>
                </thead>
                <tbody>
                  {analytics.map((r: any, i: number) => (
                    <tr key={r.id || i} className="border-b border-gray-800">
                      <td className="py-2 pr-4">{new Date(r.period_start).toLocaleDateString()}</td>
                      <td className="text-right py-2 pr-4">{r.active_trends}</td>
                      <td className="text-right py-2 pr-4">{r.total_topics}</td>
                      <td className="text-right py-2 pr-4">{r.researched_topics}</td>
                      <td className="text-right py-2 pr-4">{r.verified_facts}</td>
                      <td className="text-right py-2 text-brand-400">{(r.avg_opportunity_score || 0).toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500 text-sm text-center py-4">No analytics records yet. Analytics are generated daily by the scheduler.</p>
          )}
        </div>
      )}
    </div>
  )
}
