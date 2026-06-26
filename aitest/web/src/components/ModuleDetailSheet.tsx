/** Module detail slide-out panel — React port.
 *  Vue Teleport → ReactDOM.createPortal via fixed positioning.
 *  Vue watch(open, ...) → useEffect with open dependency.
 */
import { useState, useEffect } from 'react'
import { Play, FileText, X } from 'lucide-react'

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
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (open) {
      const t = setTimeout(() => setVisible(true), 50)
      return () => clearTimeout(t)
    } else {
      setVisible(false)
    }
  }, [open])

  if (!open) return null

  const statusBadge = () => {
    if (!info) return null
    switch (info.status) {
      case 'completed': return <span className="badge badge-ok text-xs mt-1">✅ Complete</span>
      case 'completed_with_issues': return <span className="badge badge-warn text-xs mt-1">⚠️ Issues</span>
      case 'ready': return <span className="badge badge-info text-xs mt-1">📝 Ready</span>
      default: return <span className="badge badge-info text-xs mt-1">⏳ Pending</span>
    }
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/30 z-40 transition-opacity ${visible ? 'opacity-100' : 'opacity-0'}`}
        onClick={onClose}
      />
      {/* Sheet */}
      <div
        className={`fixed right-0 top-0 h-full w-[420px] bg-card border-l border-border shadow-xl z-50 transition-transform duration-300 flex flex-col ${
          visible ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div>
            <h2 className="text-base font-semibold">{module}</h2>
            {statusBadge()}
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground cursor-pointer border-none bg-none">
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        {info && (
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {/* Lifecycle progress */}
            <div className="glass-card !rounded-lg p-4">
              <h3 className="text-xs font-semibold text-muted-foreground mb-3 flex items-center gap-1.5">
                <FileText size={13} /> Lifecycle Progress
              </h3>
              <div className="flex items-center gap-1">
                {Array.from({ length: info.phases_total || 9 }, (_, i) => (
                  <div
                    key={i}
                    className={`flex-1 h-2 rounded-full transition-all ${
                      i < info.phases_done
                        ? info.status === 'completed' ? 'bg-success' : 'bg-warning'
                        : 'bg-muted'
                    }`}
                  />
                ))}
              </div>
              <div className="text-xs text-muted-foreground mt-2 text-center">
                {info.phases_done}/{info.phases_total || 9} phases
              </div>
            </div>

            {/* Stats grid */}
            <div className="grid grid-cols-2 gap-3">
              <div className="glass-card !rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-info">{info.pages}</div>
                <div className="text-[11px] text-muted-foreground">Pages</div>
              </div>
              <div className="glass-card !rounded-lg p-3 text-center">
                <div className={`text-2xl font-bold ${info.failed ? 'text-destructive' : 'text-success'}`}>
                  {info.failed || 0}
                </div>
                <div className="text-[11px] text-muted-foreground">Failed</div>
              </div>
            </div>

            {/* Meta */}
            <div className="text-xs text-muted-foreground space-y-1">
              <div>📅 Updated: {info.updated || 'N/A'}</div>
              <div>📌 Status: {info.status}</div>
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
          <button
            onClick={() => onRun(module)}
            disabled={running}
            className={`flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 border-none rounded-md text-[13px] font-semibold cursor-pointer font-sans transition-all ${
              running ? 'bg-muted text-muted-foreground cursor-not-allowed' : 'btn-primary'
            }`}
          >
            <Play size={14} strokeWidth={3} /> {running ? 'Running...' : 'Run SOP'}
          </button>
          <button
            onClick={() => onReport(module)}
            className="btn-outline flex items-center gap-1.5 text-[13px]"
          >
            <FileText size={14} strokeWidth={2} /> Report
          </button>
        </div>
      </div>
    </>
  )
}
