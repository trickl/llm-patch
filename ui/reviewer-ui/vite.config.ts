import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { createDatasetApiHandler } from './src/server/apiHandler'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    {
      name: 'dataset-api',
      configureServer(server) {
        const handler = createDatasetApiHandler()
        server.middlewares.use((req, res, next) => {
          if (req.url?.startsWith('/api/')) {
            handler(req, res)
          } else {
            next()
          }
        })
      },
    },
  ],
})
