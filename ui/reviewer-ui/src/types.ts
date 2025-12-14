export type QualityFlag = 'good' | 'poor'
export type FinalOutcome = 'good' | 'bad' | 'pending'

export interface CaseMetrics {
  sourceQuality: QualityFlag | null
  diffQuality: QualityFlag | null
  finalOutcome: FinalOutcome
}

export interface CaseSummary {
  id: string
  caseId: string
  runId: string
  fingerprint: string
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
    before: {
      stderr: string
      stdout: string
    }
    after: {
      stderr: string
      stdout: string
    }
  }
}

export interface AnnotationState extends CaseMetrics {
  updatedAt: string | null
  updatedBy: string | null
}

export const defaultAnnotation: AnnotationState = {
  sourceQuality: null,
  diffQuality: null,
  finalOutcome: 'pending',
  updatedAt: null,
  updatedBy: null,
}
