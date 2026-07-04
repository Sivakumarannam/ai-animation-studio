import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Layers, Users, ImageIcon, Package, Camera, Sun,
  Plus, Eye, EyeOff, ZoomIn, ZoomOut,
} from 'lucide-react'
import { compositionApi, type SceneComposition } from '@/api/composition'
import { libraryApi } from '@/api/library'
import { Spinner } from '@/components/ui/Spinner'
import { clsx } from 'clsx'

type PanelTab = 'characters' | 'backgrounds' | 'props' | 'camera' | 'lighting' | 'layers'

const PANEL_TABS: { id: PanelTab; label: string; Icon: any }[] = [
  { id: 'characters', label: 'Characters', Icon: Users },
  { id: 'backgrounds', label: 'Backgrounds', Icon: ImageIcon },
  { id: 'props', label: 'Props', Icon: Package },
  { id: 'camera', label: 'Camera', Icon: Camera },
  { id: 'lighting', label: 'Lighting', Icon: Sun },
  { id: 'layers', label: 'Layers', Icon: Layers },
]

function LayersPanel({ composition }: { composition: SceneComposition }) {
  const allLayers = [
    ...composition.characters.map((c: any, i: number) => ({
      id: c.ref_id || `char-${i}`,
      type: 'character',
      name: c.name || `Character ${i + 1}`,
      visible: c.visible !== false,
      z_index: c.z_index || i,
    })),
    ...composition.props.map((p: any, i: number) => ({
      id: p.ref_id || `prop-${i}`,
      type: 'prop',
      name: p.name || `Prop ${i + 1}`,
      visible: p.visible !== false,
      z_index: p.z_index || i + 100,
    })),
  ].sort((a, b) => b.z_index - a.z_index)

  if (allLayers.length === 0) {
    return <p className="text-xs text-gray-500 text-center py-4">No layers yet. Add characters or props.</p>
  }

  return (
    <div className="space-y-1">
      {allLayers.map((layer) => (
        <div key={layer.id} className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-800 group">
          <div className={clsx('w-1.5 h-1.5 rounded-full', layer.type === 'character' ? 'bg-brand-400' : 'bg-orange-400')} />
          <span className="flex-1 text-xs text-gray-300 truncate">{layer.name}</span>
          <button className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-gray-300">
            {layer.visible ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
          </button>
        </div>
      ))}
    </div>
  )
}

function CameraPanel({ composition, compId }: { composition: SceneComposition; compId: string }) {
  const qc = useQueryClient()
  const camera = composition.camera as any
  const updateMutation = useMutation({
    mutationFn: (data: any) => compositionApi.update(compId, { camera: data }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['composition', compId] }),
  })

  return (
    <div className="space-y-3 p-1">
      {[
        { label: 'X Position', key: 'x', min: -1000, max: 1000, step: 1 },
        { label: 'Y Position', key: 'y', min: -1000, max: 1000, step: 1 },
        { label: 'Zoom', key: 'zoom', min: 0.1, max: 5, step: 0.1 },
        { label: 'Rotation', key: 'rotation', min: -180, max: 180, step: 1 },
      ].map(({ label, key, min, max, step }) => (
        <div key={key}>
          <div className="flex items-center justify-between mb-1">
            <label className="text-xs text-gray-400">{label}</label>
            <span className="text-xs text-gray-500">{camera[key] ?? 0}</span>
          </div>
          <input
            type="range" min={min} max={max} step={step}
            value={camera[key] ?? (key === 'zoom' ? 1 : 0)}
            onChange={(e) => updateMutation.mutate({ ...camera, [key]: parseFloat(e.target.value) })}
            className="w-full accent-brand-500"
          />
        </div>
      ))}
    </div>
  )
}

function LightingPanel({ composition, compId }: { composition: SceneComposition; compId: string }) {
  const qc = useQueryClient()
  const lighting = composition.lighting as any
  const updateMutation = useMutation({
    mutationFn: (data: any) => compositionApi.update(compId, { lighting: data }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['composition', compId] }),
  })

  return (
    <div className="space-y-3 p-1">
      <div>
        <label className="text-xs text-gray-400 block mb-1">Time of Day</label>
        <select
          className="input text-xs"
          value={lighting.time_of_day ?? 'day'}
          onChange={(e) => updateMutation.mutate({ ...lighting, time_of_day: e.target.value })}
        >
          {['dawn', 'morning', 'day', 'afternoon', 'sunset', 'dusk', 'night'].map((t) => (
            <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
          ))}
        </select>
      </div>
      <div>
        <div className="flex justify-between mb-1">
          <label className="text-xs text-gray-400">Ambient Light</label>
          <span className="text-xs text-gray-500">{((lighting.ambient ?? 0.8) * 100).toFixed(0)}%</span>
        </div>
        <input
          type="range" min={0} max={1} step={0.05}
          value={lighting.ambient ?? 0.8}
          onChange={(e) => updateMutation.mutate({ ...lighting, ambient: parseFloat(e.target.value) })}
          className="w-full accent-brand-500"
        />
      </div>
    </div>
  )
}

