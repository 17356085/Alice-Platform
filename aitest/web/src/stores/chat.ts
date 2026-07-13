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
import { SSE_EVENTS } from '@/api/sse-events'
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

function makeMessage(role: 'user' | 'assistant', content: string, tools?: unknown[], tasks?: unknown[]): ChatMessage {
  const truncated = content.length > ChatMemory.MAX_CONTENT
    ? content.slice(0, ChatMemory.MAX_CONTENT) + '\n\n...\n> ⚠️ Response truncated (exceeded 20KB)'
    : content
  return {
    id: Date.now().toString(36),
    role,
    content: truncated,
    timestamp: new Date().toISOString(),
    tools: (tools?.slice(0, ChatMemory.MAX_TOOLS) as { name: string; input: string }[] | undefined),
    suggestedTasks: (tasks?.slice(0, ChatMemory.MAX_TASKS) as { title: string; description: string; category: string; complexity: string }[] | undefined),
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
  // v3.1: localStorage 作为缓存，快速初始渲染
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
  // v3.1: 写入 localStorage 缓存
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

// v3.1: 从后端同步 sessions（source of truth）
async function syncFromServer(): Promise<ChatSession[]> {
  try {
    const result = await api.get<{ sessions: Array<{ id: string; title: string; messages: unknown[]; created_at: string; updated_at: string }> }>(
      ENDPOINTS.CHAT_SESSIONS + '?limit=20'
    )
    if (!result.sessions?.length) return []
    return result.sessions.map(s => ({
      id: s.id,
      name: s.title || 'Chat',
      messages: Array.isArray(s.messages) ? s.messages as ChatMessage[] : [],
      createdAt: s.created_at,
      serverId: s.id,
    }))
  } catch {
    return [] // 服务端不可用时 fallback 到 localStorage
  }
}

// ── SSE session-scoped stream ──────────────────────────────────
// Module-level singleton by design: only one active stream at a time.
// Guarded by _activeSid → cross-session events silently ignored.
// HMR: Vite dispose handler closes stale EventSource on hot reload.

type SSECallbacks = {
  onChunk: (text: string) => void
  onToolStart: (name: string) => void
  onToolEnd: (data?: Record<string, unknown>) => void
  onThinkingStart: (data: Record<string, unknown>) => void
  onObservation: (data: Record<string, unknown>) => void
  onPhaseChange: (data: Record<string, unknown>) => void
  onDone: (fullText: string) => void
  onError: (msg: string) => void
}

let _es: EventSource | null = null
let _accumulated: string[] = []
let _sseCallbacks: SSECallbacks | null = null
let _activeSid: string | null = null
let _sseTimeout: ReturnType<typeof setTimeout> | null = null

const CHAT_STREAM_TIMEOUT_MS = 30_000

function clearSseTimeout() {
  if (_sseTimeout !== null) {
    clearTimeout(_sseTimeout)
    _sseTimeout = null
  }
}

// HMR safety — Vite hot reload closes stale EventSource
// @ts-ignore — import.meta.hot provided by Vite at build time
if (import.meta?.hot) {
  import.meta.hot.dispose(() => { sseCancel() })
}

function sseStart(sid: string, streamUrl: string, callbacks: SSECallbacks) {
  sseCancel()
  _activeSid = sid
  _sseCallbacks = callbacks
  _accumulated = []

  const es = api.streamSSE(streamUrl)
  _es = es

  _sseTimeout = setTimeout(() => {
    if (!guard()) return
    es.close()
    _es = null; _activeSid = null
    callbacks.onError(`SSE stream timed out after ${CHAT_STREAM_TIMEOUT_MS}ms`)
  }, CHAT_STREAM_TIMEOUT_MS)

  const guard = () => _activeSid === sid

  // Helper: parse SSE event data, call handler
  const listen = (type: string, handler: (data: Record<string, unknown>) => void) => {
    es.addEventListener(type, (e: MessageEvent) => {
      if (!guard()) return
      try {
        handler(JSON.parse(e.data))
      } catch {
        // ignore parse errors
      }
    })
  }

  // ── UI Projection events (ui.*) ──

  listen(SSE_EVENTS.THINKING_STARTED, (data) => {
    callbacks.onThinkingStart(data)
  })

  listen(SSE_EVENTS.THINKING_CHUNK, (data) => {
    const text = (data.content as string) || ''
    if (text) {
      _accumulated.push(text)
      callbacks.onChunk(text)
    }
  })

  listen(SSE_EVENTS.THINKING_ENDED, () => {
    // Thinking phase complete — no-op for now
  })

  listen(SSE_EVENTS.SKILL_STARTED, (data) => {
    callbacks.onToolStart((data.label as string) || (data.skill_id as string) || 'Tool')
  })

  listen(SSE_EVENTS.SKILL_PROGRESS, (data) => {
    // Progress update — could surface in UI later
  })

  listen(SSE_EVENTS.SKILL_ENDED, (data) => {
    callbacks.onToolEnd(data)
  })

  listen(SSE_EVENTS.OBSERVATION, (data) => {
    callbacks.onObservation(data)
  })

  listen(SSE_EVENTS.PHASE_CHANGED, (data) => {
    callbacks.onPhaseChange(data)
  })

  listen(SSE_EVENTS.MESSAGE, (data) => {
    const text = (data.content as string) || ''
    if (text) {
      _accumulated.push(text)
      callbacks.onChunk(text)
    }
  })

  listen(SSE_EVENTS.INTERACTION, (data) => {
    // HITL interaction — handled by interaction endpoint
  })

  listen(SSE_EVENTS.DONE, (data) => {
    callbacks.onDone(_accumulated.join(''))
    clearSseTimeout()
    es.close()
    _es = null; _activeSid = null
  })

  listen(SSE_EVENTS.ERROR, (data) => {
    callbacks.onError((data.message as string) || 'Stream error')
    clearSseTimeout()
    es.close()
    _es = null; _activeSid = null
  })

  // ── Fallback: unnamed events (legacy compatibility) ──
  // v3.1: deprecation warning — this path should not be hit in normal operation
  es.onmessage = (event: MessageEvent) => {
    if (!guard()) return
    try {
      const data = JSON.parse(event.data)
      const t = data.type || ''
      if (t === 'done') {
        console.warn('[SSE] Legacy format detected: data.type="done". Use ui.done event instead.')
        callbacks.onDone(_accumulated.join(''))
        es.close(); _es = null; _activeSid = null
      } else if (t === 'error') {
        console.warn('[SSE] Legacy format detected: data.type="error". Use ui.error event instead.')
        callbacks.onError(data.error_message || 'Stream error')
        es.close(); _es = null; _activeSid = null
      }
    } catch {
      // Raw text fallback
      if (typeof event.data === 'string' && event.data.trim()) {
        _accumulated.push(event.data)
        callbacks.onChunk(event.data)
      }
    }
  }

  es.onerror = () => {
    if (!guard()) { es.close(); return }
    clearSseTimeout()
    es.close()
    _es = null; _activeSid = null
    const full = _accumulated.join('')
    if (full) callbacks.onDone(full)
    else callbacks.onError('SSE connection lost')
  }
}

function sseCancel() {
  clearSseTimeout()
  if (_es) { _es.close(); _es = null }
  _activeSid = null
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
  selectSession: (id: string) => void
  deleteSession: (id: string) => void
  renameSession: (id: string, name: string) => void
  addMessage: (role: 'user' | 'assistant', content: string, tools?: unknown[], tasks?: unknown[]) => void
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
    onThinkingStart(_data) {
      // Could show "analyzing..." indicator in UI
    },
    onObservation(_data) {
      // Could show page observation results in sidebar
    },
    onPhaseChange(_data) {
      // Could show SOP phase progress indicator
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

  // v3.1: 初始化后从后端同步（source of truth）
  // localStorage 作为缓存用于快速渲染，后端数据覆盖本地
  syncFromServer().then(serverSessions => {
    if (serverSessions.length > 0) {
      set({ sessions: serverSessions })
      persist(serverSessions)
    }
  }).catch(() => { /* 服务端不可用，保持 localStorage 缓存 */ })

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

    selectSession(id: string) {
      if (!get().sessions.some(session => session.id === id)) return
      get().cancelStream()
      set({ activeId: id, error: '' })
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

    addMessage(role: 'user' | 'assistant', content: string, tools?: unknown[], tasks?: unknown[]) {
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
        sseStart(sid, result.stream_url, sseCallbacks)
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e)
        set({ error: `Failed to start chat: ${msg}`, streaming: false })
        get().addMessage('assistant', `[Error] ${msg}`)
      }
    },

    cancelStream() {
      sseCancel()
      set({ streaming: false })
    },
  }
})
