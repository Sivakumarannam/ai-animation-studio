import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Users, ChevronRight, Pencil, Trash2 } from 'lucide-react'
import apiClient from '@/api/client'
import type { Character, PaginatedResponse } from '@/types'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Modal } from '@/components/ui/Modal'

export function CharactersPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const qc = useQueryClient()

  // Create state
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [personality, setPersonality] = useState('')
  const [gender, setGender] = useState('')
  const [ageRange, setAgeRange] = useState('')

  // Edit state
  const [selectedChar, setSelectedChar] = useState<Character | null>(null)
  const [showEdit, setShowEdit] = useState(false)
  const [editName, setEditName] = useState('')
  const [editDescription, setEditDescription] = useState('')
  const [editPersonality, setEditPersonality] = useState('')
  const [editGender, setEditGender] = useState('')
  const [editAgeRange, setEditAgeRange] = useState('')

  // Delete state
  const [showDelete, setShowDelete] = useState(false)
  const [charToDelete, setCharToDelete] = useState<Character | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['characters', projectId],
    queryFn: () =>
      apiClient
        .get<PaginatedResponse<Character>>(`/projects/${projectId}/characters`)
        .then((r) => r.data),
    enabled: !!projectId,
  })

  const createMutation = useMutation({
    mutationFn: () =>
      apiClient
        .post<Character>(`/projects/${projectId}/characters`, {
          name, description, personality, gender, age_range: ageRange,
        })
        .then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['characters', projectId] })
      setShowCreate(false)
      setName(''); setDescription(''); setPersonality(''); setGender(''); setAgeRange('')
    },
  })

  const editMutation = useMutation({
    mutationFn: () =>
      apiClient
        .patch<Character>(`/projects/${projectId}/characters/${selectedChar!.id}`, {
          name: editName,
          description: editDescription,
          personality: editPersonality,
          gender: editGender,
          age_range: editAgeRange,
        })
        .then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['characters', projectId] })
      setShowEdit(false)
      setSelectedChar(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      apiClient.delete(`/projects/${projectId}/characters/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['characters', projectId] })
      setShowDelete(false)
      setCharToDelete(null)
    },
  })

  function openEdit(char: Character) {
    setSelectedChar(char)
    setEditName(char.name)
    setEditDescription(char.description ?? '')
    setEditPersonality(char.personality ?? '')
    setEditGender(char.gender ?? '')
    setEditAgeRange((char as any).age_range ?? '')
    setShowEdit(true)
  }

  function openDelete(char: Character) {
    setCharToDelete(char)
    setShowDelete(true)
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/projects" className="hover:text-gray-300">Projects</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/projects/${projectId}`} className="hover:text-gray-300">Project</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300">Characters</span>
      </div>

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Characters</h1>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <Plus className="w-4 h-4" /> New Character
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : data?.items.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No characters yet"
          description="Add characters to populate your animation project."
          action={<button onClick={() => setShowCreate(true)} className="btn-primary"><Plus className="w-4 h-4" />Add Character</button>}
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {data?.items.map((char) => (
            <div key={char.id} className="card p-4">
              <div className="w-12 h-12 bg-purple-900/30 rounded-xl flex items-center justify-center mb-3 text-xl">
                {char.name.charAt(0)}
              </div>
              <p className="text-sm font-semibold text-gray-100 mb-0.5">{char.name}</p>
              <p className="text-xs text-gray-500 mb-2 line-clamp-2">{char.description || 'No description'}</p>
              {char.gender && <span className="badge-gray">{char.gender}</span>}
              <div className="flex gap-2 mt-3 pt-3 border-t border-gray-800">
                <button
                  onClick={() => openEdit(char)}
                  className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200 transition-colors"
                >
                  <Pencil className="w-3 h-3" /> Edit
                </button>
                <button
                  onClick={() => openDelete(char)}
                  className="flex items-center gap-1 text-xs text-red-500 hover:text-red-400 transition-colors ml-auto"
                >
                  <Trash2 className="w-3 h-3" /> Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal title="New Character" open={showCreate} onClose={() => setShowCreate(false)}>
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate() }} className="space-y-4">
          <div>
            <label className="label">Name</label>
            <input className="input" placeholder="Character name" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div>
            <label className="label">Description</label>
            <textarea className="input resize-none" rows={2} placeholder="Who is this character?" value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div>
            <label className="label">Personality</label>
            <input className="input" placeholder="Funny, caring, mischievous..." value={personality} onChange={(e) => setPersonality(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Gender</label>
              <select className="input" value={gender} onChange={(e) => setGender(e.target.value)}>
                <option value="">Select...</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label className="label">Age Range</label>
              <input className="input" placeholder="35-45" value={ageRange} onChange={(e) => setAgeRange(e.target.value)} />
            </div>
          </div>
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? <Spinner size="sm" /> : 'Add Character'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Modal */}
      <Modal title="Edit Character" open={showEdit} onClose={() => setShowEdit(false)}>
        <form onSubmit={(e) => { e.preventDefault(); editMutation.mutate() }} className="space-y-4">
          <div>
            <label className="label">Name</label>
            <input className="input" placeholder="Character name" value={editName} onChange={(e) => setEditName(e.target.value)} required />
          </div>
          <div>
            <label className="label">Description</label>
            <textarea className="input resize-none" rows={2} value={editDescription} onChange={(e) => setEditDescription(e.target.value)} />
          </div>
          <div>
            <label className="label">Personality</label>
            <input className="input" value={editPersonality} onChange={(e) => setEditPersonality(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Gender</label>
              <select className="input" value={editGender} onChange={(e) => setEditGender(e.target.value)}>
                <option value="">Select...</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label className="label">Age Range</label>
              <input className="input" placeholder="35-45" value={editAgeRange} onChange={(e) => setEditAgeRange(e.target.value)} />
            </div>
          </div>
          {editMutation.isError && <p className="text-xs text-red-400">Failed to save changes.</p>}
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setShowEdit(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={editMutation.isPending}>
              {editMutation.isPending ? <Spinner size="sm" /> : 'Save Changes'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation */}
      <Modal title="Delete Character" open={showDelete} onClose={() => setShowDelete(false)}>
        <div className="space-y-4">
          <p className="text-sm text-gray-300">
            Are you sure you want to delete <strong className="text-white">{charToDelete?.name}</strong>? This action cannot be undone.
          </p>
          {deleteMutation.isError && <p className="text-xs text-red-400">Failed to delete character.</p>}
          <div className="flex gap-3 justify-end pt-2">
            <button className="btn-secondary" onClick={() => setShowDelete(false)}>Cancel</button>
            <button
              className="btn-danger"
              disabled={deleteMutation.isPending}
              onClick={() => charToDelete && deleteMutation.mutate(charToDelete.id)}
            >
              {deleteMutation.isPending ? <Spinner size="sm" /> : 'Delete'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
