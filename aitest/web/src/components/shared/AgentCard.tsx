/** AgentCard — Agent 信息卡片组件
 *  用于 Dashboard Agent Registry 网格展示
 *
 *  视觉规范参考 Figma 设计稿：
 *  - 边框 border-border
 *  - 圆角 rounded-lg
 *  - 内边距 p-4
 *  - hover 时边框高亮 + 阴影
 *  - 状态徽章（running/success/idle）
 */
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import type { LucideIcon } from 'lucide-react'

export interface Agent {
  name: string
  kind: string
  description: string
  status: 'running' | 'success' | 'idle'
  score?: string
  runs?: string
  tools?: string[]
  icon: LucideIcon
}

interface AgentCardProps {
  agent: Agent
  onClick?: () => void
  className?: string
}

const statusConfig = {
  running: { label: 'Running', className: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' },
  success: { label: 'Success', className: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
  idle: { label: 'Idle', className: 'bg-muted text-muted-foreground border-border' },
}

export function AgentCard({ agent, onClick, className }: AgentCardProps) {
  const Icon = agent.icon
  const statusCfg = statusConfig[agent.status]

  return (
    <button
      onClick={onClick}
      className={cn(
        'flex flex-col gap-3 rounded-lg border border-border bg-card p-4 text-left transition-all',
        'hover:border-primary/30 hover:shadow-md',
        className
      )}
    >
      {/* 顶部：Kind 标签 + 状态徽章 */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Icon size={12} aria-hidden="true" />
          <span>{agent.kind}</span>
        </div>
        <Badge variant="outline" className={cn('text-[10px] font-medium', statusCfg.className)}>
          {statusCfg.label}
        </Badge>
      </div>

      {/* Agent 名称 */}
      <h3 className="text-base font-semibold text-foreground">
        {agent.name}
      </h3>

      {/* 描述 */}
      <p className="text-sm text-muted-foreground line-clamp-2">
        {agent.description}
      </p>

      {/* 元数据：分数 + 运行次数 */}
      {(agent.score || agent.runs) && (
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          {agent.score && (
            <span className="flex items-center gap-1">
              <span className="font-mono font-medium text-foreground">{agent.score}</span>
            </span>
          )}
          {agent.runs && (
            <span className="flex items-center gap-1">
              <span>{agent.runs}</span>
            </span>
          )}
        </div>
      )}

      {/* 工具列表 */}
      {agent.tools && agent.tools.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {agent.tools.map((tool) => (
            <span
              key={tool}
              className="rounded bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground"
            >
              {tool}
            </span>
          ))}
        </div>
      )}
    </button>
  )
}
