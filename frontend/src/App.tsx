import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoginPage } from '@/pages/auth/LoginPage'
import { RegisterPage } from '@/pages/auth/RegisterPage'
import { DashboardPage } from '@/pages/dashboard/DashboardPage'
import { ProjectsPage } from '@/pages/projects/ProjectsPage'
import { ProjectDetailPage } from '@/pages/projects/ProjectDetailPage'
import { StoriesPage } from '@/pages/stories/StoriesPage'
import { CharactersPage } from '@/pages/characters/CharactersPage'
import { SettingsPage } from '@/pages/settings/SettingsPage'
// Module 2 — Animation Engine
import { CharacterLibraryPage } from '@/pages/library/CharacterLibraryPage'
import { BackgroundLibraryPage } from '@/pages/library/BackgroundLibraryPage'
import { PropsLibraryPage } from '@/pages/library/PropsLibraryPage'
import { SceneEditorPage } from '@/pages/studio/SceneEditorPage'
import { TimelineEditorPage } from '@/pages/studio/TimelineEditorPage'
import { AssetManagerPage } from '@/pages/studio/AssetManagerPage'
import { PreviewPlayerPage } from '@/pages/studio/PreviewPlayerPage'
// Phase 3 — Story Intelligence
import { StoryIntelligenceDashboardPage } from '@/pages/intelligence/StoryIntelligenceDashboardPage'
import { WorldsPage } from '@/pages/intelligence/WorldsPage'
import { WorldDetailPage } from '@/pages/intelligence/WorldDetailPage'
import { SeasonDetailPage } from '@/pages/intelligence/SeasonDetailPage'
import { EpisodeDetailPage } from '@/pages/intelligence/EpisodeDetailPage'
import { StoryIdeasPage } from '@/pages/intelligence/StoryIdeasPage'
import { RetryQueuePage } from '@/pages/intelligence/RetryQueuePage'
// Phase 4 — Knowledge Intelligence
import { KnowledgeDashboardPage } from '@/pages/knowledge/KnowledgeDashboardPage'
import { CollectionsPage } from '@/pages/knowledge/CollectionsPage'
import { CollectionDetailPage } from '@/pages/knowledge/CollectionDetailPage'
import { KnowledgeMemoryPage } from '@/pages/knowledge/KnowledgeMemoryPage'
import { EmbeddingJobsPage } from '@/pages/knowledge/EmbeddingJobsPage'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function RequireGuest({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return !isAuthenticated ? <>{children}</> : <Navigate to="/dashboard" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<RequireGuest><LoginPage /></RequireGuest>} />
      <Route path="/register" element={<RequireGuest><RegisterPage /></RequireGuest>} />

      <Route element={<RequireAuth><AppLayout /></RequireAuth>}>
        {/* Core */}
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
        <Route path="/projects/:projectId/stories" element={<StoriesPage />} />
        <Route path="/projects/:projectId/characters" element={<CharactersPage />} />
        <Route path="/settings" element={<SettingsPage />} />

        {/* Phase 3 — Story Intelligence */}
        <Route path="/projects/:projectId/intelligence" element={<StoryIntelligenceDashboardPage />} />
        <Route path="/projects/:projectId/intelligence/worlds" element={<WorldsPage />} />
        <Route path="/projects/:projectId/intelligence/worlds/:worldId" element={<WorldDetailPage />} />
        <Route path="/projects/:projectId/intelligence/seasons/:seasonId" element={<SeasonDetailPage />} />
        <Route path="/projects/:projectId/intelligence/episodes/:episodeId" element={<EpisodeDetailPage />} />
        <Route path="/projects/:projectId/intelligence/ideas" element={<StoryIdeasPage />} />
        <Route path="/projects/:projectId/intelligence/jobs" element={<RetryQueuePage />} />

        {/* Phase 4 — Knowledge Intelligence */}
        <Route path="/projects/:projectId/knowledge" element={<KnowledgeDashboardPage />} />
        <Route path="/projects/:projectId/knowledge/collections" element={<CollectionsPage />} />
        <Route path="/projects/:projectId/knowledge/collections/:collectionId" element={<CollectionDetailPage />} />
        <Route path="/projects/:projectId/knowledge/memory" element={<KnowledgeMemoryPage />} />
        <Route path="/projects/:projectId/knowledge/jobs" element={<EmbeddingJobsPage />} />

        {/* Module 2 — Libraries */}
        <Route path="/library/characters" element={<CharacterLibraryPage />} />
        <Route path="/library/backgrounds" element={<BackgroundLibraryPage />} />
        <Route path="/library/props" element={<PropsLibraryPage />} />

        {/* Module 2 — Studio */}
        <Route path="/studio/asset-manager" element={<AssetManagerPage />} />
        <Route path="/scenes/:sceneId/editor" element={<SceneEditorPage />} />
        <Route path="/scenes/:sceneId/timeline" element={<TimelineEditorPage />} />
        <Route path="/projects/:projectId/stories/:storyId/preview" element={<PreviewPlayerPage />} />

        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
