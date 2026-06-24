import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// W06: Filter Vite's internal ws proxy socket ECONNABORTED noise.
// Vite 5.x logs ws proxy socket errors via server.config.logger.error().
// ECONNABORTED is harmless — browser refresh/tab-close during WS activity.
// http-proxy's own error event (configure hook) doesn't intercept Vite's log.
function quietWsProxyLogger() {
  const _info = console.info.bind(console)
  const _warn = console.warn.bind(console)
  const _error = console.error.bind(console)
  return {
    info: _info,
    warn: _warn,
    warnOnce: _warn,
    error(...args: any[]) {
      const msg = args[0]
      if (typeof msg === 'string' && msg.includes('ECONNABORTED')) return
      _error(...args)
    },
    clearScreen: () => {},
    hasErrorLogged: () => false,
    hasWarned: false,
  }
}

export default defineConfig({
  plugins: [vue()],
  customLogger: quietWsProxyLogger(),
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 15173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
