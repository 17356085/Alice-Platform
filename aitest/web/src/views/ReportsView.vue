<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { BarChart3, TrendingUp, DollarSign, Activity, Clock } from 'lucide-vue-next'

const kpi = ref<any>({})
const opMetrics = ref<any>({})
const loading = ref(true)

onMounted(async () => {
  try {
    const [kpiResp, opResp] = await Promise.all([
      fetch('http://localhost:8000/api/kpi/summary?days=30'),
      fetch('http://localhost:8000/api/kpi/operational'),
    ])
    if (kpiResp.ok) kpi.value = await kpiResp.json()
    if (opResp.ok) opMetrics.value = await opResp.json()
  } catch { /* backend offline */ }
  loading.value = false
})

interface AgentMetric { agent: string; total: number; p95: number; avg: number; rate: number }
interface CostMetric { agent: string; input: number; output: number; cost: number }

const agentMetrics = computed<AgentMetric[]>(() => {
  const lat = opMetrics.value?.agent_latency_p95 || {}
  const wf = opMetrics.value?.workflow || {}
  return Object.entries(lat).map(([agent, data]: [string, any]) => ({
    agent,
    total: data.total || 0,
    p95: data.p95 || 0,
    avg: data.avg || 0,
    rate: wf[agent]?.rate || 0,
  }))
})
const costMetrics = computed<CostMetric[]>(() => {
  const tc = opMetrics.value?.token_cost || {}
  return Object.entries(tc).map(([agent, data]: [string, any]) => ({
    agent,
    input: data.input || 0,
    output: data.output || 0,
    cost: data.cost_est || 0,
  }))
})

function pct(val: number): string { return Math.round(val * 100) + '%' }
function age(ts: string): string {
  if (!ts) return ''
  const diff = Date.now() - new Date(ts).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}
</script>

<template>
  <div class="reports">
    <div class="rp-header">
      <BarChart3 :size="20" />
      <h1>报告中心</h1>
    </div>

    <!-- KPI summary cards -->
    <div class="kpi-cards">
      <div class="kpi-card">
        <Activity :size="16" class="kpi-icon" />
        <div class="kpi-value">{{ kpi.state_drift?.audits || 0 }}</div>
        <div class="kpi-label">State Audits (30d)</div>
      </div>
      <div class="kpi-card">
        <BarChart3 :size="16" class="kpi-icon" />
        <div class="kpi-value">{{ kpi.sop_compliance?.audits || 0 }}</div>
        <div class="kpi-label">SOP Audits (30d)</div>
      </div>
      <div class="kpi-card green">
        <div class="kpi-value">{{ ((kpi.sop_compliance?.avg_compliance || 0) * 100).toFixed(0) }}%</div>
        <div class="kpi-label">SOP Compliance</div>
      </div>
      <div class="kpi-card">
        <DollarSign :size="16" class="kpi-icon" />
        <div class="kpi-value">${{ kpi.cost?.avg_cost_per_period?.toFixed(2) || '0.00' }}</div>
        <div class="kpi-label">Avg Cost (30d)</div>
      </div>
    </div>

    <!-- Operational metrics -->
    <div class="section" v-if="opMetrics.agent_latency_p95">
      <h2><TrendingUp :size="14" /> 运行指标</h2>
      <div class="metrics-table">
        <div class="metric-row header">
          <span>Agent</span><span>Runs</span><span>p95</span><span>Avg</span><span>Success</span>
        </div>
        <div v-for="m in agentMetrics" :key="m.agent" class="metric-row">
          <span class="agent-name">{{ m.agent }}</span>
          <span>{{ m.total }}</span>
          <span class="mono">{{ m.p95 }}s</span>
          <span class="mono">{{ m.avg }}s</span>
          <span :class="m.rate >= 0.9 ? 'green' : 'yellow'">{{ m.rate > 0 ? pct(m.rate) : '—' }}</span>
        </div>
      </div>
    </div>

    <!-- Cost breakdown -->
    <div class="section" v-if="opMetrics.token_cost">
      <h2><DollarSign :size="14" /> Token 消耗</h2>
      <div class="cost-grid">
        <div v-for="c in costMetrics" :key="c.agent" class="cost-card">
          <div class="cost-agent">{{ c.agent }}</div>
          <div class="cost-stats">
            <span>In: {{ c.input.toLocaleString() }}</span>
            <span>Out: {{ c.output.toLocaleString() }}</span>
          </div>
          <div class="cost-value">${{ c.cost.toFixed(4) }}</div>
        </div>
      </div>
    </div>

    <!-- Uptime -->
    <div class="section" v-if="opMetrics.uptime_s">
      <h2><Clock :size="14" /> 运行时间</h2>
      <div class="uptime-card">
        <div class="uptime-value">{{ Math.floor(opMetrics.uptime_s / 3600) }}h {{ Math.floor((opMetrics.uptime_s % 3600) / 60) }}m</div>
        <div class="uptime-label">数据始于 {{ age(opMetrics.ts) }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.reports { padding: 24px 32px; max-width: 1100px; }
.rp-header { display: flex; align-items: center; gap: 10px; margin-bottom: 24px; }
.rp-header h1 { font-size: 19px; font-weight: 700; margin: 0; }

.kpi-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 28px; }
.kpi-card {
  background: var(--bg-primary); border: 1px solid var(--border);
  border-radius: 10px; padding: 18px; text-align: center;
}
.kpi-card.green .kpi-value { color: #22c55e; }
.kpi-icon { opacity: .4; margin-bottom: 4px; }
.kpi-value { font-size: 26px; font-weight: 700; }
.kpi-label { font-size: 11px; color: var(--text-muted); margin-top: 4px; }

.section { margin-bottom: 28px; }
.section h2 { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 600; margin-bottom: 14px; }

.metrics-table { display: flex; flex-direction: column; gap: 2px; }
.metric-row { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr; gap: 8px; padding: 8px 12px; font-size: 13px; align-items: center; border-radius: 6px; }
.metric-row.header { font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: .5px; padding: 4px 12px; }
.metric-row:not(.header):nth-child(even) { background: var(--bg-secondary); }
.agent-name { font-weight: 600; }
.mono { font-family: monospace; }
.green { color: #22c55e; }
.yellow { color: #eab308; }

.cost-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; }
.cost-card {
  background: var(--bg-primary); border: 1px solid var(--border);
  border-radius: 10px; padding: 14px;
}
.cost-agent { font-size: 13px; font-weight: 600; margin-bottom: 6px; }
.cost-stats { display: flex; gap: 12px; font-size: 12px; color: var(--text-muted); margin-bottom: 6px; }
.cost-value { font-size: 18px; font-weight: 700; color: #22c55e; }

.uptime-card { background: var(--bg-primary); border: 1px solid var(--border); border-radius: 10px; padding: 20px; text-align: center; }
.uptime-value { font-size: 28px; font-weight: 700; }
.uptime-label { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
</style>
