<script setup lang="ts">
/** Live Agent Graph — SOP execution state visualization.
 *  SVG-based directed graph. No external dependencies.
 *  Shows phases as nodes, current phase pulsing, completed/failed status.
 */
import { computed } from 'vue'

export interface GraphNode {
  id: string
  label: string
  phase: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  x: number
  y: number
}

export interface GraphEdge {
  from: string
  to: string
}

const props = defineProps<{
  phases: { id: string; label: string; phase: number; status: string }[]
  currentPhase: number
}>()

// Layout: entry at top, then 8 agent nodes in 2 columns, exit at bottom
const NODE_W = 140
const NODE_H = 36
const GAP_X = 180
const GAP_Y = 52
const PAD = 30

const nodes = computed<GraphNode[]>(() => {
  const result: GraphNode[] = [
    { id: 'entry', label: '入口', phase: -1, status: 'completed', x: 0, y: 0 },
  ]

  // 8 agents in 2 columns
  const agents = props.phases
  const left = agents.slice(0, 4)
  const right = agents.slice(4, 8)

  left.forEach((a, i) => {
    result.push({
      id: a.id, label: a.label, phase: a.phase,
      status: (a.status || 'pending') as any,
      x: -GAP_X / 2, y: GAP_Y * (i + 1),
    })
  })
  right.forEach((a, i) => {
    result.push({
      id: a.id, label: a.label, phase: a.phase,
      status: (a.status || 'pending') as any,
      x: GAP_X / 2, y: GAP_Y * (i + 1),
    })
  })

  result.push({ id: 'exit', label: '退出', phase: 9, status: 'pending', x: 0, y: GAP_Y * 5 })
  return result
})

const edges = computed<GraphEdge[]>(() => {
  const e: GraphEdge[] = []
  // entry → first 2 agents
  const ns = nodes.value.filter(n => n.phase >= 0 && n.phase <= 8)
  if (ns.length > 0) {
    e.push({ from: 'entry', to: ns[0].id })
  }
  // chain within each column
  const left = ns.filter(n => n.x < 0)
  const right = ns.filter(n => n.x > 0)
  for (let i = 0; i < left.length - 1; i++) {
    e.push({ from: left[i].id, to: left[i + 1].id })
  }
  for (let i = 0; i < right.length - 1; i++) {
    e.push({ from: right[i].id, to: right[i + 1].id })
  }
  // last nodes → exit
  if (left.length > 0) e.push({ from: left[left.length - 1].id, to: 'exit' })
  if (right.length > 0) e.push({ from: right[right.length - 1].id, to: 'exit' })
  return e
})

const viewBox = computed(() => {
  const xs = nodes.value.map(n => n.x)
  const ys = nodes.value.map(n => n.y)
  const minX = Math.min(...xs) - PAD - NODE_W / 2
  const maxX = Math.max(...xs) + PAD + NODE_W / 2
  const minY = Math.min(...ys) - PAD
  const maxY = Math.max(...ys) + PAD + NODE_H
  return `${minX} ${minY} ${maxX - minX} ${maxY - minY}`
})

function nodeColor(status: string): { fill: string; stroke: string; text: string } {
  switch (status) {
    case 'completed': return { fill: '#dcfce7', stroke: '#22c55e', text: '#166534' }
    case 'running':   return { fill: '#dbeafe', stroke: '#3b82f6', text: '#1e40af' }
    case 'failed':    return { fill: '#fef2f2', stroke: '#ef4444', text: '#991b1b' }
    default:          return { fill: '#f9fafb', stroke: '#d1d5db', text: '#6b7280' }
  }
}

function edgePath(from: GraphNode, to: GraphNode): string {
  const x1 = from.x
  const y1 = from.y + NODE_H / 2
  const x2 = to.x
  const y2 = to.y - NODE_H / 2
  const cy = (y1 + y2) / 2
  return `M ${x1} ${y1} C ${x1} ${cy}, ${x2} ${cy}, ${x2} ${y2}`
}
</script>

<template>
  <div class="graph-container">
    <svg :viewBox="viewBox" class="graph-svg">
      <defs>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      <!-- Edges -->
      <path
        v-for="(edge, i) in edges"
        :key="'e' + i"
        :d="(() => {
          const f = nodes.find(n => n.id === edge.from)
          const t = nodes.find(n => n.id === edge.to)
          return f && t ? edgePath(f, t) : ''
        })()"
        fill="none"
        stroke="#d1d5db"
        stroke-width="1.5"
        stroke-dasharray="4 3"
      />

      <!-- Nodes -->
      <g v-for="node in nodes" :key="node.id">
        <rect
          :x="node.x - NODE_W / 2"
          :y="node.y - NODE_H / 2"
          :width="NODE_W"
          :height="NODE_H"
          :rx="8"
          :fill="nodeColor(node.status).fill"
          :stroke="nodeColor(node.status).stroke"
          :stroke-width="node.status === 'running' ? 2.5 : 1.5"
          :filter="node.status === 'running' ? 'url(#glow)' : undefined"
          class="graph-node"
        />
        <text
          :x="node.x"
          :y="node.y + 4"
          text-anchor="middle"
          :fill="nodeColor(node.status).text"
          font-size="11"
          font-weight="600"
        >
          {{ node.label }}
        </text>
        <!-- Status indicator -->
        <circle
          v-if="node.status === 'completed'"
          :cx="node.x + NODE_W / 2 - 12"
          :cy="node.y - NODE_H / 2 + 12"
          r="7"
          fill="#22c55e"
        />
        <text
          v-if="node.status === 'completed'"
          :x="node.x + NODE_W / 2 - 12"
          :y="node.y - NODE_H / 2 + 15"
          text-anchor="middle"
          fill="white"
          font-size="9"
          font-weight="bold"
        >✓</text>
        <text
          v-if="node.status === 'running'"
          :x="node.x + NODE_W / 2 - 12"
          :y="node.y - NODE_H / 2 + 12"
          text-anchor="middle"
          font-size="14"
        >⏳</text>
      </g>
    </svg>
  </div>
</template>

<style scoped>
.graph-container {
  width: 100%;
  min-height: 360px;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
}
.graph-svg {
  width: 100%;
  height: 100%;
}
.graph-node {
  transition: fill 0.3s, stroke 0.3s;
}
</style>
