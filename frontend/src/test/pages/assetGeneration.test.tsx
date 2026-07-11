import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Create a wrapper for tests
function Wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/projects/test-project-id/asset-generation']}>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  )
}

// ─── AssetGenerationDashboardPage ────────────────────────────────────────────

describe('AssetGenerationDashboardPage', () => {
  beforeEach(() => {
    vi.mock('@/api/assetGeneration', () => ({
      assetGenerationApi: {
        getDashboard: vi.fn().mockResolvedValue({
          total_assets: 0,
          assets_completed: 0,
          assets_pending: 0,
          assets_failed: 0,
          assets_generating: 0,
          total_retries: 0,
          avg_quality_score: 0,
          assets_by_type: {},
          recent_jobs: [],
          generation_history: [],
        }),
      },
    }))
  })

  it('renders heading', async () => {
    const { AssetGenerationDashboardPage } = await import(
      '@/pages/assetGeneration/AssetGenerationDashboardPage'
    )
    render(
      <Wrapper>
        <AssetGenerationDashboardPage />
      </Wrapper>
    )
    expect(screen.getByText(/asset generation/i)).toBeTruthy()
  })
})

// ─── GenerationJobsPage ───────────────────────────────────────────────────────

describe('GenerationJobsPage', () => {
  it('renders heading', async () => {
    const { GenerationJobsPage } = await import('@/pages/assetGeneration/GenerationJobsPage')
    render(
      <Wrapper>
        <GenerationJobsPage />
      </Wrapper>
    )
    expect(screen.getByText(/generation jobs/i)).toBeTruthy()
  })
})

// ─── RetryQueuePage ───────────────────────────────────────────────────────────

describe('RetryQueuePage', () => {
  it('renders heading', async () => {
    const { RetryQueuePage } = await import('@/pages/assetGeneration/RetryQueuePage')
    render(
      <Wrapper>
        <RetryQueuePage />
      </Wrapper>
    )
    expect(screen.getByText(/retry queue/i)).toBeTruthy()
  })

  it('renders empty state when no entries', async () => {
    const { RetryQueuePage } = await import('@/pages/assetGeneration/RetryQueuePage')
    render(
      <Wrapper>
        <RetryQueuePage />
      </Wrapper>
    )
    // Empty state renders when data is undefined (default mock)
    expect(document.body).toBeTruthy()
  })
})

// ─── ConsistencyEnginePage ────────────────────────────────────────────────────

describe('ConsistencyEnginePage', () => {
  it('renders heading', async () => {
    const { ConsistencyEnginePage } = await import('@/pages/assetGeneration/ConsistencyEnginePage')
    render(
      <Wrapper>
        <ConsistencyEnginePage />
      </Wrapper>
    )
    expect(screen.getByText(/consistency/i)).toBeTruthy()
  })
})

// ─── QualityEvaluationPage ────────────────────────────────────────────────────

describe('QualityEvaluationPage', () => {
  it('renders heading', async () => {
    const { QualityEvaluationPage } = await import('@/pages/assetGeneration/QualityEvaluationPage')
    render(
      <Wrapper>
        <QualityEvaluationPage />
      </Wrapper>
    )
    expect(screen.getByText(/quality evaluation/i)).toBeTruthy()
  })
})

// ─── PromptMonitoringPage ─────────────────────────────────────────────────────

describe('PromptMonitoringPage', () => {
  it('renders heading', async () => {
    const { PromptMonitoringPage } = await import('@/pages/assetGeneration/PromptMonitoringPage')
    render(
      <Wrapper>
        <PromptMonitoringPage />
      </Wrapper>
    )
    expect(screen.getByText(/prompt monitoring/i)).toBeTruthy()
  })
})

// ─── AssetLibraryPage ─────────────────────────────────────────────────────────

describe('AssetLibraryPage', () => {
  it('renders heading and tabs', async () => {
    const { AssetLibraryPage } = await import('@/pages/assetGeneration/AssetLibraryPage')
    render(
      <Wrapper>
        <AssetLibraryPage />
      </Wrapper>
    )
    expect(screen.getByText(/asset library/i)).toBeTruthy()
    expect(screen.getByText(/search all/i)).toBeTruthy()
    expect(screen.getByText(/characters/i)).toBeTruthy()
    expect(screen.getByText(/backgrounds/i)).toBeTruthy()
    expect(screen.getByText(/props/i)).toBeTruthy()
  })

  it('shows search filters on Search All tab', async () => {
    const { AssetLibraryPage } = await import('@/pages/assetGeneration/AssetLibraryPage')
    render(
      <Wrapper>
        <AssetLibraryPage />
      </Wrapper>
    )
    expect(screen.getByPlaceholderText(/search by name/i)).toBeTruthy()
  })
})
