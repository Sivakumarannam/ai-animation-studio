import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { TrendingUp, BookOpen, CheckCircle, Clock, Zap, Play, BarChart2 } from 'lucide-react'
import { researchApi } from '@/api/research'
import { Spinner } from '@/components/ui/Spinner'
import { Link } from 'react-router-dom'

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

export function ResearchDashboardPage() {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['research-dashboard'],
    queryFn: researchApi.getDashboard,
    refetchInterval: 30_000,
  })
  const trigger = useMutation({
    mutationFn: (phase: string) => researchApi.triggerScheduler(phase),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['research-dashboard'] }),
  })

  if (isLoading) return <div className="p-8 flex justify-center"><Spinner /></div>
  if (!data) return null

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Research Intelligence</h1>
          <p className="text-gray-400 text-sm mt-1">Autonomous trend discovery & research pipeline</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => trigger.mutate('trend_discovery')}
            disabled={trigger.isPending}
            className="btn-primary text-sm flex items-center gap-2"
          >
            <Play className="w-4 h-4" />
            Discover Trends
          </button>
          <button
            onClick={() => trigger.mutate('full')}
            disabled={trigger.isPending}
            className="btn-secondary text-sm flex items-center gap-2"
          >
            <Zap className="w-4 h-4" />
            Run Full Pipeline
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Active Trends" value={data.active_trends} icon={TrendingUp} color="bg-blue-600" />
        <StatCard label="Emerging Trends" value={data.emerging_trends} icon={Zap} color="bg-purple-600" />
        <StatCard label="Total Topics" value={data.total_topics} icon={BookOpen} color="bg-indigo-600" />
        <StatCard label="Verified Facts" value={data.verified_facts} icon={CheckCircle} color="bg-green-600" />
        <StatCard label="Researched Topics" value={data.researched_topics} icon={BarChart2} color="bg-teal-600" />
        <StatCard label="Queue Pending" value={data.queue_pending} icon={Clock} color="bg-yellow-600" />
        <StatCard label="Knowledge Docs" value={data.knowledge_docs_created} icon={BookOpen} color="bg-orange-600" />
        <StatCard label="Jobs Running" value={data.jobs_by_status?.running || 0} icon={Play} color="bg-red-600" />
      </div>

      {/* Top Trends + Opportunities */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-white">Top Trending Topics</h2>
            <Link to="/research/trends" className="text-xs text-brand-400 hover:text-brand-300">View all</Link>
          </div>
          <div className="space-y-2">
            {data.top_trends.map(t => (
              <div key={t.id} className="flex items-center justify-between p-2 rounded bg-gray-800">
                <div>
                  <p className="text-sm text-white font-medium">{t.keyword}</p>
                  <p className="text-xs text-gray-400">{t.category}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-brand-400">{t.trend_score.toFixed(0)}</p>
                  {t.is_emerging && <span className="text-xs text-green-400">↑ emerging</span>}
                </div>
              </div>
            ))}
            {data.top_trends.length === 0 && (
              <p className="text-gray-500 text-sm text-center py-4">No trends yet — trigger discovery above</p>
            )}
          </div>
        </div>

        <div className="card p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-white">Top Opportunities</h2>
            <Link to="/research/opportunities" className="text-xs text-brand-400 hover:text-brand-300">View all</Link>
          </div>
          <div className="space-y-2">
            {data.top_opportunities.map(t => (
              <div key={t.id} className="flex items-center justify-between p-2 rounded bg-gray-800">
                <div>
                  <p className="text-sm text-white font-medium">{t.canonical_name}</p>
                  <p className="text-xs text-gray-400">{t.categories[0] || 'general'}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-green-400">{t.opportunity_score.toFixed(0)}</p>
                  <p className="text-xs text-gray-500">{t.status}</p>
                </div>
              </div>
            ))}
            {data.top_opportunities.length === 0 && (
              <p className="text-gray-500 text-sm text-center py-4">No opportunities scored yet</p>
            )}
          </div>
        </div>
      </div>

      {/* Scheduler Status */}
      <div className="card p-4">
        <h2 className="font-semibold text-white mb-3">Scheduler Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {data.scheduler_status?.phases && Object.entries(data.scheduler_status.phases).map(([phase, info]: [string, any]) => (
            <div key={phase} className="p-3 rounded bg-gray-800">
              <p className="text-sm font-medium text-gray-200">{phase.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</p>
              <p className={`text-xs mt-1 ${info.last_status === 'completed' ? 'text-green-400' : info.last_status === 'failed' ? 'text-red-400' : 'text-gray-500'}`}>
                {info.last_status}
              </p>
              {info.last_run_at && (
                <p className="text-xs text-gray-500 mt-1">
                  {new Date(info.last_run_at).toLocaleString()}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
