/**
 * Vite config — AITest Web (React 18 + Tailwind 3)
 *
 * P0-1 fix (2026-06-25): cssCodeSplit:true + enhanced manualChunks
 * breaks the single-CSS-file bottleneck that caused production build OOM.
 * React.lazy() already splits views; cssCodeSplit lets each chunk carry its own CSS.
 */
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// Filter Vite's internal ws proxy socket ECONNABORTED noise.
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
  plugins: [react()],
  customLogger: quietWsProxyLogger(),
  build: {
    // P0-1: true (default) → each lazy chunk gets its own CSS
    // was false → merged all CSS into one giant file → OOM
    cssCodeSplit: true,
    target: 'es2022',
    cssMinify: 'esbuild',
    // Raise chunk size warning — lazy chunks with xterm/marked are inherently large
    chunkSizeWarningLimit: 800,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return
          // React ecosystem
          if (id.includes('node_modules/react') ||
              id.includes('node_modules/react-dom') ||
              id.includes('node_modules/react-router') ||
              id.includes('node_modules/scheduler')) return 'vendor-react'
          // State management
          if (id.includes('node_modules/zustand')) return 'vendor-state'
          // Icons — many small components, one chunk
          if (id.includes('node_modules/lucide')) return 'vendor-icons'
          // i18n
          if (id.includes('node_modules/i18next') ||
              id.includes('node_modules/react-i18next')) return 'vendor-i18n'
          // Terminal — xterm is ~500KB, only used in AgentTerminalView
          if (id.includes('node_modules/@xterm')) return 'vendor-xterm'
          // Markdown — marked is ~50KB, used in multiple views
          if (id.includes('node_modules/marked')) return 'vendor-markdown'
          // Zod — schema validation, used in stores
          if (id.includes('node_modules/zod')) return 'vendor-zod'
        },
      },
    },
  },
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
