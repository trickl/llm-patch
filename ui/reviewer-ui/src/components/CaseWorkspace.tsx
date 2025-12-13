import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels'
import { Editor } from '@monaco-editor/react'
import type { editor as MonacoEditor } from 'monaco-editor'
import type { AnnotationState, CaseDetail } from '../types'
import { AnnotationPanel } from './AnnotationPanel'

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

interface CompilerDiagnostic {
  line: number
  column: number
  message: string
}

export function CaseWorkspace({ detail, annotation }: CaseWorkspaceProps) {
  const [activeDockTab, setActiveDockTab] = useState<'diff' | 'errors'>('diff')
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

  const diagnostics = useMemo(() => extractDiagnostics(detail.errors.stderr), [detail.errors.stderr])
  const patchFailed = !detail.summary.patchApplied
  const afterMissing = detail.derived.afterSource === 'missing'
  const afterUnavailable = patchFailed || afterMissing
  const afterPlaceholder = afterUnavailable ? (patchFailed ? 'Patch failed' : 'Not available') : undefined
  const afterValue = afterUnavailable ? '' : detail.after
  const diffLineCount = detail.diff.split('\n').length
  const stderrLineCount = countNonEmptyLines(detail.errors.stderr)

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
          <span className="workspace__language">{detail.summary.language}</span>
          <span>{detail.summary.modelSlug}</span>
          <span>{detail.summary.algorithm}</span>
        </div>
      </header>
      <PanelGroup className="workspace__panels" direction="vertical">
        <Panel minSize={40} defaultSize={65} order={1}>
          <PanelGroup direction="horizontal">
            <Panel minSize={25} defaultSize={35}>
              <EditorSection
                key={modelPaths.before}
                title="Before"
                language={monacoLanguage}
                value={detail.before}
                modelPath={modelPaths.before}
                diagnostics={diagnostics}
                onEditorMount={handleBeforeMount}
              />
            </Panel>
            <PanelResizeHandle className="resize-handle vertical" />
            <Panel minSize={25} defaultSize={35}>
              <EditorSection
                key={modelPaths.after}
                title="After"
                language={monacoLanguage}
                value={afterValue}
                modelPath={modelPaths.after}
                diagnostics={diagnostics}
                placeholder={afterPlaceholder}
                onEditorMount={handleAfterMount}
              />
            </Panel>
            <PanelResizeHandle className="resize-handle vertical" />
            <Panel minSize={20} defaultSize={30}>
              <AnnotationPanel
                caseId={detail.summary.id}
                annotation={annotation}
              />
            </Panel>
          </PanelGroup>
        </Panel>
        <PanelResizeHandle className="resize-handle horizontal" />
        <Panel minSize={25} defaultSize={35} order={2}>
          <section className="dock-panel">
            <div className="dock-panel__header">
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
            <div className="dock-panel__content">
              {activeDockTab === 'diff' ? (
                <pre className="diff-view" aria-label="Unified diff patch">
                  {detail.diff || 'No diff available.'}
                </pre>
              ) : (
                <ErrorsPanel stderr={detail.errors.stderr} stdout={detail.errors.stdout} />
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
}

function ErrorsPanel({ stderr, stdout }: { stderr: string; stdout: string }) {
  return (
    <div className="errors-view">
      <pre className="errors-view__body">{stderr || 'No stderr captured.'}</pre>
      {stdout && (
        <details className="errors-view__stdout">
          <summary>compiler stdout</summary>
          <pre>{stdout}</pre>
        </details>
      )}
    </div>
  )
}

function EditorSection({ title, value, language, modelPath, diagnostics, placeholder, onEditorMount }: EditorSectionProps) {
  const modelRef = useRef<MonacoEditor.ITextModel | null>(null)
  const monacoRef = useRef<MonacoApi | null>(null)

  useEffect(() => {
    if (!modelRef.current || !monacoRef.current) return
    applyDiagnostics(monacoRef.current, modelRef.current, diagnostics)
  }, [diagnostics])

  useEffect(() => () => {
    if (modelRef.current && monacoRef.current) {
      monacoRef.current.editor.setModelMarkers(modelRef.current, 'compiler', [])
    }
  }, [])

  return (
    <section className="editor-pane">
      <header className="editor-pane__header">
        <h3>{title}</h3>
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
          }}
          height="100%"
          onMount={(editorInstance, monaco) => {
            modelRef.current = editorInstance.getModel()
            monacoRef.current = monaco
            if (modelRef.current) {
              applyDiagnostics(monaco, modelRef.current, diagnostics)
            }
            onEditorMount?.(editorInstance)
          }}
        />
        {placeholder && <div className="editor-pane__placeholder">{placeholder}</div>}
      </div>
    </section>
  )
}

function applyDiagnostics(monaco: MonacoApi, model: MonacoEditor.ITextModel, diagnostics: CompilerDiagnostic[]) {
  const markers = diagnostics.slice(0, 100).map((diag) => ({
    startLineNumber: diag.line,
    endLineNumber: diag.line,
    startColumn: diag.column,
    endColumn: diag.column + 1,
    message: diag.message,
    severity: monaco.MarkerSeverity.Error,
  }))
  monaco.editor.setModelMarkers(model, 'compiler', markers)
}

function extractDiagnostics(stderr: string): CompilerDiagnostic[] {
  if (!stderr) return []
  const diagnostics: CompilerDiagnostic[] = []
  for (const line of stderr.split('\n')) {
    const parsed = parseDiagnosticLine(line)
    if (parsed) {
      diagnostics.push(parsed)
    }
    if (diagnostics.length >= 100) {
      break
    }
  }
  return diagnostics
}

function parseDiagnosticLine(line: string): CompilerDiagnostic | null {
  const trimmed = line.trim()
  if (!trimmed) return null
  const colonMatch = trimmed.match(/:(\d+)(?::(\d+))?/)
  if (colonMatch) {
    return {
      line: Number.parseInt(colonMatch[1] ?? '1', 10) || 1,
      column: Number.parseInt(colonMatch[2] ?? '1', 10) || 1,
      message: trimmed,
    }
  }
  const lineMatch = trimmed.match(/line\s+(\d+)/i)
  if (lineMatch) {
    return {
      line: Number.parseInt(lineMatch[1] ?? '1', 10) || 1,
      column: 1,
      message: trimmed,
    }
  }
  return null
}

function countNonEmptyLines(value: string): number {
  if (!value) return 0
  return value.split('\n').filter((line) => line.trim().length > 0).length
}
