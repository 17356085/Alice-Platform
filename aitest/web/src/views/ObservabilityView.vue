<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Clock, Activity, BarChart3, DollarSign, RefreshCw } from 'lucide-vue-next'

const route = useRoute()
const projectId = computed(() => route.params.id as string)

interface TimelineEntry {
  ts: string
  type: string
  agent: string
  message: string
  duration?: string
  success?: boolean
  phase?: number
}

const timeline = ref<TimelineEntry[]>([])
const metrics = ref<any>(null)
const tab = ref<'timeline' | 'metrics' | 'cost'>('timeline')
const loading = ref(false)

const typeLabels: Record<string, string> = {
  phase_completed: '✅',
  phase_started: '🟢',
  artifact_created: '📄',
  error: '🔴',
  retry: '🔄',
  memory_hit: '🧠',
  warning: '🟡',
  checkpoint: '💾',
}

async function fetchTimeline() {
  loading.value = true
  try {
    // Fetch from operational metrics + recent events
    const resp = await fetch(`http://localhost:8000/api/kpi/operational`)
    if (resp.ok) metrics.value = await resp.json()

    // Build timeline from metrics + kanban module data
    const items: TimelineEntry[] = []

    // Add metrics-derived entries
    if (metrics.value) {
      const m = metrics.value
      if (m.agent_latency_p95) {
        for (const [agent, data] of Object.entries(m.agent_latency_p95)) {
          if ((data as any).total > 0) {
            items.push({
              ts: m.ts || '',
              type: 'phase_completed',
              agent,
              message: `${agent} — ${(data as any).total} runs, p95=${(data as any).p95}s`,
              success: true,
            })
          }
        }
      }
      if (m.workflow) {
        for (const [mod, data] of Object.entries(m.workflow)) {
          const d = data as any
          items.push({
            ts: m.ts || '',
            type: d.rate >= 0.9 ? 'phase_completed' : 'warning',
            agent: 'workflow',
            message: `${mod}: ${d.success}/${d.total} (${Math.round(d.rate * 100)}%)`,
            success: d.rate >= 0.9,
          })
        }
      }
    }
    timeline.value = items
  } catch {
    timeline.value = []
  } finally {
    loading.value = false
  }
}

onMounted(fetchTimeline)
</script>

