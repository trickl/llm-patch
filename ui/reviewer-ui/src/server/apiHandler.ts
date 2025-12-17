import { parse } from 'node:url'
import type { ServerResponse } from 'node:http'
import { DatasetLoader } from './datasetLoader'
import type { ApiHandler } from './datasetTypes'

export function createDatasetApiHandler(loader = new DatasetLoader()): ApiHandler {
  return async (req, res) => {
    const url = req.url ?? '/'
    if (!url.startsWith('/api/')) {
      res.statusCode = 404
      res.end('Not Found')
      return
    }

    const parsed = parse(url, true)
    const segments = (parsed.pathname ?? '').replace(/^\/+|\/+$/g, '').split('/')

    if (segments.length === 2 && segments[0] === 'api' && segments[1] === 'cases' && req.method === 'GET') {
      await loader.ensureLoaded()
      sendJson(res, loader.listSummaries())
      return
    }

    if (segments.length === 3 && segments[0] === 'api' && segments[1] === 'cases' && req.method === 'GET') {
      const caseId = decodeURIComponent(segments[2])
      const detail = await loader.getDetail(caseId)
      if (!detail) {
        res.statusCode = 404
        sendJson(res, { error: 'Case not found' })
        return
      }
      sendJson(res, detail)
      return
    }

    if (
      segments.length === 4 &&
      segments[0] === 'api' &&
      segments[1] === 'cases' &&
      segments[3] === 'rerun' &&
      req.method === 'POST'
    ) {
      const caseId = decodeURIComponent(segments[2])
      try {
        const result = await loader.rerunCase(caseId)
        sendJson(res, result)
      } catch (error) {
        res.statusCode = 500
        const message = error instanceof Error ? error.message : 'Failed to rerun guided loop'
        sendJson(res, { error: message })
      }
      return
    }

    if (segments.length === 3 && segments[0] === 'api' && segments[1] === 'dataset' && segments[2] === 'refresh' && req.method === 'POST') {
      try {
        await loader.refresh()
        sendJson(res, { status: 'ok' })
      } catch (error) {
        res.statusCode = 500
        const message = error instanceof Error ? error.message : 'Failed to refresh dataset'
        sendJson(res, { error: message })
      }
      return
    }

    res.statusCode = 404
    sendJson(res, { error: 'Route not found' })
  }
}

function sendJson(res: ServerResponse, payload: unknown) {
  const body = JSON.stringify(payload)
  res.statusCode ||= 200
  res.setHeader('Content-Type', 'application/json')
  res.setHeader('Content-Length', Buffer.byteLength(body))
  res.end(body)
}
