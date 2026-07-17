import React, { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import { videoAssemblyApi, VideoAssemblyDashboardStats, TriggerAssembleEpisodeRequest } from "../../api/videoAssembly";

const STATUS_COLOR: Record<string, string> = {
  completed: "bg-green-100 text-green-800",
  pending: "bg-yellow-100 text-yellow-800",
  running: "bg-blue-100 text-blue-800",
  failed: "bg-red-100 text-red-800",
};

const OUTPUT_TYPES = [
  { value: "episode_cut", label: "Episode Cut (full length)" },
  { value: "short_form_cut", label: "Short-form Cut (≤30 s)" },
];

export default function VideoAssemblyDashboardPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [stats, setStats] = useState<VideoAssemblyDashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<TriggerAssembleEpisodeRequest>({
    project_id: projectId ?? "",
    episode_id: null,
    output_type: "episode_cut",
    width: 1920,
    height: 1080,
    fps: 24,
    include_subtitles: false,
  });
  const [dispatching, setDispatching] = useState(false);
  const [dispatchMsg, setDispatchMsg] = useState("");

  const load = useCallback(async () => {
    if (!projectId) return;
    try {
      setLoading(true);
      setError("");
      const data = await videoAssemblyApi.getDashboard(projectId);
      setStats(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => { load(); }, [load]);

  const handleAssemble = async () => {
    if (!projectId) return;
    setDispatching(true);
    setDispatchMsg("");
    try {
      const res = await videoAssemblyApi.triggerAssembleEpisode({ ...form, project_id: projectId });
      setDispatchMsg(`✓ Dispatched — job ${res.job_id} (mode: ${res.mode})`);
      setShowModal(false);
      setTimeout(load, 1500);
    } catch (e: any) {
      setDispatchMsg(`✗ ${e.message}`);
    } finally {
      setDispatching(false);
    }
  };

  if (loading) return <div className="p-8 text-gray-500">Loading…</div>;
  if (error) return <div className="p-8 text-red-600">{error}</div>;
  if (!stats) return null;

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">🎬 Video Assembly</h1>
          <p className="text-gray-500 text-sm mt-1">Phase 10 — Final video compositing</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium shadow"
        >
          Assemble Video
        </button>
      </div>

      {dispatchMsg && (
        <div className={`mb-4 p-3 rounded-lg text-sm ${dispatchMsg.startsWith("✓") ? "bg-green-50 text-green-800" : "bg-red-50 text-red-700"}`}>
          {dispatchMsg}
        </div>
      )}

      {/* Stats cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { label: "Total Jobs", value: stats.total_jobs, color: "bg-gray-50" },
          { label: "Completed", value: stats.jobs_completed, color: "bg-green-50" },
          { label: "Pending / Running", value: stats.jobs_pending + stats.jobs_running, color: "bg-yellow-50" },
          { label: "Failed", value: stats.jobs_failed, color: "bg-red-50" },
          { label: "Video Outputs", value: stats.total_video_outputs, color: "bg-purple-50" },
          { label: "Retry Queue", value: stats.total_retry_entries, color: "bg-orange-50" },
        ].map((c) => (
          <div key={c.label} className={`${c.color} rounded-xl p-4`}>
            <div className="text-2xl font-bold text-gray-900">{c.value}</div>
            <div className="text-xs text-gray-500 mt-1">{c.label}</div>
          </div>
        ))}
      </div>

      {/* Recent jobs */}
      <div>
        <h2 className="text-lg font-semibold text-gray-800 mb-3">Recent Jobs</h2>
        {stats.recent_jobs.length === 0 ? (
          <div className="text-gray-400 text-sm bg-gray-50 rounded-lg p-6 text-center">
            No assembly jobs yet. Click "Assemble Video" to start.
          </div>
        ) : (
          <div className="space-y-2">
            {stats.recent_jobs.map((j) => (
              <div key={j.id} className="flex items-center justify-between bg-white border rounded-lg px-4 py-3">
                <div>
                  <span className="font-mono text-xs text-gray-400">{j.id.slice(0, 8)}…</span>
                  <span className="ml-3 text-sm text-gray-700">{j.job_type}</span>
                  {j.episode_id && (
                    <span className="ml-2 text-xs text-gray-400">ep {j.episode_id.slice(0, 8)}…</span>
                  )}
                </div>
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${STATUS_COLOR[j.status] ?? "bg-gray-100 text-gray-600"}`}>
                  {j.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Assemble modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Assemble Video</h2>

            <label className="block text-sm font-medium text-gray-700 mb-1">Output type</label>
            <select
              className="w-full border rounded-lg px-3 py-2 mb-4 text-sm"
              value={form.output_type}
              onChange={(e) => setForm({ ...form, output_type: e.target.value as any })}
            >
              {OUTPUT_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>

            <label className="block text-sm font-medium text-gray-700 mb-1">Episode ID (optional)</label>
            <input
              type="text"
              className="w-full border rounded-lg px-3 py-2 mb-4 text-sm font-mono"
              placeholder="UUID of episode to assemble"
              value={form.episode_id ?? ""}
              onChange={(e) => setForm({ ...form, episode_id: e.target.value || null })}
            />

            <div className="grid grid-cols-3 gap-3 mb-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Width</label>
                <input type="number" className="w-full border rounded px-2 py-1 text-sm" value={form.width}
                  onChange={(e) => setForm({ ...form, width: Number(e.target.value) })} />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Height</label>
                <input type="number" className="w-full border rounded px-2 py-1 text-sm" value={form.height}
                  onChange={(e) => setForm({ ...form, height: Number(e.target.value) })} />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">FPS</label>
                <input type="number" className="w-full border rounded px-2 py-1 text-sm" value={form.fps}
                  onChange={(e) => setForm({ ...form, fps: Number(e.target.value) })} />
              </div>
            </div>

            {dispatchMsg && (
              <div className="mb-3 text-sm text-red-600">{dispatchMsg}</div>
            )}

            <div className="flex gap-3">
              <button
                className="flex-1 bg-red-600 text-white rounded-lg py-2 font-medium hover:bg-red-700 disabled:opacity-50"
                onClick={handleAssemble}
                disabled={dispatching}
              >
                {dispatching ? "Dispatching…" : "Assemble"}
              </button>
              <button
                className="flex-1 bg-gray-100 text-gray-700 rounded-lg py-2 font-medium hover:bg-gray-200"
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
