import { useCallback, useEffect, useMemo, useRef, useState, type MutableRefObject, type ReactNode } from 'react'
import clsx from 'clsx'
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels'
import { Editor } from '@monaco-editor/react'
import type { editor as MonacoEditor } from 'monaco-editor'
import type { AnnotationState, CaseDetail, FinalOutcome, QualityFlag } from '../types'
import { useReviewStore } from '../store/useReviewStore'
import { parseDiagnostics, type CompilerDiagnostic } from '../utils/diagnostics'

type MonacoApi = typeof import('monaco-editor')

interface CaseWorkspaceProps {
  detail: CaseDetail
  annotation: AnnotationState
}

const languageMap: Record<string, string> = {
  javascript: 'javascript',
  typescript: 'typescript',
  python: 'python',
  java: 'java',
  c: 'c',
  cpp: 'cpp',
}

export function CaseWorkspace({ detail, annotation }: CaseWorkspaceProps) {
  const [activeDockTab, setActiveDockTab] = useState<'diff' | 'errors'>('diff')
  const updateMetrics = useReviewStore((state) => state.updateMetrics)
  const [beforeEditor, setBeforeEditor] = useState<MonacoEditor.IStandaloneCodeEditor | null>(null)
  const [afterEditor, setAfterEditor] = useState<MonacoEditor.IStandaloneCodeEditor | null>(null)
  const scrollSyncGuard = useRef(false)
  const monacoLanguage = useMemo(() => {
    const normalized = detail.summary.language.toLowerCase()
    return languageMap[normalized] ?? 'plaintext'
  }, [detail.summary.language])

  const modelPaths = useMemo(() => {
    const baseId = detail.summary.id
    return {
      before: `case://${baseId}/before`,
      after: `case://${baseId}/after`,
    }
  }, [detail.summary.id])

  const diagnosticsBefore = useMemo(
    () => parseDiagnostics(detail.errors.before.stderr, detail.summary.language),
    [detail.errors.before.stderr, detail.summary.language],
  )
  const diagnosticsAfter = useMemo(
    () => parseDiagnostics(detail.errors.after.stderr, detail.summary.language),
    [detail.errors.after.stderr, detail.summary.language],
  )
  const patchFailed = !detail.summary.patchApplied
  const afterMissing = detail.derived.afterSource === 'missing'
  const afterUnavailable = patchFailed || afterMissing
  const afterPlaceholder = afterUnavailable ? (patchFailed ? 'Patch failed' : 'Not available') : undefined
  const afterValue = afterUnavailable ? '' : detail.after
  const diffLineCount = detail.diff.split('\n').length
  const stderrLineCount = countNonEmptyLines(detail.errors.before.stderr)
  const hasAfterFile = !afterUnavailable

  const handleSourceReview = useCallback(
    (value: QualityFlag | null) => {
      updateMetrics(detail.summary.id, { sourceQuality: value ?? null })
    },
    [detail.summary.id, updateMetrics],
  )

  const handleDiffReview = useCallback(
    (value: QualityFlag | null) => {
      updateMetrics(detail.summary.id, { diffQuality: value ?? null })
    },
    [detail.summary.id, updateMetrics],
  )

  const handleFinalOutcome = useCallback(
    (value: FinalOutcome) => {
      updateMetrics(detail.summary.id, { finalOutcome: value })
    },
    [detail.summary.id, updateMetrics],
  )

  const handleBeforeMount = useCallback((editor: MonacoEditor.IStandaloneCodeEditor) => {
    setBeforeEditor(editor)
    editor.onDidDispose(() => {
      setBeforeEditor((current) => (current === editor ? null : current))
    })
  }, [])

  const handleAfterMount = useCallback((editor: MonacoEditor.IStandaloneCodeEditor) => {
    setAfterEditor(editor)
    editor.onDidDispose(() => {
      setAfterEditor((current) => (current === editor ? null : current))
    })
  }, [])

  useEffect(() => {
    if (!beforeEditor || !afterEditor) return
    const sync = (source: MonacoEditor.IStandaloneCodeEditor, target: MonacoEditor.IStandaloneCodeEditor) => () => {
      if (scrollSyncGuard.current) return
      scrollSyncGuard.current = true
      target.setScrollPosition({
        scrollLeft: source.getScrollLeft(),
        scrollTop: source.getScrollTop(),
      })
      scrollSyncGuard.current = false
    }
    const beforeListener = beforeEditor.onDidScrollChange(sync(beforeEditor, afterEditor))
    const afterListener = afterEditor.onDidScrollChange(sync(afterEditor, beforeEditor))
    return () => {
      beforeListener.dispose()
      afterListener.dispose()
    }
  }, [beforeEditor, afterEditor])

  return (
    <section className="workspace" aria-live="polite">
      <header className="workspace__header">
        <div>
          <p className="workspace__eyebrow">{detail.summary.problemId}</p>
          <h1>{detail.summary.filePath}</h1>
        </div>
        <div className="workspace__meta">
          <span>Case #{detail.summary.caseId}</span>
          <span>Fingerprint {detail.summary.fingerprint}</span>
          <span className="workspace__language">{detail.summary.language}</span>
          <span>{detail.summary.modelSlug}</span>
          <span>{detail.summary.algorithm}</span>
        </div>
      </header>
      <PanelGroup className="workspace__panels" direction="vertical">
        <Panel minSize={40} defaultSize={65} order={1}>
          <PanelGroup direction="horizontal">
            <Panel minSize={30} defaultSize={50}>
              <EditorSection
                key={modelPaths.before}
                title="Before"
                language={monacoLanguage}
                value={detail.before}
                modelPath={modelPaths.before}
                diagnostics={diagnosticsBefore}
                onEditorMount={handleBeforeMount}
                headerActions={
                  <QualityReviewButtons
                    value={annotation.sourceQuality}
                    onChange={handleSourceReview}
                    ariaLabel="Review source quality"
                  />
                }
              />
            </Panel>
            <PanelResizeHandle className="resize-handle vertical" />
            <Panel minSize={30} defaultSize={50}>
              <EditorSection
                key={modelPaths.after}
                title="After"
                language={monacoLanguage}
                value={afterValue}
                modelPath={modelPaths.after}
                diagnostics={diagnosticsAfter}
                placeholder={afterPlaceholder}
                onEditorMount={handleAfterMount}
                headerActions={
                  hasAfterFile ? (
                    <FinalOutcomeButtons
                      value={annotation.finalOutcome}
                      onChange={handleFinalOutcome}
                      ariaLabel="Final application review"
                    />
                  ) : undefined
                }
              />
            </Panel>
          </PanelGroup>
        </Panel>
        <PanelResizeHandle className="resize-handle horizontal" />
        <Panel minSize={25} defaultSize={35} order={2}>
          <section className="dock-panel">
            <div className="dock-panel__header">
              <div className="dock-panel__header-left">
                <div>
                  <h3>{activeDockTab === 'diff' ? 'Unified Diff' : 'Compiler Errors'}</h3>
                  <p>
                    {activeDockTab === 'diff'
                      ? `${diffLineCount} lines · ${detail.summary.diffName}`
                      : `${stderrLineCount} stderr lines`}
                  </p>
                </div>
                {activeDockTab === 'diff' && detail.derived.afterSource === 'missing' && (
                  <span className="dock-panel__warning">After file unavailable; showing original</span>
                )}
              </div>
              <div className="dock-panel__header-right">
                {activeDockTab === 'diff' && (
                  <QualityReviewButtons
                    value={annotation.diffQuality}
                    onChange={handleDiffReview}
                    ariaLabel="Review diff quality"
                    size="sm"
                  />
                )}
                <div className="dock-panel__tabs" role="tablist" aria-label="Diff and errors toggle">
                  <button
                    type="button"
                    role="tab"
                    aria-selected={activeDockTab === 'diff'}
                    className={activeDockTab === 'diff' ? 'dock-panel__tab dock-panel__tab--active' : 'dock-panel__tab'}
                    onClick={() => setActiveDockTab('diff')}
                  >
                    Diff
                  </button>
                  <button
                    type="button"
                    role="tab"
                    aria-selected={activeDockTab === 'errors'}
                    className={activeDockTab === 'errors' ? 'dock-panel__tab dock-panel__tab--active' : 'dock-panel__tab'}
                    onClick={() => setActiveDockTab('errors')}
                  >
                    Errors
                  </button>
                </div>
              </div>
            </div>
            <div className="dock-panel__content">
              {activeDockTab === 'diff' ? (
                <pre className="diff-view" aria-label="Unified diff patch">
                  {detail.diff || 'No diff available.'}
                </pre>
              ) : (
                <ErrorsPanel before={detail.errors.before} after={detail.errors.after} />
              )}
            </div>
          </section>
        </Panel>
      </PanelGroup>
    </section>
  )
}

