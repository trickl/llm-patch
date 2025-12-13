import { access, readFile } from 'node:fs/promises'
import path from 'node:path'
import fg from 'fast-glob'
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

        const summary: PatchSummaryPublic = {
          id: patchId,
          caseId: manifest.case_id,
          runId,
          language: manifest.language,
          problemId: manifest.problem_id,
          modelSlug: result.model_slug,
          algorithm: result.algorithm,
          diffName,
          filePath: manifest.compile_command?.at(-1) ?? 'unknown',
          patchApplied: Boolean(result.patch_applied),
          success: Boolean(result.success),
          errorsBefore: coerceNumber(result.errors_before),
          errorsAfter: coerceNumber(result.errors_after),
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
    let after = before
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
        stderr,
        stdout,
      },
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

async function resolveBeforeFile(baseDir: string): Promise<string | null> {
  const matches = await fg('before.*', { cwd: baseDir, absolute: true, onlyFiles: true })
  return matches[0] ?? null
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
