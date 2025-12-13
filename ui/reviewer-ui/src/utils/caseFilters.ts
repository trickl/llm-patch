import type { CaseSummary } from '../types'

export type CaseStatusFilter = 'success' | 'applied_failed' | 'not_applied'

export const CASE_STATUS_OPTIONS: { value: CaseStatusFilter; label: string }[] = [
  { value: 'success', label: 'Success' },
  { value: 'applied_failed', label: 'Applied Only' },
  { value: 'not_applied', label: 'Not Applied' },
]

export function deriveCaseStatus(summary: CaseSummary): CaseStatusFilter {
  if (summary.success) {
    return 'success'
  }
  if (summary.patchApplied) {
    return 'applied_failed'
  }
  return 'not_applied'
}
