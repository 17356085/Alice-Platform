/** Observability — real-time resource dashboards.
 *
 *  Fetches /api/observability/snapshot every 10s.
 *  Tabs: Overview | Memory | Threads&Tasks | Queue&WS | Storage
 */
import { useState, useEffect, useCallback } from 'react'
import { api } from '@/api/client'
import { Clock, Cpu, Database, Activity, Wifi, HardDrive, RefreshCw } from 'lucide-react'

interface Snapshot {
  timestamp: string
  memory: { rss_mb: number; vms_mb: number; pct: number }
  threads: { count: number; daemon_count?: number }
  tasks: { total: number; pending: number; done: number }
  queue: { backend: string; queued: number; running: number; completed: number; failed: number; deferred?: number }
  gc: { gen0: number; gen1: number; gen2: number; thresholds: number[]; total_objects: number }
  websocket: { total: number; endpoints: Record<string, number> }
  sqlite: Record<string, { size_kb: number; exists: boolean }>
}

const TABS = ['overview', 'memory', 'threads', 'queue'] as const
const TAB_ICONS: Record<string, React.ReactNode> = {
  overview: <Activity size={16} />, memory: <Cpu size={16} />, threads: <Database size={16} />, queue: <Wifi size={16} />,
}
const TAB_LABELS: Record<string, string> = {
  overview: 'Overview', memory: 'Memory & GC', threads: 'Threads & Tasks', queue: 'Queue & WS',
}

function StatCard({ label, value, unit, sub }: { label: string; value: string | number; unit?: string; sub?: string }) {
  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <div className="text-xs text-muted-foreground mb-1">{label}</div>
      <div className="text-2xl font-bold font-mono">
        {value}<span className="text-sm font-normal text-muted-foreground ml-1">{unit ?? ''}</span>
      </div>
      {sub && <div className="text-xs text-muted-foreground mt-1">{sub}</div>}
    </div>
  )
}

function formatMB(v: number) { return v > 0 ? v.toFixed(0) : '—' }
function formatKB(v: number) { return v > 0 ? `${v.toFixed(0)} KB` : '—' }

