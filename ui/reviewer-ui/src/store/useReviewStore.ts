import { createContext, createElement, useCallback, useContext, useMemo, useReducer, type ReactNode } from 'react'
import { fetchCaseDetail, fetchCaseSummaries, refreshDatasetCache, rerunCaseRequest } from '../api/client'
import type {
  AnnotationState,
  CaseDetail,
  CaseSummary,
  CaseMetrics,
  CaseRerunResponse,
  FinalOutcome,
} from '../types'
import { defaultAnnotation } from '../types'
import type { CaseStatusFilter } from '../utils/caseFilters'
import { deriveCaseStatus } from '../utils/caseFilters'

export type FilterKey = 'languages' | 'errorCategories' | 'models' | 'algorithms' | 'statuses'

export interface FiltersState {
  languages: string[]
  errorCategories: string[]
  models: string[]
  algorithms: string[]
  statuses: CaseStatusFilter[]
  fingerprintQuery: string
}

function createEmptyFilters(): FiltersState {
  return {
    languages: [],
    errorCategories: [],
    models: [],
    algorithms: [],
    statuses: [],
    fingerprintQuery: '',
  }
}

interface ReviewDataState {
  cases: CaseSummary[]
  casesLoading: boolean
  casesError: string | null
  caseDetails: Record<string, CaseDetail>
  detailsLoading: Record<string, boolean>
  detailsError: Record<string, string | null>
  annotations: Record<string, AnnotationState>
  selectedId: string | null
  filters: FiltersState
  datasetRefreshing: boolean
  datasetRefreshError: string | null
  caseReruns: Record<string, CaseRerunState>
}

interface CaseRerunState {
  running: boolean
  error: string | null
  lastResult: CaseRerunResponse | null
}

interface ReviewActions {
  fetchCases: () => Promise<void>
  fetchCaseDetail: (caseId: string) => Promise<void>
  selectCase: (caseId: string | null) => void
  updateMetrics: (caseId: string, updates: Partial<CaseMetrics>) => void
  markFinalOutcome: (caseId: string, outcome: FinalOutcome) => void
  setFilterValues: <K extends FilterKey>(key: K, values: FiltersState[K]) => void
  setFingerprintQuery: (query: string) => void
  clearFilters: () => void
  refreshDataset: () => Promise<void>
  rerunCase: (caseId: string) => Promise<void>
}

type ReviewContextValue = ReviewDataState & ReviewActions

const initialState: ReviewDataState = {
  cases: [],
  casesLoading: false,
  casesError: null,
  caseDetails: {},
  detailsLoading: {},
  detailsError: {},
  annotations: {},
  selectedId: null,
  filters: createEmptyFilters(),
  datasetRefreshing: false,
  datasetRefreshError: null,
  caseReruns: {},
}

type ReviewAction =
  | { type: 'FETCH_CASES_REQUEST' }
  | { type: 'FETCH_CASES_SUCCESS'; payload: CaseSummary[] }
  | { type: 'FETCH_CASES_FAILURE'; error: string }
  | { type: 'FETCH_CASE_DETAIL_REQUEST'; caseId: string }
  | { type: 'FETCH_CASE_DETAIL_SUCCESS'; caseId: string; detail: CaseDetail }
  | { type: 'FETCH_CASE_DETAIL_FAILURE'; caseId: string; error: string }
  | { type: 'SELECT_CASE'; caseId: string | null }
  | { type: 'UPDATE_METRICS'; caseId: string; updates: Partial<CaseMetrics> }
  | { type: 'SET_FILTER_VALUES'; key: FilterKey; values: FiltersState[FilterKey] }
  | { type: 'SET_FINGERPRINT_QUERY'; query: string }
  | { type: 'CLEAR_FILTERS' }
  | { type: 'DATASET_REFRESH_REQUEST' }
  | { type: 'DATASET_REFRESH_SUCCESS' }
  | { type: 'DATASET_REFRESH_FAILURE'; error: string }
  | { type: 'CLEAR_CASE_DETAILS' }
  | { type: 'CASE_RERUN_REQUEST'; caseId: string }
  | { type: 'CASE_RERUN_SUCCESS'; caseId: string; result: CaseRerunResponse }
  | { type: 'CASE_RERUN_FAILURE'; caseId: string; error: string }

