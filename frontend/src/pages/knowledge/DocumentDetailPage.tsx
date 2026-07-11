import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ChevronRight, FileText, CheckCircle2, XCircle, Clock, Loader2, RefreshCw } from 'lucide-react'
import { knowledgeApi } from '@/api/knowledge'
import { Spinner } from '@/components/ui/Spinner'

function DocumentStatusIcon({ status }: { status: string }) {
  if (status === 'ready' || status === 'completed') return <CheckCircle2 className="w-4 h-4 text-green-400" />
  if (status === 'failed' || status === 'error') return <XCircle className="w-4 h-4 text-red-400" />
  if (status === 'processing' || status === 'embedding') return <Loader2 className="w-4 h-4 text-yellow-400 animate-spin" />
  return <Clock className="w-4 h-4 text-gray-500" />
}

export function DocumentDetailPage() {
  const { projectId, collectionId, documentId } = useParams<{
    projectId: string
    collectionId: string
    documentId: string
  }>()
  const qc = useQueryClient()

  const { data: document, isLoading: loadingDoc } = useQuery({
    queryKey: ['kn-document', documentId],
    queryFn: () => knowledgeApi.getDocument(documentId!),
    enabled: !!documentId,
  })

  const { data: chunks, isLoading: loadingChunks } = useQuery({
    queryKey: ['kn-chunks', documentId],
    queryFn: () => knowledgeApi.getDocumentChunks(documentId!),
    enabled: !!documentId,
  })

  const reprocessMutation = useMutation({
    mutationFn: () => knowledgeApi.processDocument(documentId!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['kn-document', documentId] })
      qc.invalidateQueries({ queryKey: ['kn-chunks', documentId] })
    },
  })

  if (loadingDoc) {
    return <div className="flex justify-center py-20"><Spinner size="lg" /></div>
  }

  if (!document) {
    return <div className="p-6 text-gray-400">Document not found</div>
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/projects" className="hover:text-gray-300">Projects</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}`} className="hover:text-gray-300">Project</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}/knowledge`} className="hover:text-gray-300">Knowledge</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}/knowledge/collections`} className="hover:text-gray-300">Collections</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}/knowledge/collections/${collectionId}`} className="hover:text-gray-300">Collection</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300 truncate max-w-xs">{document.title}</span>
      </div>

      {/* Document Metadata */}
      <div className="card p-5 mb-6">
        <div className="flex items-start gap-3 mb-4">
          <DocumentStatusIcon status={document.status} />
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold text-white">{document.title}</h1>
            {document.original_filename && document.original_filename !== document.title && (
              <p className="text-xs text-gray-500 mt-0.5">{document.original_filename}</p>
            )}
          </div>
          <button
            onClick={() => reprocessMutation.mutate()}
            disabled={reprocessMutation.isPending}
            className="btn-secondary text-xs flex items-center gap-1.5 flex-shrink-0"
            title="Re-process and re-embed this document"
          >
            {reprocessMutation.isPending
              ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
              : <RefreshCw className="w-3.5 h-3.5" />}
            Re-embed
          </button>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div>
            <p className="text-gray-500 mb-0.5">Status</p>
            <p className="text-gray-200 capitalize font-medium">{document.status}</p>
          </div>
          <div>
            <p className="text-gray-500 mb-0.5">Source Type</p>
            <p className="text-gray-200 uppercase font-medium">{document.source_type}</p>
          </div>
          <div>
            <p className="text-gray-500 mb-0.5">Chunks</p>
            <p className="text-gray-200 font-medium">{document.chunk_count}</p>
          </div>
          <div>
            <p className="text-gray-500 mb-0.5">Size</p>
            <p className="text-gray-200 font-medium">
              {document.size_bytes > 0 ? `${(document.size_bytes / 1024).toFixed(1)} KB` : '—'}
            </p>
          </div>
          <div>
            <p className="text-gray-500 mb-0.5">Created</p>
            <p className="text-gray-200 font-medium">{new Date(document.created_at).toLocaleDateString()}</p>
          </div>
          <div>
            <p className="text-gray-500 mb-0.5">Updated</p>
            <p className="text-gray-200 font-medium">{new Date(document.updated_at).toLocaleDateString()}</p>
          </div>
        </div>
        {document.error_message && (
          <div className="mt-3 p-2.5 bg-red-900/30 border border-red-800 rounded text-xs text-red-400">
            {document.error_message}
          </div>
        )}
      </div>

      {/* Chunks */}
      <div>
        <h2 className="text-base font-semibold text-gray-200 mb-3">
          Chunks
          {chunks && <span className="text-gray-500 font-normal ml-2 text-sm">({chunks.length})</span>}
        </h2>

        {loadingChunks ? (
          <div className="flex justify-center py-10"><Spinner size="lg" /></div>
        ) : !chunks || chunks.length === 0 ? (
          <div className="card p-10 text-center">
            <FileText className="w-10 h-10 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400 font-medium">No chunks yet</p>
            <p className="text-gray-600 text-xs mt-1">
              Chunks are created when the document is processed and embedded.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {chunks.map((chunk) => (
              <div key={chunk.id} className="card p-4">
                <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-gray-500">#{chunk.chunk_index}</span>
                    <span className="text-xs text-gray-500">{chunk.token_count} tokens</span>
                    {chunk.is_embedded ? (
                      <span className="text-xs text-green-400 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> embedded
                      </span>
                    ) : (
                      <span className="text-xs text-gray-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" /> not embedded
                      </span>
                    )}
                  </div>
                  {chunk.embedding_model && (
                    <span className="text-xs text-gray-600 font-mono">{chunk.embedding_model}</span>
                  )}
                </div>
                <p className="text-sm text-gray-200 leading-relaxed whitespace-pre-wrap font-mono text-xs">
                  {chunk.content}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
