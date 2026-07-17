import React, { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import { videoAssemblyApi, VideoAssemblyJob, TriggerAssembleEpisodeRequest } from "../../api/videoAssembly";

const STATUS_COLOR: Record<string, string> = {
  completed: "bg-green-100 text-green-800",
  pending: "bg-yellow-100 text-yellow-800",
  running: "bg-blue-100 text-blue-800",
  failed: "bg-red-100 text-red-800",
};

export default function VideoAssemblyJobsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [jobs, setJobs] = useState<VideoAssemblyJob[]>([]);
  const [meta, setMeta] = useState({ total: 0, page: 1, page_size: 20, total_pages: 1 });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<TriggerAssembleEpisodeRequest>({
    project_id: projectId ?? "",
    episode_id: null,
    output_type: "episode_cut",
  });
  const [dispatching, setDispatching] = useState(false);
  const [dispatchMsg, setDispatchMsg] = useState("");

  const load = useCallback(async () => {
    if (!projectId) return;
    try {
      setLoading(true);
      setError("");
      const res = await videoAssemblyApi.listJobs(projectId, { page, page_size: 20 });
      setJobs(res.items);
      setMeta(res.meta);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [projectId, page]);

  useEffect(() => { load(); }, [load]);

  const handleAssemble = async () => {
    if (!projectId) return;
    setDispatching(true);
    setDispatchMsg("");
    try {
      const res = await videoAssemblyApi.triggerAssembleEpisode({ ...form, project_id: projectId });
      setDispatchMsg(`✓ Dispatched — job ${res.job_id}`);
      setShowModal(false);
      setTimeout(load, 1500);
    } catch (e: any) {
      setDispatchMsg(`✗ ${e.message}`);
    } finally {
      setDispatching(false);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Assembly Jobs</h1>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium"
        >
          + Assemble Video
        </button>
      </div>

      {dispatchMsg && (
        <div className={`mb-4 p-3 rounded-lg text-sm ${dispatchMsg.startsWith("✓") ? "bg-green-50 text-green-800" : "bg-red-50 text-red-700"}`}>
          {dispatchMsg}
        </div>
      )}

      {loading ? (
        <div className="text-gray-400 py-12 text-center">Loading…</div>
      ) : error ? (
        <div className="text-red-600 py-6">{error}</div>
      ) : jobs.length === 0 ? (
        <div className="text-gray-400 py-12 text-center bg-gray-50 rounded-xl">
          No assembly jobs found.
        </div>
      ) : (
        <>
          <div className="space-y-2 mb-6">
            {jobs.map((j) => (
              <div key={j.id} className="bg-white border rounded-xl px-4 py-3 flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs text-gray-400">{j.id.slice(0, 8)}…</span>
                    <span className="text-sm font-medium text-gray-800">{j.job_type}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLOR[j.status] ?? "bg-gray-100"}`}>
                      {j.status}
                    </span>
                  </div>
                  {j.episode_id && (
                    <p className="text-xs text-gray-400 mt-1">Episode: {j.episode_id}</p>
                  )}
                  {j.result && (j.result as any).duration_seconds != null && (
                    <p className="text-xs text-gray-500 mt-1">
                      Duration: {((j.result as any).duration_seconds as number).toFixed(1)}s
                      {(j.result as any).quality_score != null && ` · Quality: ${(j.result as any).quality_score}%`}
                    </p>
                  )}
                  {j.error_message && (
                    <p className="text-xs text-red-500 mt-1 truncate">{j.error_message}</p>
                  )}
                </div>
                <div className="text-xs text-gray-400 ml-4 shrink-0">
                  {new Date(j.created_at).toLocaleString()}
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

      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
            <h2 className="text-xl font-bold mb-4">Assemble Video</h2>

            <label className="block text-sm font-medium text-gray-700 mb-1">Episode ID (optional)</label>
            <input
              type="text"
              className="w-full border rounded-lg px-3 py-2 mb-4 text-sm font-mono"
              placeholder="Leave blank to assemble all available scenes"
              value={form.episode_id ?? ""}
              onChange={(e) => setForm({ ...form, episode_id: e.target.value || null })}
            />

            <label className="block text-sm font-medium text-gray-700 mb-1">Output type</label>
            <select
              className="w-full border rounded-lg px-3 py-2 mb-4 text-sm"
              value={form.output_type}
              onChange={(e) => setForm({ ...form, output_type: e.target.value as any })}
            >
              <option value="episode_cut">Episode Cut</option>
              <option value="short_form_cut">Short-form Cut (≤30 s)</option>
            </select>

            {dispatchMsg && <div className="mb-3 text-sm text-red-600">{dispatchMsg}</div>}

            <div className="flex gap-3">
              <button
                className="flex-1 bg-red-600 text-white rounded-lg py-2 font-medium hover:bg-red-700 disabled:opacity-50"
                onClick={handleAssemble}
                disabled={dispatching}
              >
                {dispatching ? "Dispatching…" : "Assemble"}
              </button>
              <button
                className="flex-1 bg-gray-100 text-gray-700 rounded-lg py-2 hover:bg-gray-200"
                onClick={() => { setShowModal(false); setDispatchMsg(""); }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
