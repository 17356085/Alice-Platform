/**
 * AgentStatusBar — Agent运行状态指示器
 * 显示运行中、已完成、失败的Agent数量
 */
import { useTranslation } from 'react-i18next'
import { Activity, CheckCircle, XCircle, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AgentStatusBarProps {
  /** 运行中的Agent数量 */
  running?: number
  /** 已完成的Agent数量 */
  completed?: number
  /** 失败的Agent数量 */
  failed?: number
  /** 等待中的Agent数量 */
  pending?: number
  /** 紧凑模式 - 只显示运行状态 */
  compact?: boolean
}

interface StatusItemProps {
  icon: React.ReactNode
  count: number
  label: string
  colorClass: string
}

function StatusItem({ icon, count, label, colorClass }: StatusItemProps) {
  if (count === 0) return null
  return (
    <div className="flex items-center gap-1.5">
      <span className={cn('flex items-center', colorClass)}>
        {icon}
      </span>
      <span className="text-xs font-medium">{count}</span>
      <span className="text-xs text-muted-foreground hidden sm:inline">{label}</span>
    </div>
  )
}

export default function AgentStatusBar({
  running = 0,
  completed = 0,
  failed = 0,
  pending = 0,
  compact = false,
}: AgentStatusBarProps) {
  const { t } = useTranslation()
  const total = running + completed + failed + pending

  if (compact) {
    // 紧凑模式 - 只显示运行状态
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-success/10 border border-success/20">
        <div className={cn(
          'w-2 h-2 rounded-full',
          running > 0 ? 'bg-success animate-pulse' : 'bg-muted-foreground/40'
        )} />
        <span className="text-xs font-medium text-success">
          {running} {t('agents.running', 'agents running')}
        </span>
      </div>
    )
  }

  // 完整模式 - 显示所有状态
  return (
    <div className="flex items-center gap-4 px-4 py-2 rounded-lg bg-muted/30 border border-border/50">
      <div className="flex items-center gap-2 text-sm font-medium text-foreground">
        <Activity size={14} className="text-primary" />
        <span>{total} {t('agents.total', 'Total')}</span>
      </div>

      <div className="h-4 w-px bg-border" />

      <div className="flex items-center gap-3">
        <StatusItem
          icon={<Activity size={12} className="animate-pulse text-success" />}
          count={running}
          label={t('agents.running', 'Running')}
          colorClass="text-success"
        />
        <StatusItem
          icon={<CheckCircle size={12} className="text-primary" />}
          count={completed}
          label={t('agents.completed', 'Completed')}
          colorClass="text-primary"
        />
        <StatusItem
          icon={<XCircle size={12} className="text-destructive" />}
          count={failed}
          label={t('agents.failed', 'Failed')}
          colorClass="text-destructive"
        />
        <StatusItem
          icon={<Clock size={12} className="text-muted-foreground" />}
          count={pending}
          label={t('agents.pending', 'Pending')}
          colorClass="text-muted-foreground"
        />
      </div>
    </div>
  )
}
