<script setup lang="ts">
/** Agent Terminal Panel — per-agent tabbed real-time log viewer.

Connects to /ws/agent-terminal for live ObservationBus events.
Each SOP agent gets its own terminal tab with color-coded event output.
*/
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { Wifi, WifiOff, Trash2, Play } from 'lucide-vue-next'

interface LogEntry {
  ts: string
  type: string
  agent: string
  text: string
  color: string
}

const AGENTS = [
  'project-agent', 'requirement-agent', 'test-design-agent',
  'automation-agent', 'execution-agent', 'bug-analysis-agent',
  'report-agent', 'knowledge-agent', 'data-sanitization',
]

const agentColors: Record<string, string> = {
  'project-agent':     '#6366f1',
  'requirement-agent': '#8b5cf6',
  'test-design-agent': '#ec4899',
  'automation-agent':  '#f59e0b',
  'execution-agent':   '#22c55e',
  'bug-analysis-agent':'#ef4444',
  'report-agent':      '#3b82f6',
  'knowledge-agent':   '#06b6d4',
  'data-sanitization': '#6b7280',
}

const eventColors: Record<string, string> = {
  skill_start:       '#a78bfa',
  skill_complete:    '#22c55e',
  skill_failed:      '#ef4444',
  skill_retry:       '#f59e0b',
  agent_start:       '#60a5fa',
  agent_complete:    '#22c55e',
  tool_call_start:   '#a78bfa',
  tool_call_complete:'#22c55e',
  tool_call_failed:  '#ef4444',
  test_passed:       '#22c55e',
  test_failed:       '#ef4444',
  context_window_warn:'#f59e0b',
  provider_fallback: '#f59e0b',
  provider_retry:    '#f59e0b',
}

const activeAgent = ref(AGENTS[0])
const logs = ref<Record<string, LogEntry[]>>({})
const connected = ref(false)
const autoScroll = ref(true)
let _ws: WebSocket | null = null

// Init empty log arrays
AGENTS.forEach(a => { logs.value[a] = [] })

function addLog(agent: string, type: string, text: string) {
  if (!logs.value[agent]) logs.value[agent] = []
  logs.value[agent].push({
    ts: new Date().toLocaleTimeString(),
    type,
    agent,
    text,
    color: eventColors[type] || '#9ca3af',
  })
  // Keep last 500 entries
  if (logs.value[agent].length > 500) {
    logs.value[agent] = logs.value[agent].slice(-500)
  }
  if (autoScroll.value) nextTick(() => scrollToBottom())
}

function scrollToBottom() {
  const el = document.querySelector('.terminal-body') as HTMLElement | null
  if (el) el.scrollTop = el.scrollHeight
}

function connect() {
  if (_ws) _ws.close()
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  _ws = new WebSocket(`${proto}//${location.host}/ws/agent-terminal`)

  _ws.onopen = () => { connected.value = true }
  _ws.onclose = () => { connected.value = false }
  _ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'pong' || data.type === 'connected') return
      const agent = data.agent || 'unknown'
      const label = data.data?.skill_id || data.data?.tool_name || data.type
      const detail = data.data?.error || data.data?.elapsed || ''
      addLog(agent, data.type, `${label} ${detail ? `(${detail})` : ''}`)
    } catch { /* ignore malformed */ }
  }
  _ws.onerror = () => { connected.value = false }
}

function clearLogs(agent?: string) {
  if (agent) logs.value[agent] = []
  else AGENTS.forEach(a => { logs.value[a] = [] })
}

function agentLabel(name: string) {
  return name.replace('-agent', '').replace('data-sanitization', 'sanitize')
}

const currentLogs = computed(() => logs.value[activeAgent.value] || [])
const agentCounts = computed(() => {
  const counts: Record<string, number> = {}
  AGENTS.forEach(a => { counts[a] = logs.value[a]?.length || 0 })
  return counts
})

onMounted(connect)
onUnmounted(() => { if (_ws) _ws.close() })
</script>

