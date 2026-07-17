import React, { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import { videoAssemblyApi, VideoRetryEntry } from "../../api/videoAssembly";

const STATUS_COLOR: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  retrying: "bg-blue-100 text-blue-800",
  resolved: "bg-green-100 text-green-800",
  exhausted: "bg-red-100 text-red-800",
};

export default function VideoAssemblyRetryQueuePage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [entries, setEntries] = useState<VideoRetryEntry[]>([]);
  const [meta, setMeta] = useState({ total: 0, page: 1, page_size: 20, total_pages: 1 });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sweeping, setSweeping] = useState(false);
  const [sweepMsg, setSweepMsg] = useState("");

  const load = useCallback(async () => {
    if (!projectId) return;
    try {
      setLoading(true);
      setError("");
      const res = await videoAssemblyApi.listRetryQueue(projectId, { page, page_size: 20 });
      setEntries(res.items);
      setMeta(res.meta);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [projectId, page]);

  useEffect(() => { load(); }, [load]);

  const handleSweep = async () => {
    if (!projectId) return;
    setSweeping(true);
    setSweepMsg("");
    try {
      const res = await videoAssemblyApi.sweepRetryQueue(projectId);
      setSweepMsg(`✓ Sweep dispatched — job ${res.job_id} (${res.mode})`);
      setTimeout(load, 2000);
    } catch (e: any) {
      setSweepMsg(`✗ ${e.message}`);
    } finally {
      setSweeping(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Assembly Retry Queue</h1>
          <p className="text-gray-500 text-sm mt-1">Failed assembly jobs awaiting retry</p>
        </div>
        <button
          onClick={handleSweep}
          disabled={sweeping}
          className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 font-medium"
        >
          {sweeping ? "Sweeping…" : "Sweep Queue"}
        </button>
      </div>

      {sweepMsg && (
        <div className={`mb-4 p-3 rounded-lg text-sm ${sweepMsg.startsWith("✓") ? "bg-green-50 text-green-800" : "bg-red-50 text-red-700"}`}>
          {sweepMsg}
        </div>
      )}

      {loading ? (
        <div className="text-gray-400 py-12 text-center">Loading…</div>
      ) : error ? (
        <div className="text-red-600">{error}</div>
      ) : entries.length === 0 ? (
        <div className="text-gray-400 py-12 text-center bg-gray-50 rounded-xl">
          Retry queue is empty. 🎉
        </div>
      ) : (
        <>
          <div className="space-y-2 mb-6">
            {entries.map((e) => (
              <div key={e.id} className="bg-white border rounded-xl px-5 py-3">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-mono text-xs text-gray-400">{e.id.slice(0, 8)}…</span>
                    <span className={`ml-3 text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLOR[e.status] ?? "bg-gray-100"}`}>
                      {e.status}
                    </span>
                    <span className="ml-3 text-xs text-gray-500">
                      retry {e.retry_count}/{e.max_retries}
                    </span>
                  </div>
                  <span className="text-xs text-gray-400">{new Date(e.created_at).toLocaleString()}</span>
                </div>
                {e.reason && (
                  <p className="text-xs text-red-500 mt-1 truncate">{e.reason}</p>
                )}
                {e.episode_id && (
                  <p className="text-xs text-gray-400 mt-1">Episode: {e.episode_id}</p>
                )}
                {e.next_retry_at && (
                  <p className="text-xs text-gray-400">
                    Next retry: {new Date(e.next_retry_at).toLocaleString()}
                  </p>
                )}
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
    </div>
  );
}
