import { useCallback, useEffect, useMemo, useRef, useState, type MutableRefObject, type ReactNode } from 'react'
import clsx from 'clsx'
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels'
import { Editor } from '@monaco-editor/react'
import type { editor as MonacoEditor } from 'monaco-editor'
import type {
  AnnotationState,
  CaseDetail,
  FinalOutcome,
  Hypothesis,
  HypothesisBuckets,
  IterationTelemetry,
  QualityFlag,
  StrategyPhaseArtifact,
  StrategyTrace,
} from '../types'
import { useReviewStore } from '../store/useReviewStore'
import { parseDiagnostics, type CompilerDiagnostic } from '../utils/diagnostics'
import { copyTextToClipboard } from '../utils/clipboard'

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
  const [activeDockTab, setActiveDockTab] = useState<DockTabId>('diff')
  const [guidedDetailTab, setGuidedDetailTab] = useState<GuidedDetailTab>('prompt')
  const [requestedStageId, setRequestedStageId] = useState<string | null>(null)
  const [flowCopyStatus, setFlowCopyStatus] = useState<'idle' | 'copied' | 'error'>('idle')
  const updateMetrics = useReviewStore((state) => state.updateMetrics)
  const [beforeEditor, setBeforeEditor] = useState<MonacoEditor.IStandaloneCodeEditor | null>(null)
  const [afterEditor, setAfterEditor] = useState<MonacoEditor.IStandaloneCodeEditor | null>(null)
  const scrollSyncGuard = useRef(false)
  const flowCopyResetRef = useRef<ReturnType<typeof setTimeout> | null>(null)
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
  const iterationGroups = useMemo(() => buildIterationDescriptors(detail.strategyTrace), [detail.strategyTrace])
  const stageTabs = useMemo(() => iterationGroups.flatMap((group) => group.stages), [iterationGroups])
  const activeStageId = useMemo(() => {
    if (!stageTabs.length) {
      return null
    }
    if (requestedStageId && stageTabs.some((tab) => tab.id === requestedStageId)) {
      return requestedStageId
    }
    return stageTabs[0].id
  }, [stageTabs, requestedStageId])
  const activeStageTab = useMemo(() => stageTabs.find((tab) => tab.id === activeStageId) ?? null, [stageTabs, activeStageId])
  const activeIteration = useMemo(() => {
    if (!iterationGroups.length) {
      return null
    }
    if (!activeStageTab) {
      return iterationGroups[0]
    }
    return iterationGroups.find((group) => group.iteration === activeStageTab.iteration) ?? iterationGroups[0]
  }, [iterationGroups, activeStageTab])
  const responseAvailableForActiveStage = useMemo(
    () => Boolean(activeStageTab?.artifact.response && activeStageTab.artifact.response.trim().length),
    [activeStageTab],
  )
  const dockTabs: DockTabDescriptor[] = useMemo(
    () => [
      { id: 'diff', label: 'Diff', shortLabel: 'Diff' },
      { id: 'errors', label: 'Errors', shortLabel: 'Errors' },
      { id: 'guided', label: 'Guided Loop', shortLabel: 'Guided' },
    ],
    [],
  )

  const dockTitle =
    activeDockTab === 'guided' && activeStageTab
      ? activeStageTab.label
      : activeDockTab === 'diff'
        ? 'Unified Diff'
        : activeDockTab === 'errors'
          ? 'Compiler Errors'
          : 'Guided Loop'

  const dockSubtitle =
    activeDockTab === 'guided' && activeStageTab
      ? describeStageSubtitle(activeStageTab)
      : activeDockTab === 'diff'
        ? `${diffLineCount} lines · ${detail.summary.diffName}`
        : activeDockTab === 'errors'
          ? `${stderrLineCount} stderr lines`
          : 'Select a guided loop stage to inspect prompts and responses.'
  const canCopyFlow = Boolean(activeIteration && activeIteration.stages.length)
  const flowCopyButtonLabel =
    flowCopyStatus === 'copied'
      ? 'Copied flow'
      : flowCopyStatus === 'error'
        ? 'Copy failed'
        : 'Copy flow'

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

  useEffect(() => () => {
    if (flowCopyResetRef.current) {
      clearTimeout(flowCopyResetRef.current)
      flowCopyResetRef.current = null
    }
  }, [])
  const effectiveGuidedDetailTab: GuidedDetailTab = guidedDetailTab === 'response' && !responseAvailableForActiveStage ? 'prompt' : guidedDetailTab

  const handleCopyFlow = useCallback(async () => {
    if (!activeIteration) {
      return
    }
    const payload = formatIterationFlowForClipboard(activeIteration)
    if (!payload) {
      return
    }
    try {
      await copyTextToClipboard(payload)
      setFlowCopyStatus('copied')
    } catch (error) {
      console.error('Failed to copy guided loop flow', error)
      setFlowCopyStatus('error')
    }
    if (flowCopyResetRef.current) {
      clearTimeout(flowCopyResetRef.current)
    }
    flowCopyResetRef.current = setTimeout(() => {
      setFlowCopyStatus('idle')
      flowCopyResetRef.current = null
    }, 2000)
  }, [activeIteration])

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
        <Panel minSize={20} defaultSize={60} order={1}>
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
        <Panel minSize={20} defaultSize={40} order={2}>
          <section className="dock-panel">
            <div className="dock-panel__header">
              <div className="dock-panel__header-left">
                <div>
                  <h3>{dockTitle}</h3>
                  <p>{dockSubtitle}</p>
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
                {activeDockTab === 'guided' && (
                  <button
                    type="button"
                    className={clsx(
                      'dock-panel__copy-flow',
                      flowCopyStatus === 'copied' && 'dock-panel__copy-flow--success',
                      flowCopyStatus === 'error' && 'dock-panel__copy-flow--error',
                    )}
                    onClick={handleCopyFlow}
                    disabled={!canCopyFlow}
                    aria-label={flowCopyButtonLabel}
                    title="Copy every LLM prompt and response for this guided loop iteration"
                  >
                    <span aria-hidden="true">
                      {flowCopyStatus === 'copied' ? '✔' : flowCopyStatus === 'error' ? '⚠' : '⧉'}
                    </span>
                  </button>
                )}
                <div className="dock-panel__tabs" role="tablist" aria-label="Diff, errors, and guided loop stages">
                  {dockTabs.map((tab) => (
                    <button
                      key={tab.id}
                      type="button"
                      role="tab"
                      aria-selected={activeDockTab === tab.id}
                      className={activeDockTab === tab.id ? 'dock-panel__tab dock-panel__tab--active' : 'dock-panel__tab'}
                      onClick={() => setActiveDockTab(tab.id)}
                      title={tab.label}
                    >
                      {tab.shortLabel}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <div className="dock-panel__content">
              {activeDockTab === 'diff' ? (
                <pre className="diff-view" aria-label="Unified diff patch">
                  {detail.diff || 'No diff available.'}
                </pre>
              ) : activeDockTab === 'errors' ? (
                <ErrorsPanel before={detail.errors.before} after={detail.errors.after} />
              ) : (
                <div className="guided-loop-pane">
                  <GuidedLoopTimeline
                    groups={iterationGroups}
                    activeStageId={activeStageId}
                    onStageSelect={(stageId) => {
                      setRequestedStageId(stageId)
                      setActiveDockTab('guided')
                    }}
                    completionStatus={detail.summary.success ? 'success' : 'failure'}
                  />
                  <div className="guided-loop-pane__detail">
                    <div className="guided-loop-pane__detail-tabs" role="tablist" aria-label="Guided loop detail view">
                      <button
                        type="button"
                        role="tab"
                        aria-selected={effectiveGuidedDetailTab === 'prompt'}
                        className={clsx(
                          'guided-loop-pane__detail-tab',
                          effectiveGuidedDetailTab === 'prompt' && 'guided-loop-pane__detail-tab--active',
                        )}
                        onClick={() => setGuidedDetailTab('prompt')}
                      >
                        LLM Request
                      </button>
                      <button
                        type="button"
                        role="tab"
                        aria-selected={effectiveGuidedDetailTab === 'response'}
                        className={clsx(
                          'guided-loop-pane__detail-tab',
                          effectiveGuidedDetailTab === 'response' && 'guided-loop-pane__detail-tab--active',
                        )}
                        onClick={() => setGuidedDetailTab('response')}
                        disabled={!responseAvailableForActiveStage}
                        title={!responseAvailableForActiveStage ? 'Response not recorded yet' : undefined}
                      >
                        LLM Response
                      </button>
                      <button
                        type="button"
                        role="tab"
                        aria-selected={effectiveGuidedDetailTab === 'insights'}
                        className={clsx(
                          'guided-loop-pane__detail-tab',
                          effectiveGuidedDetailTab === 'insights' && 'guided-loop-pane__detail-tab--active',
                        )}
                        onClick={() => setGuidedDetailTab('insights')}
                      >
                        Insights
                      </button>
                    </div>
                    {!activeStageTab ? (
                      <div className="dock-panel__empty">Guided loop output unavailable.</div>
                    ) : effectiveGuidedDetailTab === 'insights' ? (
                      <div className="guided-loop-pane__insights">
                        <HypothesisDeck iteration={activeIteration} />
                        <IterationTelemetryPanel iteration={activeIteration} />
                      </div>
                    ) : (
                      <StrategyPhaseContent
                        key={activeStageTab.id}
                        descriptor={activeStageTab}
                        view={effectiveGuidedDetailTab === 'response' ? 'response' : 'prompt'}
                      />
                    )}
                  </div>
                </div>
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
  const [requestedView, setRequestedView] = useState<'before' | 'after'>(hasAfter ? 'after' : 'before')
  const view = requestedView === 'after' && !hasAfter ? 'before' : requestedView

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
          onClick={() => setRequestedView('before')}
        >
          Before errors
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={view === 'after'}
          className={clsx('errors-view__mode-button', view === 'after' && 'is-active')}
          onClick={() => setRequestedView('after')}
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

type IterationKind = 'primary' | 'refine'
type DockTabId = 'diff' | 'errors' | 'guided'
type GuidedDetailTab = 'prompt' | 'response' | 'insights'

interface DockTabDescriptor {
  id: DockTabId
  label: string
  shortLabel: string
}

interface StageTabDescriptor {
  id: string
  label: string
  shortLabel: string
  iteration: number
  iterationLabel: string
  iterationKind: IterationKind
  artifact: StrategyPhaseArtifact
}

interface IterationGroupDescriptor {
  iteration: number
  label: string
  kind: IterationKind
  accepted: boolean
  failureReason?: string | null
  stages: StageTabDescriptor[]
  hypotheses?: HypothesisBuckets | null
  selectedHypothesisId?: string | null
  telemetry?: IterationTelemetry | null
}

function StrategyPhaseContent({ descriptor, view }: { descriptor: StageTabDescriptor; view: 'prompt' | 'response' }) {
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied' | 'error'>('idle')
  const copyResetRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const responseAvailable = Boolean(descriptor.artifact.response && descriptor.artifact.response.trim().length)
  const promptText = descriptor.artifact.prompt || 'Prompt not recorded.'
  const responseText = responseAvailable ? descriptor.artifact.response!.trim() : 'Response not captured yet.'
  const timestampLabel = formatTimestampRange(descriptor.artifact.startedAt, descriptor.artifact.completedAt)
  const displayedText = view === 'prompt' ? promptText : responseText
  const copyDisabled = view === 'response' && !responseAvailable
  const copyButtonLabel =
    copyStatus === 'copied'
      ? 'Copied'
      : copyStatus === 'error'
        ? 'Copy failed'
        : view === 'prompt'
          ? 'Copy request'
          : 'Copy response'

  useEffect(() => () => {
    if (copyResetRef.current) {
      clearTimeout(copyResetRef.current)
      copyResetRef.current = null
    }
  }, [])

  const handleCopy = useCallback(async () => {
    if (copyDisabled) {
      return
    }
    try {
      await copyTextToClipboard(displayedText)
      setCopyStatus('copied')
    } catch (error) {
      console.error('Failed to copy guided loop content', error)
      setCopyStatus('error')
    }
    if (copyResetRef.current) {
      clearTimeout(copyResetRef.current)
    }
    copyResetRef.current = setTimeout(() => {
      setCopyStatus('idle')
      copyResetRef.current = null
    }, 2000)
  }, [copyDisabled, displayedText])

  return (
    <div className="strategy-phase" aria-live="polite">
      <div className="strategy-phase__header-bar">
        <div>
          <p className="strategy-phase__meta">{descriptor.iterationLabel}</p>
          <p className="strategy-phase__status">
            {formatPhaseName(descriptor.artifact.phase)} · {humanizeStatus(descriptor.artifact.status)}
          </p>
          {timestampLabel && <p className="strategy-phase__timestamps">{timestampLabel}</p>}
        </div>
        <div className="strategy-phase__actions">
          <span className="strategy-phase__view-label">{view === 'prompt' ? 'LLM Request' : 'LLM Response'}</span>
          <button
            type="button"
            className={clsx('strategy-phase__copy', copyStatus === 'copied' && 'is-success', copyStatus === 'error' && 'is-error')}
            onClick={handleCopy}
            disabled={copyDisabled}
            aria-label={copyButtonLabel}
            title={copyButtonLabel}
          >
            <span aria-hidden="true">{copyStatus === 'copied' ? '✔' : copyStatus === 'error' ? '⚠' : '⧉'}</span>
          </button>
        </div>
      </div>
      <pre className="strategy-phase__body">{displayedText}</pre>
      {descriptor.artifact.humanNotes && (
        <div className="strategy-phase__notes">
          <h4>Notes</h4>
          <p>{descriptor.artifact.humanNotes}</p>
        </div>
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
    const frame = requestAnimationFrame(() => {
      updateBadgePositions()
    })
    return () => cancelAnimationFrame(frame)
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

function buildIterationDescriptors(trace?: StrategyTrace | null): IterationGroupDescriptor[] {
  if (!trace || !trace.iterations?.length) {
    return []
  }
  return trace.iterations
    .slice()
    .sort((a, b) => a.index - b.index)
    .map((iteration) => {
      const label = iteration.label ?? `Iteration ${iteration.index}`
      const kind: IterationKind = iteration.kind === 'refine' ? 'refine' : 'primary'
      const stages: StageTabDescriptor[] = iteration.phases.map((artifact, phaseIndex) => {
        const phaseLabel = formatPhaseName(artifact.phase)
        return {
          id: `stage-${iteration.index}-${phaseIndex}-${artifact.phase}`,
          label: `${phaseLabel} · ${label}`,
          shortLabel: phaseLabel,
          iteration: iteration.index,
          iterationLabel: label,
          iterationKind: kind,
          artifact,
        }
      })
      return {
        iteration: iteration.index,
        label,
        kind,
        accepted: iteration.accepted,
        failureReason: iteration.failureReason ?? null,
        stages,
        hypotheses: iteration.hypotheses ?? null,
        selectedHypothesisId: iteration.selectedHypothesisId ?? null,
        telemetry: iteration.telemetry ?? null,
      }
    })
}

interface GuidedLoopTimelineProps {
  groups: IterationGroupDescriptor[]
  activeStageId: string | null
  onStageSelect: (stageId: string) => void
  completionStatus: 'success' | 'failure'
}

function GuidedLoopTimeline({ groups, activeStageId, onStageSelect, completionStatus }: GuidedLoopTimelineProps) {
  if (!groups.length) {
    return <div className="loop-timeline loop-timeline--empty">No guided loop iterations recorded.</div>
  }
  const completionIcon = completionStatus === 'success' ? '✔' : '✖'
  const completionLabel = completionStatus === 'success' ? 'Guided loop completed successfully' : 'Guided loop failed to converge'
  const completionClass = clsx(
    'loop-stage',
    'loop-stage--complete',
    completionStatus === 'success' ? 'loop-stage--complete-success' : 'loop-stage--complete-failure',
  )
  return (
    <div className="loop-timeline" aria-label="Guided loop timeline">
      {groups.map((group, index) => {
        const failureLabel = formatFailureReason(group.failureReason) ?? group.failureReason
        const hasStall = Boolean(group.telemetry?.stall?.length)
        return (
          <div
            key={group.iteration}
            className={clsx('loop-timeline__row', hasStall && 'loop-timeline__row--stall')}
          >
            <div className="loop-timeline__label-block">
              <span className="loop-timeline__label">{group.label}</span>
              <div className="loop-timeline__signals">
                {group.selectedHypothesisId && (
                  <span className="loop-timeline__alert loop-timeline__alert--focus">
                    Focus {group.selectedHypothesisId}
                  </span>
                )}
                {hasStall ? (
                  <span className="loop-timeline__alert loop-timeline__alert--stall" role="status">
                    ⚠ Stall detected
                  </span>
                ) : (
                  failureLabel && (
                    <span className="loop-timeline__alert loop-timeline__alert--failure">{failureLabel}</span>
                  )
                )}
              </div>
            </div>
          <div className="loop-timeline__stages">
            {group.stages.map((stage) => {
              const statusClass = `loop-stage--${stage.artifact.status}`
              return (
                <button
                  type="button"
                  key={stage.id}
                  className={clsx('loop-stage', statusClass, activeStageId === stage.id && 'is-active')}
                  aria-pressed={activeStageId === stage.id}
                  onClick={() => onStageSelect(stage.id)}
                >
                  {stage.shortLabel}
                </button>
              )
            })}
            {index === 0 && (
              <span className={completionClass} aria-label={completionLabel} role="status">
                <span aria-hidden="true">{completionIcon}</span> Complete
              </span>
            )}
          </div>
          </div>
        )
      })}
    </div>
  )
}

const MAX_HYPOTHESES_PER_BUCKET = 3
type HypothesisBucketKey = 'active' | 'falsified' | 'rejected' | 'archived' | 'expired'
type HypothesisSectionTone = 'accent' | 'warning' | 'danger' | 'muted'

interface HypothesisSectionConfig {
  key: HypothesisBucketKey
  label: string
  icon: string
  tone: HypothesisSectionTone
}

const HYPOTHESIS_SECTIONS: HypothesisSectionConfig[] = [
  { key: 'active', label: 'Active hypotheses', icon: '🧠', tone: 'accent' },
  { key: 'falsified', label: 'Falsified', icon: '✖', tone: 'danger' },
  { key: 'rejected', label: 'Rejected', icon: '⚠', tone: 'warning' },
  { key: 'archived', label: 'Archived', icon: '📦', tone: 'muted' },
  { key: 'expired', label: 'Expired', icon: '⏳', tone: 'muted' },
]

function HypothesisDeck({ iteration }: { iteration: IterationGroupDescriptor | null }) {
  const hypotheses = iteration?.hypotheses
  const focusId = iteration?.selectedHypothesisId ?? null

  const visibleSections = HYPOTHESIS_SECTIONS.map((section) => {
    const bucket = hypotheses?.[section.key] as Hypothesis[] | undefined
    if (!bucket || !bucket.length) {
      return null
    }
    const trimmed = bucket.slice(0, MAX_HYPOTHESES_PER_BUCKET)
    const remaining = Math.max(0, bucket.length - trimmed.length)
    return {
      ...section,
      entries: trimmed,
      remaining,
    }
  }).filter(Boolean) as Array<{
    key: HypothesisBucketKey
    label: string
    icon: string
    tone: HypothesisSectionTone
    entries: Hypothesis[]
    remaining: number
  }>

  return (
    <section className="hypothesis-panel" aria-live="polite">
      <header className="hypothesis-panel__header">
        <div>
          <p className="hypothesis-panel__eyebrow">Hypotheses</p>
          <h4>{iteration?.label ?? 'No iteration selected'}</h4>
        </div>
        {focusId && <span className="hypothesis-panel__focus">Focus · {focusId}</span>}
      </header>
      {!iteration ? (
        <p className="hypothesis-panel__empty">Select a guided-loop stage to review hypotheses.</p>
      ) : !hypotheses ? (
        <p className="hypothesis-panel__empty">Hypothesis telemetry not recorded for this iteration.</p>
      ) : visibleSections.length ? (
        <div className="hypothesis-panel__grid">
          {visibleSections.map((section) => (
            <div key={section.key} className={clsx('hypothesis-panel__section', `hypothesis-panel__section--${section.tone}`)}>
              <div className="hypothesis-panel__section-header">
                <span>
                  <span aria-hidden="true">{section.icon}</span> {section.label}
                </span>
                <span className="hypothesis-panel__count">{section.entries.length + section.remaining}</span>
              </div>
              <div className="hypothesis-panel__cards">
                {section.entries.map((hypothesis) => (
                  <HypothesisCard key={hypothesis.id} hypothesis={hypothesis} isFocus={focusId === hypothesis.id} />
                ))}
              </div>
              {section.remaining > 0 && (
                <p className="hypothesis-panel__more">+{section.remaining} additional items tracked</p>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="hypothesis-panel__empty">No hypotheses recorded for this loop yet.</p>
      )}
    </section>
  )
}

interface HypothesisCardProps {
  hypothesis: Hypothesis
  isFocus: boolean
}

function HypothesisCard({ hypothesis, isFocus }: HypothesisCardProps) {
  const confidenceLabel = formatConfidence(hypothesis.confidence)
  const falsificationNote = hypothesis.falsificationNotes?.[0]
  return (
    <article className={clsx('hypothesis-card', isFocus && 'hypothesis-card--focus')}>
      <header className="hypothesis-card__header">
        <span className="hypothesis-card__id">{hypothesis.id}</span>
        {confidenceLabel && <span className="hypothesis-card__confidence">{confidenceLabel}</span>}
      </header>
      <p className="hypothesis-card__claim">{hypothesis.claim}</p>
      {hypothesis.affectedRegion && <p className="hypothesis-card__region">{hypothesis.affectedRegion}</p>}
      {hypothesis.structuralChange && <p className="hypothesis-card__structure">Δ {hypothesis.structuralChange}</p>}
      {hypothesis.expectedEffect && <p className="hypothesis-card__effect">{hypothesis.expectedEffect}</p>}
      <div className="hypothesis-card__badges">
        {typeof hypothesis.retryCount === 'number' && hypothesis.retryCount > 0 && (
          <span className="hypothesis-card__badge">Retries {hypothesis.retryCount}</span>
        )}
        {falsificationNote && (
          <span className="hypothesis-card__badge hypothesis-card__badge--warning">{falsificationNote}</span>
        )}
      </div>
    </article>
  )
}

type TelemetryTone = 'info' | 'warning' | 'success' | 'danger' | 'muted'

interface TelemetryEventDescriptor {
  key: string
  title: string
  detail?: string
  meta?: string
  icon: string
  tone: TelemetryTone
}

const MAX_TELEMETRY_EVENTS = 6

function IterationTelemetryPanel({ iteration }: { iteration: IterationGroupDescriptor | null }) {
  const events = gatherTelemetryEvents(iteration).slice(0, MAX_TELEMETRY_EVENTS)
  return (
    <section className="telemetry-panel">
      <header className="telemetry-panel__header">
        <p className="telemetry-panel__eyebrow">Loop signals</p>
        <h4>{iteration?.label ?? 'Timeline telemetry'}</h4>
      </header>
      {events.length ? (
        <ul className="telemetry-panel__list">
          {events.map((event) => (
            <li key={event.key} className={clsx('telemetry-event', `telemetry-event--${event.tone}`)}>
              <span className="telemetry-event__icon" aria-hidden="true">
                {event.icon}
              </span>
              <div>
                <p className="telemetry-event__title">{event.title}</p>
                {event.detail && <p className="telemetry-event__detail">{event.detail}</p>}
                {event.meta && <p className="telemetry-event__meta">{event.meta}</p>}
              </div>
            </li>
          ))}
        </ul>
      ) : iteration ? (
        <p className="telemetry-panel__empty">No telemetry recorded for this iteration yet.</p>
      ) : (
        <p className="telemetry-panel__empty">Select an iteration to view telemetry.</p>
      )}
    </section>
  )
}

function gatherTelemetryEvents(iteration: IterationGroupDescriptor | null): TelemetryEventDescriptor[] {
  if (!iteration) {
    return []
  }
  const telemetry = iteration.telemetry
  const events: TelemetryEventDescriptor[] = []
  const prefix = `iteration-${iteration.iteration}`
  const push = (event: Omit<TelemetryEventDescriptor, 'key'> & { key?: string }) => {
    const key = event.key ?? `${prefix}-${events.length}`
    events.push({ ...event, key })
  }

  telemetry?.stall?.forEach((entry, index) => {
    push({
      key: `${prefix}-stall-${index}`,
      title: 'Stall detected',
      detail: entry?.errorMessage || 'Diff span and error signature repeated.',
      meta: entry?.hypothesisId ? `Hypothesis ${entry.hypothesisId}` : undefined,
      icon: '⚠',
      tone: 'warning',
    })
  })

  telemetry?.falsification?.forEach((entry, index) => {
    const observed = entry?.observed?.[0]
    const pending = entry?.pending?.[0]
    const summary = entry?.summary
    push({
      key: `${prefix}-falsify-${index}`,
      title: entry?.status === 'rejected' ? `Hypothesis ${entry?.hypothesisId} falsified` : `Falsification review · ${entry?.hypothesisId}`,
      detail: observed || pending || summary || 'No contradictions reported.',
      meta: entry?.remaining != null ? `${entry.remaining} hypotheses remaining` : undefined,
      icon: entry?.status === 'rejected' ? '✖' : '🧪',
      tone: entry?.status === 'rejected' ? 'danger' : 'info',
    })
  })

  telemetry?.retries?.forEach((entry, index) => {
    push({
      key: `${prefix}-retry-${index}`,
      title: `Retry ${entry.retryCount} · ${entry.hypothesisId}`,
      detail: entry.reason || 'Retry triggered by controller.',
      icon: '🔁',
      tone: entry.retryCount >= 2 ? 'warning' : 'info',
    })
  })

  telemetry?.unchangedError?.forEach((entry, index) => {
    push({
      key: `${prefix}-unchanged-${index}`,
      title: 'Error output unchanged',
      detail: entry.previous === entry.current ? 'Error fingerprint identical between iterations.' : 'Error signature repeated.',
      meta: entry.hypothesisId ? `Hypothesis ${entry.hypothesisId}` : undefined,
      icon: '♻',
      tone: 'warning',
    })
  })

  telemetry?.hypothesisStatuses?.forEach((entry, index) => {
    push({
      key: `${prefix}-status-${index}`,
      title: `Hypothesis ${entry.id} → ${formatFailureReason(entry.status) ?? entry.status}`,
      detail: entry.reason ?? undefined,
      icon: '🗂',
      tone: entry.status === 'archived' || entry.status === 'expired' ? 'muted' : 'info',
    })
  })

  telemetry?.hypothesesCreated?.forEach((entry, index) => {
    const ids = entry.ids?.slice(0, 3).join(', ')
    const remainder = (entry.ids?.length ?? 0) - Math.min(3, entry.ids?.length ?? 0)
    push({
      key: `${prefix}-created-${index}`,
      title: `Logged ${entry.count ?? entry.ids?.length ?? 0} new hypotheses`,
      detail: ids ? `${ids}${remainder > 0 ? `, +${remainder} more` : ''}` : undefined,
      icon: '➕',
      tone: 'success',
    })
  })

  if (iteration.accepted) {
    push({
      key: `${prefix}-accepted`,
      title: 'Patch accepted',
      detail: 'Loop converged during this iteration.',
      icon: '✔',
      tone: 'success',
    })
  } else if (iteration.failureReason && !telemetry?.stall?.length) {
    push({
      key: `${prefix}-failure`,
      title: 'Iteration blocked',
      detail: formatFailureReason(iteration.failureReason) ?? iteration.failureReason,
      icon: '⛔',
      tone: 'danger',
    })
  }

  return events
}

function describeStageSubtitle(descriptor: StageTabDescriptor | null): string {
  if (!descriptor) {
    return 'Select a stage to inspect guided loop progress.'
  }
  const parts = [
    descriptor.iterationLabel,
    humanizeStatus(descriptor.artifact.status),
  ]
  const timeRange = formatTimestampRange(descriptor.artifact.startedAt, descriptor.artifact.completedAt)
  if (timeRange) {
    parts.push(timeRange)
  }
  return parts.join(' · ')
}

function formatFailureReason(reason?: string | null): string | null {
  if (!reason) {
    return null
  }
  return reason
    .split(/[-_\s]+/)
    .filter(Boolean)
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
    .join(' ')
}

function formatConfidence(value?: number | null): string | null {
  if (value === null || value === undefined) {
    return null
  }
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return null
  }
  const normalized = value <= 1 ? value * 100 : value
  const percent = Math.min(100, Math.max(0, Math.round(normalized)))
  return `${percent}%`
}

const STATUS_LABELS: Record<string, string> = {
  planned: 'Planned',
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
}

function humanizeStatus(status: string): string {
  return STATUS_LABELS[status] ?? status
}

const PHASE_LABELS: Record<string, string> = {
  interpret: 'Interpret',
  plan: 'Plan',
  draft: 'Draft',
  reflect: 'Reflect',
  verify: 'Verify',
}

function formatPhaseName(phase: string): string {
  const normalized = phase.toLowerCase()
  if (PHASE_LABELS[normalized]) {
    return PHASE_LABELS[normalized]
  }
  return normalized
    .split(/[-_\s]+/)
    .filter(Boolean)
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
    .join(' ')
}

function formatIterationFlowForClipboard(iteration: IterationGroupDescriptor | null): string | null {
  if (!iteration) {
    return null
  }
  const lines: string[] = []
  const header = iteration.label || `Iteration ${iteration.iteration}`
  lines.push(`Guided Loop Flow · ${header}`)
  iteration.stages.forEach((stage) => {
    const phaseName = formatPhaseName(stage.artifact.phase)
    const prompt = (stage.artifact.prompt || '').trim()
    const response = (stage.artifact.response || '').trim()
    lines.push('')
    lines.push(`[${phaseName}]`)
    lines.push('LLM Request:')
    lines.push(prompt || '(prompt unavailable)')
    lines.push('')
    lines.push('LLM Response:')
    lines.push(response || '(response unavailable)')
  })
  return lines.join('\n').trim()
}

function formatTimestampRange(start?: string | null, end?: string | null): string | null {
  if (!start && !end) {
    return null
  }
  const format = (value?: string | null) => {
    if (!value) return '—'
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return '—'
    return date.toLocaleTimeString(undefined, {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }
  const startLabel = format(start)
  const endLabel = format(end)
  if (startLabel === '—' && endLabel === '—') {
    return null
  }
  return `${startLabel} – ${endLabel}`
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
