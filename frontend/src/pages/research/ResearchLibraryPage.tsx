import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BookOpen, ExternalLink, Star } from 'lucide-react'
import { researchApi } from '@/api/research'
import { Spinner } from '@/components/ui/Spinner'

export function ResearchLibraryPage() {
  const [page] = useState(1)

  const { data: topicsData, isLoading: topicsLoading } = useQuery({
    queryKey: ['research-topics-library', page],
    queryFn: () => researchApi.getTopics(page, 10, 'researched'),
  })

  const selectedTopicId = topicsData?.items[0]?.id

  const { data: articles, isLoading: articlesLoading } = useQuery({
    queryKey: ['research-articles', selectedTopicId],
    queryFn: () => selectedTopicId ? researchApi.getArticles(selectedTopicId, 1, 20) : null,
    enabled: !!selectedTopicId,
  })

  const { data: facts } = useQuery({
    queryKey: ['research-facts', selectedTopicId],
    queryFn: () => selectedTopicId ? researchApi.getFacts(selectedTopicId, 1, 20) : null,
    enabled: !!selectedTopicId,
  })

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <BookOpen className="w-6 h-6 text-teal-400" /> Research Library
        </h1>
        <p className="text-gray-400 text-sm mt-1">Articles and facts collected for researched topics</p>
      </div>

      {topicsLoading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Topic list */}
          <div className="card p-4 space-y-2">
            <h2 className="font-semibold text-white text-sm mb-3">Researched Topics ({topicsData?.meta.total || 0})</h2>
            {topicsData?.items.map(t => (
              <div key={t.id} className="p-2 rounded bg-gray-800 hover:bg-gray-700 cursor-pointer">
                <p className="text-sm text-white font-medium">{t.canonical_name}</p>
                <p className="text-xs text-gray-400">{t.article_count} articles · {t.fact_count} facts</p>
              </div>
            ))}
            {topicsData?.items.length === 0 && (
              <p className="text-gray-500 text-sm text-center py-4">No researched topics yet</p>
            )}
          </div>

          {/* Articles + Facts */}
          <div className="md:col-span-2 space-y-4">
            {selectedTopicId && (
              <>
                <div className="card p-4">
                  <h2 className="font-semibold text-white mb-3">Articles</h2>
                  {articlesLoading ? <Spinner /> : (
                    <div className="space-y-3">
                      {articles?.items.map(a => (
                        <div key={a.id} className="p-3 rounded bg-gray-800 space-y-1">
                          <div className="flex items-start justify-between gap-2">
                            <p className="text-sm font-medium text-white">{a.title}</p>
                            {a.url && (
                              <a href={a.url} target="_blank" rel="noopener noreferrer" className="text-brand-400 hover:text-brand-300 flex-shrink-0">
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            )}
                          </div>
                          <p className="text-xs text-gray-400 line-clamp-2">{a.summary}</p>
                          <div className="flex gap-3 text-xs text-gray-500">
                            <span>{a.source_type}</span>
                            <span>Quality: {(a.quality_score * 100).toFixed(0)}%</span>
                            <span>Relevance: {(a.relevance_score * 100).toFixed(0)}%</span>
                          </div>
                        </div>
                      ))}
                      {articles?.items.length === 0 && <p className="text-gray-500 text-sm">No articles collected yet</p>}
                    </div>
                  )}
                </div>

                <div className="card p-4">
                  <h2 className="font-semibold text-white mb-3">Verified Facts</h2>
                  <div className="space-y-2">
                    {facts?.items.filter(f => f.is_verified).map(f => (
                      <div key={f.id} className="flex items-start gap-2 p-2 rounded bg-gray-800">
                        <Star className="w-3 h-3 text-green-400 mt-0.5 flex-shrink-0" />
                        <p className="text-xs text-gray-300">{f.statement}</p>
                        <span className="text-xs text-green-400 ml-auto flex-shrink-0">{(f.confidence * 100).toFixed(0)}%</span>
                      </div>
                    ))}
                    {!facts?.items.filter(f => f.is_verified).length && (
                      <p className="text-gray-500 text-sm">No verified facts yet</p>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
