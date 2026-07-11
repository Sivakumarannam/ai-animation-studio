import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { MessageSquare, ChevronRight } from 'lucide-react'
import { assetGenerationApi } from '@/api/assetGeneration'
import type { AssetPromptResponse } from '@/api/assetGeneration'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Modal } from '@/components/ui/Modal'

export function PromptMonitoringPage() {
  const [page, setPage] = useState(1)
  const [successfulOnly, setSuccessfulOnly] = useState(false)
  const [promptType, setPromptType] = useState('')
  const [selected, setSelected] = useState<AssetPromptResponse | null>(null)
  const [detailId, setDetailId] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['ag-prompts', page, successfulOnly, promptType],
    queryFn: () =>
      assetGenerationApi.listPrompts({
        page,
        page_size: 20,
        successful_only: successfulOnly,
        prompt_type: promptType || undefined,
      }),
  })

  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ['ag-prompt', detailId],
    queryFn: () => assetGenerationApi.getPrompt(detailId!),
    enabled: !!detailId,
  })

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
        <span>Asset Generation</span>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300">Prompt Monitoring</span>
      </div>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <MessageSquare className="w-6 h-6 text-purple-400" />
          Prompt Monitoring
        </h1>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <select
          value={promptType}
          onChange={(e) => { setPromptType(e.target.value); setPage(1) }}
          className="input text-sm py-1.5"
        >
          <option value="">All Types</option>
          <option value="character">Character</option>
          <option value="background">Background</option>
          <option value="prop">Prop</option>
          <option value="scene_layout">Scene Layout</option>
        </select>
        <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
          <input
            type="checkbox"
            checked={successfulOnly}
            onChange={(e) => { setSuccessfulOnly(e.target.checked); setPage(1) }}
            className="rounded"
          />
          Successful only
        </label>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : data?.items.length === 0 ? (
        <EmptyState icon={MessageSquare} title="No prompts found" description="Prompts appear here after generation runs." />
      ) : (
        <>
          <div className="space-y-2">
            {data?.items.map((prompt) => (
              <div
                key={prompt.id}
                className="card p-4 cursor-pointer hover:bg-gray-800 transition-colors"
                onClick={() => { setDetailId(prompt.id); setSelected(prompt) }}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="badge-gray text-xs">{prompt.prompt_type}</span>
                      {prompt.was_successful ? (
                        <span className="text-xs text-green-400">✓ successful</span>
                      ) : (
                        <span className="text-xs text-red-400">✗ failed</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-300 line-clamp-2">{prompt.full_prompt || prompt.positive_prompt || '—'}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-lg font-bold text-white">{prompt.quality_score.toFixed(0)}</p>
                    <p className="text-xs text-gray-500">quality</p>
                    <p className="text-xs text-gray-500 mt-1">used {prompt.use_count}×</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {data && data.meta.total_pages > 1 && (
            <div className="flex justify-center gap-2">
              <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="btn-secondary text-sm px-3 py-1">Prev</button>
              <span className="text-sm text-gray-400 self-center">Page {page} / {data.meta.total_pages}</span>
              <button disabled={page >= data.meta.total_pages} onClick={() => setPage(p => p + 1)} className="btn-secondary text-sm px-3 py-1">Next</button>
            </div>
          )}
        </>
      )}

      {/* Detail Modal */}
      <Modal title="Prompt Detail" open={!!detailId} onClose={() => { setDetailId(null); setSelected(null) }}>
        {detailLoading ? (
          <div className="flex justify-center py-8"><Spinner /></div>
        ) : detail ? (
          <div className="space-y-3 text-sm">
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div><span className="text-gray-400">Type:</span> <span className="text-white">{detail.prompt_type}</span></div>
              <div><span className="text-gray-400">Quality:</span> <span className="text-white">{detail.quality_score.toFixed(1)}</span></div>
              <div><span className="text-gray-400">Successful:</span> <span className={detail.was_successful ? 'text-green-400' : 'text-red-400'}>{detail.was_successful ? 'Yes' : 'No'}</span></div>
              <div><span className="text-gray-400">Used:</span> <span className="text-white">{detail.use_count}×</span></div>
            </div>
            {detail.positive_prompt && (
              <div>
                <p className="text-xs text-gray-400 mb-1">Positive Prompt</p>
                <p className="text-gray-200 text-xs bg-gray-800 rounded p-2">{detail.positive_prompt}</p>
              </div>
            )}
            {detail.negative_prompt && (
              <div>
                <p className="text-xs text-gray-400 mb-1">Negative Prompt</p>
                <p className="text-gray-200 text-xs bg-gray-800 rounded p-2">{detail.negative_prompt}</p>
              </div>
            )}
            {detail.style_prompt && (
              <div>
                <p className="text-xs text-gray-400 mb-1">Style</p>
                <p className="text-gray-200 text-xs bg-gray-800 rounded p-2">{detail.style_prompt}</p>
              </div>
            )}
            {detail.lighting_prompt && (
              <div>
                <p className="text-xs text-gray-400 mb-1">Lighting</p>
                <p className="text-gray-200 text-xs bg-gray-800 rounded p-2">{detail.lighting_prompt}</p>
              </div>
            )}
            <p className="text-xs text-gray-500">{new Date(detail.created_at).toLocaleString()}</p>
          </div>
        ) : selected ? (
          <div className="text-sm text-gray-300">
            <p className="mb-2">{selected.full_prompt || selected.positive_prompt}</p>
          </div>
        ) : null}
      </Modal>
    </div>
  )
}
