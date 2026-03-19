import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/process-invoice': {
        target: 'http://localhost:7860',
        changeOrigin: true,
      },
      '/batch-process': {
        target: 'http://localhost:7860',
        changeOrigin: true,
      },
      '/extract': {
        target: 'http://localhost:7860',
        changeOrigin: true,
      },
      '/extract_batch': {
        target: 'http://localhost:7860',
        changeOrigin: true,
      },
      '/decision-support': {
        target: 'http://localhost:7860',
        changeOrigin: true,
      },
      '/chat': {
        target: 'http://localhost:7860',
        changeOrigin: true,
      },
      '/portfolio': {
        target: 'http://localhost:7860',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:7860',
        changeOrigin: true,
      },
      '/generate-report': {
        target: 'http://localhost:7860',
        changeOrigin: true,
      },
    }
  }
})
