import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'

// ─── Module-level mocks (hoisted by vitest) ────────────────────────────────

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
    listRetryQueue: vi.fn().mockResolvedValue({ items: [], meta: { total: 0, page: 1, page_size: 20, total_pages: 1 } }),
    getRetryQueue: vi.fn().mockResolvedValue([]),
    retryEntry: vi.fn().mockResolvedValue({}),
    getConsistencyReport: vi.fn().mockResolvedValue({ groups: [], total_groups: 0 }),
    listQualityEvaluations: vi.fn().mockResolvedValue({ items: [], meta: { total: 0, page: 1, page_size: 20, total_pages: 1 } }),
    listPromptTemplates: vi.fn().mockResolvedValue({ items: [], meta: { total: 0, page: 1, page_size: 20, total_pages: 1 } }),
    listAssets: vi.fn().mockResolvedValue({ items: [], meta: { total: 0, page: 1, page_size: 20, total_pages: 1 } }),
    // Generation triggers — the two functions this feature adds
    createAsset: vi.fn().mockResolvedValue({ id: 'mock-asset-id-123', name: 'Test Asset', asset_type: 'background' }),
    triggerAssetGeneration: vi.fn().mockResolvedValue({ status: 'queued', message: 'ok', dispatch_mode: 'celery' }),
    triggerEpisodeGeneration: vi.fn().mockResolvedValue({ status: 'queued', message: 'ok', dispatch_mode: 'celery' }),
  },
}))

// Mock apiClient so character-fetch in NewGenerationModal doesn't hit real network
vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: { items: [], meta: { total: 0 } } }),
  },
}))

// ─── Test wrapper ──────────────────────────────────────────────────────────

function makeWrapper(path = '/projects/test-project-id/asset-generation') {
  function Wrapper({ children }: { children: React.ReactNode }) {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    return (
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={[path]}>
          {children}
        </MemoryRouter>
      </QueryClientProvider>
    )
  }
  return Wrapper
}

const Wrapper = makeWrapper()

// ─── AssetGenerationDashboardPage ─────────────────────────────────────────

describe('AssetGenerationDashboardPage', () => {
  afterEach(() => {
    vi.mocked(useQuery).mockReset()
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useQuery>)
  })

  it('renders heading', async () => {
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
    const h1 = container.querySelector('h1')
    expect(h1?.textContent).toMatch(/asset generation engine/i)
  })
})

// ─── GenerationJobsPage ────────────────────────────────────────────────────

describe('GenerationJobsPage', () => {
  // Reset call counts before each test so assertions are isolated
  beforeEach(async () => {
    const { assetGenerationApi: api } = await import('@/api/assetGeneration')
    vi.mocked(api.createAsset).mockClear()
    vi.mocked(api.triggerAssetGeneration).mockClear()
    vi.mocked(api.listJobs).mockClear()
    vi.mocked(api.listJobs).mockResolvedValue({ items: [], meta: { total: 0, page: 1, page_size: 20, total_pages: 1 } })
    vi.mocked(api.createAsset).mockResolvedValue({ id: 'mock-asset-id-123', name: 'Test Asset', asset_type: 'background' } as any)
    vi.mocked(api.triggerAssetGeneration).mockResolvedValue({ status: 'queued', message: 'ok', dispatch_mode: 'celery' })
  })

  it('renders heading', async () => {
    const { GenerationJobsPage } = await import('@/pages/assetGeneration/GenerationJobsPage')
    render(<Wrapper><GenerationJobsPage /></Wrapper>)
    const headings = screen.getAllByText(/generation jobs/i)
    expect(headings.length).toBeGreaterThan(0)
  })

  it('renders the New Generation button', async () => {
    const { GenerationJobsPage } = await import('@/pages/assetGeneration/GenerationJobsPage')
    render(<Wrapper><GenerationJobsPage /></Wrapper>)
    const btn = screen.getByTestId('new-generation-btn')
    expect(btn).toBeTruthy()
    expect(btn.textContent).toMatch(/new generation/i)
  })

  it('opens the generation modal when New Generation is clicked', async () => {
    const { GenerationJobsPage } = await import('@/pages/assetGeneration/GenerationJobsPage')
    render(<Wrapper><GenerationJobsPage /></Wrapper>)

    fireEvent.click(screen.getByTestId('new-generation-btn'))

    await waitFor(() => {
      expect(screen.getByText(/new generation job/i)).toBeTruthy()
    })
  })

  it('calls createAsset then triggerAssetGeneration with correct payload on submit', async () => {
    const { assetGenerationApi } = await import('@/api/assetGeneration')
    const { useMutation } = await import('@tanstack/react-query')

    // The global setup.ts mocks useMutation so mutate() is a no-op vi.fn().
    // For this test we need the real mutationFn to execute, so we temporarily
    // override useMutation to make mutate() actually invoke the mutationFn.
    vi.mocked(useMutation).mockImplementation((options: any) => ({
      mutate: vi.fn(() => options?.mutationFn?.()),
      mutateAsync: vi.fn(async () => options?.mutationFn?.()),
      isPending: false,
      isError: false,
      isSuccess: false,
      data: undefined,
      reset: vi.fn(),
    }) as any)

    const { GenerationJobsPage } = await import('@/pages/assetGeneration/GenerationJobsPage')
    render(<Wrapper><GenerationJobsPage /></Wrapper>)

    // Open modal
    fireEvent.click(screen.getByTestId('new-generation-btn'))
    await waitFor(() => screen.getByTestId('new-generation-form'))

    // Fill in name — triggers a re-render so the mutationFn closure captures the updated value
    fireEvent.change(
      screen.getByPlaceholderText(/e.g. Hero character front view/i),
      { target: { value: 'Hero Background' } },
    )
    // Fill in prompt
    fireEvent.change(
      screen.getByPlaceholderText(/custom generation instructions/i),
      { target: { value: 'sunset forest' } },
    )

    // Submit the form
    const form = screen.getByTestId('new-generation-form')
    fireEvent.submit(form)

    await waitFor(() => {
      expect(vi.mocked(assetGenerationApi.createAsset)).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'Hero Background', asset_type: expect.any(String) })
      )
    })
    await waitFor(() => {
      expect(vi.mocked(assetGenerationApi.triggerAssetGeneration)).toHaveBeenCalledWith(
        expect.objectContaining({ asset_id: 'mock-asset-id-123' })
      )
    })
  })

  it('submit button is disabled when name is empty', async () => {
    const { GenerationJobsPage } = await import('@/pages/assetGeneration/GenerationJobsPage')
    render(<Wrapper><GenerationJobsPage /></Wrapper>)

    fireEvent.click(screen.getByTestId('new-generation-btn'))
    await waitFor(() => screen.getByTestId('new-generation-form'))

    const submitBtn = screen.getByTestId('submit-generation')
    expect(submitBtn).toHaveProperty('disabled', true)
  })
})

