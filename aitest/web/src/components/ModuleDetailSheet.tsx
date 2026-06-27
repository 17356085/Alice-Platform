/** Module detail slide-out panel — shadcn/ui Sheet edition. */
import { Play, FileText } from 'lucide-react'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface ModuleDetailSheetProps {
  module: string
  info: {
    status: string; phases_done: number; phases_total: number
    pages: number; failed: number; updated: string
    progress?: number; current_phase?: string
  } | null
  open: boolean
  running?: boolean
  onClose: () => void
  onRun: (mod: string) => void
  onReport: (mod: string) => void
}

export default function ModuleDetailSheet({
  module, info, open, running, onClose, onRun, onReport,
}: ModuleDetailSheetProps) {
  const statusVariant = () => {
    if (!info) return 'secondary'
    switch (info.status) {
      case 'completed': return 'success'
      case 'completed_with_issues': return 'warning'
      case 'ready': return 'info'
      default: return 'secondary'
    }
  }

  const statusLabel = () => {
    if (!info) return 'Unknown'
    switch (info.status) {
      case 'completed': return 'Complete'
      case 'completed_with_issues': return 'Issues'
      case 'ready': return 'Ready'
      default: return 'Pending'
    }
  }

  return (
    <Sheet open={open} onOpenChange={v => !v && onClose()}>
      <SheetContent className="w-[420px] sm:max-w-[420px] flex flex-col p-0">
        {/* Header */}
        <SheetHeader className="px-5 py-4 border-b border-border">
          <SheetTitle>{module}</SheetTitle>
          {info && (
            <Badge variant={statusVariant()} className="mt-1 text-xs">
              {statusLabel()}
            </Badge>
          )}
        </SheetHeader>

        {/* Body */}
        {info && (
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {/* Lifecycle progress */}
            <div className="bg-card border border-border rounded-lg p-4">
              <h3 className="text-xs font-semibold text-muted-foreground mb-3 flex items-center gap-1.5">
                <FileText size={13} /> Lifecycle Progress
              </h3>
              <div className="flex items-center gap-1">
                {Array.from({ length: info.phases_total || 9 }, (_, i) => (
                  <div
                    key={i}
                    className={cn(
                      'flex-1 h-2 rounded-full transition-all',
                      i < info.phases_done
                        ? info.status === 'completed' ? 'bg-success' : 'bg-warning'
                        : 'bg-muted'
                    )}
                  />
                ))}
              </div>
              <div className="text-xs text-muted-foreground mt-2 text-center">
                {info.phases_done}/{info.phases_total || 9} phases
              </div>
            </div>

            {/* Stats grid */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-card border border-border rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-info">{info.pages}</div>
                <div className="text-[11px] text-muted-foreground">Pages</div>
              </div>
              <div className="bg-card border border-border rounded-lg p-3 text-center">
                <div className={cn('text-2xl font-bold', info.failed ? 'text-destructive' : 'text-success')}>
                  {info.failed || 0}
                </div>
                <div className="text-[11px] text-muted-foreground">Failed</div>
              </div>
            </div>

            {/* Meta */}
            <div className="text-xs text-muted-foreground space-y-1">
              <div>Updated: {info.updated || 'N/A'}</div>
              <div>Status: {info.status}</div>
            </div>
          </div>
        )}

        {/* Running indicator */}
        {running && info?.current_phase && (
          <div className="px-5 py-2 bg-accent/50 border-t border-border flex items-center gap-2 text-xs">
            <span className="dot-live" />
            <span className="font-semibold text-primary">{info.current_phase}</span>
            <span className="text-muted-foreground">{info.progress || 0}%</span>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2 p-4 border-t border-border">
          <Button
            onClick={() => onRun(module)}
            disabled={running}
            variant={running ? 'secondary' : 'gradient'}
            className="flex-1 gap-1.5"
          >
            <Play size={14} strokeWidth={3} /> {running ? 'Running...' : 'Run SOP'}
          </Button>
          <Button
            onClick={() => onReport(module)}
            variant="outline"
            className="gap-1.5"
          >
            <FileText size={14} strokeWidth={2} /> Report
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}
