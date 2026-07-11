/** Timeline — Execution trace with step-level detail. */
import { useState, useMemo } from 'react'
import { Clock, Trash2, ChevronDown, Zap, DollarSign, FileText } from 'lucide-react'
import { useTimelineStore, type TimelineEvent, type TimelineEventType } from '@/stores/timeline'
import { useKanbanStore } from '@/stores/kanban'
import { Card, CardContent } from '@/components/ui/card'
import { Badge, type BadgeVariant } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Collapsible, CollapsibleContent } from '@/components/ui/collapsible'
import { cn } from '@/lib/utils'

const COLOR_VARIANTS: Record<string, string> = {
  success: 'success', warning: 'warning', destructive: 'destructive',
  info: 'info', gold: 'gold', secondary: 'secondary',
}

const TYPE_LABELS: Record<TimelineEventType, string> = {
  phase_start: 'Phase Start', phase_complete: 'Phase Done',
  artifact_created: 'Artifact', artifact_updated: 'Updated',
  error: 'Error', warning: 'Warning', retry: 'Retry',
  checkpoint: 'Checkpoint', memory_hit: 'Memory Hit', info: 'Info',
}

export default function TimelineView() {
  const modules = useKanbanStore(s => s.modules)
  const events = useTimelineStore(s => s.events)
  const clear = useTimelineStore(s => s.clear)
  const [modFilter, setModFilter] = useState('all')
  const [typeFilter, setTypeFilter] = useState('all')
  const moduleList = useMemo(() => ['all', ...Object.keys(modules)], [modules])

  const filtered = useMemo(() => {
    let list = [...events].reverse()
    if (modFilter !== 'all') list = list.filter(e => e.module === modFilter)
    if (typeFilter !== 'all') list = list.filter(e => e.type === typeFilter)
    return list.slice(0, 100)
  }, [events, modFilter, typeFilter])

  const fmt = (ts: number) => {
    const d = new Date(ts)
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`
  }

  return (
    <div className="p-6 max-w-[960px]">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold flex items-center gap-2"><Clock size={20} /> 时间线</h1>
        {events.length > 0 && (
          <Button variant="ghost" size="sm" onClick={clear} className="text-muted-foreground text-xs gap-1">
            <Trash2 size={12} /> Clear
          </Button>
        )}
      </div>

      <div className="flex items-center gap-3 mb-6">
        <Select value={modFilter} onValueChange={setModFilter}>
          <SelectTrigger className="w-[180px] h-8 text-xs"><SelectValue placeholder="All Modules" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Modules</SelectItem>
            {moduleList.slice(1).map(m => <SelectItem key={m} value={m}>{m}</SelectItem>)}
          </SelectContent>
        </Select>
        <div className="flex gap-1 flex-wrap">
          {(['all', 'phase_start', 'phase_complete', 'error', 'warning', 'artifact_created'] as const).map(t => (
            <Badge key={t} variant={typeFilter === t ? (COLOR_VARIANTS[t] as BadgeVariant) || 'secondary' : 'outline'}
              className="cursor-pointer text-[10px]" onClick={() => setTypeFilter(typeFilter === t ? 'all' : t)}>
              {t === 'all' ? 'All' : TYPE_LABELS[t]}
            </Badge>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <Card className="text-center py-16">
          <CardContent>
            <Clock size={48} className="mx-auto mb-4 opacity-15" />
            <p className="text-sm text-muted-foreground">
              {events.length === 0 ? '暂无事件 — 运行 SOP 后此处将显示 Agent 活动时间线' : '无匹配事件'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="relative pl-8">
          <div className="absolute left-[15px] top-2 bottom-2 w-px bg-border" />
          <div className="space-y-3">
            {filtered.map((event) => (
              <TraceRow key={event.id} event={event} fmt={fmt} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function TraceRow({ event, fmt }: { event: TimelineEvent; fmt: (ts: number) => string }) {
  const [expanded, setExpanded] = useState(false)
  const hasTrace = !!(event.tokensIn || event.tokensOut || event.duration || event.output)

  return (
    <div className="relative">
      <div className={cn(
        'absolute left-[-23px] top-2.5 w-[17px] h-[17px] rounded-full border-2 border-background z-10 flex items-center justify-center text-[9px]',
        event.type === 'error' ? 'bg-destructive' : event.type === 'warning' ? 'bg-warning' :
        event.type === 'phase_complete' || event.type === 'artifact_created' ? 'bg-success' : 'bg-primary'
      )} />

      <Collapsible open={expanded} onOpenChange={setExpanded}>
        <div className={cn('cursor-pointer', hasTrace && 'hover:opacity-90')}
          onClick={() => hasTrace && setExpanded(!expanded)}>
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
            <span className="font-mono tabular-nums">{fmt(event.ts)}</span>
            <Badge variant={(COLOR_VARIANTS[event.color || 'secondary'] || 'outline') as BadgeVariant} className="text-[10px] gap-0.5">
              <span>{event.icon}</span> {TYPE_LABELS[event.type]}
            </Badge>
            {event.phase && <span className="text-muted-foreground/50 font-mono text-[10px]">Phase {event.phase}</span>}
            {event.agent && <span className="text-muted-foreground/50 text-[10px]">{event.agent}</span>}
          </div>
          <p className="text-sm m-0">{event.message}</p>
          {hasTrace && !expanded && <ChevronDown size={12} className="text-muted-foreground/40 mt-1" />}
          {hasTrace && (
            <div className="flex gap-3 mt-1 text-[10px] text-muted-foreground/60">
              {event.tokensIn != null && <span className="flex items-center gap-0.5"><Zap size={10} />{event.tokensIn}</span>}
              {event.duration != null && <span>{event.duration.toFixed(1)}s</span>}
              {event.cost != null && <span className="flex items-center gap-0.5"><DollarSign size={10} />{event.cost.toFixed(3)}</span>}
            </div>
          )}
        </div>

        <CollapsibleContent>
          <div className="mt-2 space-y-2 text-xs">
            {/* Metrics row */}
            {(event.tokensIn != null || event.duration != null) && (
              <div className="grid grid-cols-4 gap-2">
                {event.tokensIn != null && (
                  <div className="p-2 rounded-lg bg-muted/30 border border-border/50 text-center">
                    <div className="text-[10px] text-muted-foreground mb-0.5">Tokens In</div>
                    <div className="font-mono font-semibold tabular-nums">{event.tokensIn.toLocaleString()}</div>
                  </div>
                )}
                {event.tokensOut != null && (
                  <div className="p-2 rounded-lg bg-muted/30 border border-border/50 text-center">
                    <div className="text-[10px] text-muted-foreground mb-0.5">Tokens Out</div>
                    <div className="font-mono font-semibold tabular-nums">{event.tokensOut.toLocaleString()}</div>
                  </div>
                )}
                {event.cost != null && (
                  <div className="p-2 rounded-lg bg-muted/30 border border-border/50 text-center">
                    <div className="text-[10px] text-muted-foreground mb-0.5">Cost</div>
                    <div className="font-mono font-semibold tabular-nums">${event.cost.toFixed(4)}</div>
                  </div>
                )}
                {event.duration != null && (
                  <div className="p-2 rounded-lg bg-muted/30 border border-border/50 text-center">
                    <div className="text-[10px] text-muted-foreground mb-0.5">Duration</div>
                    <div className="font-mono font-semibold tabular-nums">{event.duration.toFixed(1)}s</div>
                  </div>
                )}
              </div>
            )}

            {/* Output JSON */}
            {event.output && (
              <div className="p-3 rounded-lg bg-muted/30 border border-border font-mono text-[11px] leading-relaxed whitespace-pre-wrap max-h-[300px] overflow-y-auto">
                {event.output}
              </div>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  )
}
