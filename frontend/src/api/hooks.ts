/**
 * TanStack Query hooks over the API (frontend.md §6). Response/request types come
 * straight from the generated OpenAPI types — no hand-kept duplicates.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError, api } from './client'
import type { components } from './generated'

type Schemas = components['schemas']
export type Config = Schemas['ConfigOut']
export type Today = Schemas['TodayOut']
export type OfferSlot = Schemas['OfferSlotOut']
export type Picked = Schemas['PickedOut']
export type FrozenEntry = Schemas['FrozenEntryOut']
export type Gallery = Schemas['GalleryOut']
export type Stats = Schemas['StatsOut']

/** Don't retry auth failures — they mean "sign in", not "flaky network". */
function retryUnlessAuth(failureCount: number, error: unknown): boolean {
  if (
    error instanceof ApiError &&
    (error.status === 401 || error.status === 403)
  )
    return false
  return failureCount < 2
}

export function useConfig() {
  return useQuery({
    queryKey: ['config'],
    queryFn: () => api.get<Config>('/config'),
  })
}

export function useToday() {
  return useQuery({
    queryKey: ['today'],
    queryFn: () => api.get<Today>('/today'),
    retry: retryUnlessAuth,
  })
}

export function useGallery() {
  return useQuery({
    queryKey: ['gallery'],
    queryFn: () => api.get<Gallery>('/gallery'),
    retry: retryUnlessAuth,
  })
}

export function useStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: () => api.get<Stats>('/stats'),
    retry: retryUnlessAuth,
  })
}

export function usePick() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (tier: string) => api.post<Picked>('/pick', { tier }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['today'] }),
  })
}

export function useSubmit() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (text: string) => api.post<FrozenEntry>('/submit', { text }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['today'] })
      qc.invalidateQueries({ queryKey: ['gallery'] })
      qc.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}

/** DEBUG-only dev-login bypass; on success, refetch everything (now authed). */
export function useDevLogin() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.post<{ ok: boolean; email: string }>('/dev/login'),
    onSuccess: () => qc.invalidateQueries(),
  })
}

/** DEBUG-only: shift the server's dev clock forward a day, then refetch. */
export function useAdvanceDay() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.post<{ today: string }>('/dev/advance-day'),
    onSuccess: () => qc.invalidateQueries(),
  })
}

/** DEBUG-only: wipe all entries + reset the clock for a clean slate. */
export function useResetDb() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.post<{ today: string }>('/dev/reset'),
    onSuccess: () => qc.invalidateQueries(),
  })
}