interface EditorSectionProps {
  title: string
  value: string
  language: string
  modelPath: string
  diagnostics: CompilerDiagnostic[]
  placeholder?: string
  onEditorMount?: (editor: MonacoEditor.IStandaloneCodeEditor) => void
  headerActions?: ReactNode
}

type EditorDisposable = ReturnType<MonacoEditor.IStandaloneCodeEditor['onDidScrollChange']>

interface ErrorBlob {
  stderr: string
  stdout: string
}

function ErrorsPanel({ before, after }: { before: ErrorBlob; after: ErrorBlob }) {
  const hasAfter = Boolean(after.stderr.trim().length || after.stdout.trim().length)
  const [view, setView] = useState<'before' | 'after'>(hasAfter ? 'after' : 'before')

  useEffect(() => {
    setView((current) => {
      if (!hasAfter && current === 'after') {
        return 'before'
      }
      return current
    })
  }, [hasAfter])

  const active = view === 'before' ? before : after
  const stdoutLabel = view === 'before' ? 'compiler stdout (before)' : 'compiler stdout (after)'

  return (
    <div className="errors-view">
      <div className="errors-view__mode-toggle" role="tablist" aria-label="Select error output">
        <button
          type="button"
          role="tab"
          aria-selected={view === 'before'}
          className={clsx('errors-view__mode-button', view === 'before' && 'is-active')}
          onClick={() => setView('before')}
        >
          Before errors
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={view === 'after'}
          className={clsx('errors-view__mode-button', view === 'after' && 'is-active')}
          onClick={() => setView('after')}
          disabled={!hasAfter}
        >
          After errors
        </button>
      </div>
      <pre className="errors-view__body">{active.stderr || 'No stderr captured.'}</pre>
      {active.stdout && (
        <details className="errors-view__stdout" open={view === 'after' && hasAfter}>
          <summary>{stdoutLabel}</summary>
          <pre>{active.stdout}</pre>
        </details>
      )}
    </div>
  )
}

