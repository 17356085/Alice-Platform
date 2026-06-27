/** Header bar — view title + subtitle + WS indicator + extra slot.
 *  shadcn/ui edition — Badge for WS status.
 */
import type { ReactNode } from 'react'
import { Wifi, WifiOff, type LucideIcon } from 'lucide-react'
import { useKanbanWS } from '@/hooks/useKanbanWS'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface KanbanHeaderProps {
  viewTitle: string
  viewIcon?: LucideIcon
  subtitle?: string
  extra?: ReactNode
}

export default function KanbanHeader({ viewTitle, viewIcon: Icon, subtitle, extra }: KanbanHeaderProps) {
  const { connected } = useKanbanWS()

  return (
    <header className="h-14 flex items-center px-6 gap-3 shrink-0 border-b border-border bg-card/60 backdrop-blur-sm">
      {Icon && <Icon size={18} strokeWidth={2} className="text-primary shrink-0" />}
      <h1 className="text-[15px] font-semibold tracking-tight">{viewTitle}</h1>
      <span className="text-xs text-muted-foreground hidden sm:inline">
        {subtitle || 'Testing Lifecycle Orchestrator'}
      </span>
      <div className="flex-1" />
      {extra}
      <Badge variant={connected ? 'success' : 'destructive'} className="gap-1 text-[10px]">
        {connected ? <Wifi size={11} strokeWidth={2} /> : <WifiOff size={11} strokeWidth={2} />}
        {connected ? 'Live' : 'Offline'}
      </Badge>
    </header>
  )
}
