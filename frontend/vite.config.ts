import type { ClientRequest } from 'node:http'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, type ProxyOptions } from 'vite'

// Dev: proxy the API + auth + photos to the Django backend (compose service "web").
const BACKEND = 'http://localhost:8000'

// Django enforces CSRF on authenticated POSTs and rejects a cross-origin `Origin`
// header. Through this proxy the browser sends `Origin: localhost:5173`, which
// wouldn't match the backend host → 403. Rewrite it to the backend origin so the
// check passes. Dev-only: in prod Caddy serves SPA + API on one origin.
const proxyToBackend: ProxyOptions = {
  target: BACKEND,
  changeOrigin: true,
  configure: (proxy) => {
    proxy.on('proxyReq', (proxyReq: ClientRequest) => {
      proxyReq.setHeader('origin', BACKEND)
    })
  },
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': proxyToBackend,
      '/accounts': proxyToBackend,
      '/photos': proxyToBackend,
    },
  },
})
