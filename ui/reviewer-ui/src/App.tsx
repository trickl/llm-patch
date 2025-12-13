import { useEffect } from 'react'
import './App.css'
import { CaseSidebar } from './components/CaseSidebar'
import { CaseWorkspace } from './components/CaseWorkspace'
import {
  useReviewStore,
  selectCases,
  selectCasesError,
  selectCasesLoading,
  selectSelectedCaseId,
  selectCaseDetail,
  selectDetailLoading,
  selectDetailError,
  selectAnnotation,
} from './store/useReviewStore'

function App() {
  const cases = useReviewStore(selectCases)
  const casesLoading = useReviewStore(selectCasesLoading)
  const casesError = useReviewStore(selectCasesError)
  const selectedId = useReviewStore(selectSelectedCaseId)
  const annotations = useReviewStore((state) => state.annotations)
  const detail = useReviewStore(selectCaseDetail(selectedId))
  const detailLoading = useReviewStore(selectDetailLoading(selectedId))
  const detailError = useReviewStore(selectDetailError(selectedId))
  const annotation = useReviewStore(selectAnnotation(selectedId))
  const selectCase = useReviewStore((state) => state.selectCase)
  const fetchCases = useReviewStore((state) => state.fetchCases)
  const fetchCaseDetail = useReviewStore((state) => state.fetchCaseDetail)

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
    return <CaseWorkspace detail={detail} annotation={annotation} />
  })()

  return (
    <div className="app-shell">
      <CaseSidebar
        cases={cases}
        annotations={annotations}
        loading={casesLoading}
        error={casesError}
        selectedId={selectedId}
        onSelect={handleSelect}
      />
      <main className="app-content">{content}</main>
    </div>
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
