import React, { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import { videoAssemblyApi, VideoOutput } from "../../api/videoAssembly";

function formatBytes(b: number): string {
  if (b < 1024) return `${b} B`;
  if (b < 1048576) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / 1048576).toFixed(1)} MB`;
}

function formatDuration(s: number): string {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
}

const TYPE_COLOR: Record<string, string> = {
  episode_cut: "bg-indigo-100 text-indigo-800",
  short_form_cut: "bg-pink-100 text-pink-800",
  preview: "bg-gray-100 text-gray-600",
};

export default function VideoAssemblyOutputsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [outputs, setOutputs] = useState<VideoOutput[]>([]);
  const [meta, setMeta] = useState({ total: 0, page: 1, page_size: 20, total_pages: 1 });
  const [page, setPage] = useState(1);
  const [typeFilter, setTypeFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<VideoOutput | null>(null);

  const load = useCallback(async () => {
    if (!projectId) return;
    try {
      setLoading(true);
      setError("");
      const res = await videoAssemblyApi.listOutputs(projectId, {
        page,
        page_size: 20,
        output_type: typeFilter || undefined,
      });
      setOutputs(res.items);
      setMeta(res.meta);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [projectId, page, typeFilter]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Video Outputs</h1>
        <select
          className="border rounded-lg px-3 py-2 text-sm"
          value={typeFilter}
          onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
        >
          <option value="">All types</option>
          <option value="episode_cut">Episode Cut</option>
          <option value="short_form_cut">Short-form Cut</option>
          <option value="preview">Preview</option>
        </select>
      </div>

      {loading ? (
        <div className="text-gray-400 py-12 text-center">Loading…</div>
      ) : error ? (
        <div className="text-red-600 py-6">{error}</div>
      ) : outputs.length === 0 ? (
        <div className="text-gray-400 py-12 text-center bg-gray-50 rounded-xl">
          No video outputs yet. Assemble an episode first.
        </div>
      ) : (
        <>
          <div className="space-y-3 mb-6">
            {outputs.map((o) => (
              <div
                key={o.id}
                className="bg-white border rounded-xl px-5 py-4 cursor-pointer hover:border-red-300 transition"
                onClick={() => setSelected(o)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${TYPE_COLOR[o.output_type] ?? "bg-gray-100"}`}>
                        {o.output_type}
                      </span>
                      {o.quality_passed ? (
                        <span className="text-xs text-green-600">✓ Quality {o.quality_score.toFixed(0)}%</span>
                      ) : (
                        <span className="text-xs text-red-600">✗ Quality {o.quality_score.toFixed(0)}%</span>
                      )}
                    </div>
                    <p className="font-mono text-xs text-gray-400">{o.id}</p>
                    <div className="flex flex-wrap gap-4 mt-2 text-sm text-gray-700">
                      <span>⏱ {formatDuration(o.duration_seconds)}</span>
                      <span>🎬 {o.scene_count} scenes</span>
                      <span>📐 {o.width}×{o.height}</span>
                      <span>💾 {formatBytes(o.file_size_bytes)}</span>
                      <span>🔧 {o.provider}</span>
                    </div>
                    <div className="flex gap-3 mt-1 text-xs text-gray-400">
                      {o.has_voice && <span>🎙 Voice</span>}
                      {o.has_music && <span>🎵 Music</span>}
                      {o.has_subtitles && <span>💬 Subtitles</span>}
                    </div>
                  </div>
                  <div className="text-xs text-gray-400 ml-4 shrink-0">
                    {new Date(o.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between text-sm text-gray-500">
            <span>{meta.total} total</span>
            <div className="flex gap-2">
              <button className="px-3 py-1 border rounded disabled:opacity-40" onClick={() => setPage(p => p - 1)} disabled={page === 1}>‹ Prev</button>
              <span className="px-2">{page} / {meta.total_pages}</span>
              <button className="px-3 py-1 border rounded disabled:opacity-40" onClick={() => setPage(p => p + 1)} disabled={page >= meta.total_pages}>Next ›</button>
            </div>
          </div>
        </>
      )}

      {/* Output detail / video preview modal */}
      {selected && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden">
            <div className="px-6 py-4 border-b flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-900">Video Output</h2>
              <button onClick={() => setSelected(null)} className="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
            </div>

            <div className="p-6">
              {/* Video player — shows native controls; storage_key displayed as source info */}
              <div className="bg-gray-900 rounded-xl flex items-center justify-center mb-5"
                style={{ aspectRatio: "16/9" }}>
                {selected.storage_key.startsWith("mock://") ? (
                  <div className="text-center text-gray-400 py-8">
                    <div className="text-4xl mb-2">🎬</div>
                    <p className="text-sm">Mock output — no real file to play.</p>
                    <p className="text-xs mt-1 font-mono opacity-60">{selected.storage_key}</p>
                  </div>
                ) : (
                  <video
                    controls
                    className="w-full h-full rounded-xl"
                    src={`/api/v1/va/outputs/${selected.id}/stream`}
                  >
                    Your browser does not support the video tag.
                  </video>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                {[
                  ["Duration", formatDuration(selected.duration_seconds)],
                  ["Resolution", `${selected.width}×${selected.height} @ ${selected.fps}fps`],
                  ["Size", formatBytes(selected.file_size_bytes)],
                  ["Scenes", String(selected.scene_count)],
                  ["Provider", selected.provider],
                  ["Type", selected.output_type],
                  ["Quality", `${selected.quality_score.toFixed(1)}% ${selected.quality_passed ? "✓" : "✗"}`],
                  ["Format", selected.format.toUpperCase()],
                ].map(([k, v]) => (
                  <div key={k} className="bg-gray-50 rounded-lg px-3 py-2">
                    <p className="text-xs text-gray-400">{k}</p>
                    <p className="font-medium text-gray-800">{v}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
