import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { FolderKanban, Film, Cpu, Plus } from 'lucide-react'
import { projectsApi } from '@/api/projects'
import { pluginsApi } from '@/api/plugins'
import { useAuthStore } from '@/stores/auth'
import { Spinner } from '@/components/ui/Spinner'

export function DashboardPage() {
  const user = useAuthStore((s) => s.user)

  const { data: projectsData, isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(1, 5),
  })

  const { data: plugins } = useQuery({
    queryKey: ['plugins'],
    queryFn: pluginsApi.list,
  })

  const stats = [
    { label: 'Total Projects', value: projectsData?.total ?? 0, icon: FolderKanban, color: 'text-blue-400' },
    { label: 'Active Plugins', value: plugins?.length ?? 0, icon: Cpu, color: 'text-purple-400' },
    { label: 'Videos Generated', value: 0, icon: Film, color: 'text-green-400' },
  ]

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">
          Welcome back, {user?.full_name?.split(' ')[0] || 'Creator'}
        </h1>
        <p className="text-gray-400 mt-1">Manage your animation projects and plugins</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card p-5">
            <div className="flex items-center gap-3 mb-3">
              <Icon className={`w-5 h-5 ${color}`} />
              <span className="text-sm text-gray-400">{label}</span>
            </div>
            <p className="text-3xl font-bold text-white">{value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-100">Recent Projects</h2>
            <Link to="/projects" className="text-xs text-brand-400 hover:text-brand-300">
              View all
            </Link>
          </div>
          {projectsLoading ? (
            <div className="flex justify-center py-8"><Spinner /></div>
          ) : projectsData?.items.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-sm text-gray-500 mb-4">No projects yet</p>
              <Link to="/projects" className="btn-primary text-xs">
                <Plus className="w-3.5 h-3.5" /> Create Project
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              {projectsData?.items.map((project) => (
                <Link
                  key={project.id}
                  to={`/projects/${project.id}`}
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-800 transition-colors"
                >
                  <div className="w-8 h-8 bg-brand-900/50 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Film className="w-4 h-4 text-brand-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-200 truncate">{project.title}</p>
                    <p className="text-xs text-gray-500">{project.plugin_id} · {project.status}</p>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        <div className="card p-5">
          <h2 className="text-base font-semibold text-gray-100 mb-4">Available Plugins</h2>
          {!plugins ? (
            <div className="flex justify-center py-8"><Spinner /></div>
          ) : (
            <div className="space-y-2">
              {plugins?.map((plugin) => (
                <div key={plugin.id} className="flex items-start gap-3 p-3 rounded-lg bg-gray-800/50">
                  <div className="w-8 h-8 bg-purple-900/50 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Cpu className="w-4 h-4 text-purple-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-200">{plugin.name}</p>
                    <p className="text-xs text-gray-500">{plugin.description}</p>
                    <div className="flex gap-1 mt-1.5 flex-wrap">
                      {plugin.tags.slice(0, 3).map((tag) => (
                        <span key={tag} className="badge-gray text-xs">{tag}</span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
