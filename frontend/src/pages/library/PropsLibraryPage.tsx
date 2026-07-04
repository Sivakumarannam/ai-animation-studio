import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Package, Search, Sparkles } from 'lucide-react'
import { libraryApi, type Prop } from '@/api/library'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'

const CATEGORY_META: Record<string, { icon: string; color: string }> = {
  furniture:   { icon: '🛋️', color: 'bg-amber-900/20 text-amber-300 border-amber-800/40' },
  vehicles:    { icon: '🚗', color: 'bg-blue-900/20 text-blue-300 border-blue-800/40' },
  kitchen:     { icon: '🍳', color: 'bg-orange-900/20 text-orange-300 border-orange-800/40' },
  school:      { icon: '📚', color: 'bg-green-900/20 text-green-300 border-green-800/40' },
  electronics: { icon: '💻', color: 'bg-cyan-900/20 text-cyan-300 border-cyan-800/40' },
  food:        { icon: '🍚', color: 'bg-yellow-900/20 text-yellow-300 border-yellow-800/40' },
  money:       { icon: '💰', color: 'bg-emerald-900/20 text-emerald-300 border-emerald-800/40' },
  nature:      { icon: '🌿', color: 'bg-lime-900/20 text-lime-300 border-lime-800/40' },
  medical:     { icon: '🏥', color: 'bg-red-900/20 text-red-300 border-red-800/40' },
  office:      { icon: '💼', color: 'bg-gray-900/20 text-gray-300 border-gray-700' },
}

function PropCard({ prop }: { prop: Prop }) {
  const meta = CATEGORY_META[prop.category] ?? { icon: '📦', color: 'bg-gray-800 text-gray-300 border-gray-700' }

  return (
    <div className={`card p-3 border hover:border-brand-600/40 transition-colors group cursor-grab active:cursor-grabbing`}
      draggable
      onDragStart={(e) => {
        e.dataTransfer.setData('application/json', JSON.stringify({
          type: 'prop',
          id: prop.id,
          name: prop.name,
          category: prop.category,
          file_url: prop.file_url,
          thumbnail_url: prop.thumbnail_url,
        }))
      }}
    >
      <div className="aspect-square rounded-lg bg-gray-800 mb-2 flex items-center justify-center overflow-hidden">
        {prop.thumbnail_url ? (
          <img src={prop.thumbnail_url} alt={prop.name} className="w-full h-full object-contain" />
        ) : (
          <span className="text-3xl">{meta.icon}</span>
        )}
      </div>
      <p className="text-xs font-medium text-gray-200 text-center truncate">{prop.name}</p>
      <div className="flex justify-center mt-1">
        <span className={`text-xs px-2 py-0.5 rounded-full border ${meta.color}`}>
          {meta.icon} {prop.category}
        </span>
      </div>
    </div>
  )
}

export function PropsLibraryPage() {
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['props', search, category],
    queryFn: () => libraryApi.getProps({
      search: search || undefined,
      category: category || undefined,
      page_size: 60,
    }),
  })

  const { data: categories } = useQuery({
    queryKey: ['prop-categories'],
    queryFn: libraryApi.getPropCategories,
  })

  const seedMutation = useMutation({
    mutationFn: libraryApi.seedProps,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['props'] }),
  })

  const props = data?.items ?? []

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Package className="w-6 h-6 text-brand-400" />
            Props Library
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Drag and drop props into your scene — furniture, vehicles, food, electronics and more
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

      <div className="flex gap-3 mb-4 flex-wrap">
        <div className="relative flex-1 min-w-48 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            className="input pl-9"
            placeholder="Search props..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setCategory('')}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
              !category ? 'bg-brand-600 border-brand-500 text-white' : 'border-gray-700 text-gray-400 hover:border-gray-500'
            }`}
          >
            All
          </button>
          {(categories ?? []).map((cat) => {
            const m = CATEGORY_META[cat]
            return (
              <button
                key={cat}
                onClick={() => setCategory(cat === category ? '' : cat)}
                className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                  category === cat ? 'bg-brand-600 border-brand-500 text-white' : 'border-gray-700 text-gray-400 hover:border-gray-500'
                }`}
              >
                {m?.icon} {cat}
              </button>
            )
          })}
        </div>
      </div>

      {data && (
        <p className="text-xs text-gray-500 mb-4">{data.total} prop{data.total !== 1 ? 's' : ''} · Drag to place in scene editor</p>
      )}

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : props.length === 0 ? (
        <EmptyState
          icon={Package}
          title="No props yet"
          description="Seed the default props library to get started."
          action={
            <button onClick={() => seedMutation.mutate()} className="btn-primary">
              <Sparkles className="w-4 h-4" /> Seed Props
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-8 gap-3">
          {props.map((prop) => (
            <PropCard key={prop.id} prop={prop} />
          ))}
        </div>
      )}
    </div>
  )
}
