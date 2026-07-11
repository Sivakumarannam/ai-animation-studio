import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CheckCircle, XCircle, Clock } from 'lucide-react'
import { researchApi } from '@/api/research'
import { Spinner } from '@/components/ui/Spinner'

export function FactVerificationPage() {
  const [page, setPage] = useState(1)
  const [selectedTopicId, setSelectedTopicId] = useState<string | undefined>()

  const { data: topicsData } = useQuery({
    queryKey: ['research-topics-facts'],
    queryFn: () => researchApi.getTopics(1, 50, 'researched'),
  })

  const activeTopicId = selectedTopicId ?? topicsData?.items[0]?.id

  const { data: factsData, isLoading } = useQuery({
    queryKey: ['research-facts-verify', activeTopicId, page],
    queryFn: () => activeTopicId ? researchApi.getFacts(activeTopicId, page, 20) : null,
    enabled: !!activeTopicId,
  })

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <CheckCircle className="w-6 h-6 text-green-400" /> Fact Verification
        </h1>
        <p className="text-gray-400 text-sm mt-1">Cross-referenced facts with confidence scores and citations</p>
      </div>

      {/* Topic selector */}
      {topicsData && topicsData.items.length > 0 && (
        <div className="card p-3 flex items-center gap-3">
          <label className="text-sm text-gray-400 flex-shrink-0">Topic:</label>
          <select
            className="input flex-1"
            value={activeTopicId || ''}
            onChange={e => { setSelectedTopicId(e.target.value || undefined); setPage(1) }}
          >
            {topicsData.items.map(t => (
              <option key={t.id} value={t.id}>{t.canonical_name}</option>
            ))}
          </select>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card p-3 text-center">
          <p className="text-2xl font-bold text-green-400">{factsData?.items.filter(f => f.is_verified).length || 0}</p>
          <p className="text-xs text-gray-400">Verified</p>
        </div>
        <div className="card p-3 text-center">
          <p className="text-2xl font-bold text-red-400">{factsData?.items.filter(f => f.is_rejected).length || 0}</p>
          <p className="text-xs text-gray-400">Rejected</p>
        </div>
        <div className="card p-3 text-center">
          <p className="text-2xl font-bold text-yellow-400">{factsData?.items.filter(f => !f.is_verified && !f.is_rejected).length || 0}</p>
          <p className="text-xs text-gray-400">Pending</p>
        </div>
        <div className="card p-3 text-center">
          <p className="text-2xl font-bold text-brand-400">{factsData?.meta.total || 0}</p>
          <p className="text-xs text-gray-400">Total Facts</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : (
        <div className="space-y-3">
          {factsData?.items.map(fact => (
            <div key={fact.id} className="card p-4 space-y-2">
              <div className="flex items-start gap-3">
                <div className="mt-0.5 flex-shrink-0">
                  {fact.is_verified ? (
                    <CheckCircle className="w-4 h-4 text-green-400" />
                  ) : fact.is_rejected ? (
                    <XCircle className="w-4 h-4 text-red-400" />
                  ) : (
                    <Clock className="w-4 h-4 text-yellow-400" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white">{fact.statement}</p>
                  <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
                    <span>Confidence: <span className={`font-medium ${fact.confidence >= 0.7 ? 'text-green-400' : fact.confidence >= 0.4 ? 'text-yellow-400' : 'text-red-400'}`}>{(fact.confidence * 100).toFixed(0)}%</span></span>
                    <span>Verified: {fact.verification_count}x</span>
                    <span className="capitalize">{fact.fact_type}</span>
                  </div>
                  {fact.rejection_reason && (
                    <p className="text-xs text-red-400 mt-1">{fact.rejection_reason}</p>
                  )}
                  {fact.supporting_sources.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {fact.supporting_sources.map((s, i) => (
                        <span key={i} className="text-xs bg-green-900/40 text-green-300 px-1.5 py-0.5 rounded">{s}</span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          {(!factsData || factsData.items.length === 0) && !isLoading && (
            <div className="text-center py-16 text-gray-500">
              No facts available. Research a topic first, then run fact verification.
            </div>
          )}

          {/* Always show pagination indicator */}
          <div className="flex justify-center gap-2 pt-2">
            <button className="btn-secondary text-sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Previous</button>
            <span className="text-gray-400 text-sm self-center">Page {page} of {factsData?.meta.total_pages ?? 1}</span>
            <button className="btn-secondary text-sm" disabled={!factsData || page >= factsData.meta.total_pages} onClick={() => setPage(p => p + 1)}>Next</button>
          </div>
        </div>
      )}
    </div>
  )
}
