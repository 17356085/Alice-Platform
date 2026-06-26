/** Chat Store — Zustand port. Real SSE-backed AI chat.
 *
 * Key differences from Vue original:
 * - No shallowRef/markRaw/triggerRef — Zustand uses plain JS objects.
 * - No effectScope — SSE lifecycle managed via hook callbacks.
 * - SSE integration via module-level singleton (same pattern as useKanbanWS).
 * - Derived values (activeSession, messages) exposed as selectors.
 */
import { create } from 'zustand'
import { api } from '@/api/client'
import { ENDPOINTS } from '@/api/endpoints'

// ── Types ──────────────────────────────────────────────────────

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
  serverId?: string
}

// ── Memory limits ──────────────────────────────────────────────

export const ChatMemory = {
  MAX_SESSIONS: 10,
  MAX_MESSAGES: 100,
  MAX_CONTENT: 20_000,
  MAX_TOOLS: 20,
  MAX_TASKS: 10,
  STORAGE_KEY: 'tlo-chat-sessions',
  EMERGENCY_SESSIONS: 3,
  EMERGENCY_MESSAGES: 50,
  EMERGENCY_CONTENT: 5_000,
} as const

// ── Helpers ────────────────────────────────────────────────────

function makeMessage(role: 'user' | 'assistant', content: string, tools?: any[], tasks?: any[]): ChatMessage {
  const truncated = content.length > ChatMemory.MAX_CONTENT
    ? content.slice(0, ChatMemory.MAX_CONTENT) + '\n\n...\n> ⚠️ Response truncated (exceeded 20KB)'
    : content
  return {
    id: Date.now().toString(36),
    role,
    content: truncated,
    timestamp: new Date().toISOString(),
    tools: tools?.slice(0, ChatMemory.MAX_TOOLS),
    suggestedTasks: tasks?.slice(0, ChatMemory.MAX_TASKS),
  }
}

function makeSession(name?: string): ChatSession {
  return {
    id: Date.now().toString(36),
    name: name || 'New Chat',
    messages: [],
    createdAt: new Date().toISOString(),
  }
}

function loadSessions(): ChatSession[] {
  try {
    const raw = localStorage.getItem(ChatMemory.STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return parsed.slice(0, ChatMemory.MAX_SESSIONS).map((s: ChatSession) => ({
      ...s,
      messages: (s.messages || []).slice(-ChatMemory.MAX_MESSAGES),
    }))
  } catch { return [] }
}

function persist(sessions: ChatSession[]) {
  try {
    localStorage.setItem(ChatMemory.STORAGE_KEY, JSON.stringify(sessions))
  } catch (e) {
    if (e instanceof DOMException && (e.name === 'QuotaExceededError' || e.name === 'NS_ERROR_DOM_QUOTA_REACHED')) {
      const slimmed = sessions.slice(0, ChatMemory.EMERGENCY_SESSIONS).map(s => ({
        ...s,
        messages: s.messages.slice(-ChatMemory.EMERGENCY_MESSAGES).map(m => ({
          id: m.id, role: m.role, timestamp: m.timestamp,
          content: m.content.length > ChatMemory.EMERGENCY_CONTENT
            ? m.content.slice(0, ChatMemory.EMERGENCY_CONTENT) + '\n\n...[trimmed]'
            : m.content,
          tools: [], suggestedTasks: [],
        })),
      }))
      try { localStorage.setItem(ChatMemory.STORAGE_KEY, JSON.stringify(slimmed)) } catch { /* lost */ }
    }
  }
}

// ── SSE module-level singleton ─────────────────────────────────

type SSECallbacks = {
  onChunk: (text: string) => void
  onToolStart: (name: string) => void
  onToolEnd: () => void
  onDone: (fullText: string) => void
  onError: (msg: string) => void
}

let _es: EventSource | null = null
let _accumulated: string[] = []
let _sseCallbacks: SSECallbacks | null = null

function sseStart(streamUrl: string, callbacks: SSECallbacks) {
  sseCancel()
  _sseCallbacks = callbacks
  _accumulated = []

  const es = new EventSource(streamUrl)
  _es = es

  es.onmessage = (event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data)
      const t = data.type || ''
      if (t === 'content_chunk' || t === 'text_delta') {
        const text = data.content || data.text || ''
        _accumulated.push(text)
        callbacks.onChunk(text)
      } else if (t === 'tool_use_start') {
        callbacks.onToolStart(data.tool_name || 'Tool')
      } else if (t === 'tool_use_end') {
        callbacks.onToolEnd()
      } else if (t === 'done') {
        callbacks.onDone(_accumulated.join(''))
        es.close()
        _es = null
      } else if (t === 'error') {
        callbacks.onError(data.error_message || 'Stream error')
        es.close()
        _es = null
      } else if (typeof event.data === 'string') {
        _accumulated.push(event.data)
        callbacks.onChunk(event.data)
      }
    } catch {
      if (typeof event.data === 'string') {
        _accumulated.push(event.data)
        callbacks.onChunk(event.data)
      }
    }
  }

  es.onerror = () => {
    es.close()
    _es = null
    const full = _accumulated.join('')
    if (full) callbacks.onDone(full)
    else callbacks.onError('SSE connection lost')
  }
}

