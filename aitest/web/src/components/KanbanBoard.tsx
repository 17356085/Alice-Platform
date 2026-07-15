/** Kanban board with drag-and-drop — React port.
 *  Vue template directives → JSX conditionals + .map().
 *  Drag/drop uses native HTML5 DnD API (same as original).
 */
import { useState } from 'react'
import { useKanbanStore, SOP_COLS, type ModuleInfo } from '@/stores/kanban'
import { Play } from 'lucide-react'

interface KanbanBoardProps {
  columns: Record<string, [string, ModuleInfo][]>
  running?: Set<string>
  onCardMove: (mod: string, from: string, to: string) => void
  onCardClick: (mod: string, info: ModuleInfo) => void
  onCardRun: (mod: string) => void
}

const colBg: Record<string, string> = {
  'Project Init': 'bg-slate-50/50 dark:bg-slate-950/20',
  'Requirement': 'bg-blue-50/50 dark:bg-blue-950/20',
  'Test Design': 'bg-indigo-50/50 dark:bg-indigo-950/20',
  'Automation': 'bg-amber-50/50 dark:bg-amber-950/20',
  'Execute & Debug': 'bg-purple-50/50 dark:bg-purple-950/20',
  'Bug Analysis': 'bg-red-50/50 dark:bg-red-950/20',
  'Data Sanitization': 'bg-teal-50/50 dark:bg-teal-950/20',
  'Report': 'bg-emerald-50/50 dark:bg-emerald-950/20',
  'Knowledge': 'bg-cyan-50/50 dark:bg-cyan-950/20',
}

