import { useEffect, useMemo } from 'react'
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels'
import './App.css'
import { CaseSidebar } from './components/CaseSidebar'
import { CaseWorkspace } from './components/CaseWorkspace'
import {
  useReviewStore,
  selectCases,
  selectFilteredCases,
  selectCasesError,
  selectCasesLoading,
  selectSelectedCaseId,
  selectCaseDetail,
  selectDetailLoading,
  selectDetailError,
  selectAnnotation,
  selectFilters,
  selectAnnotations,
  selectSelectCase,
  selectFetchCases,
  selectFetchCaseDetail,
  selectClearFilters,
  selectSetFilterValues,
  selectSetFingerprintQuery,
  selectDatasetRefreshing,
  selectDatasetRefreshError,
  selectRefreshDataset,
} from './store/useReviewStore'

function App() {
  const cases = useReviewStore(selectCases)
  const filteredCases = useReviewStore(selectFilteredCases)
  const casesLoading = useReviewStore(selectCasesLoading)
  const casesError = useReviewStore(selectCasesError)
  const selectedId = useReviewStore(selectSelectedCaseId)
  const annotations = useReviewStore(selectAnnotations)
  const detailSelector = useMemo(() => selectCaseDetail(selectedId), [selectedId])
  const detailLoadingSelector = useMemo(() => selectDetailLoading(selectedId), [selectedId])
  const detailErrorSelector = useMemo(() => selectDetailError(selectedId), [selectedId])
  const annotationSelector = useMemo(() => selectAnnotation(selectedId), [selectedId])
  const detail = useReviewStore(detailSelector)
  const detailLoading = useReviewStore(detailLoadingSelector)
  const detailError = useReviewStore(detailErrorSelector)
  const annotation = useReviewStore(annotationSelector)
  const filters = useReviewStore(selectFilters)
  const selectCase = useReviewStore(selectSelectCase)
  const fetchCases = useReviewStore(selectFetchCases)
  const fetchCaseDetail = useReviewStore(selectFetchCaseDetail)
  const clearFilters = useReviewStore(selectClearFilters)
  const setFilterValues = useReviewStore(selectSetFilterValues)
  const setFingerprintQuery = useReviewStore(selectSetFingerprintQuery)
  const datasetRefreshing = useReviewStore(selectDatasetRefreshing)
  const datasetRefreshError = useReviewStore(selectDatasetRefreshError)
  const refreshDataset = useReviewStore(selectRefreshDataset)

  useEffect(() => {
    fetchCases()
  }, [fetchCases])

  useEffect(() => {
    if (selectedId && !detail && !detailLoading) {
      fetchCaseDetail(selectedId)
    }
  }, [selectedId, detail, detailLoading, fetchCaseDetail])

  const handleSelect = (caseId: string) => {
    selectCase(caseId)
    fetchCaseDetail(caseId)
  }

  const content = (() => {
    if (casesError) {
      return <ErrorState message={casesError} />
    }
    if (casesLoading && !cases.length) {
      return <LoadingState message="Loading test cases…" />
    }
    if (!selectedId) {
      return <EmptyState />
    }
    if (detailError) {
      return <ErrorState message={detailError} />
    }
    if (!detail || detailLoading) {
      return <LoadingState message="Loading case details…" />
    }
    return <CaseWorkspace key={detail.summary.id} detail={detail} annotation={annotation} />
  })()

  return (
    <PanelGroup className="app-shell" direction="horizontal">
      <Panel className="app-shell__panel" minSize={18} defaultSize={28} order={1}>
        <CaseSidebar
          cases={filteredCases}
          allCases={cases}
          annotations={annotations}
          loading={casesLoading}
          error={casesError}
          selectedId={selectedId}
          onSelect={handleSelect}
          filters={filters}
          onSetFilterValues={setFilterValues}
          onSetFingerprintQuery={setFingerprintQuery}
          onClearFilters={clearFilters}
          datasetRefreshing={datasetRefreshing}
          datasetRefreshError={datasetRefreshError}
          onRefreshDataset={refreshDataset}
        />
      </Panel>
      <PanelResizeHandle className="app-shell__handle" />
      <Panel className="app-shell__panel app-shell__panel--content" minSize={40} defaultSize={72} order={2}>
        <main className="app-content">{content}</main>
      </Panel>
    </PanelGroup>
  )
}

function EmptyState() {
  return (
    <div className="empty-state">
      <h1>Select a test case</h1>
      <p>
        Use the sidebar to load a diff. Once loaded you can review the before/after
        panes, inspect the diff, and record your verdicts.
      </p>
    </div>
  )
}

function LoadingState({ message }: { message: string }) {
  return (
    <div className="empty-state">
      <h1>{message}</h1>
      <p>This should only take a moment.</p>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="empty-state">
      <h1>Something went wrong</h1>
      <p>{message}</p>
    </div>
  )
}

export default App
