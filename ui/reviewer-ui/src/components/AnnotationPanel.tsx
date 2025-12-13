import { useCallback } from 'react'
import type { AnnotationState, CaseMetrics, FinalOutcome } from '../types'
import { useReviewStore } from '../store/useReviewStore'

interface AnnotationPanelProps {
  caseId: string
  annotation: AnnotationState
}

const qualityOptions = [
  { value: 'good', label: 'Good' },
  { value: 'poor', label: 'Poor / Unusable' },
] as const

const finalOptions: { value: FinalOutcome; label: string }[] = [
  { value: 'good', label: 'Good' },
  { value: 'bad', label: 'Bad' },
  { value: 'pending', label: 'Pending' },
]

export function AnnotationPanel({ caseId, annotation }: AnnotationPanelProps) {
  const updateMetrics = useReviewStore((state) => state.updateMetrics)
  const updateNotes = useReviewStore((state) => state.updateNotes)

  const handleSourceQuality = useCallback(
    (value: CaseMetrics['sourceQuality']) => updateMetrics(caseId, { sourceQuality: value }),
    [caseId, updateMetrics],
  )

  const handleDiffQuality = useCallback(
    (value: CaseMetrics['diffQuality']) => updateMetrics(caseId, { diffQuality: value }),
    [caseId, updateMetrics],
  )

  const handleFinalOutcome = useCallback(
    (value: FinalOutcome) => updateMetrics(caseId, { finalOutcome: value }),
    [caseId, updateMetrics],
  )

  return (
    <section className="annotation-panel">
      <h3>Annotations</h3>
      <div className="annotation-panel__group">
        <p className="annotation-panel__label">Source Quality</p>
        <ToggleGroup
          value={annotation.sourceQuality}
          onChange={handleSourceQuality}
          options={qualityOptions}
        />
      </div>
      <div className="annotation-panel__group">
        <p className="annotation-panel__label">Diff Quality</p>
        <ToggleGroup
          value={annotation.diffQuality}
          onChange={handleDiffQuality}
          options={qualityOptions}
        />
      </div>
      <div className="annotation-panel__group">
        <p className="annotation-panel__label">Final Application</p>
        <ToggleGroup
          value={annotation.finalOutcome}
          onChange={handleFinalOutcome}
          options={finalOptions}
        />
      </div>
      <div className="annotation-panel__group">
        <p className="annotation-panel__label">Reviewer Notes</p>
        <textarea
          value={annotation.notes}
          onChange={(event) => updateNotes(caseId, event.target.value)}
          placeholder="Capture decisions, follow-ups, or blocking issues"
          rows={6}
        />
      </div>
    </section>
  )
}

interface ToggleGroupProps<T extends string> {
  value: T
  onChange: (value: T) => void
  options: readonly { value: T; label: string }[]
}

function ToggleGroup<T extends string>({ value, onChange, options }: ToggleGroupProps<T>) {
  return (
    <div className="toggle-group" role="radiogroup">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          role="radio"
          aria-checked={value === option.value}
          className={value === option.value ? 'toggle-group__button active' : 'toggle-group__button'}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}