function reviewReducer(state: ReviewDataState, action: ReviewAction): ReviewDataState {
  switch (action.type) {
    case 'FETCH_CASES_REQUEST':
      return { ...state, casesLoading: true, casesError: null }
    case 'FETCH_CASES_SUCCESS': {
      const nextSelected = state.selectedId ?? action.payload[0]?.id ?? null
      return {
        ...state,
        cases: action.payload,
        casesLoading: false,
        casesError: null,
        selectedId: nextSelected,
      }
    }
    case 'FETCH_CASES_FAILURE':
      return { ...state, casesLoading: false, casesError: action.error }
    case 'FETCH_CASE_DETAIL_REQUEST':
      return {
        ...state,
        detailsLoading: { ...state.detailsLoading, [action.caseId]: true },
        detailsError: { ...state.detailsError, [action.caseId]: null },
      }
    case 'FETCH_CASE_DETAIL_SUCCESS':
      return {
        ...state,
        caseDetails: { ...state.caseDetails, [action.caseId]: action.detail },
        detailsLoading: { ...state.detailsLoading, [action.caseId]: false },
      }
    case 'FETCH_CASE_DETAIL_FAILURE':
      return {
        ...state,
        detailsLoading: { ...state.detailsLoading, [action.caseId]: false },
        detailsError: { ...state.detailsError, [action.caseId]: action.error },
      }
    case 'SELECT_CASE':
      return { ...state, selectedId: action.caseId }
    case 'UPDATE_METRICS':
      return {
        ...state,
        annotations: {
          ...state.annotations,
          [action.caseId]: annotate(state.annotations[action.caseId], action.updates),
        },
      }
    case 'SET_FILTER_VALUES':
      return {
        ...state,
        filters: {
          ...state.filters,
          [action.key]: action.values,
        },
      }
    case 'SET_FINGERPRINT_QUERY':
      return {
        ...state,
        filters: {
          ...state.filters,
          fingerprintQuery: action.query,
        },
      }
    case 'CLEAR_FILTERS':
      return {
        ...state,
        filters: createEmptyFilters(),
      }
    case 'DATASET_REFRESH_REQUEST':
      return {
        ...state,
        datasetRefreshing: true,
        datasetRefreshError: null,
      }
    case 'DATASET_REFRESH_SUCCESS':
      return {
        ...state,
        datasetRefreshing: false,
      }
    case 'DATASET_REFRESH_FAILURE':
      return {
        ...state,
        datasetRefreshing: false,
        datasetRefreshError: action.error,
      }
    case 'CLEAR_CASE_DETAILS':
      return {
        ...state,
        caseDetails: {},
        detailsLoading: {},
        detailsError: {},
      }
    case 'CASE_RERUN_REQUEST':
      return {
        ...state,
        caseReruns: {
          ...state.caseReruns,
          [action.caseId]: {
            running: true,
            error: null,
            lastResult: null,
          },
        },
      }
    case 'CASE_RERUN_SUCCESS':
      return {
        ...state,
        caseReruns: {
          ...state.caseReruns,
          [action.caseId]: {
            running: false,
            error: null,
            lastResult: action.result,
          },
        },
      }
    case 'CASE_RERUN_FAILURE':
      return {
        ...state,
        caseReruns: {
          ...state.caseReruns,
          [action.caseId]: {
            running: false,
            error: action.error,
            lastResult: null,
          },
        },
      }
    default:
      return state
  }
}

const ReviewContext = createContext<ReviewContextValue | undefined>(undefined)

