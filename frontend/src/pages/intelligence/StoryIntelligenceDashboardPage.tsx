import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ChevronRight, Globe2, Layers, Clapperboard, Film, Lightbulb, Database,
  ListChecks, Sparkles, Star,
} from 'lucide-react'
import { storyIntelligenceApi } from '@/api/storyIntelligence'
import { Spinner } from '@/components/ui/Spinner'
import { Modal } from '@/components/ui/Modal'

export function StoryIntelligenceDashboardPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const qc = useQueryClient()
  const [showGenerate, setShowGenerate] = useState(false)
  const [genre, setGenre] = useState('comedy')
  const [storyType, setStoryType] = useState('comedy')
  const [episodeCount, setEpisodeCount] = useState(3)

  const { data: stats, isLoading } = useQuery({
    queryKey: ['si-stats', projectId],
    queryFn: () => storyIntelligenceApi.getStats(projectId!),
    enabled: !!projectId,
    refetchInterval: 10000,
  })

  const generateMutation = useMutation({
    mutationFn: () =>
      storyIntelligenceApi.runFullPipeline(projectId!, {
        genre, story_type: storyType, episode_count: episodeCount,
      }),
    onSuccess: () => {
      setShowGenerate(false)
      qc.invalidateQueries({ queryKey: ['si-stats', projectId] })
    },
  })

  if (isLoading) {
    return <div className="flex justify-center py-20"><Spinner size="lg" /></div>
  }

  const statCards = [
    { label: 'Worlds', value: stats?.worlds ?? 0, icon: Globe2, color: 'text-blue-400', to: `/projects/${projectId}/intelligence/worlds` },
    { label: 'Seasons', value: stats?.seasons ?? 0, icon: Layers, color: 'text-purple-400' },
    { label: 'Episodes', value: stats?.episodes ?? 0, icon: Clapperboard, color: 'text-green-400' },
    { label: 'Scenes', value: stats?.scenes ?? 0, icon: Film, color: 'text-orange-400' },
    { label: 'Ideas', value: stats?.ideas ?? 0, icon: Lightbulb, color: 'text-yellow-400', to: `/projects/${projectId}/intelligence/ideas` },
    { label: 'Memory Entries', value: stats?.memories ?? 0, icon: Database, color: 'text-cyan-400' },
  ]

  const jobsByStatus = stats?.jobs_by_status ?? {}
  const runningJobs = jobsByStatus.running ?? 0
  const queuedJobs = jobsByStatus.queued ?? jobsByStatus.pending ?? 0
  const failedJobs = jobsByStatus.failed ?? 0

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/projects" className="hover:text-gray-300">Projects</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}`} className="hover:text-gray-300">Project</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300">Story Intelligence</span>
      </div>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Story Intelligence</h1>
          <p className="text-gray-400 text-sm mt-1">Worlds, seasons, episodes, and AI story generation</p>
        </div>
        <button onClick={() => setShowGenerate(true)} className="btn-primary">
          <Sparkles className="w-4 h-4" /> Generate Full Pipeline
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        {statCards.map(({ label, value, icon: Icon, color, to }) => {
          const Card = (
            <div className="card p-4 h-full">
              <Icon className={`w-5 h-5 ${color} mb-2`} />
              <p className="text-2xl font-bold text-white">{value}</p>
              <p className="text-xs text-gray-500">{label}</p>
            </div>
          )
          return to ? <Link key={label} to={to}>{Card}</Link> : <div key={label}>{Card}</div>
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <ListChecks className="w-4 h-4 text-brand-400" />
            <h2 className="text-base font-semibold text-gray-100">Generation Queue</h2>
          </div>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div>
              <p className="text-xl font-bold text-blue-400">{queuedJobs}</p>
              <p className="text-xs text-gray-500">Queued</p>
            </div>
            <div>
              <p className="text-xl font-bold text-yellow-400">{runningJobs}</p>
              <p className="text-xs text-gray-500">Running</p>
            </div>
            <div>
              <p className="text-xl font-bold text-red-400">{failedJobs}</p>
              <p className="text-xs text-gray-500">Failed</p>
            </div>
          </div>
          <Link to={`/projects/${projectId}/intelligence/jobs`} className="text-xs text-brand-400 hover:text-brand-300 mt-4 inline-block">
            View retry queue &amp; job history →
          </Link>
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Star className="w-4 h-4 text-brand-400" />
            <h2 className="text-base font-semibold text-gray-100">Story Quality</h2>
          </div>
          <p className="text-3xl font-bold text-white">{stats?.avg_story_score?.toFixed(1) ?? '0.0'}<span className="text-sm text-gray-500"> / 100</span></p>
          <p className="text-xs text-gray-500 mt-1">Average story score across evaluated episodes</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Link to={`/projects/${projectId}/intelligence/worlds`} className="card p-5 hover:border-gray-700 transition-colors flex items-center gap-4">
          <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center flex-shrink-0">
            <Globe2 className="w-5 h-5 text-brand-400" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-gray-100">World Builder</p>
            <p className="text-xs text-gray-500">Manage worlds, seasons &amp; episodes</p>
          </div>
          <ChevronRight className="w-4 h-4 text-gray-600" />
        </Link>
        <Link to={`/projects/${projectId}/intelligence/ideas`} className="card p-5 hover:border-gray-700 transition-colors flex items-center gap-4">
          <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center flex-shrink-0">
            <Lightbulb className="w-5 h-5 text-brand-400" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-gray-100">Story Library</p>
            <p className="text-xs text-gray-500">Browse &amp; generate story ideas</p>
          </div>
          <ChevronRight className="w-4 h-4 text-gray-600" />
        </Link>
        <Link to={`/projects/${projectId}/intelligence/jobs`} className="card p-5 hover:border-gray-700 transition-colors flex items-center gap-4">
          <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center flex-shrink-0">
            <ListChecks className="w-5 h-5 text-brand-400" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-gray-100">Retry Queue</p>
            <p className="text-xs text-gray-500">Monitor &amp; retry generation jobs</p>
          </div>
          <ChevronRight className="w-4 h-4 text-gray-600" />
        </Link>
      </div>

      <Modal title="Generate Full Story Pipeline" open={showGenerate} onClose={() => setShowGenerate(false)}>
        <form onSubmit={(e) => { e.preventDefault(); generateMutation.mutate() }} className="space-y-4">
          <p className="text-xs text-gray-500">
            Automatically creates a world, season, and episodes using the AI story pipeline.
          </p>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Genre</label>
              <input className="input" value={genre} onChange={(e) => setGenre(e.target.value)} />
            </div>
            <div>
              <label className="label">Story Type</label>
              <input className="input" value={storyType} onChange={(e) => setStoryType(e.target.value)} />
            </div>
          </div>
          <div>
            <label className="label">Episode Count</label>
            <input
              type="number" min={1} max={20} className="input" value={episodeCount}
              onChange={(e) => setEpisodeCount(Number(e.target.value))}
            />
          </div>
          {generateMutation.isError && (
            <p className="text-xs text-red-400">Failed to start generation. Please try again.</p>
          )}
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowGenerate(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={generateMutation.isPending}>
              {generateMutation.isPending ? <Spinner size="sm" /> : 'Start Generation'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
