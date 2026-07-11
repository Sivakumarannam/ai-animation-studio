import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ShieldCheck, ChevronRight } from 'lucide-react'
import { assetGenerationApi } from '@/api/assetGeneration'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.min(100, Math.max(0, value))
  const color = pct >= 80 ? 'bg-green-500' : pct >= 60 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-400 w-32 flex-shrink-0">{label}</span>
      <div className="flex-1 bg-gray-700 rounded-full h-1.5">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-300 w-8 text-right">{value.toFixed(0)}</span>
    </div>
  )
}

export function QualityEvaluationPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const [assetId, setAssetId] = useState('')
  const [inputVal, setInputVal] = useState('')
  const [assetPage, setAssetPage] = useState(1)
  const [evalPage, setEvalPage] = useState(1)

  const { data: assetList, isLoading: assetsLoading } = useQuery({
    queryKey: ['ag-assets-selector', projectId, assetPage],
    queryFn: () => assetGenerationApi.listAssets(projectId!, { page: assetPage, page_size: 20 }),
    enabled: !!projectId,
  })

  const { data: evals, isLoading: evalsLoading } = useQuery({
    queryKey: ['ag-evaluations', assetId, evalPage],
    queryFn: () => assetGenerationApi.listEvaluations(assetId, evalPage, 20),
    enabled: !!assetId,
  })

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
        <span>Asset Generation</span>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300">Quality Evaluation</span>
      </div>

      <h1 className="text-2xl font-bold text-white flex items-center gap-2">
        <ShieldCheck className="w-6 h-6 text-green-400" />
        Quality Evaluation
      </h1>
      <p className="text-gray-400 text-sm">Select an asset to view its quality evaluations.</p>

      {/* Asset Selector */}
      <div className="card p-4">
        <h2 className="text-sm font-semibold text-gray-300 mb-3">Select Asset</h2>
        {assetsLoading ? (
          <div className="flex justify-center py-4"><Spinner /></div>
        ) : assetList?.items.length === 0 ? (
          <p className="text-sm text-gray-500">No assets found for this project.</p>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-52 overflow-y-auto">
              {assetList?.items.map((asset) => (
                <button
                  key={asset.id}
                  onClick={() => { setAssetId(asset.id); setEvalPage(1) }}
                  className={`text-left p-2 rounded text-sm transition-colors ${assetId === asset.id ? 'bg-brand-600/30 text-brand-300 border border-brand-500' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}
                >
                  <p className="font-medium truncate">{asset.name}</p>
                  <p className="text-xs text-gray-500">{asset.asset_type} · {asset.status}</p>
                </button>
              ))}
            </div>
            {assetList && assetList.meta.total_pages > 1 && (
              <div className="flex gap-2 mt-2">
                <button disabled={assetPage <= 1} onClick={() => setAssetPage(p => p - 1)} className="btn-secondary text-xs px-2 py-1">Prev</button>
                <span className="text-xs text-gray-400 self-center">{assetPage}/{assetList.meta.total_pages}</span>
                <button disabled={assetPage >= assetList.meta.total_pages} onClick={() => setAssetPage(p => p + 1)} className="btn-secondary text-xs px-2 py-1">Next</button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Evaluations */}
      {!assetId ? (
        <EmptyState icon={ShieldCheck} title="No asset selected" description="Pick an asset above to view its quality evaluations." />
      ) : evalsLoading ? (
        <div className="flex justify-center py-12"><Spinner size="lg" /></div>
      ) : evals?.items.length === 0 ? (
        <EmptyState icon={ShieldCheck} title="No evaluations yet" description="Quality evaluations appear after the AI evaluates generated assets." />
      ) : (
        <>
          <div className="space-y-4">
            {evals?.items.map((ev) => (
              <div key={ev.id} className="card p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className={`text-lg font-bold ${ev.overall_score >= 80 ? 'text-green-400' : ev.overall_score >= 60 ? 'text-yellow-400' : 'text-red-400'}`}>
                        {ev.overall_score.toFixed(1)}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${ev.passed_threshold ? 'bg-green-900/40 text-green-400' : 'bg-red-900/40 text-red-400'}`}>
                        {ev.passed_threshold ? 'Passed' : 'Failed'}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">by {ev.evaluated_by} · {new Date(ev.created_at).toLocaleString()}</p>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <ScoreBar label="Image Quality" value={ev.image_quality} />
                  <ScoreBar label="Prompt Quality" value={ev.prompt_quality} />
                  <ScoreBar label="Char. Consistency" value={ev.character_consistency} />
                  <ScoreBar label="Bg Consistency" value={ev.background_consistency} />
                  <ScoreBar label="Composition" value={ev.composition_score} />
                  <ScoreBar label="Lighting" value={ev.lighting_score} />
                  <ScoreBar label="Style Match" value={ev.style_match} />
                  <ScoreBar label="Face Score" value={ev.face_score} />
                  <ScoreBar label="Hands Score" value={ev.hands_score} />
                </div>

                {ev.failure_reasons.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs text-red-400 font-medium mb-1">Failure Reasons:</p>
                    <ul className="list-disc list-inside space-y-0.5">
                      {ev.failure_reasons.map((r, i) => (
                        <li key={i} className="text-xs text-red-300">{r}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {ev.notes && (
                  <p className="text-xs text-gray-400 mt-2 italic">{ev.notes}</p>
                )}
              </div>
            ))}
          </div>
          {evals && evals.meta.total_pages > 1 && (
            <div className="flex justify-center gap-2">
              <button disabled={evalPage <= 1} onClick={() => setEvalPage(p => p - 1)} className="btn-secondary text-sm px-3 py-1">Prev</button>
              <span className="text-sm text-gray-400 self-center">Page {evalPage} / {evals.meta.total_pages}</span>
              <button disabled={evalPage >= evals.meta.total_pages} onClick={() => setEvalPage(p => p + 1)} className="btn-secondary text-sm px-3 py-1">Next</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
