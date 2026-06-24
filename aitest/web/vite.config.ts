import { defineConfig, type Plugin } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { readFileSync, writeFileSync } from 'fs'

// v2.5 Stabilization: strip ALL CSS for OOM isolation testing
// Set env: STRIP_CSS=true to remove all CSS from build
function stripCSSPlugin(): Plugin {
  return {
    name: 'strip-css',
    apply: 'build',
    transformIndexHtml: {
      order: 'post',
      handler(html, ctx) {
        if (process.env.STRIP_CSS !== 'true') return html
        // Remove all CSS <link> tags
        html = html.replace(/<link[^>]*\.css[^>]*>/g, '')
        // Remove any <style> tags injected by other plugins
        html = html.replace(/<style>[^<]*<\/style>/g, '')
        return html
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
  plugins: [vue(), stripCSSPlugin()],
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
