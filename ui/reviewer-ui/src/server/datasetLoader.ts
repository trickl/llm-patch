import { spawn } from 'node:child_process'
import { access, readFile } from 'node:fs/promises'
import { createHash } from 'node:crypto'
import path from 'node:path'
import fg from 'fast-glob'
import type { CaseRerunResponse } from '../shared/apiTypes'
import type {
  ManifestRecord,
  PatchDetailResponse,
  PatchSummaryPublic,
  ResultRecord,
} from './datasetTypes'

const DEFAULT_DATASET_ROOT = process.env.REVIEWER_DATASET_ROOT
  ? path.resolve(process.env.REVIEWER_DATASET_ROOT)
  : path.resolve(process.cwd(), '..', '..', 'benchmarks', 'generated')

interface PatchRecordInternal {
  summary: PatchSummaryPublic
  manifest: ManifestRecord
  result: ResultRecord
  paths: {
    baseDir: string
    before: string
    after: string | null
    diff: string
    resultFile: string
    stderr: string
    stdout: string
  }
}

interface RerunOptions {
  pythonExecutable?: string
  extraArgs?: string[]
}

export class DatasetLoader {
  private isLoaded = false
  private readonly summaries: PatchRecordInternal[] = []
  private readonly datasetRoot: string

  constructor(datasetRoot: string = DEFAULT_DATASET_ROOT) {
    this.datasetRoot = datasetRoot
  }

  async ensureLoaded() {
    if (this.isLoaded) {
      return
    }
    await this.refresh()
  }

  async refresh() {
    this.summaries.length = 0
    try {
      await access(this.datasetRoot)
    } catch (error) {
      console.warn('Dataset root not accessible', this.datasetRoot, error)
      this.isLoaded = true
      return
    }
    const manifestPaths = await fg('**/manifest.json', {
      cwd: this.datasetRoot,
      absolute: true,
    })

    for (const manifestPath of manifestPaths) {
      const manifestRaw = await readFile(manifestPath, 'utf8').catch(() => null)
      if (!manifestRaw) continue
      const manifest = safeParseJSON<ManifestRecord>(manifestRaw)
      if (!manifest) continue

      const baseDir = path.dirname(manifestPath)
      const runId = getRunId(this.datasetRoot, baseDir)
      const beforePath = await resolveBeforeFile(baseDir)
      if (!beforePath) continue
      const fingerprint = await computeFingerprint(runId, manifest.case_id, beforePath)

      const stderrPath = path.join(baseDir, 'compiler_stderr.txt')
      const stdoutPath = path.join(baseDir, 'compiler_stdout.txt')
      const resultFiles = await fg('results/*.json', {
        cwd: baseDir,
        absolute: true,
      })

      for (const resultFile of resultFiles) {
        const resultRaw = await readFile(resultFile, 'utf8').catch(() => null)
        if (!resultRaw) continue
        const result = safeParseJSON<ResultRecord>(resultRaw)
        if (!result?.diff_path) continue
        const diffPath = path.resolve(baseDir, result.diff_path)
        const diffName = path.basename(result.diff_path)

        const patchId = [runId, result.case_id, result.model_slug, result.algorithm, diffName]
          .filter(Boolean)
          .join('::')

        const patchApplied = Boolean(result.patch_applied)
        const errorsBefore = coerceNumber(result.errors_before)
        const errorsAfter = coerceNumber(result.errors_after)
        const compileReturncode = typeof result.compile_returncode === 'number' ? result.compile_returncode : null

        const firstErrorCategory = coerceNumber((manifest as Record<string, unknown>)['first_error_category'])
        const firstErrorMessage =
          typeof (manifest as Record<string, unknown>)['first_error_message'] === 'string'
            ? String((manifest as Record<string, unknown>)['first_error_message'])
            : null
        const summary: PatchSummaryPublic = {
          id: patchId,
          caseId: manifest.case_id,
          runId,
          fingerprint,
          language: manifest.language,
          problemId: manifest.problem_id,
          modelSlug: result.model_slug,
          algorithm: result.algorithm,
          diffName,
          filePath: manifest.compile_command?.at(-1) ?? 'unknown',
          firstErrorCategory,
          firstErrorMessage,
          patchApplied,
          success: normalizeSuccess(Boolean(result.success), patchApplied, compileReturncode),
          errorsBefore,
          errorsAfter,
          patchDiagnostics: result.patch_diagnostics ?? null,
        }

        const afterPath = typeof result.after_path === 'string' ? path.resolve(baseDir, result.after_path) : null

        this.summaries.push({
          summary,
          manifest,
          result,
          paths: {
            baseDir,
            before: beforePath,
            after: afterPath,
            diff: diffPath,
            resultFile,
            stderr: stderrPath,
            stdout: stdoutPath,
          },
        })
      }
    }

    this.isLoaded = true
  }

