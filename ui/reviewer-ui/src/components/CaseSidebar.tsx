import clsx from 'clsx'
import type { AnnotationState, CaseSummary } from '../types'
import { defaultAnnotation } from '../types'

interface CaseSidebarProps {
  cases: CaseSummary[]
  annotations: Record<string, AnnotationState>
  selectedId: string | null
  loading: boolean
  error: string | null
  onSelect: (caseId: string) => void
}

export function CaseSidebar({ cases, annotations, selectedId, loading, error, onSelect }: CaseSidebarProps) {
  const suiteLabel = cases[0]?.problemId ?? 'Test Cases'
  return (
    <aside className="sidebar">
      <div className="sidebar__header">
        <div>
          <p className="sidebar__eyebrow">Dataset</p>
          <h2>{suiteLabel}</h2>
        </div>
        <span className="sidebar__count">{cases.length}</span>
      </div>
      <div className="sidebar__input-wrapper">
        <input
          type="search"
          placeholder="Filter by file or status"
          className="sidebar__filter"
          aria-label="Filter test cases"
          disabled
        />
      </div>
      {loading && !cases.length && <p className="sidebar__status">Loading…</p>}
      {error && <p className="sidebar__status sidebar__status--error">{error}</p>}
      <ul className="sidebar__list">
        {cases.map((testCase) => {
          const active = testCase.id === selectedId
          const annotation = annotations[testCase.id] ?? defaultAnnotation
          return (
            <li key={testCase.id}>
              <button
                type="button"
                className={clsx('sidebar__item', active && 'sidebar__item--active')}
                onClick={() => onSelect(testCase.id)}
              >
                <div className="sidebar__item-main">
                  <div>
                    <span className="sidebar__item-title">{testCase.filePath}</span>
                    <span className="sidebar__item-subtitle">{testCase.modelSlug}</span>
                  </div>
                  <span className="sidebar__item-subtitle">{testCase.diffName}</span>
                </div>
                <div className="sidebar__chips">
                  <StatusChip label="Src" value={annotation.sourceQuality} />
                  <StatusChip label="Diff" value={annotation.diffQuality} />
                  <OutcomeChip value={annotation.finalOutcome} />
                  <PatchChip applied={testCase.patchApplied} success={testCase.success} />
                </div>
              </button>
            </li>
          )
        })}
      </ul>
    </aside>
  )
}

interface StatusChipProps {
  label?: string
  value: AnnotationState['sourceQuality']
}

function StatusChip({ label, value }: StatusChipProps) {
  return (
    <span className={clsx('chip', `chip--${value}`)}>
      {label && <strong>{label}: </strong>}
      {value === 'good' ? 'Good' : 'Poor'}
    </span>
  )
}

interface OutcomeChipProps {
  value: AnnotationState['finalOutcome']
}

function OutcomeChip({ value }: OutcomeChipProps) {
  if (value === 'pending') {
    return <span className="chip chip--pending">Pending</span>
  }
  return (
    <span className={clsx('chip', value === 'good' ? 'chip--good' : 'chip--bad')}>
      Final: {value === 'good' ? 'Good' : 'Bad'}
    </span>
  )
}

function PatchChip({ applied, success }: { applied: boolean; success: boolean }) {
  if (success) {
    return <span className="chip chip--good">Success</span>
  }
  if (applied) {
    return <span className="chip chip--pending">Applied</span>
  }
  return <span className="chip chip--poor">Failed</span>
}
