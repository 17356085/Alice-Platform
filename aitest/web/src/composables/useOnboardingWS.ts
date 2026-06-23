import { ref, watch, onUnmounted } from 'vue'
import { useOnboardingStore } from '@/stores/onboarding'

/**
 * WebSocket composable for real-time onboarding progress.
 *
 * Usage:
 *   const { connect, disconnect } = useOnboardingWS()
 *   // Auto-connects when session starts
 */
export function useOnboardingWS() {
  const store = useOnboardingStore()
  const ws = ref<WebSocket | null>(null)
  const wsError = ref('')

  let pollTimer: ReturnType<typeof setInterval> | null = null

  function getWsUrl(sessionId: string): string {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${proto}//${location.host}/api/onboarding/ws/${sessionId}`
  }

  function connect() {
    if (!store.sessionId) return

    // Try WebSocket first
    try {
      const socket = new WebSocket(getWsUrl(store.sessionId))
      ws.value = socket

      socket.onopen = () => {
        store.wsConnected = true
        wsError.value = ''
      }

      socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          switch (msg.type) {
            case 'step':
              store.step = msg.step
              store.progress = msg.progress
              break
            case 'menu':
              if (msg.menu_tree?.length) {
                store.menuTree = msg.menu_tree
              }
              break
            case 'page_progress':
              store.currentPage = msg.current
              store.completedPages = msg.completed
              store.totalPages = msg.total
              store.progress = msg.progress
              break
            case 'error':
              store.errors.push(msg.message)
              break
            case 'completed':
              store.step = 'completed'
              store.progress = 1
              store.result = msg.result
              store.isRunning = false
              break
            case 'failed':
              store.step = 'failed'
              store.isRunning = false
              break
            case 'cancelled':
              store.step = 'cancelled'
              store.isRunning = false
              break
          }
        } catch (e) {
          // ignore parse errors
        }
      }

      socket.onerror = () => {
        wsError.value = 'WebSocket connection error — falling back to polling'
        store.wsConnected = false
        startPolling()
      }

      socket.onclose = () => {
        store.wsConnected = false
        if (store.isRunning) {
          // Fall back to polling
          startPolling()
        }
      }
    } catch (e: any) {
      wsError.value = e.message
      startPolling()
    }
  }

  function startPolling() {
    if (pollTimer) return
    pollTimer = setInterval(async () => {
      if (!store.isRunning) {
        stopPolling()
        return
      }
      await store.pollStatus()
    }, 1500) // poll every 1.5s
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  function disconnect() {
    stopPolling()
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
  }

  // Auto-connect when sessionId becomes available
  watch(() => store.sessionId, (newId) => {
    if (newId) {
      connect()
    }
  })

  onUnmounted(() => {
    disconnect()
  })

  return { connect, disconnect, wsError }
}
