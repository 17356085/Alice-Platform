import { defineConfig, type Plugin } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { readFileSync, writeFileSync } from 'fs'

// v2.5 Stabilization: inline CSS into HTML to avoid render-blocking crash
function inlineCSSPlugin(): Plugin {
  let css = ''
  return {
    name: 'inline-css',
    apply: 'build',
    transformIndexHtml: {
      order: 'post',
      handler(html, ctx) {
        // Collect CSS from chunks
        for (const [name, info] of Object.entries(ctx.bundle || {})) {
          if (name.endsWith('.css') && info.type === 'asset') {
            css += (info as any).source + '\n'
          }
        }
        if (!css) return html
        // Replace CSS links with inline style
        return html.replace(/<link[^>]*\.css[^>]*>/g, `<style>${css}</style>`)
      },
    },
  }
}

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
  plugins: [vue(), inlineCSSPlugin()],
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