export default function KanbanBoard({ columns, running, onCardMove, onCardClick, onCardRun }: KanbanBoardProps) {
  const [dragMod, setDragMod] = useState('')
  const [dragFrom, setDragFrom] = useState('')
  const [dragOverCol, setDragOverCol] = useState('')

  function onDragStart(e: React.DragEvent, mod: string, stage: string) {
    setDragMod(mod)
    setDragFrom(stage)
    const el = e.target as HTMLElement
    el.classList.add('scale-95', 'opacity-40', 'rotate-1', 'shadow-xl')
    e.dataTransfer.effectAllowed = 'move'
  }

  function onDragEnd(e: React.DragEvent) {
    const el = e.target as HTMLElement
    el.classList.remove('scale-95', 'opacity-40', 'rotate-1', 'shadow-xl')
    setDragOverCol('')
  }

  function onDrop(stage: string) {
    setDragOverCol('')
    if (dragMod && dragFrom !== stage) {
      onCardMove(dragMod, dragFrom, stage)
      window.__tlo_toast?.add(`${dragMod}: ${dragFrom} → ${stage}`, 'success')
    }
    setDragMod('')
    setDragFrom('')
  }

  const runningSet = running

  return (
    <div
      className="flex gap-3 overflow-x-auto pb-3 min-h-[calc(100vh-180px)]"
      style={{ scrollSnapType: 'x mandatory' }}
    >
      {SOP_COLS.map(col => {
        const items = columns[col.key] || []
        const isDragOver = dragOverCol === col.key
        const bg = colBg[col.key] || ''

        return (
          <div
            key={col.key}
            className={`rounded-2xl p-2.5 flex flex-col gap-2 transition-all duration-300 border-2 flex-shrink-0 w-[170px] ${
              isDragOver
                ? `scale-[1.02] border-dashed border-ring shadow-lg ${bg}`
                : `border-transparent ${bg}`
            }`}
            onDragOver={e => { e.preventDefault(); setDragOverCol(col.key) }}
            onDragLeave={() => setDragOverCol(prev => prev === col.key ? '' : prev)}
            onDrop={e => { e.preventDefault(); onDrop(col.key) }}
          >
            {/* Column header */}
            <div className="flex items-center gap-1.5 px-1 pb-2 border-b mb-1" style={{ borderColor: 'var(--border)' }}>
              <col.icon size={14} strokeWidth={2} className="flex-shrink-0 text-primary" />
              <div className="text-[10px] font-bold uppercase tracking-wider leading-tight" style={{ color: 'var(--primary)' }}>
                {col.label}
              </div>
              <span className="ml-auto text-[10px] font-bold opacity-40">{items.length}</span>
            </div>

            {/* Cards */}
            {items.map(([mod, info]) => {
              const isRunning = runningSet?.has(mod)
              return (
                <div
                  key={mod}
                  draggable
                  onDragStart={e => onDragStart(e, mod, col.key)}
                  onDragEnd={onDragEnd}
                  onClick={() => onCardClick(mod, info)}
                  className="glass-card !rounded-lg p-2.5 cursor-grab active:cursor-grabbing select-none transition-all duration-200 group"
                >
                  {/* Header row */}
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span className="font-semibold text-[13px] truncate">{mod}</span>
                      {isRunning && (
                        <span className="badge badge-info text-[9px] animate-pulse">LIVE</span>
                      )}
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      {isRunning ? (
                        <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
                      ) : info.failed ? (
                        <span className="w-2 h-2 rounded-full bg-destructive" title="Has failures" />
                      ) : null}
                    </div>
                  </div>

                  {/* Phase dots */}
                  <div className="flex gap-px mb-2">
                    {Object.entries(info.phase_status || {}).map(([phase, ok]) => (
                      <span
                        key={phase}
                        className={`w-1 h-1 rounded-full flex-shrink-0 ${ok ? 'bg-success' : 'bg-muted-foreground/15'}`}
                        title={`${phase}${ok ? ' ✅' : ''}`}
                      />
                    ))}
                  </div>

                  {/* Stats */}
                  <div className="flex flex-wrap gap-x-2 gap-y-0.5 text-[10px] text-muted-foreground mb-2">
                    <span>📄{info.pages}</span>
                    <span>📦{info.artifacts || 0}</span>
                    <span className="font-mono">{info.phases_done}/{info.phases_total}</span>
                  </div>

                  {/* Progress bar */}
                  <div className="h-1.5 bg-muted/50 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-1000 ease-out ${
                        col.key === 'Knowledge' ? '!bg-success' : '!bg-primary/60'
                      }`}
                      style={{
                        width: isRunning && info.progress
                          ? `${info.progress}%`
                          : `${info.phases_done / info.phases_total * 100}%`,
                        background: isRunning ? 'hsl(var(--primary))' : '',
                      }}
                    />
                  </div>

                  {/* Status text */}
                  {isRunning && info.current_phase ? (
                    <div className="text-[10px] text-muted-foreground mt-1 truncate">{info.current_phase}</div>
                  ) : (
                    <div className="text-[10px] text-muted-foreground mt-1 truncate">
                      {info.note || (col.key === 'Knowledge' ? '✅ Complete' : `${info.phases_done} phases done`)}
                    </div>
                  )}

                  {/* Run button (hover) */}
                  {!isRunning && (
                    <div
                      className="flex gap-1.5 mt-3 pt-2.5 opacity-0 group-hover:opacity-100 transition-opacity"
                      style={{ borderTop: '1px solid var(--border)' }}
                    >
                      <button
                        onClick={e => { e.stopPropagation(); onCardRun(mod) }}
                        className="flex-1 flex items-center justify-center gap-1 px-2.5 py-1.5 rounded-md text-[11px] font-semibold cursor-pointer transition-all border-none"
                        style={{ background: 'hsl(var(--primary))', color: 'hsl(var(--primary-foreground))' }}
                      >
                        <Play size={12} strokeWidth={3} /> Run SOP
                      </button>
                    </div>
                  )}
                </div>
              )
            })}

            {/* Empty placeholder */}
            {!items.length && (
              <div className="py-8 text-center text-muted-foreground/30 text-xs italic">Drop here</div>
            )}
          </div>
        )
      })}
    </div>
  )
}