export default function ObservabilityView() {
  const [snap, setSnap] = useState<Snapshot | null>(null)
  const [error, setError] = useState('')
  const [tab, setTab] = useState<string>('overview')
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchSnapshot = useCallback(async () => {
    try {
      const data = await api.get<Snapshot>('/api/observability/snapshot')
      setSnap(data)
      setError('')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }, [])

  useEffect(() => {
    fetchSnapshot()
    if (!autoRefresh) return
    const i = setInterval(fetchSnapshot, 10_000)
    return () => clearInterval(i)
  }, [fetchSnapshot, autoRefresh])

  if (!snap) {
    return (
      <div className="p-6 text-center text-muted-foreground">
        <Activity size={48} className="mx-auto mb-4 opacity-20" />
        {error ? `Error: ${error}` : 'Loading...'}
      </div>
    )
  }

  const { memory, threads, tasks, queue, gc, websocket, sqlite } = snap

  return (
    <div className="p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <Activity size={20} /> Observability
        </h1>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <label className="flex items-center gap-1 cursor-pointer">
            <input type="checkbox" checked={autoRefresh} onChange={e => setAutoRefresh(e.target.checked)} />
            Auto-refresh
          </label>
          <button onClick={fetchSnapshot} className="p-1 hover:text-white transition-colors" title="Refresh now">
            <RefreshCw size={14} />
          </button>
          <span className="font-mono">{new Date(snap.timestamp).toLocaleTimeString()}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        {TABS.map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors flex items-center gap-2 ${
              tab === t ? 'bg-primary text-primary-foreground border-primary' : 'bg-card border-border hover:bg-accent'
            }`}>
            {TAB_ICONS[t]}{TAB_LABELS[t]}
          </button>
        ))}
      </div>

      {/* ── Overview ── */}
      {tab === 'overview' && (
        <div className="space-y-4">
          <div className="grid grid-cols-4 gap-3">
            <StatCard label="RSS" value={formatMB(memory.rss_mb)} unit="MB" sub={`VMS ${formatMB(memory.vms_mb)} MB`} />
            <StatCard label="Threads" value={threads.count} />
            <StatCard label="Tasks" value={tasks.pending} unit="pending" sub={`${tasks.done} done`} />
            <StatCard label="WS Connections" value={websocket.total} />
          </div>
          <div className="grid grid-cols-4 gap-3">
            <StatCard label="GC Gen2" value={gc.gen2} sub={`Gen0: ${gc.gen0} Gen1: ${gc.gen1}`} />
            <StatCard label="Queue" value={queue.queued} unit="queued" sub={`${queue.completed} done · ${queue.failed} failed`} />
            <StatCard label="audit.db" value={formatKB(sqlite.audit?.size_kb ?? 0)} />
            <StatCard label="runs.db" value={formatKB(sqlite.runs?.size_kb ?? 0)} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <StatCard label="checkpoints.sqlite" value={formatKB(sqlite.checkpoints?.size_kb ?? 0)} />
            <StatCard label="Total Objects (GC)" value={gc.total_objects > 0 ? gc.total_objects.toLocaleString() : '—'} />
          </div>
        </div>
      )}

      {/* ── Memory & GC ── */}
      {tab === 'memory' && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <StatCard label="RSS" value={formatMB(memory.rss_mb)} unit="MB" />
            <StatCard label="VMS" value={formatMB(memory.vms_mb)} unit="MB" />
            <StatCard label="Memory %" value={memory.pct > 0 ? memory.pct.toFixed(1) : '—'} unit="%" />
          </div>
          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="text-sm font-semibold mb-3">GC Generations</h3>
            <div className="space-y-3">
              {[
                { label: 'Gen 0', value: gc.gen0, threshold: gc.thresholds[0], pct: gc.gen0 / gc.thresholds[0] * 100 },
                { label: 'Gen 1', value: gc.gen1, threshold: gc.thresholds[1], pct: gc.gen1 / gc.thresholds[1] * 100 },
                { label: 'Gen 2', value: gc.gen2, threshold: gc.thresholds[2], pct: gc.gen2 / gc.thresholds[2] * 100 },
              ].map(g => (
                <div key={g.label}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-mono font-semibold">{g.label}</span>
                    <span className="text-muted-foreground">{g.value} / {g.threshold}</span>
                  </div>
                  <div className="h-2 bg-sidebar rounded-full overflow-hidden">
                    <div className={`h-full rounded-full transition-all ${g.pct > 80 ? 'bg-destructive' : g.pct > 50 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                      style={{ width: `${Math.min(g.pct, 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-3 text-xs text-muted-foreground">
              Total tracked objects: <span className="font-mono text-white">{gc.total_objects > 0 ? gc.total_objects.toLocaleString() : '—'}</span>
            </div>
          </div>
        </div>
      )}

      {/* ── Threads & Tasks ── */}
      {tab === 'threads' && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <StatCard label="Thread Count" value={threads.count} />
            <StatCard label="Total Tasks" value={tasks.total} />
            <StatCard label="Pending Tasks" value={tasks.pending} />
          </div>
          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="text-sm font-semibold mb-3">Task Breakdown</h3>
            <div className="space-y-3">
              {[
                { label: 'Pending', value: tasks.pending, color: 'bg-amber-500' },
                { label: 'Done', value: tasks.done, color: 'bg-emerald-500' },
              ].map(t => (
                <div key={t.label} className="flex items-center gap-3">
                  <span className="text-xs w-16">{t.label}</span>
                  <div className="flex-1 h-2 bg-sidebar rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${t.color}`}
                      style={{ width: `${tasks.total > 0 ? (t.value / tasks.total * 100) : 0}%` }} />
                  </div>
                  <span className="text-xs font-mono w-8 text-right">{t.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Queue & WebSocket ── */}
      {tab === 'queue' && (
        <div className="space-y-4">
          <div className="grid grid-cols-4 gap-3">
            <StatCard label="Queue Backend" value={queue.backend} />
            <StatCard label="Queued" value={queue.queued} />
            <StatCard label="Running" value={queue.running} />
            <StatCard label="Completed" value={queue.completed} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <StatCard label="Failed" value={queue.failed} />
            <StatCard label="Deferred" value={queue.deferred ?? 0} />
          </div>

          <h3 className="text-sm font-semibold mt-4 mb-2 flex items-center gap-2"><Wifi size={14} /> WebSocket</h3>
          <div className="grid grid-cols-3 gap-3">
            <StatCard label="Total Connections" value={websocket.total} />
            {Object.entries(websocket.endpoints).map(([name, count]) => (
              <StatCard key={name} label={name} value={count} />
            ))}
          </div>

          <h3 className="text-sm font-semibold mt-4 mb-2 flex items-center gap-2"><HardDrive size={14} /> Storage</h3>
          <div className="grid grid-cols-3 gap-3">
            {Object.entries(sqlite).map(([name, info]) => (
              <StatCard key={name} label={name} value={info.exists ? `${info.size_kb}` : '—'} unit="KB" />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