function sseCancel() {
  if (_es) { _es.close(); _es = null }
  _accumulated = []
  _sseCallbacks = null
}

// ── Selectors ──────────────────────────────────────────────────

export const selectActiveSession = (state: ChatState) =>
  state.sessions.find(s => s.id === state.activeId)

export const selectMessages = (state: ChatState) =>
  state.sessions.find(s => s.id === state.activeId)?.messages || []

// ── Store ──────────────────────────────────────────────────────

export interface ChatState {
  sessions: ChatSession[]
  activeId: string
  streaming: boolean
  streamContent: string
  currentTool: string
  error: string

  newSession: () => void
  deleteSession: (id: string) => void
  renameSession: (id: string, name: string) => void
  addMessage: (role: 'user' | 'assistant', content: string, tools?: any[], tasks?: any[]) => void
  sendMessage: (text: string) => Promise<void>
  cancelStream: () => void
}

export const useChatStore = create<ChatState>((set, get) => {
  // SSE callbacks that update store state
  const sseCallbacks: SSECallbacks = {
    onChunk(text) {
      set(state => ({ streamContent: state.streamContent + text }))
    },
    onToolStart(name) {
      set({ currentTool: name })
    },
    onToolEnd() {
      set({ currentTool: '' })
    },
    onDone(fullText) {
      if (fullText) get().addMessage('assistant', fullText)
      set({ streamContent: '', streaming: false })
    },
    onError(msg) {
      set({ error: msg, streaming: false })
      const sc = get().streamContent
      if (sc) {
        get().addMessage('assistant', sc + `\n\n[${msg}]`)
        set({ streamContent: '' })
      }
    },
  }

  return {
    sessions: loadSessions(),
    activeId: '',
    streaming: false,
    streamContent: '',
    currentTool: '',
    error: '',

    newSession() {
      get().cancelStream()
      const s = makeSession()
      set(state => ({
        sessions: [s, ...state.sessions].slice(0, ChatMemory.MAX_SESSIONS),
        activeId: s.id,
      }))
      persist(get().sessions)
    },

    deleteSession(id: string) {
      if (get().activeId === id) get().cancelStream()
      set(state => {
        const sessions = state.sessions.filter(s => s.id !== id)
        return {
          sessions,
          activeId: state.activeId === id ? (sessions[0]?.id || '') : state.activeId,
        }
      })
      persist(get().sessions)
    },

    renameSession(id: string, name: string) {
      set(state => ({
        sessions: state.sessions.map(s => s.id === id ? { ...s, name } : s),
      }))
      persist(get().sessions)
    },

    addMessage(role: 'user' | 'assistant', content: string, tools?: any[], tasks?: any[]) {
      let sid = get().activeId
      if (!sid) {
        get().newSession()
        sid = get().activeId
      }
      set(state => {
        const idx = state.sessions.findIndex(s => s.id === sid)
        if (idx === -1) return state
        const s = state.sessions[idx]
        const msg = makeMessage(role, content, tools, tasks)
        const needsPrune = s.messages.length + 1 > ChatMemory.MAX_MESSAGES
        const isFirstUser = role === 'user' && s.messages.filter(m => m.role === 'user').length === 0
        const updated: ChatSession = {
          ...s,
          messages: needsPrune
            ? [...s.messages, msg].slice(-ChatMemory.MAX_MESSAGES)
            : [...s.messages, msg],
          ...(isFirstUser ? { name: content.slice(0, 40) } : {}),
        }
        return {
          sessions: [
            ...state.sessions.slice(0, idx),
            updated,
            ...state.sessions.slice(idx + 1),
          ],
        }
      })
      persist(get().sessions)
    },

    async sendMessage(text: string) {
      get().cancelStream()
      set({ error: '' })
      get().addMessage('user', text)
      set({ streaming: true, streamContent: '', currentTool: '' })

      try {
        let sid = get().sessions.find(s => s.id === get().activeId)?.serverId
        if (!sid) {
          const created = await api.post<{ session_id: string }>(ENDPOINTS.CHAT_SESSIONS, { title: text.slice(0, 40) })
          sid = created.session_id
          set(state => ({
            sessions: state.sessions.map(s =>
              s.id === get().activeId ? { ...s, serverId: sid } : s
            ),
          }))
          persist(get().sessions)
        }

        const result = await api.post<{ stream_url: string; message_id: string }>(
          ENDPOINTS.CHAT_MESSAGES(sid), { content: text },
        )
        sseStart(result.stream_url, sseCallbacks)
      } catch (e: any) {
        set({ error: `Failed to start chat: ${e.message}`, streaming: false })
        get().addMessage('assistant', `[Error] ${e.message}`)
      }
    },

    cancelStream() {
      sseCancel()
      set({ streaming: false })
    },
  }
})
