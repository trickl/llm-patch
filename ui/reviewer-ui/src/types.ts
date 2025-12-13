export type QualityFlag = 'good' | 'poor'
export type FinalOutcome = 'good' | 'bad' | 'pending'

export interface CaseMetrics {
  sourceQuality: QualityFlag
  diffQuality: QualityFlag
  finalOutcome: FinalOutcome
}

export interface CaseSummary {
  id: string
  caseId: string
  runId: string
  language: string
  problemId: string
  modelSlug: string
  algorithm: string
  diffName: string
  filePath: string
  patchApplied: boolean
  success: boolean
  errorsBefore: number | null
  errorsAfter: number | null
  patchDiagnostics: string | null
}

export interface CaseDetail {
  summary: CaseSummary
  before: string
  after: string
  diff: string
  diffPath: string
  derived: {
    afterSource: 'dataset' | 'missing'
  }
  metadata: {
    manifest: Record<string, unknown>
    result: Record<string, unknown>
  }
  errors: {
    stderr: string
    stdout: string
  }
}

export interface AnnotationState extends CaseMetrics {
  notes: string
  updatedAt: string | null
  updatedBy: string | null
}

export const defaultAnnotation: AnnotationState = {
  sourceQuality: 'good',
  diffQuality: 'good',
  finalOutcome: 'pending',
  notes: '',
  updatedAt: null,
  updatedBy: null,
}
