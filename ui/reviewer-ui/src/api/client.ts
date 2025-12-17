import type { CaseDetail, CaseRerunResponse, CaseSummary } from '../types'

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

export async function refreshDatasetCache(): Promise<{ status: string }> {
  const response = await fetch('/api/dataset/refresh', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: '{}',
  })
  return handleResponse<{ status: string }>(response)
}

export async function rerunCaseRequest(caseId: string): Promise<CaseRerunResponse> {
  const response = await fetch(`/api/cases/${encodeURIComponent(caseId)}/rerun`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: '{}',
  })
  return handleResponse<CaseRerunResponse>(response)
}
