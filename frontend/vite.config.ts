import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { loadEnv } from 'vite'
import { defineConfig } from 'vitest/config'

const DEFAULT_API_PROXY_TARGET = 'http://localhost:8000'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  return {
    plugins: [react(), tailwindcss()],
    server: {
      proxy: {
        '/api': {
          target: env.VITE_API_PROXY_TARGET || DEFAULT_API_PROXY_TARGET,
          changeOrigin: true,
        },
      },
    },
    test: { environment: 'jsdom', setupFiles: ['./src/test/setup.ts'] },
  }
})