<template>
  <div class="observability">
    <div class="obs-header">
      <div class="header-left">
        <Activity :size="20" />
        <h1>可观测性 — {{ projectId }}</h1>
      </div>
      <button class="btn-refresh" @click="fetchTimeline" :disabled="loading">
        <RefreshCw :size="14" :class="{ spinning: loading }" /> 刷新
      </button>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button :class="{ active: tab === 'timeline' }" @click="tab = 'timeline'">
        <Clock :size="14" /> 时间线
      </button>
      <button :class="{ active: tab === 'metrics' }" @click="tab = 'metrics'">
        <BarChart3 :size="14" /> 指标
      </button>
      <button :class="{ active: tab === 'cost' }" @click="tab = 'cost'">
        <DollarSign :size="14" /> 成本
      </button>
    </div>

    <!-- Timeline tab -->
    <div v-if="tab === 'timeline'" class="timeline-panel">
      <div v-if="loading && timeline.length === 0" class="muted">加载中...</div>
      <div v-else-if="timeline.length === 0" class="empty">
        <p>暂无活动记录</p>
        <p class="hint">运行 SOP 后将在此显示 Agent 活动时间线</p>
      </div>
      <div v-else class="timeline-list">
        <div
          v-for="(entry, i) in timeline"
          :key="i"
          class="timeline-entry"
          :class="{ error: entry.type === 'error', warning: entry.type === 'warning' }"
        >
          <span class="tl-icon">{{ typeLabels[entry.type] || '•' }}</span>
          <div class="tl-content">
            <div class="tl-header">
              <span class="tl-agent">{{ entry.agent }}</span>
              <span class="tl-time">{{ entry.ts?.slice(11, 19) || '' }}</span>
            </div>
            <div class="tl-message">{{ entry.message }}</div>
            <div v-if="entry.duration" class="tl-meta">耗时: {{ entry.duration }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Metrics tab -->
    <div v-if="tab === 'metrics'" class="metrics-panel">
      <div v-if="!metrics" class="muted">无法获取指标 — 请确认后端已启动</div>
      <div v-else class="metrics-grid">
        <div class="metric-card">
          <div class="metric-label">Agent 延迟 (p95)</div>
          <div class="metric-value" v-for="(v, k) in metrics.agent_latency_p95" :key="k">
            {{ k }}: {{ (v as any).p95 }}s
          </div>
          <div v-if="!metrics.agent_latency_p95 || Object.keys(metrics.agent_latency_p95).length === 0" class="muted">暂无数据</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Workflow 成功率</div>
          <div v-for="(v, k) in metrics.workflow" :key="k" class="metric-row">
            <span>{{ k }}</span>
            <span :class="(v as any).rate >= 0.9 ? 'green' : 'yellow'">{{ Math.round((v as any).rate * 100) }}%</span>
          </div>
          <div v-if="!metrics.workflow || Object.keys(metrics.workflow).length === 0" class="muted">暂无数据</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Memory 命中率</div>
          <div v-for="(v, k) in metrics.memory" :key="k" class="metric-row">
            <span>{{ k }}</span>
            <span>{{ Math.round((v as any).hit_rate * 100) }}%</span>
          </div>
          <div v-if="!metrics.memory || Object.keys(metrics.memory).length === 0" class="muted">暂无数据</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Recovery 成功率</div>
          <div v-for="(v, k) in metrics.recovery" :key="k" class="metric-row">
            <span>{{ k }}</span>
            <span>{{ Math.round((v as any).rate * 100) }}%</span>
          </div>
          <div v-if="!metrics.recovery || Object.keys(metrics.recovery).length === 0" class="muted">暂无数据</div>
        </div>
      </div>
    </div>

    <!-- Cost tab -->
    <div v-if="tab === 'cost'" class="cost-panel">
      <div v-if="!metrics?.token_cost" class="muted">暂无成本数据</div>
      <div v-else class="cost-grid">
        <div v-for="(v, k) in metrics.token_cost" :key="k" class="metric-card">
          <div class="metric-label">{{ k }}</div>
          <div class="metric-row"><span>Input</span><span>{{ (v as any).input?.toLocaleString() }} tokens</span></div>
          <div class="metric-row"><span>Output</span><span>{{ (v as any).output?.toLocaleString() }} tokens</span></div>
          <div class="metric-row"><span>Cost</span><span class="green">${{ (v as any).cost_est?.toFixed(4) }}</span></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.observability { padding: 24px 32px; max-width: 1200px; }
.obs-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.header-left { display: flex; align-items: center; gap: 10px; }
.header-left h1 { font-size: 19px; font-weight: 700; margin: 0; }
.btn-refresh { display: flex; align-items: center; gap: 4px; font-size: 13px; padding: 6px 14px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-primary); cursor: pointer; }
.spinning { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.tabs { display: flex; gap: 2px; margin-bottom: 20px; border-bottom: 1px solid var(--border); }
.tabs button {
  display: flex; align-items: center; gap: 6px; padding: 8px 18px;
  background: none; border: none; border-bottom: 2px solid transparent;
  font-size: 13px; cursor: pointer; color: var(--text-muted);
}
.tabs button.active { color: var(--text-primary); border-bottom-color: var(--accent); }

.timeline-list { display: flex; flex-direction: column; gap: 2px; }
.timeline-entry {
  display: flex; gap: 12px; padding: 10px 14px; border-radius: 8px;
  border-left: 3px solid var(--border); background: var(--bg-primary);
}
.timeline-entry.error { border-left-color: #ef4444; background: #fef2f2; }
.timeline-entry.warning { border-left-color: #eab308; background: #fffef0; }
.tl-icon { font-size: 16px; flex-shrink: 0; }
.tl-content { flex: 1; }
.tl-header { display: flex; justify-content: space-between; margin-bottom: 2px; }
.tl-agent { font-weight: 600; font-size: 13px; }
.tl-time { font-size: 11px; color: var(--text-muted); font-family: monospace; }
.tl-message { font-size: 13px; }
.tl-meta { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

.metrics-grid, .cost-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; }
.metric-card {
  background: var(--bg-primary); border: 1px solid var(--border);
  border-radius: 10px; padding: 16px;
}
.metric-label { font-size: 12px; color: var(--text-muted); margin-bottom: 8px; text-transform: uppercase; letter-spacing: .5px; }
.metric-value { font-size: 15px; font-weight: 600; margin-bottom: 2px; }
.metric-row { display: flex; justify-content: space-between; font-size: 13px; padding: 3px 0; }
.green { color: #22c55e; } .yellow { color: #eab308; }

.empty { text-align: center; padding: 48px 0; color: var(--text-muted); }
.hint { font-size: 13px; margin-top: 8px; }
.muted { color: var(--text-muted); font-size: 13px; padding: 16px 0; }
</style>