export function ReviewProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reviewReducer, initialState)

  const fetchCases = useCallback(async () => {
    dispatch({ type: 'FETCH_CASES_REQUEST' })
    try {
      const summaries = await fetchCaseSummaries()
      dispatch({ type: 'FETCH_CASES_SUCCESS', payload: summaries })
    } catch (error) {
      dispatch({
        type: 'FETCH_CASES_FAILURE',
        error: error instanceof Error ? error.message : 'Failed to load cases',
      })
    }
  }, [])

  const fetchCaseDetailAction = useCallback(async (caseId: string) => {
    dispatch({ type: 'FETCH_CASE_DETAIL_REQUEST', caseId })
    try {
      const detail = await fetchCaseDetail(caseId)
      dispatch({ type: 'FETCH_CASE_DETAIL_SUCCESS', caseId, detail })
    } catch (error) {
      dispatch({
        type: 'FETCH_CASE_DETAIL_FAILURE',
        caseId,
        error: error instanceof Error ? error.message : 'Failed to load case detail',
      })
    }
  }, [])

  const selectCase = useCallback((caseId: string | null) => {
    dispatch({ type: 'SELECT_CASE', caseId })
  }, [])

  const updateMetrics = useCallback((caseId: string, updates: Partial<CaseMetrics>) => {
    dispatch({ type: 'UPDATE_METRICS', caseId, updates })
  }, [])

  const markFinalOutcome = useCallback(
    (caseId: string, outcome: FinalOutcome) => {
      updateMetrics(caseId, { finalOutcome: outcome })
    },
    [updateMetrics],
  )

  const setFilterValues = useCallback(
    <K extends FilterKey>(key: K, values: FiltersState[K]) => {
      dispatch({ type: 'SET_FILTER_VALUES', key, values })
    },
    [],
  )

  const setFingerprintQuery = useCallback((query: string) => {
    dispatch({ type: 'SET_FINGERPRINT_QUERY', query })
  }, [])

  const clearFilters = useCallback(() => {
    dispatch({ type: 'CLEAR_FILTERS' })
  }, [])

  const selectedCaseId = state.selectedId

  const refreshDataset = useCallback(async () => {
    dispatch({ type: 'DATASET_REFRESH_REQUEST' })
    try {
      await refreshDatasetCache()
      dispatch({ type: 'CLEAR_CASE_DETAILS' })
      await fetchCases()
      if (selectedCaseId) {
        await fetchCaseDetailAction(selectedCaseId)
      }
      dispatch({ type: 'DATASET_REFRESH_SUCCESS' })
    } catch (error) {
      dispatch({
        type: 'DATASET_REFRESH_FAILURE',
        error: error instanceof Error ? error.message : 'Failed to refresh dataset',
      })
    }
  }, [fetchCases, fetchCaseDetailAction, selectedCaseId])

  const rerunCase = useCallback(
    async (caseId: string) => {
      dispatch({ type: 'CASE_RERUN_REQUEST', caseId })
      try {
        const result = await rerunCaseRequest(caseId)
        dispatch({ type: 'CASE_RERUN_SUCCESS', caseId, result })
        await refreshDataset()
      } catch (error) {
        dispatch({
          type: 'CASE_RERUN_FAILURE',
          caseId,
          error: error instanceof Error ? error.message : 'Failed to rerun case',
        })
      }
    },
    [refreshDataset],
  )

  const contextValue = useMemo<ReviewContextValue>(
    () => ({
      ...state,
      fetchCases,
      fetchCaseDetail: fetchCaseDetailAction,
      selectCase,
      updateMetrics,
      markFinalOutcome,
      setFilterValues,
      setFingerprintQuery,
      clearFilters,
      refreshDataset,
      rerunCase,
    }),
    [
      state,
      fetchCases,
      fetchCaseDetailAction,
      selectCase,
      updateMetrics,
      markFinalOutcome,
      setFilterValues,
      setFingerprintQuery,
      clearFilters,
      refreshDataset,
      rerunCase,
    ],
  )

  return createElement(ReviewContext.Provider, { value: contextValue, children })
}

function useReviewContext() {
  const context = useContext(ReviewContext)
  if (!context) {
    throw new Error('useReviewStore must be used within a ReviewProvider')
  }
  return context
}

export function useReviewStore<T>(selector: (state: ReviewContextValue) => T): T {
  const context = useReviewContext()
  return selector(context)
}

