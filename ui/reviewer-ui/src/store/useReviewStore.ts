import { create } from 'zustand'
import { fetchCaseDetail, fetchCaseSummaries } from '../api/client'
import type { AnnotationState, CaseDetail, CaseSummary, CaseMetrics, FinalOutcome } from '../types'
import { defaultAnnotation } from '../types'

interface ReviewState {
  cases: CaseSummary[]
  casesLoading: boolean
  casesError: string | null
  caseDetails: Record<string, CaseDetail>
  detailsLoading: Record<string, boolean>
  detailsError: Record<string, string | null>
  annotations: Record<string, AnnotationState>
  selectedId: string | null
  fetchCases: () => Promise<void>
  fetchCaseDetail: (caseId: string) => Promise<void>
  selectCase: (caseId: string | null) => void
  updateMetrics: (caseId: string, updates: Partial<CaseMetrics>) => void
  updateNotes: (caseId: string, notes: string) => void
  markFinalOutcome: (caseId: string, outcome: FinalOutcome) => void
}

export const useReviewStore = create<ReviewState>((set, get) => ({
  cases: [],
  casesLoading: false,
  casesError: null,
  caseDetails: {},
  detailsLoading: {},
  detailsError: {},
  annotations: {},
  selectedId: null,
  async fetchCases() {
    set({ casesLoading: true, casesError: null })
    try {
      const summaries = await fetchCaseSummaries()
      set((state) => ({
        cases: summaries,
        casesLoading: false,
        selectedId: state.selectedId ?? summaries[0]?.id ?? null,
      }))
    } catch (error) {
      set({
        casesLoading: false,
        casesError: error instanceof Error ? error.message : 'Failed to load cases',
      })
    }
  },
  async fetchCaseDetail(caseId) {
    set((state) => ({
      detailsLoading: { ...state.detailsLoading, [caseId]: true },
      detailsError: { ...state.detailsError, [caseId]: null },
    }))
    try {
      const detail = await fetchCaseDetail(caseId)
      set((state) => ({
        caseDetails: { ...state.caseDetails, [caseId]: detail },
        detailsLoading: { ...state.detailsLoading, [caseId]: false },
      }))
    } catch (error) {
      set((state) => ({
        detailsLoading: { ...state.detailsLoading, [caseId]: false },
        detailsError: {
          ...state.detailsError,
          [caseId]: error instanceof Error ? error.message : 'Failed to load case detail',
        },
      }))
    }
  },
  selectCase(caseId) {
    set({ selectedId: caseId })
  },
  updateMetrics(caseId, updates) {
    set((state) => ({
      annotations: {
        ...state.annotations,
        [caseId]: annotate(state.annotations[caseId], updates),
      },
    }))
  },
  updateNotes(caseId, notes) {
    set((state) => ({
      annotations: {
        ...state.annotations,
        [caseId]: annotate(state.annotations[caseId], undefined, notes),
      },
    }))
  },
  markFinalOutcome(caseId, outcome) {
    get().updateMetrics(caseId, { finalOutcome: outcome })
  },
}))

function annotate(
  existing: AnnotationState | undefined,
  updates?: Partial<CaseMetrics>,
  notes?: string,
): AnnotationState {
  const nextMetrics = {
    ...defaultAnnotation,
    ...existing,
    ...updates,
  }
  const nextNotes = notes ?? existing?.notes ?? defaultAnnotation.notes
  return {
    ...nextMetrics,
    notes: nextNotes,
    updatedAt: new Date().toISOString(),
    updatedBy: 'local-reviewer',
  }
}

export const selectCases = (state: ReviewState) => state.cases
export const selectCasesLoading = (state: ReviewState) => state.casesLoading
export const selectCasesError = (state: ReviewState) => state.casesError
export const selectSelectedCaseId = (state: ReviewState) => state.selectedId
export const selectCaseDetail = (caseId: string | null) => (state: ReviewState) =>
  caseId ? state.caseDetails[caseId] ?? null : null
export const selectDetailLoading = (caseId: string | null) => (state: ReviewState) =>
  caseId ? Boolean(state.detailsLoading[caseId]) : false
export const selectDetailError = (caseId: string | null) => (state: ReviewState) =>
  caseId ? state.detailsError[caseId] ?? null : null
export const selectAnnotation = (caseId: string | null) => (state: ReviewState) =>
  caseId ? state.annotations[caseId] ?? defaultAnnotation : defaultAnnotation
