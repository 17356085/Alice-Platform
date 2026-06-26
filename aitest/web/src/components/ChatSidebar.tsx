/** Chat session sidebar — React port.
 *  Vue store binding → Zustand selectors.
 */
import { useChatStore } from '@/stores/chat'

export default function ChatSidebar() {
  const sessions = useChatStore(s => s.sessions)
  const activeId = useChatStore(s => s.activeId)
  const newSession = useChatStore(s => s.newSession)
  const deleteSession = useChatStore(s => s.deleteSession)

  return (
    <div className="w-[240px] bg-sidebar border-r border-border flex flex-col flex-shrink-0">
      <div className="p-3 border-b border-white/5">
        <button
          onClick={() => newSession()}
          className="w-full px-3 py-2 text-[13px] bg-primary/20 text-primary rounded-md border-none cursor-pointer font-sans hover:bg-primary/30 transition-colors"
        >
          + New Chat
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {sessions.map(s => (
          <div
            key={s.id}
            className={`group flex items-center gap-2 px-3 py-2 rounded-md text-xs cursor-pointer transition-colors ${
              activeId === s.id
                ? 'bg-primary/15 text-sidebar-active'
                : 'text-sidebar-foreground/70 hover:bg-sidebar-hover hover:text-sidebar-foreground'
            }`}
            onClick={() => useChatStore.setState({ activeId: s.id })}
          >
            <span className="truncate flex-1">{s.name}</span>
            <button
              onClick={e => { e.stopPropagation(); deleteSession(s.id) }}
              className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive cursor-pointer border-none bg-none text-[10px]"
            >
              ✕
            </button>
          </div>
        ))}
        {sessions.length === 0 && (
          <div className="p-4 text-center text-xs text-muted-foreground/50">
            No conversations yet
          </div>
        )}
      </div>
    </div>
  )
}
