import { ref } from 'vue'
import { useKanbanStore } from '@/stores/kanban'

const connected = ref(false)
const lastEvent = ref<any>(null)
let ws: WebSocket | null = null
let reconnectTimer: number | null = null
let pingTimer: number | null = null

const PING_INTERVAL = 30_000  // 30s keepalive — prevent idle timeout

export function useKanbanWS() {
  const store = useKanbanStore()

  function connect() {
    if (ws?.readyState === WebSocket.OPEN) return
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    try {
      ws = new WebSocket(`${protocol}//${location.host}/ws/kanban`)
      ws.onopen = () => {
        connected.value = true
        // Start keepalive pings to prevent proxy/OS idle timeout
        pingTimer = window.setInterval(() => {
          if (ws?.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: 'ping' }))
          }
        }, PING_INTERVAL)
      }
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          lastEvent.value = msg

          // 🆕 Route event types to appropriate handlers
          if (msg.type === 'phase_change') {
            store.onPhaseChange(msg)
          } else if (msg.type === 'card_moved') {
            store.fetchModules()  // Refresh all module data
          }
        } catch {}
      }
      ws.onclose = () => {
        connected.value = false
        if (pingTimer) { clearInterval(pingTimer); pingTimer = null }
        reconnectTimer = window.setTimeout(connect, 3000)
      }
      ws.onerror = () => {
        connected.value = false
        if (pingTimer) { clearInterval(pingTimer); pingTimer = null }
      }
    } catch { connected.value = false }
  }

  function disconnect() {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    if (pingTimer) { clearInterval(pingTimer); pingTimer = null }
    ws?.close()
    ws = null
    connected.value = false
  }

  function sendCardMove(mod: string, from: string, to: string) {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'card_move', module: mod, from_stage: from, to_stage: to }))
    }
  }

  return { connected, lastEvent, connect, disconnect, sendCardMove }
}
