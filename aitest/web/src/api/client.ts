/** API Client — unified HTTP/SSE/WS abstraction.

Replaces scattered raw `fetch()` calls across all stores/views.
Provides error interception, base URL management, SSE streaming helper.

Usage:
  import { api } from '@/api/client'
  const data = await api.get('/api/sop-status')
  await api.post('/api/chat/sessions', { title: 'New Chat' })
  const es = api.streamSSE('/api/chat/sessions/x/stream/y')
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

const BASE = '' // Same-origin; override for dev proxies

class ApiClient {
  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const opts: RequestInit = {
      method,
      headers: { 'Content-Type': 'application/json' },
    }
    if (body && method !== 'GET') {
      opts.body = JSON.stringify(body)
    }

    const url = `${BASE}${path}`
    let res: Response
    try {
      res = await fetch(url, opts)
    } catch (e) {
      throw new ApiError(0, `Network error: ${e}`, null)
    }

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

  get<T = unknown>(path: string): Promise<T> {
    return this.request<T>('GET', path)
  }

  post<T = unknown>(path: string, body?: unknown): Promise<T> {
    return this.request<T>('POST', path, body)
  }

  put<T = unknown>(path: string, body?: unknown): Promise<T> {
    return this.request<T>('PUT', path, body)
  }

  delete<T = unknown>(path: string): Promise<T> {
    return this.request<T>('DELETE', path)
  }

  /** Stream Server-Sent Events. Returns EventSource. Caller must close() it. */
  streamSSE(path: string): EventSource {
    return new EventSource(`${BASE}${path}`)
  }

  /** Connect WebSocket (relative or absolute URL). */
  connectWS(pathOrUrl: string): WebSocket {
    const url = pathOrUrl.startsWith('ws') ? pathOrUrl : `${location.origin.replace('http', 'ws')}${pathOrUrl}`
    return new WebSocket(url)
  }
}

export const api = new ApiClient()
