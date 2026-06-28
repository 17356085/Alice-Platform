/** xterm.js Terminal panel — React port.
 *  Vue onMounted/onUnmounted → React useEffect with useRef for DOM mounting.
 *  key: useRef for container, Terminal instance in ref, cleanup on unmount.
 */
import { useEffect, useRef, useState, useCallback } from 'react'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebLinksAddon } from '@xterm/addon-web-links'
import '@xterm/xterm/css/xterm.css'

interface TerminalPanelProps {
  wsUrl?: string
  autoConnect?: boolean
}

const MAX_RECONNECT_DELAY = 30_000
const BASE_RECONNECT_DELAY = 1_000
const MAX_RECONNECT_ATTEMPTS = 5

export default function TerminalPanel({ wsUrl, autoConnect = true }: TerminalPanelProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const termRef = useRef<Terminal | null>(null)
  const fitRef = useRef<FitAddon | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<number | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const [connected, setConnected] = useState(false)

  const clear = useCallback(() => {
    const term = termRef.current
    if (term) { term.clear(); term.writeln('\x1b[1;34m  Cleared\x1b[0m\n') }
  }, [])

  const connect = useCallback(() => {
    if (!wsUrl) return
    const ws = wsRef.current
    if (ws) { try { ws.close() } catch {}; wsRef.current = null }
    if (reconnectTimerRef.current) { clearTimeout(reconnectTimerRef.current); reconnectTimerRef.current = null }

    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const socket = new WebSocket(`${protocol}//${location.host}${wsUrl}`)
    wsRef.current = socket
    const term = termRef.current!

    socket.onopen = () => {
      setConnected(true)
      reconnectAttemptsRef.current = 0
      term.writeln('\x1b[32m  ✅ WebSocket connected\x1b[0m')
    }
    socket.onclose = () => {
      setConnected(false)
      // MEM-AUDIT: stop retrying after max attempts
      if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
        term.writeln(`\x1b[31m  ❌ Disconnected — giving up after ${MAX_RECONNECT_ATTEMPTS} retries\x1b[0m`)
        return
      }
      term.writeln('\x1b[31m  ❌ Disconnected — retrying...\x1b[0m')
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current)
      const delay = Math.min(BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttemptsRef.current), MAX_RECONNECT_DELAY)
      reconnectAttemptsRef.current++
      reconnectTimerRef.current = window.setTimeout(connect, delay)
    }
    socket.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        const ts = msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : ''
        switch (msg.type) {
          case 'card_moved':
            term.writeln(`\x1b[36m[${ts}]\x1b[0m \x1b[33m${msg.module}\x1b[0m: ${msg.from_stage} → \x1b[32m${msg.to_stage}\x1b[0m`)
            break
          case 'connected':
            term.writeln(`\x1b[2m[${ts}]\x1b[0m \x1b[2m${msg.connections} client(s) connected\x1b[0m`)
            break
          default:
            term.writeln(`\x1b[2m[${ts}]\x1b[0m ${JSON.stringify(msg).slice(0, 200)}`)
        }
      } catch {
        term.writeln(`\x1b[2m[raw]\x1b[0m ${e.data.slice(0, 300)}`)
      }
    }
  }, [wsUrl])

  // Mount terminal
  useEffect(() => {
    const term = new Terminal({
      fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
      fontSize: 13,
      theme: {
        background: '#0b0b0f', foreground: '#e6e6e6', cursor: '#5b7fff', selectionBackground: '#1e2040',
        black: '#1a1a1f', red: '#ff5c5c', green: '#4ebe96',
        yellow: '#d2d714', blue: '#818cf8', magenta: '#d946ef',
        cyan: '#479ffa', white: '#e6e6e6',
        brightBlack: '#868f97', brightRed: '#ff8080', brightGreen: '#6ee7b7',
        brightYellow: '#f0f000', brightBlue: '#a5b4fc', brightMagenta: '#e879f9',
        brightCyan: '#67e8f9', brightWhite: '#ffffff',
      },
      cursorBlink: true,
      allowProposedApi: true,
      rows: 20,
    })

    const fit = new FitAddon()
    term.loadAddon(fit)
    term.loadAddon(new WebLinksAddon())

    if (containerRef.current) {
      term.open(containerRef.current)
      fit.fit()
    }

    termRef.current = term
    fitRef.current = fit

    if (autoConnect !== false && wsUrl) connect()
    term.writeln('\x1b[1;34m  TLO Terminal — Ready\x1b[0m')
    term.writeln('  Type \x1b[33maitest sop run\x1b[0m to start...\n')

    return () => {
      if (reconnectTimerRef.current) { clearTimeout(reconnectTimerRef.current); reconnectTimerRef.current = null }
      if (wsRef.current) { try { wsRef.current.close() } catch {}; wsRef.current = null }
      term.dispose()
    }
  }, []) // mount only

  return (
    <div className="card rounded-lg border border-border overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-sidebar border-b border-border">
        <div className="flex items-center gap-2 text-xs">
          <span className={`w-2 h-2 rounded-full ${connected ? 'bg-success' : 'bg-destructive'}`} />
          <span className="text-white font-semibold">Terminal</span>
        </div>
        <div className="flex gap-2">
          <button onClick={clear} className="text-xs text-muted-foreground hover:text-white cursor-pointer border-none bg-none font-mono">clear</button>
          <button onClick={connect} className="text-xs text-muted-foreground hover:text-white cursor-pointer border-none bg-none font-mono">reconnect</button>
        </div>
      </div>
      <div ref={containerRef} className="h-[360px]" />
    </div>
  )
}
