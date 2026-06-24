<script setup lang="ts">
/** Simple SVG line chart for metrics trending. No dependencies. */
import { computed } from 'vue'

interface Point { ts: string; total_tokens: number; workflow_rate: number; uptime_s: number }

const props = defineProps<{
  points: Point[]
  metric: 'total_tokens' | 'workflow_rate'
  width?: number
  height?: number
}>()

const W = computed(() => props.width || 600)
const H = computed(() => props.height || 160)
const PAD = { top: 16, right: 16, bottom: 24, left: 48 }

const chartW = computed(() => W.value - PAD.left - PAD.right)
const chartH = computed(() => H.value - PAD.top - PAD.bottom)

const values = computed(() => props.points.map(p => p[props.metric] || 0))
const maxVal = computed(() => Math.max(...values.value, 1))
const minVal = computed(() => Math.min(...values.value, 0))

function x(i: number): number {
  if (values.value.length <= 1) return PAD.left + chartW.value / 2
  return PAD.left + (i / (values.value.length - 1)) * chartW.value
}
function y(v: number): number {
  const range = maxVal.value - minVal.value || 1
  return PAD.top + chartH.value - ((v - minVal.value) / range) * chartH.value
}

const pathD = computed(() => {
  if (values.value.length === 0) return ''
  const pts = values.value.map((v, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(1)} ${y(v).toFixed(1)}`)
  return pts.join(' ')
})

const areaD = computed(() => {
  if (values.value.length === 0) return ''
  const line = values.value.map((v, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(1)} ${y(v).toFixed(1)}`)
  const lastX = x(values.value.length - 1)
  const baseY = y(minVal.value)
  const firstX = x(0)
  return `${line.join(' ')} L ${lastX.toFixed(1)} ${baseY.toFixed(1)} L ${firstX.toFixed(1)} ${baseY.toFixed(1)} Z`
})

const yTicks = computed(() => {
  const count = 4
  const ticks: { value: number; y: number; label: string }[] = []
  for (let i = 0; i <= count; i++) {
    const v = minVal.value + (maxVal.value - minVal.value) * (i / count)
    ticks.push({
      value: v,
      y: y(v),
      label: props.metric === 'workflow_rate'
        ? Math.round(v * 100) + '%'
        : v >= 1000 ? (v / 1000).toFixed(1) + 'k' : v.toFixed(0),
    })
  }
  return ticks
})

const label = computed(() => props.metric === 'workflow_rate' ? 'Success Rate' : 'Tokens')
</script>

<template>
  <div class="chart-wrap">
    <svg :viewBox="`0 0 ${W} ${H}`" class="chart-svg">
      <!-- Grid lines -->
      <line v-for="t in yTicks" :key="'g'+t.value"
        :x1="PAD.left" :x2="W - PAD.right" :y1="t.y" :y2="t.y"
        stroke="#e5e7eb" stroke-width="0.5" stroke-dasharray="3 3"
      />
      <!-- Y labels -->
      <text v-for="t in yTicks" :key="'yl'+t.value"
        :x="PAD.left - 6" :y="t.y + 4"
        text-anchor="end" font-size="10" fill="#9ca3af"
      >{{ t.label }}</text>

      <!-- Area fill -->
      <path v-if="values.length > 1" :d="areaD" fill="url(#grad)" opacity="0.15" />
      <defs>
        <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#3b82f6" />
          <stop offset="100%" stop-color="#3b82f6" stop-opacity="0" />
        </linearGradient>
      </defs>

      <!-- Line -->
      <path v-if="values.length > 1" :d="pathD" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />

      <!-- Dots -->
      <circle v-for="(v, i) in values" :key="'d'+i"
        :cx="x(i)" :cy="y(v)" r="3"
        fill="white" stroke="#3b82f6" stroke-width="1.5"
      />

      <!-- X labels (first, last) -->
      <text v-if="points.length > 0"
        :x="x(0)" :y="H - 4" text-anchor="start" font-size="9" fill="#9ca3af"
      >{{ points[0].ts?.slice(5, 16) || '' }}</text>
      <text v-if="points.length > 1"
        :x="x(points.length - 1)" :y="H - 4" text-anchor="end" font-size="9" fill="#9ca3af"
      >{{ points[points.length - 1].ts?.slice(5, 16) || '' }}</text>
    </svg>
    <div class="chart-label">{{ label }}</div>
  </div>
</template>

<style scoped>
.chart-wrap {
  width: 100%; background: var(--bg-primary);
  border: 1px solid var(--border); border-radius: 10px;
  padding: 8px 0 0;
}
.chart-svg { width: 100%; height: auto; display: block; }
.chart-label { text-align: center; font-size: 11px; color: var(--text-muted); padding: 4px 0 8px; }
</style>
