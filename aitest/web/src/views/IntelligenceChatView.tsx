/** AI Chat view — React port.
 *  Vue ref/nextTick → React useState/useRef + requestAnimationFrame scroll.
 *  Vue onUnmounted → React useEffect cleanup.
 */
import { useState, useRef, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useChatStore, selectMessages } from '@/stores/chat'
import ChatSidebar from '@/components/ChatSidebar'
import ToolIndicator from '@/components/ToolIndicator'
import Markdown from '@/components/Markdown'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'

export default function IntelligenceChatView() {
  const { t } = useTranslation()
  const store = useChatStore
  const streaming = useChatStore(s => s.streaming)
  const streamContent = useChatStore(s => s.streamContent)
  const currentTool = useChatStore(s => s.currentTool)
  const messages = useChatStore(selectMessages)
  const sendMessage = useChatStore(s => s.sendMessage)
  const cancelStream = useChatStore(s => s.cancelStream)

  const [input, setInput] = useState('')
  const [showSidebar, setShowSidebar] = useState(true)
  const chatEl = useRef<HTMLDivElement>(null)

  const suggestions = [
    { icon: '📊', label: t('chat.suggestions.coverage'), q: t('chat.suggestions.coverage_query') },
    { icon: '🐛', label: t('chat.suggestions.bugs'), q: t('chat.suggestions.bugs_query') },
    { icon: '🛡', label: t('chat.suggestions.security'), q: t('chat.suggestions.security_query') },
    { icon: '📋', label: t('chat.suggestions.modules'), q: t('chat.suggestions.modules_query') },
  ]

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      chatEl.current?.scrollTo({ top: chatEl.current.scrollHeight, behavior: 'smooth' })
    })
  }, [])

  // Auto-scroll on messages/streaming change
  useEffect(() => { scrollToBottom() }, [messages.length, streamContent, scrollToBottom])

  // Cancel SSE on unmount
  useEffect(() => {
    return () => { cancelStream() }
  }, [cancelStream])

  async function send() {
    const text = input.trim()
    if (!text || streaming) return
    setInput('')
    await sendMessage(text)
    scrollToBottom()
  }

  function onKeydown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  function selSuggestion(q: string) { setInput(q); /* will send in next tick via useEffect? No — manually call send */ }
  function clickSuggestion(q: string) {
    setInput(q)
    // Need to send after state update. Use setTimeout to ensure input is set.
    setTimeout(async () => {
      if (!useChatStore.getState().streaming) {
        await useChatStore.getState().sendMessage(q)
        scrollToBottom()
      }
    }, 0)
  }

  return (
    <div className="flex h-[calc(100vh-100px)] -m-5">
      {/* Sidebar toggle */}
      <button
        onClick={() => setShowSidebar(!showSidebar)}
        className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-6 h-12 bg-card border border-border rounded-r-md flex items-center justify-center cursor-pointer text-muted-foreground hover:text-foreground transition-colors"
      >
        {showSidebar ? '◀' : '▶'}
      </button>

      {showSidebar && <ChatSidebar />}

      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div ref={chatEl} className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {/* Empty state */}
          {messages.length === 0 && !streaming && (
            <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
              <div className="text-4xl">💬</div>
              <div className="text-lg font-semibold">Test Intelligence Chat</div>
              <div className="text-xs text-muted-foreground max-w-sm">
                Ask questions about your test suite. AI can search TEST_CASES.md, trace logs, and RAG knowledge base.
              </div>
              <div className="grid grid-cols-2 gap-2 mt-4">
                {suggestions.map(s => (
                  <Button
                    key={s.label}
                    variant="outline"
                    size="sm"
                    onClick={() => clickSuggestion(s.q)}
                    className="justify-start gap-2 h-auto py-2 text-xs"
                  >
                    <span>{s.icon}</span> {s.label}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* Messages */}
          {messages.map(m => (
            <div key={m.id} className="space-y-1">
              {/* User */}
              {m.role === 'user' && (
                <div className="flex justify-end">
                  <div className="bg-primary/10 text-foreground rounded-2xl rounded-br-md px-4 py-2.5 max-w-[75%] text-sm">
                    {m.content}
                  </div>
                </div>
              )}

              {/* Assistant */}
              {m.role === 'assistant' && (
                <div className="space-y-2">
                  {/* Tool usage */}
                  {m.tools && m.tools.length > 0 && (
                    <div className="ml-2 space-y-0.5">
                      {m.tools.map((t, i) => (
                        <div key={i} className="flex items-center gap-2 text-[11px] text-muted-foreground/60">
                          <span>{t.name === 'Read' ? '📄' : t.name === 'Grep' ? '🔎' : '📁'}</span>
                          <span className="truncate">{t.input}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="flex justify-start">
                    <div className="bg-card border border-border rounded-2xl rounded-bl-md px-5 py-3 max-w-[85%] text-sm">
                      <Markdown content={m.content} />
                    </div>
                  </div>
                  {/* Suggested tasks */}
                  {m.suggestedTasks && m.suggestedTasks.length > 0 && (
                    <div className="ml-2 space-y-1.5">
                      {m.suggestedTasks.map((t, i) => (
                        <div key={i} className="bg-card border border-primary/30 rounded-lg p-3 max-w-[350px]">
                          <div className="text-[13px] font-semibold">{t.title}</div>
                          <div className="text-[11px] text-muted-foreground mt-0.5">{t.description}</div>
                          <div className="flex gap-1.5 mt-2">
                            {t.category && <Badge variant="info" className="text-[10px]">{t.category}</Badge>}
                            {t.complexity && <span className="text-[10px] text-muted-foreground">{t.complexity}</span>}
                            <Button size="sm" className="ml-auto h-auto py-0.5 px-2.5 text-[11px]">
                              Create Task
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {/* Streaming indicator */}
          {streaming && (
            <div className="space-y-2">
              {currentTool && <ToolIndicator tool={currentTool.split(':')[0]} input={currentTool} />}
              <div className="bg-card border border-border rounded-2xl rounded-bl-md px-5 py-3 max-w-[85%] text-sm">
                <Markdown content={streamContent} /><span className="animate-pulse">▊</span>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-border p-3">
          <div className="flex gap-2">
            <Textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={onKeydown}
              disabled={streaming}
              placeholder="Ask about your test suite..."
              rows={2}
              className="flex-1 resize-none"
            />
            <Button
              onClick={send}
              disabled={streaming || !input.trim()}
              size="icon"
            >
              ↑
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
