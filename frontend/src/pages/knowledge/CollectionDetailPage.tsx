import { useState, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ChevronRight, FileText, Upload, Search, Trash2, Plus,
  Loader2, CheckCircle2, XCircle, Clock,
} from 'lucide-react'
import { knowledgeApi, type SearchResultItem } from '@/api/knowledge'
import { Spinner } from '@/components/ui/Spinner'
import { Modal } from '@/components/ui/Modal'

function DocumentStatusIcon({ status }: { status: string }) {
  if (status === 'ready' || status === 'completed') return <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />
  if (status === 'failed' || status === 'error') return <XCircle className="w-3.5 h-3.5 text-red-400" />
  if (status === 'processing' || status === 'embedding') return <Loader2 className="w-3.5 h-3.5 text-yellow-400 animate-spin" />
  return <Clock className="w-3.5 h-3.5 text-gray-500" />
}

export function CollectionDetailPage() {
  const { projectId, collectionId } = useParams<{ projectId: string; collectionId: string }>()
  const qc = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [activeTab, setActiveTab] = useState<'documents' | 'search'>('documents')
  const [showAddText, setShowAddText] = useState(false)
  const [docTitle, setDocTitle] = useState('')
  const [docText, setDocText] = useState('')
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResultItem[] | null>(null)
  const [searching, setSearching] = useState(false)
  const [docPage, setDocPage] = useState(1)

  const { data: collection, isLoading: loadingCollection } = useQuery({
    queryKey: ['kn-collection', collectionId],
    queryFn: () => knowledgeApi.getCollection(collectionId!),
    enabled: !!collectionId,
  })

  const { data: docsData, isLoading: loadingDocs } = useQuery({
    queryKey: ['kn-documents', collectionId, docPage],
    queryFn: () => knowledgeApi.listDocuments(collectionId!, docPage),
    enabled: !!collectionId,
  })

  const createTextMutation = useMutation({
    mutationFn: () => knowledgeApi.createTextDocument(collectionId!, { title: docTitle, source_type: 'text', raw_text: docText }),
    onSuccess: () => {
      setShowAddText(false)
      setDocTitle('')
      setDocText('')
      qc.invalidateQueries({ queryKey: ['kn-documents', collectionId] })
      qc.invalidateQueries({ queryKey: ['kn-collection', collectionId] })
      qc.invalidateQueries({ queryKey: ['kn-stats', projectId] })
    },
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => knowledgeApi.uploadDocument(collectionId!, file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['kn-documents', collectionId] })
      qc.invalidateQueries({ queryKey: ['kn-collection', collectionId] })
      qc.invalidateQueries({ queryKey: ['kn-stats', projectId] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (docId: string) => knowledgeApi.deleteDocument(docId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['kn-documents', collectionId] })
      qc.invalidateQueries({ queryKey: ['kn-collection', collectionId] })
      qc.invalidateQueries({ queryKey: ['kn-stats', projectId] })
    },
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) uploadMutation.mutate(file)
    e.target.value = ''
  }

  const handleSearch = async () => {
    if (!query.trim() || !collectionId) return
    setSearching(true)
    try {
      const r = await knowledgeApi.search(collectionId, query, 10)
      setSearchResults(r.results)
    } finally {
      setSearching(false)
    }
  }

  if (loadingCollection) {
    return <div className="flex justify-center py-20"><Spinner size="lg" /></div>
  }

  if (!collection) {
    return <div className="p-6 text-gray-400">Collection not found</div>
  }

  const docs = docsData?.items ?? []
  const docMeta = docsData?.meta

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/projects" className="hover:text-gray-300">Projects</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}`} className="hover:text-gray-300">Project</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}/knowledge`} className="hover:text-gray-300">Knowledge</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}/knowledge/collections`} className="hover:text-gray-300">Collections</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300">{collection.name}</span>
      </div>

      <div className="flex items-center justify-between mb-2">
        <div>
          <h1 className="text-2xl font-bold text-white">{collection.name}</h1>
          {collection.description && <p className="text-gray-400 text-sm mt-1">{collection.description}</p>}
        </div>
        <div className="flex gap-2">
          <input ref={fileInputRef} type="file" accept=".txt,.md,.csv,.json,.pdf" className="hidden" onChange={handleFileChange} />
          <button onClick={() => fileInputRef.current?.click()} className="btn-secondary" disabled={uploadMutation.isPending}>
            {uploadMutation.isPending ? <Spinner size="sm" /> : <Upload className="w-4 h-4" />}
            Upload File
          </button>
          <button onClick={() => setShowAddText(true)} className="btn-primary">
            <Plus className="w-4 h-4" /> Add Text
          </button>
        </div>
      </div>

      <div className="flex items-center gap-4 text-xs text-gray-500 mb-6">
        <span>{collection.document_count} documents</span>
        <span>{collection.chunk_count} chunks</span>
        <span className="capitalize">{collection.collection_type}</span>
        <span className={`capitalize px-1.5 py-0.5 rounded font-medium ${
          collection.status === 'ready' ? 'bg-green-900/40 text-green-400' :
          collection.status === 'indexing' ? 'bg-yellow-900/40 text-yellow-400' :
          'bg-gray-800 text-gray-400'
        }`}>{collection.status}</span>
      </div>

      {uploadMutation.isSuccess && (
        <div className="mb-4 p-3 bg-green-900/30 border border-green-800 rounded text-xs text-green-400">
          File uploaded and queued for processing.
        </div>
      )}
      {uploadMutation.isError && (
        <div className="mb-4 p-3 bg-red-900/30 border border-red-800 rounded text-xs text-red-400">
          Upload failed. Please try again.
        </div>
      )}

      <div className="flex gap-1 mb-6 border-b border-gray-800">
        {(['documents', 'search'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm capitalize border-b-2 transition-colors ${
              activeTab === tab ? 'border-brand-500 text-white' : 'border-transparent text-gray-500 hover:text-gray-300'
            }`}
          >
            {tab === 'documents' ? <><FileText className="w-3.5 h-3.5 inline mr-1" />Documents</> : <><Search className="w-3.5 h-3.5 inline mr-1" />Semantic Search</>}
          </button>
        ))}
      </div>

      {activeTab === 'documents' && (
        <>
          {loadingDocs ? (
            <div className="flex justify-center py-10"><Spinner size="lg" /></div>
          ) : docs.length === 0 ? (
            <div className="card p-10 text-center">
              <FileText className="w-10 h-10 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400 font-medium">No documents yet</p>
              <p className="text-gray-600 text-xs mt-1">Upload a file or add text to get started.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {docs.map((doc) => (
                <div key={doc.id} className="card p-4 flex items-center gap-4">
                  <DocumentStatusIcon status={doc.status} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-100 font-medium truncate">{doc.title}</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {doc.source_type} · {doc.chunk_count} chunks · {doc.size_bytes > 0 ? `${(doc.size_bytes / 1024).toFixed(1)} KB` : 'text'} · {doc.status}
                    </p>
                    {doc.error_message && <p className="text-xs text-red-400 mt-0.5">{doc.error_message}</p>}
                  </div>
                  <button
                    onClick={() => { if (confirm(`Delete "${doc.title}"?`)) deleteMutation.mutate(doc.id) }}
                    className="text-gray-600 hover:text-red-400"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {docMeta && docMeta.total_pages > 1 && (
            <div className="flex items-center justify-center gap-3 mt-6">
              <button className="btn-secondary text-xs" disabled={docPage <= 1} onClick={() => setDocPage(docPage - 1)}>← Prev</button>
              <span className="text-xs text-gray-500">Page {docMeta.page} of {docMeta.total_pages}</span>
              <button className="btn-secondary text-xs" disabled={docPage >= docMeta.total_pages} onClick={() => setDocPage(docPage + 1)}>Next →</button>
            </div>
          )}
        </>
      )}

      {activeTab === 'search' && (
        <div>
          <div className="flex gap-3 mb-6">
            <input
              className="input flex-1"
              placeholder="Search this collection with natural language..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button className="btn-primary" onClick={handleSearch} disabled={searching || !query.trim()}>
              {searching ? <Spinner size="sm" /> : <Search className="w-4 h-4" />}
              Search
            </button>
          </div>

          {searchResults === null ? (
            <div className="card p-10 text-center">
              <Search className="w-10 h-10 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400 font-medium">Enter a query to search</p>
              <p className="text-gray-600 text-xs mt-1">Semantic search finds the most relevant document chunks.</p>
            </div>
          ) : searchResults.length === 0 ? (
            <div className="card p-8 text-center">
              <p className="text-gray-400 text-sm">No results found for "{query}"</p>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-xs text-gray-500">{searchResults.length} results for "{query}"</p>
              {searchResults.map((r) => (
                <div key={r.chunk_id} className="card p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-gray-500 font-mono">Score: {r.score.toFixed(4)}</span>
                    <span className="text-xs text-gray-600">chunk {r.chunk_id.slice(0, 8)}…</span>
                  </div>
                  <p className="text-sm text-gray-200 leading-relaxed">{r.content}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <Modal title="Add Text Document" open={showAddText} onClose={() => setShowAddText(false)}>
        <form onSubmit={(e) => { e.preventDefault(); createTextMutation.mutate() }} className="space-y-4">
          <div>
            <label className="label">Title *</label>
            <input className="input" value={docTitle} onChange={(e) => setDocTitle(e.target.value)} required placeholder="Document title" />
          </div>
          <div>
            <label className="label">Content *</label>
            <textarea
              className="input resize-none font-mono text-xs"
              rows={8}
              value={docText}
              onChange={(e) => setDocText(e.target.value)}
              required
              placeholder="Paste text content here..."
            />
          </div>
          {createTextMutation.isError && (
            <p className="text-xs text-red-400">Failed to add document.</p>
          )}
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowAddText(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={createTextMutation.isPending || !docTitle.trim() || !docText.trim()}>
              {createTextMutation.isPending ? <Spinner size="sm" /> : 'Add Document'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
