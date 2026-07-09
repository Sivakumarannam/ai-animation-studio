import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  getAsset, listAssetVersions, listEvaluations, promoteVersion, triggerAssetGeneration,
  type Asset, type AssetVersion, type AssetEvaluation,
} from '@/api/assets'

const SCORE_FIELDS: [string, string][] = [
  ['overall_score', 'Overall'],
  ['image_quality', 'Image Quality'],
  ['prompt_quality', 'Prompt Quality'],
  ['character_consistency', 'Char. Consistency'],
  ['composition_score', 'Composition'],
  ['lighting_score', 'Lighting'],
  ['style_match', 'Style Match'],
  ['face_score', 'Face Score'],
  ['hands_score', 'Hands Score'],
]

function ScoreBar({ label, score }: { label: string; score: number }) {
  const color = score >= 90 ? 'bg-green-500' : score >= 70 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-gray-400 w-36 shrink-0">{label}</span>
      <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${score}%` }} />
      </div>
      <span className={`text-xs font-medium w-10 text-right ${score >= 90 ? 'text-green-400' : score >= 70 ? 'text-yellow-400' : 'text-red-400'}`}>
        {score.toFixed(0)}
      </span>
    </div>
  )
}

export default function AssetViewer() {
  const { id } = useParams<{ id: string }>()
  const [asset, setAsset] = useState<Asset | null>(null)
  const [versions, setVersions] = useState<AssetVersion[]>([])
  const [evaluations, setEvaluations] = useState<AssetEvaluation[]>([])
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<'versions' | 'evaluations'>('evaluations')

  const load = () => {
    if (!id) return
    getAsset(id).then(r => setAsset(r.data)).catch(() => setError('Asset not found'))
    listAssetVersions(id).then(r => setVersions(r.data.items))
    listEvaluations(id).then(r => setEvaluations(r.data.items))
  }

  useEffect(() => { load() }, [id])

  const handleGenerate = async () => {
    if (!id) return
    setGenerating(true)
    setError(null)
    try {
      await triggerAssetGeneration(id, true)
      setTimeout(load, 3000) // refresh after 3s
    } catch {
      setError('Generation dispatch failed')
    } finally {
      setGenerating(false)
    }
  }

  const handlePromote = async (versionId: string) => {
    if (!id) return
    await promoteVersion(id, versionId)
    load()
  }

  if (!asset) {
    return (
      <div className="min-h-screen bg-gray-950 text-white p-6 flex items-center justify-center">
        <p className="text-gray-400">{error ?? 'Loading…'}</p>
      </div>
    )
  }

  const latestEval = evaluations[0]

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <div className="flex items-center gap-4 mb-6">
        <Link to="/assets/library" className="text-gray-400 hover:text-white text-sm">← Library</Link>
        <div className="flex-1">
          <h1 className="text-xl font-bold">{asset.name}</h1>
          <p className="text-sm text-gray-400 capitalize">{asset.asset_type.replace('_', ' ')} · {asset.status}</p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors"
        >
          {generating ? 'Dispatching…' : 'Regenerate'}
        </button>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-3 text-red-300 text-sm mb-4">{error}</div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Asset image */}
        <div>
          <div className="bg-gray-800 rounded-xl border border-gray-700 aspect-square flex items-center justify-center overflow-hidden">
            {asset.storage_key ? (
              <img
                src={`/api/v1/assets/file/${asset.storage_key}`}
                alt={asset.name}
                className="w-full h-full object-contain"
                onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
              />
            ) : (
              <div className="text-6xl opacity-20">🎨</div>
            )}
          </div>
          {/* Quality overview */}
          {latestEval && (
            <div className="mt-4 bg-gray-800 rounded-xl border border-gray-700 p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-gray-300">Quality Evaluation</h3>
                <span className={`text-xs px-2 py-0.5 rounded-full border ${latestEval.passed_threshold ? 'bg-green-900/50 text-green-300 border-green-700' : 'bg-red-900/50 text-red-300 border-red-700'}`}>
                  {latestEval.passed_threshold ? '✓ Passed' : '✗ Failed'}
                </span>
              </div>
              <div className="space-y-2">
                {SCORE_FIELDS.map(([field, label]) => (
                  <ScoreBar key={field} label={label} score={(latestEval as never)[field] as number} />
                ))}
              </div>
              {latestEval.failure_reasons.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-700">
                  <p className="text-xs text-gray-400 mb-1">Failure reasons:</p>
                  <div className="flex flex-wrap gap-1">
                    {latestEval.failure_reasons.map(r => (
                      <span key={r} className="text-xs bg-red-900/30 text-red-300 px-2 py-0.5 rounded-full border border-red-800">{r}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Tabs: versions / evaluations */}
        <div>
          <div className="flex border-b border-gray-700 mb-4">
            {(['evaluations', 'versions'] as const).map(t => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-4 py-2 text-sm font-medium capitalize ${tab === t ? 'text-white border-b-2 border-indigo-500' : 'text-gray-400 hover:text-white'}`}
              >
                {t} ({t === 'versions' ? versions.length : evaluations.length})
              </button>
            ))}
          </div>

          {tab === 'versions' ? (
            <div className="space-y-3">
              {versions.length === 0 ? (
                <p className="text-gray-400 text-sm">No versions yet.</p>
              ) : (
                versions.map(v => (
                  <div key={v.id} className={`bg-gray-800 rounded-xl border p-4 ${v.id === asset.best_version_id ? 'border-indigo-500/50' : 'border-gray-700'}`}>
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <span className="text-sm font-medium text-white">v{v.version_number}</span>
                        {v.id === asset.best_version_id && (
                          <span className="ml-2 text-xs bg-indigo-900/50 text-indigo-300 px-2 py-0.5 rounded-full border border-indigo-700">best</span>
                        )}
                      </div>
                      <div className="flex gap-2">
                        <span className={`text-xs font-medium ${v.quality_score >= 90 ? 'text-green-400' : v.quality_score >= 70 ? 'text-yellow-400' : 'text-red-400'}`}>
                          {v.quality_score.toFixed(1)}
                        </span>
                        {v.id !== asset.best_version_id && (
                          <button
                            onClick={() => handlePromote(v.id)}
                            className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                          >
                            Promote
                          </button>
                        )}
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-xs text-gray-400">
                      <span>Steps: {v.generation_steps}</span>
                      <span>CFG: {v.cfg_scale}</span>
                      <span>{v.sampler}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {evaluations.length === 0 ? (
                <p className="text-gray-400 text-sm">No evaluations yet.</p>
              ) : (
                evaluations.map(e => (
                  <div key={e.id} className="bg-gray-800 rounded-xl border border-gray-700 p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-gray-400">{new Date(e.created_at).toLocaleString()}</span>
                      <span className={`text-xs font-semibold ${e.passed_threshold ? 'text-green-400' : 'text-red-400'}`}>
                        {e.overall_score.toFixed(1)} — {e.passed_threshold ? 'Passed' : 'Failed'}
                      </span>
                    </div>
                    {e.failure_reasons.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {e.failure_reasons.map(r => (
                          <span key={r} className="text-xs text-red-300 bg-red-900/20 px-2 py-0.5 rounded border border-red-800">{r}</span>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
