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
    className: 'bg-success/10 text-success border-success/20',
    dotClass: 'bg-success',
  },
  running: {
    label: 'Running',
    className: 'bg-info/10 text-info border-info/20',
    dotClass: 'bg-info animate-pulse',
  },
  pending: {
    label: 'Pending',
    className: 'bg-warning/10 text-warning border-warning/20',
    dotClass: 'bg-warning',
  },
  failed: {
    label: 'Failed',
    className: 'bg-destructive/10 text-destructive border-destructive/20',
    dotClass: 'bg-destructive',
  },
  error: {
    label: 'Error',
    className: 'bg-destructive/10 text-destructive border-destructive/20',
    dotClass: 'bg-destructive',
  },
  idle: {
    label: 'Idle',
    className: 'bg-muted text-muted-foreground border-border',
    dotClass: 'bg-muted-foreground',
  },
  warning: {
    label: 'Warning',
    className: 'bg-warning/10 text-warning border-warning/20',
    dotClass: 'bg-warning',
  },
  info: {
    label: 'Info',
    className: 'bg-info/10 text-info border-info/20',
    dotClass: 'bg-info',
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
