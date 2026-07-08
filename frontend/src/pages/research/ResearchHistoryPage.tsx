import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { History, CheckCircle, XCircle } from 'lucide-react'
import { researchApi, ResearchHistory } from '@/api/research'
import { Spinner } from '@/components/ui/Spinner'

export function ResearchHistoryPage() {
  const [page, setPage] = useState(1)
  const [runType, setRunType] = useState<string | undefined>()

  const { data, isLoading } = useQuery({
    queryKey: ['research-history', page, runType],
    queryFn: () => researchApi.getHistory(page, 20, runType),
  })

  const RUN_TYPES = ['trend_discovery', 'research_refresh', 'opportunity_report', 'manual']

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <History className="w-6 h-6 text-gray-400" /> Research History
        </h1>
        <p className="text-gray-400 text-sm mt-1">Full audit log of all pipeline executions</p>
      </div>

      <div className="flex gap-2 flex-wrap">
        {[undefined, ...RUN_TYPES].map(t => (
          <button
            key={t || 'all'}
            onClick={() => { setRunType(t); setPage(1) }}
            className={`text-xs px-3 py-1 rounded-full transition-colors ${runType === t ? 'bg-brand-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
          >
            {t?.replace(/_/g, ' ') || 'All'}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : (
        <div className="space-y-3">
          {data?.items.map((run: ResearchHistory) => (
            <div key={run.id} className="card p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  {run.status === 'completed' ? (
                    <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                  )}
                  <div>
                    <p className="text-sm font-medium text-white">{run.run_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(run.created_at).toLocaleString()} · {run.duration_seconds.toFixed(1)}s · by {run.triggered_by}
                    </p>
                  </div>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${run.status === 'completed' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`}>
                  {run.status}
                </span>
              </div>

              <div className="mt-3 grid grid-cols-2 md:grid-cols-5 gap-2 text-xs text-gray-400">
                <div><span className="font-medium text-gray-200">{run.trends_discovered}</span> trends</div>
                <div><span className="font-medium text-gray-200">{run.topics_researched}</span> topics</div>
                <div><span className="font-medium text-gray-200">{run.facts_verified}</span> facts verified</div>
                <div><span className="font-medium text-gray-200">{run.opportunities_scored}</span> scored</div>
                <div><span className="font-medium text-gray-200">{run.knowledge_docs_created}</span> knowledge docs</div>
              </div>

              {run.error_message && (
                <p className="mt-2 text-xs text-red-400 font-mono">{run.error_message}</p>
              )}
            </div>
          ))}
          {data?.items.length === 0 && (
            <div className="text-center py-16 text-gray-500">No history records yet</div>
          )}
          {data && data.meta.total_pages > 1 && (
            <div className="flex justify-center gap-2 pt-2">
              <button className="btn-secondary text-sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Previous</button>
              <span className="text-gray-400 text-sm self-center">Page {page} of {data.meta.total_pages}</span>
              <button className="btn-secondary text-sm" disabled={page >= data.meta.total_pages} onClick={() => setPage(p => p + 1)}>Next</button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
