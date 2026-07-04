import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Users, ChevronRight } from 'lucide-react'
import apiClient from '@/api/client'
import type { Character, PaginatedResponse } from '@/types'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Modal } from '@/components/ui/Modal'

export function CharactersPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [personality, setPersonality] = useState('')
  const [gender, setGender] = useState('')
  const [ageRange, setAgeRange] = useState('')

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
      setName('')
      setDescription('')
      setPersonality('')
    },
  })

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
            </div>
          ))}
        </div>
      )}

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
    </div>
  )
}
