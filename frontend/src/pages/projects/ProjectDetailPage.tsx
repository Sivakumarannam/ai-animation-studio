import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { BookOpen, Users, ChevronRight, Sparkles, Library, Wand2, GitBranch, Film } from 'lucide-react'
import { projectsApi } from '@/api/projects'
import { Spinner } from '@/components/ui/Spinner'

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>()

  const { data: project, isLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectsApi.get(projectId!),
    enabled: !!projectId,
  })

  if (isLoading) {
    return <div className="flex justify-center py-20"><Spinner size="lg" /></div>
  }

  if (!project) {
    return <div className="p-6 text-gray-400">Project not found</div>
  }

  const sections = [
    { label: 'Stories', description: 'Scripts and episode stories', icon: BookOpen, to: `/projects/${projectId}/stories` },
    { label: 'Characters', description: 'Character library for this project', icon: Users, to: `/projects/${projectId}/characters` },
    { label: 'Story Intelligence', description: 'AI-driven worlds, seasons, episodes & analytics', icon: Sparkles, to: `/projects/${projectId}/intelligence` },
    { label: 'Knowledge Intelligence', description: 'RAG knowledge base for AI story generation', icon: Library, to: `/projects/${projectId}/knowledge` },
    { label: 'Asset Generation', description: 'AI asset generation engine — images, audio, animations', icon: Wand2, to: `/projects/${projectId}/asset-generation` },
    { label: 'Animation Engine', description: 'Phase 7 — composite assets into animated scene clips', icon: Film, to: `/projects/${projectId}/animation` },
    { label: 'Automation Pipeline', description: 'Full 7-step generation pipeline — story to video', icon: GitBranch, to: `/projects/${projectId}/pipeline` },
  ]

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/projects" className="hover:text-gray-300">Projects</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300">{project.title}</span>
      </div>

      <div className="card p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white mb-1">{project.title}</h1>
            {project.description && <p className="text-gray-400 text-sm">{project.description}</p>}
          </div>
          <span className="badge-blue">{project.plugin_id}</span>
        </div>
        <div className="flex gap-4 mt-4 pt-4 border-t border-gray-800 text-xs text-gray-500">
          <span>Style: <span className="text-gray-300">{project.animation_style}</span></span>
          <span>Status: <span className="text-gray-300">{project.status}</span></span>
          <span>Created: <span className="text-gray-300">{new Date(project.created_at).toLocaleDateString()}</span></span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {sections.map(({ label, description, icon: Icon, to }) => (
          <Link key={label} to={to} className="card p-5 hover:border-gray-700 transition-colors flex items-center gap-4">
            <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center flex-shrink-0">
              <Icon className="w-5 h-5 text-brand-400" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-gray-100">{label}</p>
              <p className="text-xs text-gray-500">{description}</p>
            </div>
            <ChevronRight className="w-4 h-4 text-gray-600" />
          </Link>
        ))}
      </div>
    </div>
  )
}
