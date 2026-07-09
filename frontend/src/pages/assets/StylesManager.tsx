import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listStyles, listLightingPresets, listPosePresets, listExpressionPresets, type AssetStyle, type LightingPreset, type PosePreset, type ExpressionPreset } from '@/api/assets'

type TabKey = 'styles' | 'lighting' | 'poses' | 'expressions'

export default function StylesManager() {
  const [tab, setTab] = useState<TabKey>('styles')
  const [styles, setStyles] = useState<AssetStyle[]>([])
  const [lighting, setLighting] = useState<LightingPreset[]>([])
  const [poses, setPoses] = useState<PosePreset[]>([])
  const [expressions, setExpressions] = useState<ExpressionPreset[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      listStyles().then(r => setStyles(r.data.items)),
      listLightingPresets().then(r => setLighting(r.data.items)),
      listPosePresets().then(r => setPoses(r.data.items)),
      listExpressionPresets().then(r => setExpressions(r.data.items)),
    ]).finally(() => setLoading(false))
  }, [])

  const TABS: { key: TabKey; label: string; count: number }[] = [
    { key: 'styles', label: 'Visual Styles', count: styles.length },
    { key: 'lighting', label: 'Lighting', count: lighting.length },
    { key: 'poses', label: 'Poses', count: poses.length },
    { key: 'expressions', label: 'Expressions', count: expressions.length },
  ]

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <div className="flex items-center gap-4 mb-6">
        <Link to="/assets" className="text-gray-400 hover:text-white text-sm">← Dashboard</Link>
        <h1 className="text-2xl font-bold">Styles & Presets</h1>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-700 mb-6">
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium ${tab === t.key ? 'text-white border-b-2 border-indigo-500' : 'text-gray-400 hover:text-white'}`}
          >
            {t.label}
            {t.count > 0 && (
              <span className="ml-2 text-xs bg-gray-700 text-gray-300 px-1.5 py-0.5 rounded-full">{t.count}</span>
            )}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-gray-400 text-sm">Loading presets…</p>
      ) : (
        <>
          {tab === 'styles' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {styles.length === 0 ? (
                <p className="text-gray-400 text-sm col-span-3">No styles configured. Styles are seeded automatically on first generation.</p>
              ) : styles.map(s => (
                <div key={s.id} className={`bg-gray-800 rounded-xl border p-4 ${s.is_default ? 'border-indigo-500/50' : 'border-gray-700'}`}>
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="text-sm font-semibold text-white">{s.name}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{s.style_type}</p>
                    </div>
                    {s.is_default && (
                      <span className="text-xs bg-indigo-900/50 text-indigo-300 px-2 py-0.5 rounded-full border border-indigo-700">default</span>
                    )}
                  </div>
                  <p className="text-xs text-gray-400 mb-3 line-clamp-2">{s.description || 'No description'}</p>
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>Used {s.usage_count}×</span>
                    <span>Avg quality: {s.avg_quality_score.toFixed(0)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {tab === 'lighting' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {lighting.length === 0 ? (
                <p className="text-gray-400 text-sm">No lighting presets configured.</p>
              ) : lighting.map(l => (
                <div key={l.id} className="bg-gray-800 rounded-xl border border-gray-700 p-4">
                  <p className="text-sm font-semibold text-white">{l.name}</p>
                  <p className="text-xs text-gray-400 mt-0.5 mb-2">{l.lighting_type} · {l.time_of_day} · {l.weather}</p>
                  <p className="text-xs text-gray-500 line-clamp-2">{l.lighting_prompt || 'No prompt'}</p>
                  <div className="flex gap-3 mt-3 text-xs text-gray-500">
                    <span>Intensity: {(l.intensity * 100).toFixed(0)}%</span>
                    <span>{l.color_temperature}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {tab === 'poses' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {poses.length === 0 ? (
                <p className="text-gray-400 text-sm">No pose presets configured.</p>
              ) : poses.map(p => (
                <div key={p.id} className="bg-gray-800 rounded-xl border border-gray-700 p-4">
                  <p className="text-sm font-semibold text-white">{p.name}</p>
                  <p className="text-xs text-gray-400 mt-0.5 mb-2">{p.pose_type} · {p.body_orientation}</p>
                  <p className="text-xs text-gray-500 line-clamp-2">{p.pose_prompt || 'No prompt'}</p>
                  <div className="flex gap-3 mt-3 text-xs text-gray-500">
                    <span>Used {p.use_count}×</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {tab === 'expressions' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {expressions.length === 0 ? (
                <p className="text-gray-400 text-sm">No expression presets configured.</p>
              ) : expressions.map(e => (
                <div key={e.id} className="bg-gray-800 rounded-xl border border-gray-700 p-4">
                  <p className="text-sm font-semibold text-white">{e.name}</p>
                  <p className="text-xs text-gray-400 mt-0.5 mb-2">{e.expression_type} · intensity {(e.intensity * 100).toFixed(0)}%</p>
                  <p className="text-xs text-gray-500 line-clamp-2">{e.expression_prompt || 'No prompt'}</p>
                  <div className="flex gap-3 mt-3 text-xs text-gray-500">
                    <span>Used {e.use_count}×</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
