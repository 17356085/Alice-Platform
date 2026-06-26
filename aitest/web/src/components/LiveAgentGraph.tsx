/** Live Agent Graph — SVG SOP execution visualization. React port. */
import { useMemo } from 'react'

export interface GraphNode {
  id: string; label: string; phase: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  x: number; y: number
}

interface LiveAgentGraphProps {
  phases: { id: string; label: string; phase: number; status: string }[]
  currentPhase: number
}

const NODE_W = 140, NODE_H = 36, GAP_X = 180, GAP_Y = 52, PAD = 30

function nodeColor(status: string): { fill: string; stroke: string; text: string } {
  switch (status) {
    case 'completed': return { fill: '#dcfce7', stroke: '#22c55e', text: '#166534' }
    case 'running':   return { fill: '#dbeafe', stroke: '#3b82f6', text: '#1e40af' }
    case 'failed':    return { fill: '#fef2f2', stroke: '#ef4444', text: '#991b1b' }
    default:          return { fill: '#f9fafb', stroke: '#d1d5db', text: '#6b7280' }
  }
}

function edgePath(from: GraphNode, to: GraphNode): string {
  const x1 = from.x, y1 = from.y + NODE_H / 2
  const x2 = to.x, y2 = to.y - NODE_H / 2
  const cy = (y1 + y2) / 2
  return `M ${x1} ${y1} C ${x1} ${cy}, ${x2} ${cy}, ${x2} ${y2}`
}

export default function LiveAgentGraph({ phases, currentPhase }: LiveAgentGraphProps) {
  const { nodes, edges, viewBox } = useMemo(() => {
    const nodes: GraphNode[] = [
      { id: 'entry', label: '入口', phase: -1, status: 'completed', x: 0, y: 0 },
    ]
    const agents = phases
    const left = agents.slice(0, 4)
    const right = agents.slice(4, 8)
    left.forEach((a, i) => nodes.push({ id: a.id, label: a.label, phase: a.phase, status: a.status as any, x: -GAP_X / 2, y: GAP_Y * (i + 1) }))
    right.forEach((a, i) => nodes.push({ id: a.id, label: a.label, phase: a.phase, status: a.status as any, x: GAP_X / 2, y: GAP_Y * (i + 1) }))
    nodes.push({ id: 'exit', label: '退出', phase: 9, status: 'pending', x: 0, y: GAP_Y * 5 })

    const edges: { from: string; to: string }[] = []
    const ns = nodes.filter(n => n.phase >= 0 && n.phase <= 8)
    if (ns.length > 0) edges.push({ from: 'entry', to: ns[0].id })
    const leftNs = ns.filter(n => n.x < 0)
    const rightNs = ns.filter(n => n.x > 0)
    for (let i = 0; i < leftNs.length - 1; i++) edges.push({ from: leftNs[i].id, to: leftNs[i + 1].id })
    for (let i = 0; i < rightNs.length - 1; i++) edges.push({ from: rightNs[i].id, to: rightNs[i + 1].id })
    if (leftNs.length > 0) edges.push({ from: leftNs[leftNs.length - 1].id, to: 'exit' })
    if (rightNs.length > 0) edges.push({ from: rightNs[rightNs.length - 1].id, to: 'exit' })

    const xs = nodes.map(n => n.x), ys = nodes.map(n => n.y)
    const minX = Math.min(...xs) - PAD - NODE_W / 2, maxX = Math.max(...xs) + PAD + NODE_W / 2
    const minY = Math.min(...ys) - PAD, maxY = Math.max(...ys) + PAD + NODE_H
    const viewBox = `${minX} ${minY} ${maxX - minX} ${maxY - minY}`

    return { nodes, edges, viewBox }
  }, [phases])

  const nodeMap = useMemo(() => {
    const m = new Map<string, GraphNode>()
    nodes.forEach(n => m.set(n.id, n))
    return m
  }, [nodes])

  return (
    <div className="graph-container">
      <svg viewBox={viewBox} className="graph-svg">
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>
        {edges.map((edge, i) => {
          const f = nodeMap.get(edge.from), t = nodeMap.get(edge.to)
          if (!f || !t) return null
          return <path key={`e${i}`} d={edgePath(f, t)} fill="none" stroke="#d1d5db" strokeWidth={1.5} strokeDasharray="4 3" />
        })}
        {nodes.map(node => {
          const c = nodeColor(node.status)
          return (
            <g key={node.id}>
              <rect x={node.x - NODE_W / 2} y={node.y - NODE_H / 2}
                width={NODE_W} height={NODE_H} rx={8}
                fill={c.fill} stroke={c.stroke}
                strokeWidth={node.status === 'running' ? 2.5 : 1.5}
                filter={node.status === 'running' ? 'url(#glow)' : undefined}
                className="graph-node"
              />
              <text x={node.x} y={node.y + 4} textAnchor="middle" fill={c.text} fontSize={11} fontWeight={600}>
                {node.label}
              </text>
              {node.status === 'completed' && (
                <>
                  <circle cx={node.x + NODE_W / 2 - 12} cy={node.y - NODE_H / 2 + 12} r={7} fill="#22c55e" />
                  <text x={node.x + NODE_W / 2 - 12} y={node.y - NODE_H / 2 + 15} textAnchor="middle" fill="white" fontSize={9} fontWeight="bold">✓</text>
                </>
              )}
              {node.status === 'running' && (
                <text x={node.x + NODE_W / 2 - 12} y={node.y - NODE_H / 2 + 12} textAnchor="middle" fontSize={14}>⏳</text>
              )}
            </g>
          )
        })}
      </svg>
      <style>{`
        .graph-container { width: 100%; min-height: 360px; background: var(--bg-primary); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
        .graph-svg { width: 100%; height: 100%; }
        .graph-node { transition: fill 0.3s, stroke 0.3s; }
      `}</style>
    </div>
  )
}