function annotate(existing: AnnotationState | undefined, updates?: Partial<CaseMetrics>): AnnotationState {
  const nextMetrics = {
    ...defaultAnnotation,
    ...existing,
    ...updates,
  }
  return {
    ...nextMetrics,
    updatedAt: new Date().toISOString(),
    updatedBy: 'local-reviewer',
  }
}

function applyFilters(cases: CaseSummary[], filters: FiltersState): CaseSummary[] {
  const fingerprintQuery = filters.fingerprintQuery.trim().toLowerCase()
  if (
    !fingerprintQuery.length &&
    !filters.languages.length &&
    !filters.errorCategories.length &&
    !filters.models.length &&
    !filters.algorithms.length &&
    !filters.statuses.length
  ) {
    return cases
  }
  return cases.filter((summary) => {
    if (fingerprintQuery.length) {
      const fingerprint = summary.fingerprint.trim().toLowerCase()
      if (!fingerprint.includes(fingerprintQuery)) {
        return false
      }
    }
    if (filters.languages.length && !filters.languages.includes(summary.language)) {
      return false
    }
    if (filters.errorCategories.length) {
      const key = summary.firstErrorCategory == null ? 'unlabeled' : String(summary.firstErrorCategory)
      if (!filters.errorCategories.includes(key)) {
        return false
      }
    }
    if (filters.models.length && !filters.models.includes(summary.modelSlug)) {
      return false
    }
    if (filters.algorithms.length && !filters.algorithms.includes(summary.algorithm)) {
      return false
    }
    if (filters.statuses.length) {
      const status = deriveCaseStatus(summary)
      if (!filters.statuses.includes(status)) {
        return false
      }
    }
    return true
  })
}

export const selectCases = (state: ReviewContextValue) => state.cases
export const selectFilteredCases = (state: ReviewContextValue) => applyFilters(state.cases, state.filters)
export const selectCasesLoading = (state: ReviewContextValue) => state.casesLoading
export const selectCasesError = (state: ReviewContextValue) => state.casesError
export const selectSelectedCaseId = (state: ReviewContextValue) => state.selectedId
export const selectCaseDetail = (caseId: string | null) => (state: ReviewContextValue) =>
  caseId ? state.caseDetails[caseId] ?? null : null
export const selectDetailLoading = (caseId: string | null) => (state: ReviewContextValue) =>
  caseId ? Boolean(state.detailsLoading[caseId]) : false
export const selectDetailError = (caseId: string | null) => (state: ReviewContextValue) =>
  caseId ? state.detailsError[caseId] ?? null : null
export const selectAnnotation = (caseId: string | null) => (state: ReviewContextValue) =>
  caseId ? state.annotations[caseId] ?? defaultAnnotation : defaultAnnotation
export const selectFilters = (state: ReviewContextValue) => state.filters
export const selectAnnotations = (state: ReviewContextValue) => state.annotations
export const selectSelectCase = (state: ReviewContextValue) => state.selectCase
export const selectFetchCases = (state: ReviewContextValue) => state.fetchCases
export const selectFetchCaseDetail = (state: ReviewContextValue) => state.fetchCaseDetail
export const selectClearFilters = (state: ReviewContextValue) => state.clearFilters
export const selectSetFilterValues = (state: ReviewContextValue) => state.setFilterValues
export const selectSetFingerprintQuery = (state: ReviewContextValue) => state.setFingerprintQuery
export const selectDatasetRefreshing = (state: ReviewContextValue) => state.datasetRefreshing
export const selectDatasetRefreshError = (state: ReviewContextValue) => state.datasetRefreshError
export const selectRefreshDataset = (state: ReviewContextValue) => state.refreshDataset
export const selectCaseRerunState = (caseId: string | null) => (state: ReviewContextValue) =>
  caseId ? state.caseReruns[caseId] ?? { running: false, error: null, lastResult: null } : { running: false, error: null, lastResult: null }
export const selectRerunCase = (state: ReviewContextValue) => state.rerunCase
