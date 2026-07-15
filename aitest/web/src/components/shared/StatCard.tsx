/** StatCard — 统计卡片组件
 *  用于 Dashboard/Reports/RunInspector 的 KPI 指标展示
 *
 *  视觉规范参考 Figma 设计稿：
 *  - 边框 border-border
 *  - 圆角 rounded-lg
 *  - 内边距 p-4
 *  - 图标与数值同色（根据 tone 参数）
 */
import { cn } from '@/lib/utils'
import type { LucideIcon } from 'lucide-react'

interface StatCardProps {
  /** 标题（大写，小字号灰色） */
  label: string
  /** 主数值（大字号，带色调） */
  value: string
  /** 辅助说明（小字号，灰色） */
  detail: string
  /** Lucide 图标组件 */
  icon: LucideIcon
  /** 语义色调 */
  tone?: 'primary' | 'info' | 'success' | 'warning' | 'destructive' | 'neutral'
  /** 自定义类名 */
  className?: string
  /** 点击回调 */
  onClick?: () => void
}

const toneClasses = {
  primary: 'text-primary',
  info: 'text-info',
  success: 'text-success',
  warning: 'text-warning',
  destructive: 'text-destructive',
  neutral: 'text-foreground',
}

export function StatCard({
  label,
  value,
  detail,
  icon: Icon,
  tone = 'primary',
  className,
  onClick,
}: StatCardProps) {
  const Component = onClick ? 'button' : 'div'

  return (
    <Component
      onClick={onClick}
      className={cn(
        'flex flex-col gap-2 rounded-lg border border-border bg-card p-4 text-left transition-all',
        onClick && 'cursor-pointer hover:border-primary/30 hover:shadow-md',
        className
      )}
    >
      {/* 顶部：标题 + 图标 */}
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          {label}
        </span>
        <Icon size={16} className={cn('shrink-0', toneClasses[tone])} aria-hidden="true" />
      </div>

      {/* 主数值 */}
      <div className={cn('text-2xl font-bold tracking-tight', toneClasses[tone])}>
        {value}
      </div>

      {/* 辅助说明 */}
      <div className="text-xs text-muted-foreground">
        {detail}
      </div>
    </Component>
  )
}
