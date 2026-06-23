/** Chat Store — real SSE-backed AI chat.

v3.0: Replaced simulated/mock responses with real SSE stream from backend.
Backend contract:
  POST /api/chat/sessions              → { session_id }
  POST /api/chat/sessions/{id}/messages → { stream_url, message_id }
  GET  /api/chat/sessions/{id}/stream/{mid} → SSE (EventSource)
  GET  /api/chat/sessions/{id}/history    → ChatMessage[]
*/
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api/client'
import { ENDPOINTS } from '@/api/endpoints'
import { useChatSSE } from '@/composables/useChatSSE'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  tools?: { name: string; input: string }[]
  suggestedTasks?: { title: string; description: string; category: string; complexity: string }[]
}

export interface ChatSession {
  id: string
  name: string
  messages: ChatMessage[]
  createdAt: string
  /** Server-side session ID (different from local ID if loaded from server) */
  serverId?: string
}

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<ChatSession[]>(loadSessions())
  const activeId = ref(sessions.value[0]?.id || '')
  const streaming = ref(false)
  const streamContent = ref('')
  const currentTool = ref('')
  const error = ref('')

  const activeSession = computed(() => sessions.value.find(s => s.id === activeId.value))
  const messages = computed(() => activeSession.value?.messages || [])

  // ── Persistence ────────────────────────────────────────────

  function loadSessions(): ChatSession[] {
    try {
      return JSON.parse(localStorage.getItem('tlo-chat-sessions') || '[]')
    } catch { return [] }
  }
  function save() { localStorage.setItem('tlo-chat-sessions', JSON.stringify(sessions.value)) }

  // ── Session management ─────────────────────────────────────

  function newSession() {
    cancelStream() // stop any active stream
    const s: ChatSession = {
      id: Date.now().toString(36),
      name: 'New Chat',
      messages: [],
      createdAt: new Date().toISOString(),
    }
    sessions.value.unshift(s)
    activeId.value = s.id
    save()
  }

  function deleteSession(id: string) {
    if (activeId.value === id) cancelStream()
    sessions.value = sessions.value.filter(s => s.id !== id)
    if (activeId.value === id) activeId.value = sessions.value[0]?.id || ''
    save()
  }

  function renameSession(id: string, name: string) {
    const s = sessions.value.find(s => s.id === id)
    if (s) { s.name = name; save() }
  }

  // ── Messages ───────────────────────────────────────────────

  function addMessage(role: 'user' | 'assistant', content: string, tools?: any[], tasks?: any[]) {
    if (!activeId.value) newSession()
    const s = sessions.value.find(s => s.id === activeId.value)
    if (!s) return
    s.messages.push({
      id: Date.now().toString(36),
      role, content,
      timestamp: new Date().toISOString(),
      tools,
      suggestedTasks: tasks,
    })
    if (role === 'user' && s.messages.length === 1) {
      s.name = content.slice(0, 40)
    }
    save()
  }

  // ── Real SSE streaming (v3.0) ──────────────────────────────

  const { start: _startSSE, cancel: _cancelSSE } = useChatSSE({
    onChunk: (text) => { streamContent.value += text },
    onToolStart: (name) => { currentTool.value = name },
    onToolEnd: () => { currentTool.value = '' },
    onDone: (fullText) => {
      if (fullText) addMessage('assistant', fullText)
      streamContent.value = ''
      streaming.value = false
    },
    onError: (msg) => {
      error.value = msg
      streaming.value = false
      if (streamContent.value) {
        addMessage('assistant', streamContent.value + `\n\n[${msg}]`)
        streamContent.value = ''
      }
    },
  })

  function cancelStream() { _cancelSSE() }

  /** Send message via real backend SSE stream. */
  async function sendMessage(text: string) {
    cancelStream()
    error.value = ''
    addMessage('user', text)
    streaming.value = true
    streamContent.value = ''
    currentTool.value = ''

    try {
      let sid = activeSession.value?.serverId
      if (!sid) {
        const created = await api.post<{ session_id: string }>(ENDPOINTS.CHAT_SESSIONS, { title: text.slice(0, 40) })
        sid = created.session_id
        const s = sessions.value.find(s => s.id === activeId.value)
        if (s) { s.serverId = sid; save() }
      }

      const result = await api.post<{ stream_url: string; message_id: string }>(
        ENDPOINTS.CHAT_MESSAGES(sid), { content: text },
      )
      _startSSE(result.stream_url)
    } catch (e: any) {
      error.value = `Failed to start chat: ${e.message}`
      streaming.value = false
      addMessage('assistant', `[Error] ${e.message}`)
    }
  }

  return {
    sessions, activeId, activeSession, messages,
    streaming, streamContent, currentTool, error,
    newSession, deleteSession, renameSession, sendMessage, cancelStream,
  }
})
