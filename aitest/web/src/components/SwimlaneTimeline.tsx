/** SwimlaneTimeline — Chrome-DevTools-style horizontal timeline.
 *
 * Epic 3: Timeline Experience.
 * Features: swimlane bars, time ruler, zoom, click-to-expand, replay mode.
 *
 * Usage:
 *   <SwimlaneTimeline entries={timeline} />
 */
import { useState, useMemo, useCallback, useRef, useEffect } from 'react'
import { Clock, Play, Pause, SkipBack, SkipForward, ZoomIn, ZoomOut, ChevronRight, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'

// ── Types ────────────────────────────────────────────────────────────────

export interface SwimlaneEntry {
  ts: string           // ISO timestamp
  type: string         // event type
  message: string      // display text
  detail?: Record<string, unknown>
  duration_ms?: number
  tokens?: number
  cost?: number
  phase?: string
}

interface SwimlaneTimelineProps {
  entries: SwimlaneEntry[]
  onEntryClick?: (entry: SwimlaneEntry) => void
  className?: string
}

// ── Color map ────────────────────────────────────────────────────────────

const TYPE_BAR_COLOR: Record<string, string> = {
  run_created: 'bg-blue-500',
  execution_requested: 'bg-slate-500',
  execution_started: 'bg-blue-400',
  phase_started: 'bg-indigo-500',
  phase_completed: 'bg-emerald-500',
  artifact_created: 'bg-purple-500',
  run_completed: 'bg-emerald-500',
  run_failed: 'bg-red-500',
  run_cancelled: 'bg-amber-500',
  cost_recorded: 'bg-amber-400',
  queued: 'bg-slate-600',
}

function barColor(type: string): string {
  for (const [key, color] of Object.entries(TYPE_BAR_COLOR)) {
    if (type.includes(key.replace('_', '')) || type === key) return color
  }
  if (type.includes('fail') || type.includes('error')) return 'bg-red-500'
  if (type.includes('complete')) return 'bg-emerald-500'
  if (type.includes('start')) return 'bg-blue-500'
  if (type.includes('artifact')) return 'bg-purple-500'
  return 'bg-slate-600'
}

// ── Component ────────────────────────────────────────────────────────────

export default function SwimlaneTimeline({ entries, onEntryClick, className }: SwimlaneTimelineProps) {
  const [zoom, setZoom] = useState(1)  // 1x, 2x, 4x, 0.5x
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null)
  const [replaying, setReplaying] = useState(false)
  const [replayIdx, setReplayIdx] = useState(0)
  const replayRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Parse timestamps → ms from start
  const { startTs, endTs, positioned } = useMemo(() => {
    if (entries.length === 0) return { startTs: 0, endTs: 0, positioned: [] as Array<SwimlaneEntry & { offsetMs: number }> }

    const times = entries.map(e => {
      try { return new Date(e.ts).getTime() } catch { return 0 }
    }).filter(t => t > 0)

    const start = Math.min(...times)
    const end = Math.max(...times, start + 1000)

    const positioned = entries.map((e, i) => {
      let ts = 0
      try { ts = new Date(e.ts).getTime() } catch { ts = start }
      return { ...e, offsetMs: ts - start }
    })

    return { startTs: start, endTs: end, positioned }
  }, [entries])

  const totalMs = endTs - startTs || 1

  // Zoom levels
  const zoomMultipliers = [0.25, 0.5, 1, 2, 4]
  const zoomLevels = ['0.25×', '0.5×', '1×', '2×', '4×']
  const pxPerMs = (600 / totalMs) * zoom  // base 600px for full duration at 1x
  const totalPx = Math.max(totalMs * pxPerMs, 800)

  // Time ruler ticks
  const ticks = useMemo(() => {
    const tickInterval = totalMs / Math.max(Math.floor(totalPx / 80), 1)
    const result: Array<{ label: string; leftPx: number }> = []
    for (let ms = 0; ms <= totalMs; ms += tickInterval) {
      const sec = ms / 1000
      const label = sec < 60 ? `${sec.toFixed(1)}s` :
        `${Math.floor(sec / 60)}m ${Math.round(sec % 60)}s`
      result.push({ label, leftPx: ms * pxPerMs })
    }
    return result
  }, [totalMs, totalPx, pxPerMs])

  // Replay
  useEffect(() => {
    if (!replaying) {
      if (replayRef.current) { clearInterval(replayRef.current); replayRef.current = null }
      return
    }
    replayRef.current = setInterval(() => {
      setReplayIdx(prev => {
        if (prev >= positioned.length - 1) {
          setReplaying(false)
          return prev
        }
        return prev + 1
      })
    }, 500 / zoom) // faster when zoomed in
    return () => { if (replayRef.current) clearInterval(replayRef.current) }
  }, [replaying, positioned.length, zoom])

  // Keyboard nav
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (selectedIdx === null) return
      if (e.key === 'ArrowRight' && selectedIdx < positioned.length - 1) setSelectedIdx(selectedIdx + 1)
      if (e.key === 'ArrowLeft' && selectedIdx > 0) setSelectedIdx(selectedIdx - 1)
      if (e.key === 'Escape') setSelectedIdx(null)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [selectedIdx, positioned.length])

  const handleZoomIn = () => setZoom(z => Math.min(z * 2, 8))
  const handleZoomOut = () => setZoom(z => Math.max(z / 2, 0.125))

  if (entries.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-muted-foreground text-sm">
          <Clock size={32} className="mx-auto mb-3 opacity-20" />
          No timeline data
        </CardContent>
      </Card>
    )
  }

  const selected = selectedIdx !== null ? positioned[selectedIdx] : null

  return (
    <div className={cn('space-y-3', className)}>
      {/* Controls */}
      <div className="flex items-center gap-2 flex-wrap">
        <div className="flex items-center gap-0.5 bg-muted rounded-md p-0.5">
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleZoomOut}><ZoomOut size={14} /></Button>
          <span className="text-[10px] font-mono w-12 text-center">{zoomLevels[zoomMultipliers.indexOf(zoom)] || `${zoom}×`}</span>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleZoomIn}><ZoomIn size={14} /></Button>
        </div>
        <div className="flex items-center gap-0.5 bg-muted rounded-md p-0.5">
          <Button variant="ghost" size="icon" className="h-7 w-7"
            onClick={() => { setReplayIdx(0); setReplaying(false) }}><SkipBack size={14} /></Button>
          <Button variant={replaying ? 'default' : 'ghost'} size="icon" className="h-7 w-7"
            onClick={() => setReplaying(!replaying)}>
            {replaying ? <Pause size={14} /> : <Play size={14} />}
          </Button>
          <Button variant="ghost" size="icon" className="h-7 w-7"
            onClick={() => { setReplaying(false); setReplayIdx(positioned.length - 1) }}><SkipForward size={14} /></Button>
        </div>
        <span className="text-[10px] text-muted-foreground">
          {positioned.length} events · {replaying ? `Replaying (${replayIdx + 1}/${positioned.length})` : 'Paused'}
        </span>
        <div className="flex-1" />
        {selected && (
          <Button variant="ghost" size="sm" className="text-xs" onClick={() => setSelectedIdx(null)}>
            <X size={12} className="mr-1" /> Close detail
          </Button>
        )}
      </div>

      {/* Swimlane */}
      <Card>
        <CardContent className="p-0">
          <div ref={containerRef} className="overflow-x-auto" style={{ maxHeight: '400px', overflowY: 'auto' }}>
            <div style={{ width: `${totalPx}px`, minWidth: '100%' }}>
              {/* Time ruler */}
              <div className="h-6 border-b border-border relative bg-muted/30 sticky top-0 z-10">
                {ticks.map((t, i) => (
                  <div key={i} className="absolute top-0 h-full" style={{ left: `${t.leftPx}px` }}>
                    <div className="absolute top-0 w-px h-2 bg-border" />
                    <span className="absolute top-2 left-1 text-[9px] font-mono text-muted-foreground whitespace-nowrap">
                      {t.label}
                    </span>
                  </div>
                ))}
              </div>

              {/* Swimlane rows */}
              <div className="relative" style={{ minHeight: `${Math.max(positioned.length * 28, 200)}px` }}>
                {/* Replay cursor */}
                {replaying && (
                  <div className="absolute top-0 bottom-0 w-0.5 bg-primary z-20 transition-all duration-300"
                    style={{ left: `${positioned[replayIdx]?.offsetMs * pxPerMs || 0}px` }} />
                )}

                {/* Event bars */}
                {positioned.map((entry, i) => {
                  const left = entry.offsetMs * pxPerMs
                  const width = Math.max(entry.duration_ms ? entry.duration_ms * pxPerMs : 8, 6)
                  const isSelected = selectedIdx === i
                  const isReplay = replaying && replayIdx === i

                  return (
                    <div
                      key={i}
                      className={cn(
                        'absolute h-6 rounded-sm cursor-pointer transition-all flex items-center px-1.5',
                        barColor(entry.type),
                        isSelected && 'ring-2 ring-white/50 h-7 -top-0.5 z-10',
                        isReplay && 'ring-2 ring-primary brightness-125 z-10',
                        'hover:brightness-125'
                      )}
                      style={{ left: `${left}px`, top: `${i * 28 + 1}px`, width: `${width}px`, maxWidth: '400px' }}
                      onClick={() => { setSelectedIdx(i); onEntryClick?.(entry) }}
                      title={`${entry.message} — ${entry.ts?.slice(11, 19)}`}
                    >
                      <span className="text-[10px] text-white truncate font-medium">
                        {entry.message.slice(0, 40)}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detail panel */}
      {selected && (
        <Card className="bg-muted/20 border-border/50">
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className={cn('w-3 h-3 rounded-full', barColor(selected.type))} />
                <span className="text-sm font-semibold">{selected.type.replace(/_/g, ' ')}</span>
                <Badge variant="outline" className="text-[9px] font-mono">{selected.ts?.slice(11, 19)}</Badge>
              </div>
              <div className="flex gap-2 text-[10px] text-muted-foreground">
                {selected.duration_ms && <span>{(selected.duration_ms / 1000).toFixed(1)}s</span>}
                {selected.tokens && <span>{selected.tokens} tokens</span>}
                {selected.cost && <span>${selected.cost.toFixed(4)}</span>}
              </div>
            </div>
            <p className="text-sm">{selected.message}</p>
            {selected.detail && Object.keys(selected.detail).length > 0 && (
              <pre className="text-[10px] font-mono bg-muted p-3 rounded-md overflow-x-auto max-h-[200px] overflow-y-auto">
                {JSON.stringify(selected.detail, null, 2)}
              </pre>
            )}
            <div className="flex gap-2 text-[10px] text-muted-foreground">
              <span>← → navigate</span>
              <span>Esc close</span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