function EditorSection({ title, value, language, modelPath, diagnostics, placeholder, onEditorMount, headerActions }: EditorSectionProps) {
  const modelRef = useRef<MonacoEditor.ITextModel | null>(null)
  const monacoRef = useRef<MonacoApi | null>(null)
  const editorRef = useRef<MonacoEditor.IStandaloneCodeEditor | null>(null)
  const decorationsRef = useRef<string[]>([])
  const badgeListenersRef = useRef<EditorDisposable[]>([])
  const lineLeaderRef = useRef<CompilerDiagnostic[]>([])
  const [badgePositions, setBadgePositions] = useState<InlineBadgePosition[]>([])

  useEffect(() => {
    if (!modelRef.current || !monacoRef.current) return
    syncDiagnostics(monacoRef.current, modelRef.current, editorRef.current, decorationsRef, diagnostics)
  }, [diagnostics])

  useEffect(() => () => {
    if (modelRef.current && monacoRef.current) {
      monacoRef.current.editor.setModelMarkers(modelRef.current, 'compiler', [])
    }
    if (editorRef.current && decorationsRef.current.length) {
      editorRef.current.deltaDecorations(decorationsRef.current, [])
    }
    decorationsRef.current = []
    disposeBadgeListeners(badgeListenersRef)
    editorRef.current = null
    setBadgePositions([])
  }, [])

  const updateBadgePositions = useCallback(() => {
    const editor = editorRef.current
    if (!editor) {
      setBadgePositions([])
      return
    }
    const editorDomNode = editor.getDomNode()
    const parent = editorDomNode?.parentElement
    if (!editorDomNode || !parent) {
      setBadgePositions([])
      return
    }
    const parentRect = parent.getBoundingClientRect()
    const editorRect = editorDomNode.getBoundingClientRect()
    const offsetTop = editorRect.top - parentRect.top
    const offsetLeft = editorRect.left - parentRect.left
    const leaders = lineLeaderRef.current
    const badges: InlineBadgePosition[] = []
    for (let index = 0; index < leaders.length; index += 1) {
      const diag = leaders[index]
      const visible = editor.getScrolledVisiblePosition({
        lineNumber: Math.max(1, diag.line),
        column: Math.max(1, diag.column),
      })
      if (!visible) continue
      badges.push({
        id: `${diag.line}-${diag.column}-${index}`,
        severity: diag.severity,
        message: diag.message,
        top: visible.top + offsetTop - 6,
        left: visible.left + offsetLeft + 8,
      })
    }
    setBadgePositions(badges)
  }, [])

  useEffect(() => {
    lineLeaderRef.current = selectLineLeaders(diagnostics)
    updateBadgePositions()
  }, [diagnostics, updateBadgePositions])


  return (
    <section className="editor-pane">
      <header className="editor-pane__header">
        <h3>{title}</h3>
        {headerActions && <div className="editor-pane__header-actions">{headerActions}</div>}
      </header>
      <div className="editor-pane__body">
        <Editor
          language={language}
          value={value}
          path={modelPath}
          keepCurrentModel
          theme="vs-dark"
          options={{
            readOnly: true,
            domReadOnly: true,
            minimap: { enabled: false },
            renderLineHighlight: 'all',
            fontSize: 14,
            scrollBeyondLastLine: false,
            smoothScrolling: true,
            renderWhitespace: 'selection',
            renderValidationDecorations: 'on',
            glyphMargin: true,
          }}
          height="100%"
          onMount={(editorInstance, monaco) => {
            modelRef.current = editorInstance.getModel()
            monacoRef.current = monaco
            editorRef.current = editorInstance
            if (modelRef.current) {
              syncDiagnostics(monaco, modelRef.current, editorRef.current, decorationsRef, diagnostics)
            }
            disposeBadgeListeners(badgeListenersRef)
            badgeListenersRef.current = [
              editorInstance.onDidScrollChange(() => updateBadgePositions()),
              editorInstance.onDidLayoutChange(() => updateBadgePositions()),
              editorInstance.onDidContentSizeChange(() => updateBadgePositions()),
            ]
            updateBadgePositions()
            editorInstance.onDidDispose(() => {
              if (decorationsRef.current.length) {
                editorInstance.deltaDecorations(decorationsRef.current, [])
                decorationsRef.current = []
              }
              disposeBadgeListeners(badgeListenersRef)
              editorRef.current = null
              modelRef.current = null
              setBadgePositions([])
            })
            onEditorMount?.(editorInstance)
          }}
        />
        {placeholder && <div className="editor-pane__placeholder">{placeholder}</div>}
        <div className="diagnostic-badge-layer" aria-hidden="true">
          {badgePositions.map((badge) => (
            <div
              key={badge.id}
              className={clsx('diagnostic-inline-badge', `diagnostic-inline-badge--${badge.severity}`)}
              style={{ top: `${badge.top}px`, left: `${badge.left}px` }}
            >
              <span className="diagnostic-inline-badge__icon">{severityIcon(badge.severity)}</span>
              <span className="diagnostic-inline-badge__text">{truncateMessage(badge.message, 90)}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

interface QualityReviewButtonsProps {
  value: QualityFlag | null
  onChange: (value: QualityFlag | null) => void
  ariaLabel: string
  size?: 'sm' | 'md'
}

function QualityReviewButtons({ value, onChange, ariaLabel, size = 'md' }: QualityReviewButtonsProps) {
  return (
    <div className={clsx('review-toggle', size === 'sm' && 'review-toggle--sm')} role="group" aria-label={ariaLabel}>
      {QUALITY_OPTIONS.map((option) => {
        const isActive = value === option.value
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={isActive}
            aria-label={option.label}
            title={option.label}
            className={clsx('review-toggle__button', `review-toggle__button--${option.value}`, isActive && 'is-active')}
            onClick={() => onChange(isActive ? null : option.value)}
          >
            <span aria-hidden="true">{option.icon}</span>
          </button>
        )
      })}
    </div>
  )
}

interface FinalOutcomeButtonsProps {
  value: FinalOutcome
  onChange: (value: FinalOutcome) => void
  ariaLabel: string
}

function FinalOutcomeButtons({ value, onChange, ariaLabel }: FinalOutcomeButtonsProps) {
  return (
    <div className="review-toggle" role="group" aria-label={ariaLabel}>
      {FINAL_OPTIONS.map((option) => {
        const isActive = value === option.value
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={isActive}
            aria-label={option.label}
            title={option.label}
            className={clsx('review-toggle__button', `review-toggle__button--${option.tone}`, isActive && 'is-active')}
            onClick={() => onChange(isActive ? 'pending' : option.value)}
          >
            <span aria-hidden="true">{option.icon}</span>
          </button>
        )
      })}
    </div>
  )
}

const QUALITY_OPTIONS: { value: QualityFlag; label: string; icon: string }[] = [
  { value: 'good', label: 'Mark as good', icon: '✔' },
  { value: 'poor', label: 'Mark as bad', icon: '✖' },
]

const FINAL_OPTIONS: { value: Exclude<FinalOutcome, 'pending'>; label: string; icon: string; tone: 'good' | 'poor' }[] = [
  { value: 'good', label: 'Approve patched file', icon: '✔', tone: 'good' },
  { value: 'bad', label: 'Reject patched file', icon: '✖', tone: 'poor' },
]

function syncDiagnostics(
  monaco: MonacoApi,
  model: MonacoEditor.ITextModel,
  editor: MonacoEditor.IStandaloneCodeEditor | null,
  decorationsRef: MutableRefObject<string[]>,
  diagnostics: CompilerDiagnostic[],
) {
  applyMarkers(monaco, model, diagnostics)
  if (editor) {
    applyDecorations(monaco, editor, decorationsRef, diagnostics)
  }
}

function applyMarkers(monaco: MonacoApi, model: MonacoEditor.ITextModel, diagnostics: CompilerDiagnostic[]) {
  const markers = diagnostics.slice(0, 100).map((diag) => ({
    startLineNumber: Math.max(1, diag.line),
    endLineNumber: Math.max(1, diag.line),
    startColumn: Math.max(1, diag.column),
    endColumn: Math.max(1, diag.column + 1),
    message: diag.message,
    severity: mapSeverity(monaco, diag.severity),
  }))
  monaco.editor.setModelMarkers(model, 'compiler', markers)
}

function applyDecorations(
  monaco: MonacoApi,
  editor: MonacoEditor.IStandaloneCodeEditor,
  decorationsRef: MutableRefObject<string[]>,
  diagnostics: CompilerDiagnostic[],
) {
  const capped = diagnostics.slice(0, 100)
  const lineLeaders = pickLineLeaders(capped)

  const decorations = capped.map((diag) => {
    const hoverMessage = createHoverMessage(diag.message)
    const showLabel = lineLeaders.get(diag.line) === diag
    return {
      range: new monaco.Range(
        Math.max(1, diag.line),
        Math.max(1, diag.column),
        Math.max(1, diag.line),
        Math.max(1, diag.column + 1),
      ),
      options: {
        inlineClassName: `diagnostic-inline diagnostic-inline--${diag.severity}`,
        beforeContentClassName: `diagnostic-anchor diagnostic-anchor--${diag.severity}`,
        glyphMarginClassName: `diagnostic-gutter diagnostic-gutter--${diag.severity}`,
        linesDecorationsClassName: `diagnostic-line diagnostic-line--${diag.severity}`,
        hoverMessage,
        stickiness: monaco.editor.TrackedRangeStickiness.NeverGrowsWhenTypingAtEdges,
        renderOptions: showLabel
          ? {
              after: {
                contentText: truncateMessage(diag.message),
                inlineClassName: `diagnostic-tooltip diagnostic-tooltip--${diag.severity}`,
              },
            }
          : undefined,
      },
    }
  })
  decorationsRef.current = editor.deltaDecorations(decorationsRef.current, decorations)
}

function pickLineLeaders(diagnostics: CompilerDiagnostic[]): Map<number, CompilerDiagnostic> {
  const leaders = new Map<number, CompilerDiagnostic>()
  for (const diag of diagnostics) {
    const current = leaders.get(diag.line)
    if (!current || severityRank(diag.severity) < severityRank(current.severity)) {
      leaders.set(diag.line, diag)
    }
  }
  return leaders
}

function severityRank(severity: CompilerDiagnostic['severity']) {
  switch (severity) {
    case 'error':
      return 0
    case 'warning':
      return 1
    default:
      return 2
  }
}

function truncateMessage(message: string, limit = 120): string {
  const singleLine = message.replace(/\s+/g, ' ').trim()
  if (singleLine.length <= limit) return singleLine
  return `${singleLine.slice(0, limit - 1)}…`
}

function createHoverMessage(message: string) {
  const escapedTicks = message.replace(/`/g, '\\`')
  const safe = escapedTicks.replace(/</g, '&lt;').replace(/>/g, '&gt;')
  return { value: `\`${safe}\`` }
}

function selectLineLeaders(diagnostics: CompilerDiagnostic[]): CompilerDiagnostic[] {
  return Array.from(pickLineLeaders(diagnostics).values())
}

interface InlineBadgePosition {
  id: string
  severity: CompilerDiagnostic['severity']
  message: string
  top: number
  left: number
}

function disposeBadgeListeners(ref: MutableRefObject<EditorDisposable[]>) {
  for (const disposable of ref.current) {
    disposable.dispose()
  }
  ref.current = []
}

function severityIcon(severity: CompilerDiagnostic['severity']) {
  switch (severity) {
    case 'warning':
      return '⚠'
    case 'info':
      return 'ℹ'
    default:
      return '✖'
  }
}

function mapSeverity(monaco: MonacoApi, severity: CompilerDiagnostic['severity']) {
  switch (severity) {
    case 'warning':
      return monaco.MarkerSeverity.Warning
    case 'info':
      return monaco.MarkerSeverity.Info
    default:
      return monaco.MarkerSeverity.Error
  }
}

function countNonEmptyLines(value: string): number {
  if (!value) return 0
  return value.split('\n').filter((line) => line.trim().length > 0).length
}
