import { ref } from 'vue'

const connected = ref(false)
const lastEvent = ref<any>(null)
let ws: WebSocket | null = null
let reconnectTimer: number | null = null

export function useKanbanWS() {
  function connect() {
    if (ws?.readyState === WebSocket.OPEN) return
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    try {
      ws = new WebSocket(`${protocol}//${location.host}/ws/kanban`)
      ws.onopen = () => { connected.value = true }
      ws.onmessage = (e) => { lastEvent.value = JSON.parse(e.data) }
      ws.onclose = () => {
        connected.value = false
        reconnectTimer = window.setTimeout(connect, 3000)
      }
      ws.onerror = () => { connected.value = false }
    } catch { connected.value = false }
  }

  function disconnect() {
    if (reconnectTimer) clearTimeout(reconnectTimer)
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
