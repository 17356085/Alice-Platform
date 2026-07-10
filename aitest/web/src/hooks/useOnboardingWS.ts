/** Onboarding WebSocket hook — React port.
 *  Auto-connects when sessionId becomes available, falls back to polling.
 *  Vue watch(sessionId, ...) → useEffect with sessionId dependency.
 *  Vue onUnmounted → useEffect return cleanup.
 */
import { useEffect, useRef, useCallback, useState } from 'react'
import { api } from '@/api/client'
import { useOnboardingStore } from '@/stores/onboarding'

export function useOnboardingWS() {
  const [wsError, setWsError] = useState('')
  const wsRef = useRef<WebSocket | null>(null)
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const sessionId = useOnboardingStore(s => s.sessionId)
  const isRunning = useOnboardingStore(s => s.isRunning)

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current)
      pollTimerRef.current = null
    }
  }, [])

  const startPolling = useCallback(() => {
    if (pollTimerRef.current) return
    pollTimerRef.current = setInterval(async () => {
      const store = useOnboardingStore.getState()
      if (!store.isRunning) {
        stopPolling()
        return
      }
      await store.pollStatus()
    }, 1500)
  }, [stopPolling])

  const connect = useCallback(() => {
    const store = useOnboardingStore.getState()
    if (!store.sessionId) return

    // Close previous socket
    if (wsRef.current) { try { wsRef.current.close() } catch {}; wsRef.current = null }
    stopPolling()

    try {
      const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
      const socket = api.connectWS(`/api/v1/onboarding/ws/${store.sessionId}`)
      wsRef.current = socket

      socket.onopen = () => {
        useOnboardingStore.setState({ wsConnected: true })
        setWsError('')
      }

      socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          const s = useOnboardingStore.getState()
          switch (msg.type) {
            case 'step':
              useOnboardingStore.setState({ step: msg.step, progress: msg.progress })
              break
            case 'menu':
              if (msg.menu_tree?.length) useOnboardingStore.setState({ menuTree: msg.menu_tree })
              break
            case 'page_progress':
              useOnboardingStore.setState({
                currentPage: msg.current, completedPages: msg.completed,
                totalPages: msg.total, progress: msg.progress,
              })
              break
            case 'error':
              if (s.errors.length < 50) {
                useOnboardingStore.setState({ errors: [...s.errors, msg.message] })
              }
              break
            case 'completed':
              useOnboardingStore.setState({
                step: 'completed', progress: 1, result: msg.result, isRunning: false,
              })
              break
            case 'failed':
              useOnboardingStore.setState({ step: 'failed', isRunning: false })
              break
            case 'cancelled':
              useOnboardingStore.setState({ step: 'cancelled', isRunning: false })
              break
          }
        } catch { /* ignore parse errors */ }
      }

      socket.onerror = () => {
        setWsError('WebSocket connection error — falling back to polling')
        useOnboardingStore.setState({ wsConnected: false })
        startPolling()
      }

      socket.onclose = () => {
        useOnboardingStore.setState({ wsConnected: false })
        if (useOnboardingStore.getState().isRunning) startPolling()
      }
    } catch (e: unknown) {
      setWsError(e instanceof Error ? e.message : String(e))
      startPolling()
    }
  }, [stopPolling, startPolling])

  const disconnect = useCallback(() => {
    stopPolling()
    if (wsRef.current) { wsRef.current.close(); wsRef.current = null }
  }, [stopPolling])

  // Auto-connect when sessionId becomes available
  useEffect(() => {
    if (sessionId) connect()
  }, [sessionId, connect])

  // Cleanup on unmount
  useEffect(() => {
    return () => { disconnect() }
  }, [disconnect])

  return { connect, disconnect, wsError }
}
