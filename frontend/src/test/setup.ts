import '@testing-library/jest-dom'
import { vi } from 'vitest'
import React from 'react'

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useParams: vi.fn(() => ({ projectId: 'test-project-id' })),
    useNavigate: vi.fn(() => vi.fn()),
    Link: ({ children, to }: { children: React.ReactNode; to: string }) =>
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (React as any).createElement('a', { href: to }, children),
  }
})

// Mock @tanstack/react-query
vi.mock('@tanstack/react-query', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-query')>('@tanstack/react-query')
  return {
    ...actual,
    useQuery: vi.fn(() => ({ data: undefined, isLoading: false, isError: false })),
    useMutation: vi.fn(() => ({
      mutate: vi.fn(),
      mutateAsync: vi.fn(),
      isPending: false,
      isError: false,
      isSuccess: false,
      reset: vi.fn(),
    })),
    useQueryClient: vi.fn(() => ({
      invalidateQueries: vi.fn(),
    })),
  }
})
