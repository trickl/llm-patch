import type { CaseDetail, CaseSummary } from '../types'

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || 'Request failed')
  }
  return (await response.json()) as T
}

export async function fetchCaseSummaries(signal?: AbortSignal): Promise<CaseSummary[]> {
  const response = await fetch('/api/cases', { signal })
  return handleResponse<CaseSummary[]>(response)
}

export async function fetchCaseDetail(caseId: string, signal?: AbortSignal): Promise<CaseDetail> {
  const response = await fetch(`/api/cases/${encodeURIComponent(caseId)}`, { signal })
  return handleResponse<CaseDetail>(response)
}
