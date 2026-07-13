/** StatusBadge — 状态徽章组件
 *  统一的状态指示器，用于所有页面的状态展示
 *
 *  视觉规范参考 Figma 设计稿：
 *  - 使用 shadcn Badge 组件
 *  - 根据状态自动配色（success/running/pending/failed/idle）
 *  - 支持带圆点指示器的样式
 */
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import type { VariantProps } from 'class-variance-authority'

type Status = 'success' | 'running' | 'pending' | 'failed' | 'error' | 'idle' | 'warning' | 'info'

interface StatusBadgeProps {
  /** 状态值 */
  status: Status
  /** 显示文本（默认使用状态的首字母大写） */
  label?: string
  /** 是否显示圆点指示器 */
  showDot?: boolean
  /** 自定义类名 */
  className?: string
}

const statusConfig: Record<Status, { label: string; className: string; dotClass: string }> = {
  success: {
    label: 'Success',
    className: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    dotClass: 'bg-emerald-400',
  },
  running: {
    label: 'Running',
    className: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
    dotClass: 'bg-cyan-400 animate-pulse',
  },
  pending: {
    label: 'Pending',
    className: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    dotClass: 'bg-amber-400',
  },
  failed: {
    label: 'Failed',
    className: 'bg-red-500/10 text-red-400 border-red-500/20',
    dotClass: 'bg-red-400',
  },
  error: {
    label: 'Error',
    className: 'bg-red-500/10 text-red-400 border-red-500/20',
    dotClass: 'bg-red-400',
  },
  idle: {
    label: 'Idle',
    className: 'bg-muted text-muted-foreground border-border',
    dotClass: 'bg-muted-foreground',
  },
  warning: {
    label: 'Warning',
    className: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    dotClass: 'bg-amber-400',
  },
  info: {
    label: 'Info',
    className: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    dotClass: 'bg-blue-400',
  },
}

export function StatusBadge({
  status,
  label,
  showDot = false,
  className,
}: StatusBadgeProps) {
  const config = statusConfig[status]
  const displayLabel = label ?? config.label

  return (
    <Badge
      variant="outline"
      className={cn(
        'text-[10px] font-medium',
        config.className,
        showDot && 'flex items-center gap-1.5',
        className
      )}
    >
      {showDot && (
        <span className={cn('h-1.5 w-1.5 rounded-full', config.dotClass)} aria-hidden="true" />
      )}
      {displayLabel}
    </Badge>
  )
}
