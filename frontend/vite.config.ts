import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const CTMS_BACKEND_PORT = process.env.CTMS_BACKEND_PORT || '9200'
const CTMS_FRONTEND_PORT = process.env.CTMS_FRONTEND_PORT || '5281'

export default defineConfig({
  plugins: [react()],
  server: {
    port: parseInt(CTMS_FRONTEND_PORT, 10),
    proxy: {
      '/api': {
        target: `http://localhost:${CTMS_BACKEND_PORT}`,
        changeOrigin: true,
      },
    },
  },
})