<template>
  <div class="terminal-view">
    <!-- Toolbar -->
    <div class="terminal-toolbar">
      <span class="toolbar-title">Agent 终端</span>
      <div class="toolbar-spacer" />
      <span class="conn-status" :class="{ live: connected }">
        <component :is="connected ? Wifi : WifiOff" :size="14" />
        {{ connected ? 'Live' : 'Disconnected' }}
      </span>
      <button class="toolbar-btn" @click="connect">重连</button>
      <button class="toolbar-btn" @click="clearLogs()" title="清空所有日志">
        <Trash2 :size="14" />
      </button>
      <label class="auto-scroll">
        <input v-model="autoScroll" type="checkbox" />
        自动滚动
      </label>
    </div>

    <div class="terminal-layout">
      <!-- Agent tabs -->
      <div class="agent-tabs">
        <button
          v-for="a in AGENTS" :key="a"
          :class="['agent-tab', { active: activeAgent === a }]"
          :style="activeAgent === a ? { borderLeftColor: agentColors[a] } : {}"
          @click="activeAgent = a"
        >
          <span class="tab-dot" :style="{ background: agentColors[a] }" />
          <span class="tab-label">{{ agentLabel(a) }}</span>
          <span v-if="agentCounts[a]" class="tab-badge">{{ agentCounts[a] }}</span>
        </button>
      </div>

      <!-- Terminal body -->
      <div class="terminal-body">
        <div v-if="!currentLogs.length" class="terminal-empty">
          <Play :size="32" class="empty-icon" />
          <p>等待 Agent 事件...</p>
          <span class="empty-hint">运行 SOP 后此处将显示实时日志</span>
        </div>
        <div v-for="(entry, i) in currentLogs" :key="i" class="log-line">
          <span class="log-time">{{ entry.ts }}</span>
          <span class="log-type" :style="{ color: entry.color }">{{ entry.type }}</span>
          <span class="log-text">{{ entry.text }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.terminal-view { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
.terminal-toolbar {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 16px; border-bottom: 1px solid var(--border);
  background: var(--bg-secondary); flex-shrink: 0;
}
.toolbar-title { font-weight: 700; font-size: 14px; }
.toolbar-spacer { flex: 1; }
.conn-status { display: flex; align-items: center; gap: 4px; font-size: 11px; }
.conn-status.live { color: #22c55e; }
.toolbar-btn {
  padding: 4px 8px; border-radius: 6px; border: 1px solid var(--border);
  background: transparent; cursor: pointer; font-size: 11px; color: var(--text-secondary);
}
.toolbar-btn:hover { background: var(--bg-hover); }
.auto-scroll { display: flex; align-items: center; gap: 4px; font-size: 11px; cursor: pointer; }

.terminal-layout { display: flex; flex: 1; overflow: hidden; }

.agent-tabs {
  display: flex; flex-direction: column; gap: 2px;
  padding: 8px; width: 160px; background: var(--bg-secondary);
  border-right: 1px solid var(--border); overflow-y: auto; flex-shrink: 0;
}
.agent-tab {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; border-radius: 6px; border: none; border-left: 3px solid transparent;
  background: transparent; cursor: pointer; font-size: 12px; color: var(--text-secondary);
  text-align: left; transition: all .1s;
}
.agent-tab:hover { background: var(--bg-hover); }
.agent-tab.active { background: var(--bg-primary); color: var(--text-primary); font-weight: 600; }
.tab-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.tab-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tab-badge {
  font-size: 10px; padding: 1px 6px; border-radius: 8px;
  background: var(--bg-hover); color: var(--text-muted); flex-shrink: 0;
}

.terminal-body {
  flex: 1; overflow-y: auto; padding: 8px 12px;
  font-family: 'Cascadia Code', 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 12px; line-height: 1.6; background: var(--bg-primary);
}
.terminal-empty {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 100%; color: var(--text-muted); gap: 8px;
}
.empty-icon { opacity: .3; }
.empty-hint { font-size: 11px; }

.log-line { display: flex; gap: 10px; padding: 1px 0; white-space: nowrap; }
.log-line:hover { background: var(--bg-secondary); }
.log-time { color: var(--text-muted); min-width: 70px; flex-shrink: 0; }
.log-type { min-width: 120px; flex-shrink: 0; font-weight: 600; }
.log-text { color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; }
</style>
