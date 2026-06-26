/** Agent Terminal — per-agent tabbed real-time log viewer. React port. */
import { useState, useEffect, useRef, useCallback } from 'react'
import { Wifi, WifiOff, Trash2, Play } from 'lucide-react'

interface LogEntry { ts: string; type: string; agent: string; text: string; color: string }

const AGENTS = [
  'project-agent', 'requirement-agent', 'test-design-agent',
  'automation-agent', 'execution-agent', 'bug-analysis-agent',
  'report-agent', 'knowledge-agent', 'data-sanitization',
]

const agentColors: Record<string, string> = {
  'project-agent': '#6366f1', 'requirement-agent': '#8b5cf6',
  'test-design-agent': '#ec4899', 'automation-agent': '#f59e0b',
  'execution-agent': '#22c55e', 'bug-analysis-agent': '#ef4444',
  'report-agent': '#3b82f6', 'knowledge-agent': '#06b6d4',
  'data-sanitization': '#6b7280',
}

const eventColors: Record<string, string> = {
  skill_start: '#a78bfa', skill_complete: '#22c55e', skill_failed: '#ef4444',
  skill_retry: '#f59e0b', agent_start: '#60a5fa', agent_complete: '#22c55e',
  tool_call_start: '#a78bfa', tool_call_complete: '#22c55e', tool_call_failed: '#ef4444',
  test_passed: '#22c55e', test_failed: '#ef4444',
  context_window_warn: '#f59e0b', provider_fallback: '#f59e0b', provider_retry: '#f59e0b',
}

function agentLabel(name: string) {
  return name.replace('-agent', '').replace('data-sanitization', 'sanitize')
}

