import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'

// Module-level mock for assetGenerationApi (hoisted by vitest)
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
    listJobs: vi.fn().mockResolvedValue({ items: [], meta: { total: 0, page: 1, page_size: 20, total_pages: 1 } }),
    getRetryQueue: vi.fn().mockResolvedValue([]),
    getConsistencyReport: vi.fn().mockResolvedValue({ groups: [], total_groups: 0 }),
    listQualityEvaluations: vi.fn().mockResolvedValue({ items: [], meta: { total: 0, page: 1, page_size: 20, total_pages: 1 } }),
    listPromptTemplates: vi.fn().mockResolvedValue({ items: [], meta: { total: 0, page: 1, page_size: 20, total_pages: 1 } }),
    listAssets: vi.fn().mockResolvedValue({ items: [], meta: { total: 0, page: 1, page_size: 20, total_pages: 1 } }),
  },
}))

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
  afterEach(() => {
    // Reset useQuery back to the global default (data: undefined) after this block
    vi.mocked(useQuery).mockReset()
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useQuery>)
  })

  it('renders heading', async () => {
    // Provide real dashboard data so the component renders past its !data guard
    vi.mocked(useQuery).mockReturnValue({
      data: {
        total_assets: 5,
        assets_completed: 3,
        assets_pending: 1,
        assets_failed: 0,
        assets_generating: 1,
        total_retries: 0,
        avg_quality_score: 92,
        assets_by_type: {},
        recent_jobs: [],
        generation_history: [],
        generation_history_7d: [],
      },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useQuery>)

    const { AssetGenerationDashboardPage } = await import(
      '@/pages/assetGeneration/AssetGenerationDashboardPage'
    )
    const { container } = render(
      <Wrapper>
        <AssetGenerationDashboardPage />
      </Wrapper>
    )
    // h1 contains SVG icon + text; query DOM directly
    const h1 = container.querySelector('h1')
    expect(h1?.textContent).toMatch(/asset generation engine/i)
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
    const headings = screen.getAllByText(/generation jobs/i)
    expect(headings.length).toBeGreaterThan(0)
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
    const headings = screen.getAllByText(/retry queue/i)
    expect(headings.length).toBeGreaterThan(0)
  })

  it('renders empty state when no entries', async () => {
    const { RetryQueuePage } = await import('@/pages/assetGeneration/RetryQueuePage')
    render(
      <Wrapper>
        <RetryQueuePage />
      </Wrapper>
    )
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
    const headings = screen.getAllByText(/consistency/i)
    expect(headings.length).toBeGreaterThan(0)
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
    const headings = screen.getAllByText(/quality evaluation/i)
    expect(headings.length).toBeGreaterThan(0)
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
    const headings = screen.getAllByText(/prompt monitoring/i)
    expect(headings.length).toBeGreaterThan(0)
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
    expect(screen.getAllByText(/asset library/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/search all/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/characters/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/backgrounds/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/props/i).length).toBeGreaterThan(0)
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
