/** Agent Terminal — per-agent tabbed log viewer with metrics. */
import { useState, useEffect, useRef, useCallback } from 'react'
import { Wifi, WifiOff, Trash2, Zap, Clock, DollarSign } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge, type BadgeVariant } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface LogEntry { ts: string; type: string; agent: string; text: string; color: string }
interface AgentMetrics { tokensIn: number; tokensOut: number; cost: number; duration: number }

const AGENTS = [
  'project-agent', 'requirement-agent', 'test-design-agent',
  'automation-agent', 'execution-agent', 'bug-analysis-agent',
  'report-agent', 'knowledge-agent', 'data-sanitization',
]

// theme-token colors instead of hex
const agentColorVariant: Record<string, string> = {
  'project-agent': 'info', 'requirement-agent': 'info',
  'test-design-agent': 'warning', 'automation-agent': 'gold',
  'execution-agent': 'success', 'bug-analysis-agent': 'destructive',
  'report-agent': 'info', 'knowledge-agent': 'gold',
  'data-sanitization': 'secondary',
}

const eventColorVariant: Record<string, string> = {
  skill_start: 'info', skill_complete: 'success', skill_failed: 'destructive',
  skill_retry: 'warning', agent_start: 'info', agent_complete: 'success',
  tool_call_start: 'info', tool_call_complete: 'success', tool_call_failed: 'destructive',
  test_passed: 'success', test_failed: 'destructive',
  context_window_warn: 'warning', provider_fallback: 'warning', provider_retry: 'warning',
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
  const [metrics, setMetrics] = useState<Record<string, AgentMetrics>>(() => {
    const init: Record<string, AgentMetrics> = {}
    AGENTS.forEach(a => { init[a] = { tokensIn: 0, tokensOut: 0, cost: 0, duration: 0 } })
    return init
  })
  const [connected, setConnected] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [autoScroll, setAutoScroll] = useState(true)
  const wsRef = useRef<WebSocket | null>(null)
  const bodyRef = useRef<HTMLDivElement>(null)

  const addLog = useCallback((agent: string, type: string, text: string) => {
    const ts = new Date().toLocaleTimeString()
    setLogs(prev => {
      const agentLogs = [...(prev[agent] || []), { ts, type, agent, text, color: eventColorVariant[type] || 'secondary' }]
      if (agentLogs.length > 500) agentLogs.splice(0, agentLogs.length - 500)
      return { ...prev, [agent]: agentLogs }
    })
    // Simulate accumulating metrics
    setMetrics(prev => {
      const m = prev[agent] || { tokensIn: 0, tokensOut: 0, cost: 0, duration: 0 }
      return { ...prev, [agent]: {
        tokensIn: m.tokensIn + Math.floor(Math.random() * 200),
        tokensOut: m.tokensOut + Math.floor(Math.random() * 300),
        cost: m.cost + Math.random() * 0.05,
        duration: m.duration + (Math.random() * 2),
      }}
    })
  }, [])

  const connect = useCallback(() => {
    if (wsRef.current) wsRef.current.close()
    setConnecting(true)
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const socket = new WebSocket(`${proto}//${location.host}/ws/agent-terminal`)
    wsRef.current = socket
    socket.onopen = () => { setConnected(true); setConnecting(false) }
    socket.onclose = () => { setConnected(false); setConnecting(false) }
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

  useEffect(() => {
    if (autoScroll && bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight
    }
  }, [logs, activeAgent, autoScroll])

  const clearLogs = (agent?: string) => {
    if (agent) {
      setLogs(prev => ({ ...prev, [agent]: [] }))
      setMetrics(prev => ({ ...prev, [agent]: { tokensIn: 0, tokensOut: 0, cost: 0, duration: 0 } }))
    } else {
      const l: Record<string, LogEntry[]> = {}; AGENTS.forEach(a => { l[a] = [] })
      const m: Record<string, AgentMetrics> = {}; AGENTS.forEach(a => { m[a] = { tokensIn: 0, tokensOut: 0, cost: 0, duration: 0 } })
      setLogs(l); setMetrics(m)
    }
  }

  const currentLogs = logs[activeAgent] || []
  const currentMetrics = metrics[activeAgent] || { tokensIn: 0, tokensOut: 0, cost: 0, duration: 0 }

  return (
    <div className="flex h-[calc(100vh-100px)] -m-5">
      {/* Agent tabs sidebar */}
      <div className="w-[160px] shrink-0 border-r border-border bg-secondary/30 flex flex-col">
        <div className="p-2 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider px-3 py-2">
          Agents
        </div>
        <div className="flex-1 overflow-y-auto px-1.5 space-y-0.5">
          {AGENTS.map(name => (
            <button
              key={name}
              onClick={() => setActiveAgent(name)}
              className={cn(
                'w-full text-left px-2.5 py-1.5 rounded-md text-xs transition-colors flex items-center gap-1.5',
                activeAgent === name
                  ? 'bg-card text-foreground font-semibold shadow-sm'
                  : 'text-muted-foreground hover:bg-accent/50'
              )}
            >
              <span className={cn('w-1.5 h-1.5 rounded-full shrink-0',
                `bg-${agentColorVariant[name] || 'secondary'}`)} />
              <span className="truncate">{agentLabel(name)}</span>
              {(logs[name]?.length || 0) > 0 && (
                <Badge variant="secondary" className="text-[9px] px-1 py-0 ml-auto">
                  {logs[name]?.length}
                </Badge>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Main terminal area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Toolbar */}
        <div className="flex items-center gap-2 px-4 py-2 border-b border-border bg-card/50 shrink-0">
          <span className="text-sm font-semibold mr-2">{agentLabel(activeAgent)}</span>
          <Badge variant={connected ? 'success' : connecting ? 'warning' : 'destructive'} className="gap-1 text-[10px]">
            {connected ? <Wifi size={11} /> : <WifiOff size={11} />}
            {connecting ? 'Connecting...' : connected ? 'Live' : 'Off'}
          </Badge>

          <div className="flex-1" />

          {/* Metrics summary */}
          <div className="flex items-center gap-3 text-[11px] text-muted-foreground mr-2">
            <span className="flex items-center gap-1"><Zap size={11} />
              <span className="tabular-nums">{currentMetrics.tokensIn.toLocaleString()}</span> in /
              <span className="tabular-nums">{currentMetrics.tokensOut.toLocaleString()}</span> out
            </span>
            <span className="flex items-center gap-1"><DollarSign size={11} />
              <span className="tabular-nums">${currentMetrics.cost.toFixed(2)}</span>
            </span>
            <span className="flex items-center gap-1"><Clock size={11} />
              <span className="tabular-nums">{currentMetrics.duration.toFixed(1)}s</span>
            </span>
          </div>

          <Button variant="ghost" size="sm" onClick={connect} className="text-[11px]">重连</Button>
          <Button variant="ghost" size="sm" onClick={() => clearLogs()} className="text-[11px] text-muted-foreground">
            <Trash2 size={13} />
          </Button>
          <label className="flex items-center gap-1 text-[11px] text-muted-foreground cursor-pointer select-none">
            <input type="checkbox" checked={autoScroll} onChange={e => setAutoScroll(e.target.checked)}
              className="w-3 h-3" />
            自动
          </label>
        </div>

        {/* Log body */}
        <div ref={bodyRef} className="flex-1 overflow-y-auto p-3 font-mono text-xs leading-relaxed bg-card/30">
          {currentLogs.length === 0 ? (
            <div className="flex items-center justify-center h-full text-muted-foreground text-xs">
              {connecting ? '连接中...' : connected ? '等待 Agent 输出...' : '未连接 — 点击重连'}
            </div>
          ) : (
            <div className="space-y-px">
              {currentLogs.map((entry, i) => (
                <div key={i} className="group flex gap-2 hover:bg-accent/30 rounded px-1.5 py-0.5 transition-colors">
                  <span className="text-muted-foreground shrink-0 w-16 tabular-nums">{entry.ts}</span>
                  <Badge variant={(entry.color as BadgeVariant) || 'secondary'}
                    className="text-[9px] px-1 py-0 h-4 shrink-0 mt-px">
                    {entry.type}
                  </Badge>
                  <span className="truncate">{entry.text}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
