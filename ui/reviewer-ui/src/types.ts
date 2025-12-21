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
  firstErrorCategory: number | null
  firstErrorMessage: string | null
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
  strategyTrace?: StrategyTrace | null
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

export interface StrategyTrace {
  strategy: string
  targetLanguage?: string
  caseId?: string
  buildCommand?: string
  iterations: StrategyIteration[]
  notes?: string | null
}

export interface Hypothesis {
  id: string
  claim: string
  affectedRegion: string
  expectedEffect: string
  interpretation?: string | null
  explanation?: string | null
  structuralChange?: string | null
  confidence?: number | null
  status: string
  retryCount?: number
  falsificationNotes?: string[]
}

export interface HypothesisBuckets {
  active?: Hypothesis[]
  falsified?: Hypothesis[]
  rejected?: Hypothesis[]
  archived?: Hypothesis[]
  expired?: Hypothesis[]
  [bucket: string]: Hypothesis[] | undefined
}

export interface StallTelemetryEntry {
  hypothesisId?: string
  errorMessage?: string
  errorLocation?: number | null
  diffSpan?: [number, number] | number[]
}

export interface FalsificationTelemetryEntry {
  hypothesisId: string
  observed: string[]
  pending: string[]
  summary?: string | null
  status?: string
  remaining?: number
  auto?: Record<string, unknown>
}

export interface RetryTelemetryEntry {
  hypothesisId: string
  retryCount: number
  reason?: string | null
}

export interface HypothesisStatusEntry {
  id: string
  status: string
  reason?: string | null
}

export interface UnchangedErrorEntry {
  hypothesisId?: string
  previous: string | null
  current: string | null
}

export interface HypothesisCreatedEntry {
  ids: string[]
  count: number
}

export interface IterationTelemetry {
  stall?: StallTelemetryEntry[]
  falsification?: FalsificationTelemetryEntry[]
  retries?: RetryTelemetryEntry[]
  hypothesisStatuses?: HypothesisStatusEntry[]
  unchangedError?: UnchangedErrorEntry[]
  hypothesesCreated?: HypothesisCreatedEntry[]
  [key: string]: unknown
}

export interface StrategyIteration {
  index: number
  phases: StrategyPhaseArtifact[]
  accepted: boolean
  failureReason?: string | null
  kind?: 'primary' | 'refine'
  label?: string | null
  historyContext?: string | null
  historyEntry?: string | null
  hypotheses?: HypothesisBuckets | null
  selectedHypothesisId?: string | null
  telemetry?: IterationTelemetry | null
}

export type StrategyPhaseStatus = 'planned' | 'running' | 'completed' | 'failed'

export interface StrategyPhaseArtifact {
  phase: string
  status: StrategyPhaseStatus
  prompt: string
  response?: string | null
  machineChecks?: Record<string, unknown>
  humanNotes?: string | null
  metrics?: Record<string, number>
  startedAt?: string | null
  completedAt?: string | null
}

export type { CaseRerunResponse } from './shared/apiTypes'
