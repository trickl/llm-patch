export interface CaseRerunResponse {
  caseId: string
  command: string[]
  pythonExecutable: string
  exitCode: number | null
  stdout: string
  stderr: string
  startedAt: string
  finishedAt: string
  durationMs: number
  success: boolean
  datasetReloaded: boolean
}
