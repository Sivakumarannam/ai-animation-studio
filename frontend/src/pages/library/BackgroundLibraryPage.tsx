import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ImageIcon, Search, Sparkles } from 'lucide-react'
import { libraryApi, type Background } from '@/api/library'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'

const CATEGORY_ICONS: Record<string, string> = {
  indoor: '🏠', outdoor: '🌳', educational: '🏫', medical: '🏥',
  commercial: '🏪', workplace: '💼', religious: '🛕',
}

function BackgroundCard({ bg }: { bg: Background }) {
  return (
    <div className="card overflow-hidden hover:border-brand-600/40 transition-colors group cursor-pointer">
      <div className="aspect-video bg-gray-800 relative overflow-hidden">
        {bg.thumbnail_url ? (
          <img
            src={bg.thumbnail_url}
            alt={bg.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center gap-2">
            <span className="text-3xl">{CATEGORY_ICONS[bg.category] ?? '🖼️'}</span>
            <span className="text-xs text-gray-500">{bg.name}</span>
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
        {bg.category && (
          <div className="absolute top-2 left-2">
            <span className="text-xs px-2 py-0.5 rounded-full bg-black/60 text-gray-200 backdrop-blur-sm">
              {CATEGORY_ICONS[bg.category]} {bg.category}
            </span>
          </div>
        )}
      </div>
      <div className="p-3">
        <p className="text-sm font-medium text-gray-100 truncate">{bg.name}</p>
        {bg.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1.5">
            {bg.tags.slice(0, 3).map((tag) => (
              <span key={tag} className="text-xs text-gray-500">#{tag}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export function BackgroundLibraryPage() {
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['backgrounds', search, category],
    queryFn: () => libraryApi.getBackgrounds({
      search: search || undefined,
      category: category || undefined,
      page_size: 48,
    }),
  })

  const { data: categories } = useQuery({
    queryKey: ['bg-categories'],
    queryFn: libraryApi.getBgCategories,
  })

  const seedMutation = useMutation({
    mutationFn: libraryApi.seedBackgrounds,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['backgrounds'] }),
  })

  const backgrounds = data?.items ?? []

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <ImageIcon className="w-6 h-6 text-brand-400" />
            Background Library
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Reusable scene backgrounds — villages, homes, schools, markets and more
          </p>
        </div>
        <button
          onClick={() => seedMutation.mutate()}
          disabled={seedMutation.isPending}
          className="btn-secondary flex items-center gap-2"
        >
          {seedMutation.isPending ? <Spinner size="sm" /> : <Sparkles className="w-4 h-4" />}
          Seed Defaults
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4 flex-wrap">
        <div className="relative flex-1 min-w-48 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            className="input pl-9"
            placeholder="Search backgrounds..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {/* Category pills */}
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setCategory('')}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
              category === '' ? 'bg-brand-600 border-brand-500 text-white' : 'border-gray-700 text-gray-400 hover:border-gray-500'
            }`}
          >
            All
          </button>
          {(categories ?? []).map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat === category ? '' : cat)}
              className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                category === cat ? 'bg-brand-600 border-brand-500 text-white' : 'border-gray-700 text-gray-400 hover:border-gray-500'
              }`}
            >
              {CATEGORY_ICONS[cat]} {cat}
            </button>
          ))}
        </div>
      </div>

      {data && (
        <p className="text-xs text-gray-500 mb-4">{data.total} background{data.total !== 1 ? 's' : ''}</p>
      )}

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : backgrounds.length === 0 ? (
        <EmptyState
          icon={ImageIcon}
          title="No backgrounds yet"
          description="Seed the default background library to get started."
          action={
            <button onClick={() => seedMutation.mutate()} className="btn-primary">
              <Sparkles className="w-4 h-4" /> Seed Backgrounds
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {backgrounds.map((bg) => (
            <BackgroundCard key={bg.id} bg={bg} />
          ))}
        </div>
      )}
    </div>
  )
}
