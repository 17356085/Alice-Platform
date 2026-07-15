/** Knowledge Graph — SVG force-directed visualization of Agent memory nodes. */
import { useMemo } from 'react'
import { Network, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { PageHeader } from '@/components/shared'

interface GraphNode {
  id: string; label: string; group: string; x: number; y: number; r: number
}
interface GraphEdge { from: string; to: string }

// Simulated knowledge graph data — modules + known issues + locator patterns
const NODES: GraphNode[] = [
  { id: 'equipment', label: 'Equipment', group: 'module', x: 400, y: 50, r: 28 },
  { id: 'personnel', label: 'Personnel', group: 'module', x: 200, y: 180, r: 22 },
  { id: 'system', label: 'System Mgmt', group: 'module', x: 600, y: 180, r: 24 },
  { id: 'contractor', label: 'Contractor', group: 'module', x: 100, y: 320, r: 20 },
  { id: 'production', label: 'Production', group: 'module', x: 700, y: 320, r: 20 },

  { id: 'el-dialog', label: 'el-dialog', group: 'issue', x: 350, y: 200, r: 16 },
  { id: 'el-table', label: 'el-table', group: 'issue', x: 500, y: 200, r: 16 },
  { id: 'el-cascader', label: 'el-cascader', group: 'issue', x: 250, y: 300, r: 14 },
  { id: 'teleport', label: 'append-to-body', group: 'issue', x: 450, y: 280, r: 14 },
  { id: 'lazy-render', label: 'lazy-render', group: 'issue', x: 550, y: 300, r: 12 },

  { id: 'css-selector', label: 'CSS Selector', group: 'pattern', x: 300, y: 100, r: 14 },
  { id: 'xpath', label: 'XPath', group: 'pattern', x: 500, y: 100, r: 14 },
  { id: 'wait-visible', label: 'wait_visible', group: 'pattern', x: 380, y: 150, r: 12 },
  { id: 'data-testid', label: 'data-testid', group: 'pattern', x: 480, y: 150, r: 12 },
]

const EDGES: GraphEdge[] = [
  { from: 'equipment', to: 'el-dialog' }, { from: 'equipment', to: 'el-table' },
  { from: 'system', to: 'el-table' }, { from: 'system', to: 'el-cascader' },
  { from: 'personnel', to: 'el-cascader' }, { from: 'equipment', to: 'teleport' },
  { from: 'contractor', to: 'lazy-render' }, { from: 'production', to: 'el-table' },
  { from: 'el-table', to: 'lazy-render' },
  { from: 'css-selector', to: 'el-dialog' }, { from: 'xpath', to: 'el-table' },
  { from: 'wait-visible', to: 'el-table' }, { from: 'data-testid', to: 'el-cascader' },
  { from: 'el-dialog', to: 'teleport' }, { from: 'css-selector', to: 'data-testid' },
]

const GROUP_COLORS: Record<string, string> = {
  module: 'hsl(var(--primary))', issue: 'hsl(var(--destructive))', pattern: 'hsl(var(--success))',
}

export default function KnowledgeGraphView() {
  const edges = useMemo(() => EDGES.map(e => {
    const f = NODES.find(n => n.id === e.from)!
    const t = NODES.find(n => n.id === e.to)!
    return { from: f, to: t }
  }), [])

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-5 p-4 sm:p-6">
      <PageHeader title="知识图谱" description="查看模块、已知问题与定位器模式之间的关联。" actions={<div className="flex items-center gap-2">
          <div className="hidden gap-2 mr-4 sm:flex">
            {Object.entries(GROUP_COLORS).map(([k, c]) => (
              <div key={k} className="flex items-center gap-1 text-[10px] text-muted-foreground">
                <span className="w-2 h-2 rounded-full" style={{ background: c }} />
                {k}
              </div>
            ))}
          </div>
          <Button variant="outline" size="icon" aria-label="放大">
            <ZoomIn />
          </Button>
          <Button variant="outline" size="icon" aria-label="缩小">
            <ZoomOut />
          </Button>
          <Button variant="outline" size="sm" className="gap-1"><RotateCcw data-icon="inline-start" />重置
          </Button>
        </div>} />

      <Card className="overflow-hidden">
        <CardContent className="p-0">
          <svg viewBox="0 0 800 400" className="h-[360px] w-full bg-card sm:h-[500px]">
            {/* Edge lines */}
            {edges.map((e, i) => (
              <line key={i} x1={e.from.x} y1={e.from.y} x2={e.to.x} y2={e.to.y}
                stroke="hsl(var(--border))" strokeWidth={1} strokeOpacity={0.6} />
            ))}

            {/* Nodes */}
            {NODES.map(node => (
              <g key={node.id} className="cursor-pointer">
                {/* Glow circle */}
                <circle cx={node.x} cy={node.y} r={node.r + 6}
                  fill={GROUP_COLORS[node.group]} opacity={0.06} />
                {/* Main circle */}
                <circle cx={node.x} cy={node.y} r={node.r}
                  fill={GROUP_COLORS[node.group]} opacity={0.15}
                  stroke={GROUP_COLORS[node.group]} strokeWidth={1.5} strokeOpacity={0.6} />
                {/* Label */}
                <text x={node.x} y={node.y + node.r + 14}
                  textAnchor="middle" fontSize={10}
                  fill="hsl(var(--muted-foreground))" fontFamily="Inter, sans-serif"
                  fontWeight={node.group === 'module' ? 600 : 400}>
                  {node.label}
                </text>
              </g>
            ))}
          </svg>
        </CardContent>
      </Card>

      {/* Legend card */}
      <div className="grid gap-3 sm:grid-cols-3">
        <Card className="p-3 text-center">
          <div className="text-xs text-muted-foreground mb-1">模块节点</div>
          <div className="text-sm font-semibold">{NODES.filter(n => n.group === 'module').length}</div>
        </Card>
        <Card className="p-3 text-center">
          <div className="text-xs text-muted-foreground mb-1">已知问题</div>
          <div className="text-sm font-semibold text-destructive">{NODES.filter(n => n.group === 'issue').length}</div>
        </Card>
        <Card className="p-3 text-center">
          <div className="text-xs text-muted-foreground mb-1">定位器模式</div>
          <div className="text-sm font-semibold text-success">{NODES.filter(n => n.group === 'pattern').length}</div>
        </Card>
      </div>
    </div>
  )
}
