/** Kanban WebSocket hook — React port of useKanbanWS composable.
 *
 * Module-level singleton state shared across all consumers.
 * Each consumer gets the same `connected` / `lastEvent` / `connect` / `disconnect` / `sendCardMove`.
 */
import { useSyncExternalStore } from 'react'
import { api } from '@/api/client'
import { useKanbanStore } from '@/stores/kanban'

// ── Module-level state (singleton) ─────────────────────────────

const PING_INTERVAL = 30_000
const MAX_RECONNECT_DELAY = 30_000
const BASE_RECONNECT_DELAY = 1_000
const MAX_RECONNECT_ATTEMPTS = 5

let ws: WebSocket | null = null
let reconnectTimer: number | null = null
let pingTimer: number | null = null
let reconnectAttempts = 0
let manualClose = false  // MEM-AUDIT: prevent reconnect after explicit disconnect()

// Subscribers for React reactivity
const listeners = new Set<() => void>()
let connected = false
let lastEvent: unknown = null

function notify() {
  listeners.forEach(fn => fn())
}

function backoffDelay(): number {
  return Math.min(BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttempts), MAX_RECONNECT_DELAY)
}

// ── Connection logic ───────────────────────────────────────────

function connect() {
  if (ws?.readyState === WebSocket.OPEN) return
  if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
  if (ws) {
    try { ws.close() } catch {}
    ws = null
  }
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  try {
    ws = api.connectWS('/ws/kanban')
    ws.onopen = () => {
      connected = true
      reconnectAttempts = 0
      manualClose = false
      if (pingTimer) { clearInterval(pingTimer); pingTimer = null }
      pingTimer = window.setInterval(() => {
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ action: 'ping' }))
        }
      }, PING_INTERVAL)
      notify()
    }
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        lastEvent = msg
        notify()
        const store = useKanbanStore.getState()
        if (msg.type === 'phase_change') {
          store.onPhaseChange(msg)
        } else if (msg.type === 'card_moved') {
          store.fetchModules()
        }
      } catch {}
    }
    ws.onclose = () => {
      connected = false
      if (pingTimer) { clearInterval(pingTimer); pingTimer = null }
      // MEM-AUDIT: stop reconnecting if manually disconnected or max attempts reached
      if (manualClose) {
        notify()
        return
      }
      if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
        console.warn('[KanbanWS] Max reconnect attempts (%d) reached — giving up', MAX_RECONNECT_ATTEMPTS)
        notify()
        return
      }
      const delay = backoffDelay()
      reconnectAttempts++
      reconnectTimer = window.setTimeout(connect, delay)
      notify()
    }
    ws.onerror = () => {
      connected = false
      if (pingTimer) { clearInterval(pingTimer); pingTimer = null }
      notify()
    }
  } catch {
    connected = false
    notify()
  }
}

function disconnect() {
  manualClose = true  // MEM-AUDIT: prevent reconnect after explicit disconnect
  if (reconnectTimer) clearTimeout(reconnectTimer)
  if (pingTimer) { clearInterval(pingTimer); pingTimer = null }
  ws?.close()
  ws = null
  connected = false
  notify()
}

function sendCardMove(mod: string, from: string, to: string) {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: 'card_move', module: mod, from_stage: from, to_stage: to }))
  }
}

// ── Subscriber (for useSyncExternalStore) ──────────────────────
// CRITICAL: getSnapshot must return referentially stable value.
// Returning a new object every call causes infinite re-render loop.

let cachedSnapshot: { connected: boolean; lastEvent: unknown } = { connected: false, lastEvent: null }

function subscribe(cb: () => void) {
  listeners.add(cb)
  return () => { listeners.delete(cb) }
}

function getSnapshot() {
  if (cachedSnapshot.connected !== connected || cachedSnapshot.lastEvent !== lastEvent) {
    cachedSnapshot = { connected, lastEvent }
  }
  return cachedSnapshot
}

// ── Hook ───────────────────────────────────────────────────────

export function useKanbanWS() {
  const snap = useSyncExternalStore(subscribe, getSnapshot)
  return {
    connected: snap.connected,
    lastEvent: snap.lastEvent,
    connect,
    disconnect,
    sendCardMove,
  }
}

// HMR safety: close WebSocket on hot reload to prevent stale connections
// @ts-ignore — import.meta.hot provided by Vite at build time
if (import.meta?.hot) {
  import.meta.hot.dispose(() => {
    disconnect()
  })
}