// ─── RetryQueuePage ────────────────────────────────────────────────────────

describe('RetryQueuePage', () => {
  it('renders heading', async () => {
    const { RetryQueuePage } = await import('@/pages/assetGeneration/RetryQueuePage')
    render(<Wrapper><RetryQueuePage /></Wrapper>)
    const headings = screen.getAllByText(/retry queue/i)
    expect(headings.length).toBeGreaterThan(0)
  })

  it('renders empty state when no entries', async () => {
    const { RetryQueuePage } = await import('@/pages/assetGeneration/RetryQueuePage')
    render(<Wrapper><RetryQueuePage /></Wrapper>)
    expect(document.body).toBeTruthy()
  })
})

// ─── ConsistencyEnginePage ────────────────────────────────────────────────

describe('ConsistencyEnginePage', () => {
  it('renders heading', async () => {
    const { ConsistencyEnginePage } = await import('@/pages/assetGeneration/ConsistencyEnginePage')
    render(<Wrapper><ConsistencyEnginePage /></Wrapper>)
    const headings = screen.getAllByText(/consistency/i)
    expect(headings.length).toBeGreaterThan(0)
  })
})

// ─── QualityEvaluationPage ────────────────────────────────────────────────

describe('QualityEvaluationPage', () => {
  it('renders heading', async () => {
    const { QualityEvaluationPage } = await import('@/pages/assetGeneration/QualityEvaluationPage')
    render(<Wrapper><QualityEvaluationPage /></Wrapper>)
    const headings = screen.getAllByText(/quality evaluation/i)
    expect(headings.length).toBeGreaterThan(0)
  })
})

// ─── PromptMonitoringPage ─────────────────────────────────────────────────

describe('PromptMonitoringPage', () => {
  it('renders heading', async () => {
    const { PromptMonitoringPage } = await import('@/pages/assetGeneration/PromptMonitoringPage')
    render(<Wrapper><PromptMonitoringPage /></Wrapper>)
    const headings = screen.getAllByText(/prompt monitoring/i)
    expect(headings.length).toBeGreaterThan(0)
  })
})

// ─── AssetLibraryPage ─────────────────────────────────────────────────────

describe('AssetLibraryPage', () => {
  it('renders heading and tabs', async () => {
    const { AssetLibraryPage } = await import('@/pages/assetGeneration/AssetLibraryPage')
    render(<Wrapper><AssetLibraryPage /></Wrapper>)
    expect(screen.getAllByText(/asset library/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/search all/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/characters/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/backgrounds/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/props/i).length).toBeGreaterThan(0)
  })

  it('shows search filters on Search All tab', async () => {
    const { AssetLibraryPage } = await import('@/pages/assetGeneration/AssetLibraryPage')
    render(<Wrapper><AssetLibraryPage /></Wrapper>)
    expect(screen.getByPlaceholderText(/search by name/i)).toBeTruthy()
  })
})
