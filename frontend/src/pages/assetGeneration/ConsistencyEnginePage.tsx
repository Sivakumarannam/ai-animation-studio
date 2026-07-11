import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Layers, ChevronRight } from 'lucide-react'
import { assetGenerationApi } from '@/api/assetGeneration'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'

export function ConsistencyEnginePage() {
  const { projectId } = useParams<{ projectId: string }>()
  const [tab, setTab] = useState<'compositions' | 'shots'>('compositions')
  const [compPage, setCompPage] = useState(1)
  const [episodeId, setEpisodeId] = useState('')
  const [shotPage, setShotPage] = useState(1)

  const { data: compositions, isLoading: compLoading } = useQuery({
    queryKey: ['ag-compositions', projectId, compPage],
    queryFn: () => assetGenerationApi.listCompositions(projectId!, compPage, 20),
    enabled: !!projectId && tab === 'compositions',
  })

  const { data: shots, isLoading: shotsLoading } = useQuery({
    queryKey: ['ag-shots', episodeId, shotPage],
    queryFn: () => assetGenerationApi.listShots(episodeId, shotPage, 50),
    enabled: !!episodeId && tab === 'shots',
  })

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
        <span>Asset Generation</span>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300">Consistency Engine</span>
      </div>

      <h1 className="text-2xl font-bold text-white flex items-center gap-2">
        <Layers className="w-6 h-6 text-teal-400" />
        Consistency Engine
      </h1>
      <p className="text-gray-400 text-sm">Review scene compositions and camera shots for visual consistency.</p>

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-gray-900 rounded-lg w-fit">
        <button
          onClick={() => setTab('compositions')}
          className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${tab === 'compositions' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-gray-200'}`}
        >
          Scene Compositions
        </button>
        <button
          onClick={() => setTab('shots')}
          className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${tab === 'shots' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-gray-200'}`}
        >
          Camera Shots
        </button>
      </div>

      {tab === 'compositions' && (
        <>
          {compLoading ? (
            <div className="flex justify-center py-20"><Spinner size="lg" /></div>
          ) : compositions?.items.length === 0 ? (
            <EmptyState icon={Layers} title="No compositions" description="Scene compositions appear here after generation runs." />
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {compositions?.items.map((comp) => (
                  <div key={comp.id} className="card p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="text-sm font-semibold text-white">{comp.name || 'Unnamed Composition'}</h3>
                      <span className="badge-gray text-xs">{comp.composition_type}</span>
                    </div>
                    <p className="text-xs text-gray-400 mb-3 line-clamp-2">{comp.description || comp.composition_prompt || '—'}</p>
                    <div className="grid grid-cols-3 gap-1 text-xs">
                      <div>
                        <p className="text-gray-500 mb-1">Foreground</p>
                        {comp.foreground_elements.slice(0, 2).map((e, i) => (
                          <p key={i} className="text-gray-300 truncate">{e}</p>
                        ))}
                        {comp.foreground_elements.length === 0 && <p className="text-gray-600">—</p>}
                      </div>
                      <div>
                        <p className="text-gray-500 mb-1">Midground</p>
                        {comp.midground_elements.slice(0, 2).map((e, i) => (
                          <p key={i} className="text-gray-300 truncate">{e}</p>
                        ))}
                        {comp.midground_elements.length === 0 && <p className="text-gray-600">—</p>}
                      </div>
                      <div>
                        <p className="text-gray-500 mb-1">Background</p>
                        {comp.background_elements.slice(0, 2).map((e, i) => (
                          <p key={i} className="text-gray-300 truncate">{e}</p>
                        ))}
                        {comp.background_elements.length === 0 && <p className="text-gray-600">—</p>}
                      </div>
                    </div>
                    {comp.focus_point && (
                      <p className="text-xs text-gray-500 mt-2">Focus: {comp.focus_point}</p>
                    )}
                    {comp.color_harmony && (
                      <p className="text-xs text-gray-500">Harmony: {comp.color_harmony}</p>
                    )}
                  </div>
                ))}
              </div>
              {compositions && compositions.meta.total_pages > 1 && (
                <div className="flex justify-center gap-2">
                  <button disabled={compPage <= 1} onClick={() => setCompPage(p => p - 1)} className="btn-secondary text-sm px-3 py-1">Prev</button>
                  <span className="text-sm text-gray-400 self-center">Page {compPage} / {compositions.meta.total_pages}</span>
                  <button disabled={compPage >= compositions.meta.total_pages} onClick={() => setCompPage(p => p + 1)} className="btn-secondary text-sm px-3 py-1">Next</button>
                </div>
              )}
            </>
          )}
        </>
      )}

      {tab === 'shots' && (
        <>
          <div className="flex gap-3">
            <input
              className="input text-sm py-1.5 flex-1 max-w-xs"
              placeholder="Episode ID (UUID)"
              value={episodeId}
              onChange={(e) => { setEpisodeId(e.target.value); setShotPage(1) }}
            />
          </div>
          {!episodeId ? (
            <EmptyState icon={Layers} title="Enter an Episode ID" description="Type an episode UUID above to load its camera shots." />
          ) : shotsLoading ? (
            <div className="flex justify-center py-20"><Spinner size="lg" /></div>
          ) : shots?.items.length === 0 ? (
            <EmptyState icon={Layers} title="No shots for this episode" description="Camera shots appear after generation runs for this episode." />
          ) : (
            <>
              <div className="space-y-2">
                {shots?.items.map((shot) => (
                  <div key={shot.id} className="card p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-bold text-gray-300">#{shot.shot_order}</span>
                          <span className="badge-gray text-xs">{shot.shot_type}</span>
                          {shot.camera_movement && (
                            <span className="text-xs text-gray-500">{shot.camera_movement}</span>
                          )}
                        </div>
                        <p className="text-sm text-gray-300 line-clamp-2">{shot.description || shot.camera_prompt || '—'}</p>
                        {shot.focal_length && (
                          <p className="text-xs text-gray-500 mt-1">Focal: {shot.focal_length} · DoF: {shot.depth_of_field}</p>
                        )}
                      </div>
                      <div className="text-right flex-shrink-0">
                        <p className="text-lg font-bold text-white">{shot.quality_score.toFixed(0)}</p>
                        <p className="text-xs text-gray-500">quality</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              {shots && shots.meta.total_pages > 1 && (
                <div className="flex justify-center gap-2">
                  <button disabled={shotPage <= 1} onClick={() => setShotPage(p => p - 1)} className="btn-secondary text-sm px-3 py-1">Prev</button>
                  <span className="text-sm text-gray-400 self-center">Page {shotPage} / {shots.meta.total_pages}</span>
                  <button disabled={shotPage >= shots.meta.total_pages} onClick={() => setShotPage(p => p + 1)} className="btn-secondary text-sm px-3 py-1">Next</button>
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  )
}
