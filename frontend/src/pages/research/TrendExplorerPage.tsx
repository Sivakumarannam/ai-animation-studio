import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { TrendingUp, Filter, Zap, Archive } from 'lucide-react'
import { researchApi, ResearchTrend } from '@/api/research'
import { Spinner } from '@/components/ui/Spinner'

const CATEGORIES = ['technology', 'science', 'education', 'environment', 'history', 'health', 'culture', 'nature', 'food', 'general']

export function TrendExplorerPage() {
  const [category, setCategory] = useState<string | undefined>()
  const [emergingOnly, setEmergingOnly] = useState(false)
  const [page, setPage] = useState(1)
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['research-trends', page, category, emergingOnly],
    queryFn: () => researchApi.getTrends(page, 20, category, emergingOnly),
  })

  const archiveMutation = useMutation({
    mutationFn: (id: string) => researchApi.updateTrend(id, { status: 'archived' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['research-trends'] }),
  })

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-blue-400" /> Trend Explorer
          </h1>
          <p className="text-gray-400 text-sm mt-1">Browse discovered trends from free open sources</p>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4 flex flex-wrap items-center gap-3">
        <Filter className="w-4 h-4 text-gray-400" />
        <select
          value={category || ''}
          onChange={e => { setCategory(e.target.value || undefined); setPage(1) }}
          className="input text-sm py-1 px-2"
        >
          <option value="">All categories</option>
          {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
          <input
            type="checkbox"
            checked={emergingOnly}
            onChange={e => { setEmergingOnly(e.target.checked); setPage(1) }}
            className="rounded"
          />
          Emerging only
        </label>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data?.items.map((trend: ResearchTrend) => (
              <div key={trend.id} className="card p-4 space-y-2">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-white">{trend.keyword}</p>
                    <span className="text-xs text-gray-400 capitalize">{trend.category} · {trend.region}</span>
                  </div>
                  <div className="flex items-start gap-2 ml-2">
                    <div className="text-right">
                      <p className="text-lg font-bold text-brand-400">{trend.trend_score.toFixed(0)}</p>
                      {trend.is_emerging && (
                        <span className="flex items-center gap-1 text-xs text-green-400">
                          <Zap className="w-3 h-3" /> Emerging
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => archiveMutation.mutate(trend.id)}
                      disabled={archiveMutation.isPending}
                      className="btn-secondary p-1.5 text-xs flex items-center gap-1 flex-shrink-0"
                      title="Archive this trend"
                    >
                      <Archive className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs text-gray-400">
                  <div>
                    <p className="font-medium text-gray-300">{trend.velocity.toFixed(1)}</p>
                    <p>Velocity</p>
                  </div>
                  <div>
                    <p className="font-medium text-gray-300">{(trend.growth_rate * 100).toFixed(0)}%</p>
                    <p>Growth</p>
                  </div>
                  <div>
                    <p className="font-medium text-gray-300">{trend.popularity_index.toFixed(0)}</p>
                    <p>Popularity</p>
                  </div>
                </div>
              </div>
            ))}
            {data?.items.length === 0 && (
              <div className="col-span-3 text-center py-16 text-gray-500">
                No trends found. Trigger trend discovery from the Research Dashboard.
              </div>
            )}
          </div>

          {/* Pagination */}
          {data && data.meta.total_pages > 1 && (
            <div className="flex justify-center gap-2">
              <button className="btn-secondary text-sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Previous</button>
              <span className="text-gray-400 text-sm self-center">Page {page} of {data.meta.total_pages}</span>
              <button className="btn-secondary text-sm" disabled={page >= data.meta.total_pages} onClick={() => setPage(p => p + 1)}>Next</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