export function SceneEditorPage() {
  const { sceneId } = useParams<{ sceneId: string }>()
  const [activeTab, setActiveTab] = useState<PanelTab>('layers')
  const [zoom, setZoom] = useState(0.6)
  const qc = useQueryClient()

  const { data: composition, isLoading } = useQuery({
    queryKey: ['composition', sceneId],
    queryFn: () => compositionApi.getByScene(sceneId!),
    enabled: !!sceneId,
  })

  const { data: characters } = useQuery({
    queryKey: ['character-templates'],
    queryFn: () => libraryApi.getCharacterTemplates({ page_size: 50 }),
    enabled: activeTab === 'characters',
  })

  const { data: backgrounds } = useQuery({
    queryKey: ['backgrounds'],
    queryFn: () => libraryApi.getBackgrounds({ page_size: 48 }),
    enabled: activeTab === 'backgrounds',
  })

  const { data: props } = useQuery({
    queryKey: ['props'],
    queryFn: () => libraryApi.getProps({ page_size: 60 }),
    enabled: activeTab === 'props',
  })

  const addCharMutation = useMutation({
    mutationFn: (char: any) => compositionApi.addCharacter(composition!.id, {
      ref_id: crypto.randomUUID(),
      template_id: char.id,
      name: char.name,
      archetype: char.archetype,
      position: { x: 640, y: 400 },
      scale: 1.0,
      rotation: 0,
      z_index: 10,
      visible: true,
    }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['composition', sceneId] }),
  })

  const addBgMutation = useMutation({
    mutationFn: (bg: any) => compositionApi.update(composition!.id, { background_id: bg.id }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['composition', sceneId] }),
  })

  const addPropMutation = useMutation({
    mutationFn: (prop: any) => compositionApi.addProp(composition!.id, {
      ref_id: crypto.randomUUID(),
      prop_id: prop.id,
      name: prop.name,
      position: { x: 300, y: 500 },
      scale: 1.0,
      rotation: 0,
      z_index: 5,
      visible: true,
    }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['composition', sceneId] }),
  })

  if (isLoading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>
  if (!composition) return null

  const canvas_w = composition.canvas_width
  const canvas_h = composition.canvas_height

  return (
    <div className="flex h-full bg-gray-950">
      {/* Left sidebar — library panels */}
      <div className="w-72 bg-gray-900 border-r border-gray-800 flex flex-col">
        {/* Tabs */}
        <div className="flex flex-wrap border-b border-gray-800 p-1 gap-0.5">
          {PANEL_TABS.map(({ id, label, Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={clsx(
                'flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors',
                activeTab === id
                  ? 'bg-brand-600/20 text-brand-400'
                  : 'text-gray-500 hover:text-gray-300'
              )}
            >
              <Icon className="w-3 h-3" />
              {label}
            </button>
          ))}
        </div>

        {/* Panel content */}
        <div className="flex-1 overflow-y-auto p-2">
          {activeTab === 'layers' && <LayersPanel composition={composition} />}
          {activeTab === 'camera' && <CameraPanel composition={composition} compId={composition.id} />}
          {activeTab === 'lighting' && <LightingPanel composition={composition} compId={composition.id} />}

          {activeTab === 'characters' && (
            <div className="space-y-1.5">
              <p className="text-xs text-gray-500 mb-2">Click to add to scene</p>
              {(characters?.items ?? []).map((char) => (
                <button
                  key={char.id}
                  onClick={() => addCharMutation.mutate(char)}
                  className="w-full text-left flex items-center gap-2 p-2 rounded hover:bg-gray-800 transition-colors"
                >
                  <div className="w-8 h-8 rounded-lg bg-brand-900/30 flex items-center justify-center text-sm flex-shrink-0">
                    {char.name.charAt(0)}
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-gray-200 truncate">{char.name}</p>
                    <p className="text-xs text-gray-500 truncate">{char.name_local || char.archetype}</p>
                  </div>
                  <Plus className="w-3 h-3 text-gray-500 flex-shrink-0 ml-auto" />
                </button>
              ))}
            </div>
          )}

          {activeTab === 'backgrounds' && (
            <div className="grid grid-cols-2 gap-1.5">
              {(backgrounds?.items ?? []).map((bg) => (
                <button
                  key={bg.id}
                  onClick={() => addBgMutation.mutate(bg)}
                  className={clsx(
                    'aspect-video rounded overflow-hidden border-2 transition-colors hover:border-brand-500',
                    composition.background_id === bg.id ? 'border-brand-500' : 'border-gray-700'
                  )}
                >
                  {bg.thumbnail_url ? (
                    <img src={bg.thumbnail_url} alt={bg.name} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full bg-gray-800 flex items-center justify-center text-xs text-gray-500">
                      {bg.name}
                    </div>
                  )}
                </button>
              ))}
            </div>
          )}

          {activeTab === 'props' && (
            <div className="grid grid-cols-3 gap-1.5">
              {(props?.items ?? []).map((prop) => (
                <button
                  key={prop.id}
                  onClick={() => addPropMutation.mutate(prop)}
                  className="aspect-square rounded overflow-hidden border border-gray-700 hover:border-brand-500 transition-colors bg-gray-800 flex items-center justify-center"
                >
                  {prop.thumbnail_url ? (
                    <img src={prop.thumbnail_url} alt={prop.name} className="w-full h-full object-contain p-1" />
                  ) : (
                    <span className="text-xs text-gray-400 text-center px-1">{prop.name}</span>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main canvas */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="h-10 bg-gray-900 border-b border-gray-800 flex items-center gap-3 px-4">
          <span className="text-xs text-gray-400">Scene Editor</span>
          <div className="flex-1" />
          <button onClick={() => setZoom(Math.max(0.2, zoom - 0.1))} className="p-1 rounded hover:bg-gray-800 text-gray-400">
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-xs text-gray-400 w-12 text-center">{Math.round(zoom * 100)}%</span>
          <button onClick={() => setZoom(Math.min(2, zoom + 0.1))} className="p-1 rounded hover:bg-gray-800 text-gray-400">
            <ZoomIn className="w-4 h-4" />
          </button>
          <div className="w-px h-4 bg-gray-700" />
          <span className="text-xs text-gray-500">v{composition.version}</span>
          <span className={clsx(
            'text-xs px-2 py-0.5 rounded',
            composition.status === 'ready' ? 'bg-green-900/30 text-green-400' : 'bg-gray-800 text-gray-400'
          )}>
            {composition.status}
          </span>
        </div>

        {/* Canvas area */}
        <div className="flex-1 overflow-auto bg-gray-950 flex items-center justify-center p-8">
          <div
            style={{
              width: canvas_w * zoom,
              height: canvas_h * zoom,
              position: 'relative',
            }}
            className="bg-gray-800 rounded-lg shadow-2xl overflow-hidden border border-gray-700"
          >
            {/* Background */}
            {composition.background_id && (
              <div className="absolute inset-0 bg-gradient-to-b from-sky-900 to-green-900 opacity-60" />
            )}

            {/* Characters */}
            {composition.characters.map((char: any, i: number) => (
              <div
                key={char.ref_id || i}
                className="absolute flex flex-col items-center"
                style={{
                  left: (char.position?.x ?? 200) * zoom,
                  top: (char.position?.y ?? 200) * zoom,
                  transform: `scale(${char.scale ?? 1}) rotate(${char.rotation ?? 0}deg)`,
                  zIndex: char.z_index ?? i,
                }}
              >
                <div className="w-16 h-20 rounded-t-full bg-brand-700/60 border-2 border-brand-500/50 flex items-end justify-center pb-2">
                  <span className="text-white font-bold text-lg">{char.name?.charAt(0) ?? '?'}</span>
                </div>
                <p className="text-xs text-white bg-black/60 px-1.5 py-0.5 rounded mt-1 whitespace-nowrap">
                  {char.name}
                </p>
              </div>
            ))}

            {/* Props */}
            {composition.props.map((prop: any, i: number) => (
              <div
                key={prop.ref_id || i}
                className="absolute"
                style={{
                  left: (prop.position?.x ?? 100) * zoom,
                  top: (prop.position?.y ?? 300) * zoom,
                  zIndex: prop.z_index ?? i,
                }}
              >
                <div className="w-12 h-12 bg-orange-700/40 border border-orange-600/40 rounded flex items-center justify-center">
                  <Package className="w-6 h-6 text-orange-300/60" />
                </div>
                <p className="text-xs text-white/60 text-center mt-0.5 whitespace-nowrap">
                  {prop.name}
                </p>
              </div>
            ))}

            {/* Empty state */}
            {composition.characters.length === 0 && composition.props.length === 0 && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <Layers className="w-8 h-8 text-gray-600 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">Add characters, backgrounds and props from the left panel</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Status bar */}
        <div className="h-6 bg-gray-900 border-t border-gray-800 flex items-center px-4 gap-4 text-xs text-gray-600">
          <span>{canvas_w} × {canvas_h}</span>
          <span>{composition.characters.length} character{composition.characters.length !== 1 ? 's' : ''}</span>
          <span>{composition.props.length} prop{composition.props.length !== 1 ? 's' : ''}</span>
        </div>
      </div>
    </div>
  )
}
