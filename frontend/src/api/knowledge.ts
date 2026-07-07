import apiClient from './client'

export interface KnowledgeCollection {
  id: string
  project_id: string
  world_id: string | null
  name: string
  description: string
  collection_type: string
  status: string
  document_count: number
  chunk_count: number
  settings: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface KnowledgeDocument {
  id: string
  collection_id: string
  project_id: string
  title: string
  source_type: string
  original_filename: string
  size_bytes: number
  status: string
  error_message: string
  chunk_count: number
  created_at: string
  updated_at: string
}

export interface KnowledgeChunk {
  id: string
  document_id: string
  chunk_index: number
  content: string
  token_count: number
  embedding_model: string
  embedding_dims: number
  is_embedded: boolean
}

export interface EmbeddingJob {
  id: string
  project_id: string | null
  collection_id: string | null
  document_id: string | null
  job_type: string
  status: string
  execution_mode: string
  progress_percent: number
  current_step: string
  chunks_processed: number
  chunks_total: number
  result: Record<string, unknown>
  error_message: string
  retry_count: number
  created_at: string
}

export interface KnowledgeMemory {
  id: string
  project_id: string
  world_id: string | null
  collection_id: string | null
  source_chunk_id: string | null
  memory_type: string
  key: string
  value: Record<string, unknown>
  confidence: number
  is_active: boolean
  created_at: string
}

export interface SearchResultItem {
  chunk_id: string
  document_id: string
  content: string
  score: number
}

export interface SearchResponse {
  query: string
  results: SearchResultItem[]
  result_count: number
}

export interface KnowledgeStats {
  collections: number
  documents: number
  chunks: number
  embedded_chunks: number
  memories: number
  jobs_by_status: Record<string, number>
  embedding_provider: string
  vector_store_provider: string
}

export interface KnowledgeDispatchResult {
  job_id: string
  task_id: string
  mode: string
  status: string
  result?: Record<string, unknown>
}

interface ListResponse<T> {
  items: T[]
  meta: { page: number; page_size: number; total: number; total_pages: number }
}

export const knowledgeApi = {
  // ── Collections ────────────────────────────────────────────────────────────
  listCollections: (projectId: string, page = 1, pageSize = 20, status?: string) =>
    apiClient
      .get<ListResponse<KnowledgeCollection>>(`/kn/projects/${projectId}/collections`, {
        params: { page, page_size: pageSize, ...(status ? { status } : {}) },
      })
      .then((r) => r.data),

  createCollection: (projectId: string, data: { name: string; description?: string; collection_type?: string; world_id?: string | null }) =>
    apiClient.post<KnowledgeCollection>(`/kn/projects/${projectId}/collections`, data).then((r) => r.data),

  getCollection: (collectionId: string) =>
    apiClient.get<KnowledgeCollection>(`/kn/collections/${collectionId}`).then((r) => r.data),

  updateCollection: (collectionId: string, data: Partial<KnowledgeCollection>) =>
    apiClient.patch<KnowledgeCollection>(`/kn/collections/${collectionId}`, data).then((r) => r.data),

  deleteCollection: (collectionId: string) =>
    apiClient.delete(`/kn/collections/${collectionId}`),

  // ── Documents ──────────────────────────────────────────────────────────────
  listDocuments: (collectionId: string, page = 1, pageSize = 20, status?: string) =>
    apiClient
      .get<ListResponse<KnowledgeDocument>>(`/kn/collections/${collectionId}/documents`, {
        params: { page, page_size: pageSize, ...(status ? { status } : {}) },
      })
      .then((r) => r.data),

  createTextDocument: (collectionId: string, data: { title: string; source_type?: string; raw_text?: string }) =>
    apiClient.post<KnowledgeDocument>(`/kn/collections/${collectionId}/documents`, data).then((r) => r.data),

  uploadDocument: (collectionId: string, file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return apiClient
      .post<KnowledgeDispatchResult>(`/kn/collections/${collectionId}/documents/upload`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((r) => r.data)
  },

  getDocument: (documentId: string) =>
    apiClient.get<KnowledgeDocument>(`/kn/documents/${documentId}`).then((r) => r.data),

  getDocumentChunks: (documentId: string) =>
    apiClient.get<KnowledgeChunk[]>(`/kn/documents/${documentId}/chunks`).then((r) => r.data),

  processDocument: (documentId: string) =>
    apiClient.post<KnowledgeDispatchResult>(`/kn/documents/${documentId}/process`).then((r) => r.data),

  deleteDocument: (documentId: string) =>
    apiClient.delete(`/kn/documents/${documentId}`),

  // ── Search ─────────────────────────────────────────────────────────────────
  search: (collectionId: string, query: string, topK?: number, minScore?: number) =>
    apiClient
      .post<SearchResponse>(`/kn/collections/${collectionId}/search`, {
        query,
        ...(topK !== undefined ? { top_k: topK } : {}),
        ...(minScore !== undefined ? { min_score: minScore } : {}),
      })
      .then((r) => r.data),

  // ── Jobs ───────────────────────────────────────────────────────────────────
  listJobs: (projectId: string, page = 1, pageSize = 20, status?: string) =>
    apiClient
      .get<ListResponse<EmbeddingJob>>(`/kn/projects/${projectId}/jobs`, {
        params: { page, page_size: pageSize, ...(status ? { status } : {}) },
      })
      .then((r) => r.data),

  getJob: (jobId: string) =>
    apiClient.get<EmbeddingJob>(`/kn/jobs/${jobId}`).then((r) => r.data),

  getRetryQueue: () =>
    apiClient.get<EmbeddingJob[]>('/kn/jobs/retry-queue').then((r) => r.data),

  // ── Memory ─────────────────────────────────────────────────────────────────
  listMemory: (projectId: string, page = 1, pageSize = 20, memoryType?: string) =>
    apiClient
      .get<ListResponse<KnowledgeMemory>>(`/kn/projects/${projectId}/memory`, {
        params: { page, page_size: pageSize, ...(memoryType ? { memory_type: memoryType } : {}) },
      })
      .then((r) => r.data),

  listMemoryByWorld: (worldId: string, page = 1, pageSize = 20, memoryType?: string) =>
    apiClient
      .get<ListResponse<KnowledgeMemory>>(`/kn/worlds/${worldId}/memory`, {
        params: { page, page_size: pageSize, ...(memoryType ? { memory_type: memoryType } : {}) },
      })
      .then((r) => r.data),

  createMemory: (projectId: string, data: {
    memory_type: string; key: string; value?: Record<string, unknown>;
    world_id?: string | null; collection_id?: string | null; confidence?: number
  }) =>
    apiClient.post<KnowledgeMemory>(`/kn/projects/${projectId}/memory`, data).then((r) => r.data),

  deactivateMemory: (memoryId: string) =>
    apiClient.delete(`/kn/memory/${memoryId}`),

  // ── Stats ──────────────────────────────────────────────────────────────────
  getStats: (projectId: string) =>
    apiClient.get<KnowledgeStats>(`/kn/projects/${projectId}/stats`).then((r) => r.data),
}
