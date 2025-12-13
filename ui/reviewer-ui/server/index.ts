import { createServer } from 'node:http'
import path from 'node:path'
import sirv from 'sirv'
import { createDatasetApiHandler } from '../src/server/apiHandler'

const distDir = path.resolve(process.cwd(), 'dist')
const PORT = Number(process.env.PORT ?? 4173)

const apiHandler = createDatasetApiHandler()
const serveStatic = sirv(distDir, { single: true })

const server = createServer((req, res) => {
  if (req.url?.startsWith('/api/')) {
    apiHandler(req, res)
    return
  }
  serveStatic(req, res)
})

server.listen(PORT, () => {
  console.log(`Reviewer UI available at http://localhost:${PORT}`)
})
