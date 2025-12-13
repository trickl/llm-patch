import { useMemo } from 'react'
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels'
import { DiffEditor, Editor } from '@monaco-editor/react'
import type { AnnotationState, CaseDetail } from '../types'
import { AnnotationPanel } from './AnnotationPanel'

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
  const monacoLanguage = useMemo(() => {
    const normalized = detail.summary.language.toLowerCase()
    return languageMap[normalized] ?? 'plaintext'
  }, [detail.summary.language])

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
              <EditorSection title="Before" language={monacoLanguage} value={detail.before} />
            </Panel>
            <PanelResizeHandle className="resize-handle vertical" />
            <Panel minSize={25} defaultSize={35}>
              <EditorSection title="After" language={monacoLanguage} value={detail.after} />
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
          <PanelGroup direction="horizontal">
            <Panel minSize={30} defaultSize={60}>
              <section className="diff-dock">
                <div className="diff-dock__header">
                  <div>
                    <h3>Unified Diff</h3>
                    <p>{detail.diff.split('\n').length} lines · {detail.summary.diffName}</p>
                  </div>
                  {detail.derived.afterSource === 'missing' && (
                    <span className="diff-dock__warning">After file unavailable; showing original</span>
                  )}
                </div>
                <DiffEditor
                  className="diff-dock__editor"
                  language={monacoLanguage}
                  original={detail.before}
                  modified={detail.after}
                  theme="vs-dark"
                  options={{
                    readOnly: true,
                    domReadOnly: true,
                    minimap: { enabled: false },
                    renderOverviewRuler: false,
                    scrollBeyondLastLine: false,
                  }}
                />
              </section>
            </Panel>
            <PanelResizeHandle className="resize-handle vertical" />
            <Panel minSize={20} defaultSize={40}>
              <ErrorsPanel stderr={detail.errors.stderr} stdout={detail.errors.stdout} />
            </Panel>
          </PanelGroup>
        </Panel>
      </PanelGroup>
    </section>
  )
}

interface EditorSectionProps {
  title: string
  value: string
  language: string
}

function ErrorsPanel({ stderr, stdout }: { stderr: string; stdout: string }) {
  return (
    <section className="errors-pane">
      <header className="errors-pane__header">
        <div>
          <h3>Compiler Errors</h3>
          <p>stderr · {stderr ? `${stderr.split('\n').length} lines` : 'empty'}</p>
        </div>
      </header>
      <pre className="errors-pane__body">{stderr || 'No stderr captured.'}</pre>
      {stdout && (
        <details className="errors-pane__stdout">
          <summary>compiler stdout</summary>
          <pre>{stdout}</pre>
        </details>
      )}
    </section>
  )
}

function EditorSection({ title, value, language }: EditorSectionProps) {
  return (
    <section className="editor-pane">
      <header className="editor-pane__header">
        <h3>{title}</h3>
      </header>
      <Editor
        language={language}
        value={value}
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
      />
    </section>
  )
}
