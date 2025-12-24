import type { IncomingMessage, ServerResponse } from 'node:http'

export interface ManifestRecord {
  case_id: string
  language: string
  problem_id: string
  model?: string
  provider?: string
  compile_command?: string[]
  [key: string]: unknown
}

export interface ResultRecord {
  case_id: string
  language: string
  model_slug: string
  algorithm: string
  diff_path: string
  after_path?: string | null
  patch_applied: boolean
  patch_diagnostics?: string
  compile_returncode?: number
  errors_before?: number
  errors_after?: number
  first_error_removed?: boolean
  added_lines?: number
  removed_lines?: number
  hunks?: number
  delete_only?: boolean
  success?: boolean
  notes?: string
  stderr_after?: string
  stdout_after?: string
  strategy_trace?: StrategyTrace | null
  [key: string]: unknown
}

export interface PatchSummaryPublic {
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

export interface PatchDetailResponse {
  summary: PatchSummaryPublic
  before: string
  after: string
  diff: string
  diffPath: string
  derived: {
    afterSource: 'dataset' | 'missing'
  }
  metadata: {
    manifest: ManifestRecord
    result: ResultRecord
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

export interface StrategyTrace {
  strategy: string
  targetLanguage?: string | null
  caseId?: string | null
  buildCommand?: string | null
  iterations: StrategyIteration[]
  notes?: string | null
}

export interface StrategyIteration {
  index: number
  phases: StrategyPhaseArtifact[]
  accepted: boolean
  failureReason?: string | null
  kind?: 'primary' | 'refine'
  label?: string | null

  // Optional per-iteration outputs (if recorded by the guided loop runner).
  patchApplied?: boolean | null
  patchedText?: string | null
  diffText?: string | null
  patchDiagnostics?: string | null
  compileReturncode?: number | null
  compileStdout?: string | null
  compileStderr?: string | null
}

export interface StrategyPhaseArtifact {
  phase: string
  status: 'planned' | 'running' | 'completed' | 'failed'
  prompt: string
  response?: string | null
  machineChecks?: Record<string, unknown>
  humanNotes?: string | null
  metrics?: Record<string, number>
  startedAt?: string | null
  completedAt?: string | null
}

export type ApiHandler = (req: IncomingMessage, res: ServerResponse) => void
