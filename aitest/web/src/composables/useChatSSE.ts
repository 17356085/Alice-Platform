/** SSE stream handler for AI chat responses.

Extracted from chat store per 07-MIGRATION_PLAN.md Week 4 Day 3.
Handles: content streaming, tool call indicators, error recovery, connection lifecycle.

Usage:
  const { start, cancel } = useChatSSE({
    onChunk: (text) => streamContent.value += text,
    onToolStart: (name) => currentTool.value = name,
    onToolEnd: () => currentTool.value = '',
    onDone: (fullText) => { addMessage('assistant', fullText); streaming.value = false },
    onError: (msg) => error.value = msg,
  })
  start(streamUrl)
*/
import { ref } from 'vue'

export interface ChatSSECallbacks {
  onChunk: (text: string) => void
  onToolStart?: (name: string) => void
  onToolEnd?: (name: string) => void
  onContentStart?: () => void
  onContentEnd?: () => void
  onDone: (fullText: string) => void
  onError: (message: string) => void
}

export function useChatSSE(callbacks: ChatSSECallbacks) {
  const streaming = ref(false)
  const error = ref('')
  let _es: EventSource | null = null
  let _accumulated = ''

  function start(streamUrl: string) {
    cancel()
    streaming.value = true
    error.value = ''
    _accumulated = ''

    const es = new EventSource(streamUrl)
    _es = es

    es.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)
        const t = data.type || ''
        if (t === 'content_start') {
          _accumulated = ''
          callbacks.onContentStart?.()
        } else if (t === 'content_chunk' || t === 'text_delta') {
          const text = data.content || data.text || ''
          _accumulated += text
          callbacks.onChunk(text)
        } else if (t === 'content_end') {
          callbacks.onContentEnd?.()
        } else if (t === 'tool_use_start') {
          callbacks.onToolStart?.(data.tool_name || 'Tool')
        } else if (t === 'tool_use_end') {
          callbacks.onToolEnd?.(data.tool_name || '')
        } else if (t === 'done') {
          callbacks.onDone(_accumulated)
          streaming.value = false
          es.close()
          _es = null
        } else if (t === 'error') {
          callbacks.onError(data.error_message || 'Stream error')
          streaming.value = false
          es.close()
          _es = null
        } else if (typeof event.data === 'string') {
          _accumulated += event.data
          callbacks.onChunk(event.data)
        }
      } catch {
        if (typeof event.data === 'string') {
          _accumulated += event.data
          callbacks.onChunk(event.data)
        }
      }
    }

    es.onerror = () => {
      error.value = 'SSE connection lost'
      streaming.value = false
      _es = null
      if (_accumulated) callbacks.onDone(_accumulated)
      else callbacks.onError('SSE connection lost')
    }
  }

  function cancel() {
    if (_es) { _es.close(); _es = null }
    streaming.value = false
    _accumulated = ''
  }

  return { streaming, error, start, cancel }
}