export default function AgentTerminalView() {
  const [activeAgent, setActiveAgent] = useState(AGENTS[0])
  const [logs, setLogs] = useState<Record<string, LogEntry[]>>(() => {
    const init: Record<string, LogEntry[]> = {}
    AGENTS.forEach(a => { init[a] = [] })
    return init
  })
  const [connected, setConnected] = useState(false)
  const [autoScroll, setAutoScroll] = useState(true)
  const wsRef = useRef<WebSocket | null>(null)
  const bodyRef = useRef<HTMLDivElement>(null)

  const addLog = useCallback((agent: string, type: string, text: string) => {
    setLogs(prev => {
      const entry: LogEntry = {
        ts: new Date().toLocaleTimeString(),
        type, agent, text,
        color: eventColors[type] || '#9ca3af',
      }
      const agentLogs = [...(prev[agent] || []), entry]
      if (agentLogs.length > 500) agentLogs.splice(0, agentLogs.length - 500)
      return { ...prev, [agent]: agentLogs }
    })
  }, [])

  const connect = useCallback(() => {
    if (wsRef.current) wsRef.current.close()
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const socket = new WebSocket(`${proto}//${location.host}/ws/agent-terminal`)
    wsRef.current = socket
    socket.onopen = () => setConnected(true)
    socket.onclose = () => setConnected(false)
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'pong' || data.type === 'connected') return
        const agent = data.agent || 'unknown'
        const label = data.data?.skill_id || data.data?.tool_name || data.type
        const detail = data.data?.error || data.data?.elapsed || ''
        addLog(agent, data.type, `${label} ${detail ? `(${detail})` : ''}`)
      } catch { /* ignore */ }
    }
    socket.onerror = () => setConnected(false)
  }, [addLog])

  useEffect(() => { connect(); return () => { wsRef.current?.close() } }, [connect])

  // Auto-scroll
  useEffect(() => {
    if (autoScroll && bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight
    }
  }, [logs, activeAgent, autoScroll])

  const clearLogs = (agent?: string) => {
    if (agent) setLogs(prev => ({ ...prev, [agent]: [] }))
    else setLogs(() => { const l: Record<string, LogEntry[]> = {}; AGENTS.forEach(a => { l[a] = [] }); return l })
  }

  const currentLogs = logs[activeAgent] || []
  const agentCounts: Record<string, number> = {}
  AGENTS.forEach(a => { agentCounts[a] = logs[a]?.length || 0 })

  return (
    <div className="terminal-view">
      <div className="terminal-toolbar">
        <span className="toolbar-title">Agent 终端</span>
        <div className="toolbar-spacer" />
        <span className={`conn-status ${connected ? 'live' : ''}`}>
          {connected ? <Wifi size={14} /> : <WifiOff size={14} />}
          {connected ? 'Live' : 'Disconnected'}
        </span>
        <button className="toolbar-btn" onClick={connect}>重连</button>
        <button className="toolbar-btn" onClick={() => clearLogs()} title="清空所有日志">
          <Trash2 size={14} />
        </button>
        <label className="auto-scroll">
          <input type="checkbox" checked={autoScroll} onChange={e => setAutoScroll(e.target.checked)} />
          自动滚动
        </label>
      </div>
      <div className="terminal-layout">
        <div className="agent-tabs">
          {AGENTS.map(a => (
            <button
              key={a}
              className={`agent-tab ${activeAgent === a ? 'active' : ''}`}
              style={activeAgent === a ? { borderLeftColor: agentColors[a] } : {}}
              onClick={() => setActiveAgent(a)}
            >
              <span className="tab-dot" style={{ background: agentColors[a] }} />
              <span className="tab-label">{agentLabel(a)}</span>
              {agentCounts[a] > 0 && <span className="tab-badge">{agentCounts[a]}</span>}
            </button>
          ))}
        </div>
        <div className="terminal-body" ref={bodyRef}>
          {!currentLogs.length && (
            <div className="terminal-empty">
              <Play size={32} className="empty-icon" />
              <p>等待 Agent 事件...</p>
              <span className="empty-hint">运行 SOP 后此处将显示实时日志</span>
            </div>
          )}
          {currentLogs.map((entry, i) => (
            <div key={i} className="log-line">
              <span className="log-time">{entry.ts}</span>
              <span className="log-type" style={{ color: entry.color }}>{entry.type}</span>
              <span className="log-text">{entry.text}</span>
            </div>
          ))}
        </div>
      </div>
      <style>{`
        .terminal-view { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
        .terminal-toolbar { display: flex; align-items: center; gap: 12px; padding: 10px 16px; border-bottom: 1px solid var(--border); background: var(--bg-secondary); flex-shrink: 0; }
        .toolbar-title { font-weight: 700; font-size: 14px; }
        .toolbar-spacer { flex: 1; }
        .conn-status { display: flex; align-items: center; gap: 4px; font-size: 11px; }
        .conn-status.live { color: #22c55e; }
        .toolbar-btn { padding: 4px 8px; border-radius: 6px; border: 1px solid var(--border); background: transparent; cursor: pointer; font-size: 11px; color: var(--text-secondary); }
        .toolbar-btn:hover { background: var(--bg-hover); }
        .auto-scroll { display: flex; align-items: center; gap: 4px; font-size: 11px; cursor: pointer; }
        .terminal-layout { display: flex; flex: 1; overflow: hidden; }
        .agent-tabs { display: flex; flex-direction: column; gap: 2px; padding: 8px; width: 160px; background: var(--bg-secondary); border-right: 1px solid var(--border); overflow-y: auto; flex-shrink: 0; }
        .agent-tab { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border-radius: 6px; border: none; border-left: 3px solid transparent; background: transparent; cursor: pointer; font-size: 12px; color: var(--text-secondary); text-align: left; transition: all .1s; }
        .agent-tab:hover { background: var(--bg-hover); }
        .agent-tab.active { background: var(--bg-primary); color: var(--text-primary); font-weight: 600; }
        .tab-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
        .tab-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .tab-badge { font-size: 10px; padding: 1px 6px; border-radius: 8px; background: var(--bg-hover); color: var(--text-muted); flex-shrink: 0; }
        .terminal-body { flex: 1; overflow-y: auto; padding: 8px 12px; font-family: 'Cascadia Code', 'JetBrains Mono', 'Fira Code', 'Consolas', monospace; font-size: 12px; line-height: 1.6; background: var(--bg-primary); }
        .terminal-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: var(--text-muted); gap: 8px; }
        .empty-icon { opacity: .3; }
        .empty-hint { font-size: 11px; }
        .log-line { display: flex; gap: 10px; padding: 1px 0; white-space: nowrap; }
        .log-line:hover { background: var(--bg-secondary); }
        .log-time { color: var(--text-muted); min-width: 70px; flex-shrink: 0; }
        .log-type { min-width: 120px; flex-shrink: 0; font-weight: 600; }
        .log-text { color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; }
      `}</style>
    </div>
  )
}
