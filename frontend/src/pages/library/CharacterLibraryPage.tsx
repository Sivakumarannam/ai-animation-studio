import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Users, Search, RefreshCw, Sparkles, Mic, ChevronDown } from 'lucide-react'
import { libraryApi, type CharacterTemplate } from '@/api/library'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'

const CATEGORY_COLORS: Record<string, string> = {
  grandfather: 'bg-amber-900/30 text-amber-300',
  grandmother: 'bg-pink-900/30 text-pink-300',
  father: 'bg-blue-900/30 text-blue-300',
  mother: 'bg-green-900/30 text-green-300',
  'son-in-law': 'bg-purple-900/30 text-purple-300',
  daughter: 'bg-rose-900/30 text-rose-300',
  child: 'bg-yellow-900/30 text-yellow-300',
}

function CharacterCard({ template }: { template: CharacterTemplate }) {
  const [expanded, setExpanded] = useState(false)
  const colorClass = CATEGORY_COLORS[template.archetype] ?? 'bg-gray-800 text-gray-300'

  return (
    <div className="card p-4 flex flex-col gap-3 hover:border-brand-600/40 transition-colors">
      <div className="flex items-start gap-3">
        <div className="w-12 h-12 rounded-xl bg-brand-900/30 border border-brand-800/50 flex items-center justify-center text-2xl flex-shrink-0">
          {template.thumbnail_url ? (
            <img src={template.thumbnail_url} alt={template.name} className="w-full h-full object-cover rounded-xl" />
          ) : (
            <Users className="w-6 h-6 text-brand-400" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-sm font-semibold text-gray-100 truncate">{template.name}</h3>
            {template.name_local && (
              <span className="text-xs text-gray-400">{template.name_local}</span>
            )}
          </div>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <span className={`text-xs px-2 py-0.5 rounded-full ${colorClass}`}>
              {template.archetype || 'character'}
            </span>
            {template.gender && <span className="badge-gray">{template.gender}</span>}
            {template.age_range && <span className="badge-gray">{template.age_range}</span>}
          </div>
        </div>
      </div>

      {template.personality && (
        <p className="text-xs text-gray-400 line-clamp-2">{template.personality}</p>
      )}

      {template.typical_expressions.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {template.typical_expressions.slice(0, 4).map((expr) => (
            <span key={expr} className="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-gray-400">
              {expr}
            </span>
          ))}
          {template.typical_expressions.length > 4 && (
            <span className="text-xs text-gray-500">+{template.typical_expressions.length - 4}</span>
          )}
        </div>
      )}

      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300 transition-colors"
      >
        <ChevronDown className={`w-3 h-3 transition-transform ${expanded ? 'rotate-180' : ''}`} />
        {expanded ? 'Hide details' : 'Show details'}
      </button>

      {expanded && (
        <div className="space-y-2 border-t border-gray-800 pt-2">
          {Object.keys(template.voice_profile).length > 0 && (
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <Mic className="w-3 h-3" />
              <span>Voice: {(template.voice_profile as any).style || 'default'}</span>
            </div>
          )}
          {template.clothing_variants.length > 0 && (
            <p className="text-xs text-gray-500">
              {template.clothing_variants.length} clothing variant{template.clothing_variants.length !== 1 ? 's' : ''}
            </p>
          )}
          {template.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {template.tags.map((tag) => (
                <span key={tag} className="text-xs text-brand-400">#{tag}</span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function CharacterLibraryPage() {
  const [search, setSearch] = useState('')
  const [pluginFilter, setPluginFilter] = useState('')

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['character-templates', search, pluginFilter],
    queryFn: () => libraryApi.getCharacterTemplates({
      search: search || undefined,
      plugin_id: pluginFilter || undefined,
      page_size: 50,
    }),
  })

  const seedMutation = useMutation({
    mutationFn: () => libraryApi.seedCharacterTemplates('telugu_family_comedy'),
    onSuccess: () => refetch(),
  })

  const templates = data?.items ?? []

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Users className="w-6 h-6 text-brand-400" />
            Character Library
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Reusable character templates with full rigs, voice profiles, and expression libraries
          </p>
        </div>
        <button
          onClick={() => seedMutation.mutate()}
          disabled={seedMutation.isPending}
          className="btn-secondary flex items-center gap-2"
        >
          {seedMutation.isPending ? <Spinner size="sm" /> : <Sparkles className="w-4 h-4" />}
          Seed Telugu Characters
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            className="input pl-9"
            placeholder="Search characters..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select
          className="input w-52"
          value={pluginFilter}
          onChange={(e) => setPluginFilter(e.target.value)}
        >
          <option value="">All plugins</option>
          <option value="telugu_family_comedy">Telugu Family Comedy</option>
        </select>
        <button onClick={() => refetch()} className="btn-secondary p-2">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Stats bar */}
      {data && (
        <div className="flex items-center gap-2 text-xs text-gray-500 mb-4">
          <span>{data.total} character{data.total !== 1 ? 's' : ''}</span>
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : templates.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No character templates"
          description="Seed the Telugu Family Comedy plugin to add default characters."
          action={
            <button onClick={() => seedMutation.mutate()} className="btn-primary">
              <Sparkles className="w-4 h-4" /> Seed Characters
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {templates.map((t) => (
            <CharacterCard key={t.id} template={t} />
          ))}
        </div>
      )}
    </div>
  )
}
