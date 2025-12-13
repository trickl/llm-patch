export interface CompilerDiagnostic {
  line: number
  column: number
  message: string
  severity: 'error' | 'warning' | 'info'
}

type DiagnosticParser = (stderr: string) => CompilerDiagnostic[]

export function parseDiagnostics(stderr: string, language: string): CompilerDiagnostic[] {
  if (!stderr) {
    return []
  }
  const normalizedLang = language.toLowerCase()
  const parser = languageParsers[normalizedLang] ?? parseGeneric
  const diagnostics = parser(stderr)
  if (diagnostics.length) {
    return diagnostics.slice(0, 200)
  }
  return parseGeneric(stderr).slice(0, 200)
}

const languageParsers: Record<string, DiagnosticParser> = {
  python: parsePython,
  javascript: parseJsTs,
  typescript: parseJsTs,
  ts: parseJsTs,
  java: parseGeneric,
  c: parseGeneric,
  cpp: parseGeneric,
  cplusplus: parseGeneric,
}

function parseGeneric(stderr: string): CompilerDiagnostic[] {
  const diagnostics: CompilerDiagnostic[] = []
  const pattern = /^(?<file>[^:\n]+?):(?<line>\d+)(?::(?<column>\d+))?:\s*(?<rest>.+)$/
  for (const rawLine of stderr.split(/\r?\n/)) {
    const line = rawLine.trim()
    if (!line) continue
    const match = line.match(pattern)
    if (!match || !match.groups) continue
    const column = match.groups.column ? Number.parseInt(match.groups.column, 10) : 1
    diagnostics.push({
      line: Number.parseInt(match.groups.line, 10) || 1,
      column: column || 1,
      message: match.groups.rest.trim(),
      severity: inferSeverity(match.groups.rest),
    })
    if (diagnostics.length >= 200) break
  }
  return diagnostics
}

function parseJsTs(stderr: string): CompilerDiagnostic[] {
  const diagnostics: CompilerDiagnostic[] = []
  const pattern = /^(?<file>.+?)\((?<line>\d+),(?<column>\d+)\):\s*(?<severity>error|warning)?\s*(?<code>TS\d+)?\s*:?\s*(?<message>.+)$/i
  for (const rawLine of stderr.split(/\r?\n/)) {
    const line = rawLine.trim()
    if (!line) continue
    const match = line.match(pattern)
    if (!match || !match.groups) continue
    diagnostics.push({
      line: Number.parseInt(match.groups.line, 10) || 1,
      column: Number.parseInt(match.groups.column, 10) || 1,
      message: buildTsMessage(match.groups),
      severity: match.groups.severity?.toLowerCase() === 'warning' ? 'warning' : 'error',
    })
    if (diagnostics.length >= 200) break
  }
  return diagnostics
}

function buildTsMessage(groups: Record<string, string | undefined>): string {
  const parts = []
  if (groups.code) parts.push(groups.code)
  if (groups.message) parts.push(groups.message.trim())
  return parts.join(': ')
}

function parsePython(stderr: string): CompilerDiagnostic[] {
  const diagnostics: CompilerDiagnostic[] = []
  const lines = stderr.split(/\r?\n/)
  let pendingMessage: string | null = null
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const match = line.match(/File "(?<file>.+?)", line (?<line>\d+)/)
    if (match && match.groups) {
      const message = collectPythonMessage(lines, i + 1)
      diagnostics.push({
        line: Number.parseInt(match.groups.line, 10) || 1,
        column: 1,
        message: message ?? line.trim(),
        severity: 'error',
      })
    }
    if (line.trim() && !line.trim().startsWith('File ')) {
      pendingMessage = line.trim()
    }
  }
  if (diagnostics.length === 0 && pendingMessage) {
    diagnostics.push({ line: 1, column: 1, message: pendingMessage, severity: 'error' })
  }
  return diagnostics
}

function collectPythonMessage(lines: string[], startIndex: number): string | null {
  for (let j = startIndex; j < lines.length; j++) {
    const candidate = lines[j].trim()
    if (!candidate) continue
    if (candidate.startsWith('File ')) break
    return candidate
  }
  const tail = lines[lines.length - 1]?.trim()
  return tail || null
}

function inferSeverity(message: string): CompilerDiagnostic['severity'] {
  if (/warning/i.test(message)) return 'warning'
  if (/note/i.test(message)) return 'info'
  return 'error'
}
