/** API Client — unified HTTP/SSE/WS abstraction.

Replaces scattered raw `fetch()` calls across all stores/views.
Provides error interception, base URL management, SSE streaming helper.

Usage:
  import { api } from '@/api/client'
  const data = await api.get('/api/v1/kpi/sop-status')
  await api.post('/api/v1/chat/sessions', { title: 'New Chat' })
  const es = api.streamSSE('/api/v1/chat/sessions/x/stream/y')
*/

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: unknown,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

const isTauri = typeof window !== 'undefined' && '__TAURI__' in window
const BASE = isTauri ? 'http://localhost:8000' : ''

/** Default request timeout (30s). */
const DEFAULT_TIMEOUT_MS = 30_000

export interface RequestOptions {
  signal?: AbortSignal
  timeoutMs?: number
}

class ApiClient {
  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    options?: RequestOptions,
  ): Promise<T> {
    const timeoutMs = options?.timeoutMs ?? DEFAULT_TIMEOUT_MS
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

    // Merge external signal with internal timeout
    const signal = options?.signal
    if (signal) {
      signal.addEventListener('abort', () => controller.abort())
    }

    const opts: RequestInit = {
      method,
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
    }
    if (body && method !== 'GET') {
      opts.body = JSON.stringify(body)
    }

    const url = `${BASE}${path}`
    let res: Response
    try {
      res = await fetch(url, opts)
    } catch (e: unknown) {
      clearTimeout(timeoutId)
      if (e instanceof Error && e.name === 'AbortError') {
        throw new ApiError(408, `Request timeout after ${timeoutMs}ms`, null)
      }
      throw new ApiError(0, `Network error: ${e}`, null)
    }
    clearTimeout(timeoutId)

    if (!res.ok) {
      const text = await res.text().catch(() => '')
      throw new ApiError(res.status, `HTTP ${res.status}: ${text.slice(0, 200)}`, text)
    }

    const ct = res.headers.get('content-type') || ''
    if (ct.includes('application/json')) {
      return res.json() as Promise<T>
    }
    return res.text() as unknown as T
  }

  get<T = unknown>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>('GET', path, undefined, options)
  }

  post<T = unknown>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>('POST', path, body, options)
  }

  put<T = unknown>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>('PUT', path, body, options)
  }

  delete<T = unknown>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>('DELETE', path, undefined, options)
  }

  /** Stream Server-Sent Events. Returns EventSource. Caller must close() it. */
  streamSSE(path: string): EventSource {
    return new EventSource(`${BASE}${path}`)
  }

  /**
   * Stream SSE with automatic reconnection (exponential backoff, max 5 retries).
   * Returns EventSource + cleanup function. Caller calls cleanup() to stop.
   */
  streamSSEWithRetry(
    path: string,
    onMessage: (event: MessageEvent) => void,
    onError?: (err: Event) => void,
    maxRetries = 5,
  ): { close: () => void } {
    let es: EventSource | null = null
    let retries = 0
    let closed = false
    const baseDelay = 1000
    const maxDelay = 30_000

    const connect = () => {
      if (closed) return
      es = new EventSource(`${BASE}${path}`)
      es.onmessage = onMessage
      es.onerror = (ev) => {
        if (closed) { es?.close(); return }
        es?.close()
        if (retries >= maxRetries) {
          onError?.(ev)
          return
        }
        retries++
        const delay = Math.min(baseDelay * Math.pow(2, retries), maxDelay)
        setTimeout(connect, delay)
      }
    }

    connect()
    return {
      close: () => {
        closed = true
        es?.close()
        es = null
      },
    }
  }

  /** Connect WebSocket (relative or absolute URL). */
  connectWS(pathOrUrl: string): WebSocket {
    const url = pathOrUrl.startsWith('ws') ? pathOrUrl : `${location.origin.replace('http', 'ws')}${pathOrUrl}`
    return new WebSocket(url)
  }
}

export const api = new ApiClient()