  async rerunCase(caseId: string, options: RerunOptions = {}): Promise<CaseRerunResponse> {
    await this.ensureLoaded()
    const record = this.summaries.find((entry) => entry.summary.caseId === caseId)
    if (!record) {
      throw new Error(`Case ${caseId} is not loaded; refresh the dataset and try again.`)
    }

    const repoRoot = path.resolve(this.datasetRoot, '..', '..')
    const pythonExecutable =
      options.pythonExecutable ??
      process.env.REVIEWER_PYTHON_BIN ??
      process.env.REVIEWER_PYTHON ??
      process.env.PYTHON ??
      'python3'
    const scriptPath = path.resolve(repoRoot, 'scripts', 'run_guided_loop.py')
    const args = [scriptPath, record.summary.caseId, '--dataset-root', this.datasetRoot]
    const modelOverride = process.env.REVIEWER_GUIDED_LOOP_MODEL
    if (modelOverride) {
      args.push('--model', modelOverride)
    }
    if (Array.isArray(options.extraArgs) && options.extraArgs.length) {
      args.push(...options.extraArgs)
    }

    const startedAt = new Date()
    const runResult = await runCommand(pythonExecutable, args, repoRoot)
    const finishedAt = new Date()

    let datasetReloaded = true
    try {
      await this.refresh()
    } catch (error) {
      datasetReloaded = false
      console.warn('Failed to refresh dataset after rerun', error)
    }

    return {
      caseId,
      command: [pythonExecutable, ...args],
      pythonExecutable,
      exitCode: runResult.exitCode,
      stdout: runResult.stdout,
      stderr: runResult.stderr,
      startedAt: startedAt.toISOString(),
      finishedAt: finishedAt.toISOString(),
      durationMs: finishedAt.getTime() - startedAt.getTime(),
      success: runResult.exitCode === 0,
      datasetReloaded,
    }
  }

  listSummaries(): PatchSummaryPublic[] {
    return this.summaries.map((record) => record.summary)
  }

  getRecord(id: string): PatchRecordInternal | undefined {
    return this.summaries.find((record) => record.summary.id === id)
  }

  async getDetail(id: string): Promise<PatchDetailResponse | null> {
    await this.ensureLoaded()
    const record = this.getRecord(id)
    if (!record) return null

    const afterPromise = record.paths.after
      ? readFile(record.paths.after, 'utf8').catch(() => null)
      : Promise.resolve(null)

    const [before, afterRaw, diff, stderr, stdout] = await Promise.all([
      readFile(record.paths.before, 'utf8').catch(() => ''),
      afterPromise,
      readFile(record.paths.diff, 'utf8').catch(() => ''),
      readFile(record.paths.stderr, 'utf8').catch(() => ''),
      readFile(record.paths.stdout, 'utf8').catch(() => ''),
    ])

    let afterSource: 'dataset' | 'missing' = 'missing'
    let after = ''
    if (afterRaw !== null) {
      after = afterRaw
      afterSource = 'dataset'
    }

    return {
      summary: record.summary,
      before,
      after,
      diff,
      diffPath: path.relative(this.datasetRoot, record.paths.diff),
      derived: { afterSource },
      metadata: {
        manifest: record.manifest,
        result: record.result,
      },
      errors: {
        before: {
          stderr,
          stdout,
        },
        after: {
          stderr: typeof record.result.stderr_after === 'string' ? record.result.stderr_after : '',
          stdout: typeof record.result.stdout_after === 'string' ? record.result.stdout_after : '',
        },
      },
      strategyTrace: (record.result.strategy_trace ?? null) as PatchDetailResponse['strategyTrace'],
    }
  }
}

function safeParseJSON<T>(raw: string): T | null {
  try {
    return JSON.parse(raw) as T
  } catch (error) {
    console.warn('Failed to parse JSON', error)
    return null
  }
}

function normalizeSuccess(
  successFlag: boolean,
  patchApplied: boolean,
  compileReturncode: number | null,
): boolean {
  if (!patchApplied) return false
  if (!successFlag) return false
  if (compileReturncode !== null && compileReturncode !== 0) return false
  return true
}

async function resolveBeforeFile(baseDir: string): Promise<string | null> {
  const matches = await fg('before.*', { cwd: baseDir, absolute: true, onlyFiles: true })
  return matches[0] ?? null
}

async function computeFingerprint(runId: string, caseId: string, filePath: string): Promise<string> {
  const contents = await readFile(filePath, 'utf8').catch(() => '')
  const hash = createHash('sha256')
  hash.update(runId)
  hash.update(':')
  hash.update(caseId)
  hash.update(':')
  hash.update(contents)
  return hash.digest('hex').slice(0, 12)
}

function coerceNumber(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string') {
    const parsed = Number.parseFloat(value)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

function getRunId(datasetRoot: string, baseDir: string): string {
  const relative = path.relative(datasetRoot, baseDir)
  return relative.split(path.sep)[0] ?? 'unknown-run'
}

function runCommand(
  command: string,
  args: string[],
  cwd: string,
): Promise<{ exitCode: number | null; stdout: string; stderr: string }> {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd,
      env: process.env,
      stdio: ['ignore', 'pipe', 'pipe'],
    })

    let stdout = ''
    let stderr = ''
    child.stdout?.on('data', (chunk) => {
      stdout += chunk.toString()
    })
    child.stderr?.on('data', (chunk) => {
      stderr += chunk.toString()
    })
    child.on('error', (error) => {
      reject(error)
    })
    child.on('close', (code) => {
      resolve({ exitCode: code, stdout, stderr })
    })
  })
}
