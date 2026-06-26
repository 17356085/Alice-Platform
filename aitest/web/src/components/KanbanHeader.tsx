/** Header bar — view title + icon + subtitle + WS indicator + extra slot.
 *  React port: <slot name="extra"> → extra prop (React Node).
 */
import type { ReactNode } from 'react'
import { Wifi, WifiOff, type LucideIcon } from 'lucide-react'
import { useKanbanWS } from '@/hooks/useKanbanWS'

interface KanbanHeaderProps {
  viewTitle: string
  viewIcon?: LucideIcon
  subtitle?: string
  extra?: ReactNode
}

export default function KanbanHeader({ viewTitle, viewIcon: Icon, subtitle, extra }: KanbanHeaderProps) {
  const { connected } = useKanbanWS()

  return (
    <header
      className="h-14 flex items-center px-6 gap-3 flex-shrink-0 glass-card !rounded-none !border-x-0 !border-t-0"
      style={{ borderBottom: '1px solid var(--border)' }}
    >
      {Icon && <Icon size={18} strokeWidth={2} className="text-primary flex-shrink-0" />}
      <h1 className="text-[15px] font-semibold tracking-tight">{viewTitle}</h1>
      <span className="text-xs text-muted-foreground hidden sm:inline">
        {subtitle || 'Testing Lifecycle Orchestrator'}
      </span>
      <div className="flex-1" />
      {extra}
      <div className="flex items-center gap-1.5 text-[10px]">
        {connected ? (
          <Wifi size={13} strokeWidth={2} className="text-success" />
        ) : (
          <WifiOff size={13} strokeWidth={2} className="text-destructive" />
        )}
        <span className={connected ? 'text-success font-semibold' : 'text-destructive'}>
          {connected ? 'Live' : 'Offline'}
        </span>
      </div>
    </header>
  )
}
