/** Gap Discovery View — full React port with real API scanner. */
import { useEffect } from 'react'
import { useGapScanner, type TestGap } from '@/hooks/useGapScanner'
import { Search, AlertTriangle, RefreshCw, X } from 'lucide-react'

const severityColors: Record<string, string> = {
  critical: 'bg-red-100 text-red-800 border-red-300',
  high: 'bg-orange-100 text-orange-800 border-orange-300',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  low: 'bg-blue-100 text-blue-800 border-blue-300',
}

const typeIcons: Record<string, string> = {
  missing_test: '❌', missing_type: '⚠️', low_coverage: '📉',
  flaky_test: '🔄', untested_component: '🧩',
}

export default function GapDiscoveryView() {
  const {
    gaps, allGaps, scanning, progress, stats,
    selectedType, showDismissed,
    setSelectedType, setShowDismissed,
    scan, dismissGap, dismissAll, convertToTask, archiveGap,
  } = useGapScanner()

  useEffect(() => {
    scan()
  }, []) // auto-scan on mount

  return (
    <div className="p-6 max-w-1200">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <Search size={20} /> 缺口发现
        </h1>
        <button onClick={scan} disabled={scanning} className="btn-outline text-xs flex items-center gap-1.5">
          <RefreshCw size={13} className={scanning ? 'animate-spin' : ''} /> {scanning ? '扫描中...' : '重新扫描'}
        </button>
      </div>

      {/* Stats */}
      {allGaps.length > 0 && (
        <div className="flex gap-4 mb-4 text-xs text-muted-foreground">
          <span>{stats.total} 个缺口</span>
          <span className="text-red-500 font-semibold">{stats.critical} 严重</span>
          <span className="text-orange-500 font-semibold">{stats.high} 高</span>
        </div>
      )}

      {/* Progress */}
      {scanning && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
          <RefreshCw size={14} className="animate-spin" /> {progress}
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2 mb-4 flex-wrap">
        <button onClick={() => setSelectedType('all')} className={`filter-chip ${selectedType === 'all' ? 'active' : ''}`}>全部</button>
        <button onClick={() => setSelectedType('missing_test')} className={`filter-chip ${selectedType === 'missing_test' ? 'active' : ''}`}>❌ 缺失测试</button>
        <button onClick={() => setSelectedType('missing_type')} className={`filter-chip ${selectedType === 'missing_type' ? 'active' : ''}`}>⚠️ 缺失类型</button>
        <button onClick={() => setSelectedType('low_coverage')} className={`filter-chip ${selectedType === 'low_coverage' ? 'active' : ''}`}>📉 覆盖不足</button>
        <button onClick={() => setSelectedType('flaky_test')} className={`filter-chip ${selectedType === 'flaky_test' ? 'active' : ''}`}>🔄 不稳定</button>
        <button onClick={() => setSelectedType('untested_component')} className={`filter-chip ${selectedType === 'untested_component' ? 'active' : ''}`}>🧩 未测组件</button>
        <div className="flex-1" />
        <label className="flex items-center gap-1 text-xs cursor-pointer">
          <input type="checkbox" checked={showDismissed} onChange={e => setShowDismissed(e.target.checked)} />
          显示已忽略
        </label>
        <button onClick={dismissAll} className="text-xs text-muted-foreground hover:text-destructive">全部忽略</button>
      </div>

      {/* Gap list */}
      {gaps.length === 0 && !scanning ? (
        <div className="text-center py-16 text-muted-foreground text-sm">
          <AlertTriangle size={48} className="mx-auto mb-4 opacity-20" />
          <p>未发现缺口</p>
          <span className="text-xs">所有模块测试覆盖充足。</span>
        </div>
      ) : (
        <div className="space-y-3">
          {gaps.map(gap => (
            <GapCard key={gap.id} gap={gap} onDismiss={dismissGap} onConvert={convertToTask} onArchive={archiveGap} />
          ))}
        </div>
      )}

      <style>{`
        .filter-chip { padding: 3px 10px; border-radius: 9999px; border: 1px solid var(--border); background: transparent; cursor: pointer; font-size: 11px; color: var(--text-secondary); transition: all .15s; }
        .filter-chip:hover { border-color: var(--primary); color: var(--primary); }
        .filter-chip.active { background: var(--primary); color: var(--primary-foreground); border-color: var(--primary); }
      `}</style>
    </div>
  )
}

function GapCard({ gap, onDismiss, onConvert, onArchive }: {
  gap: TestGap
  onDismiss: (id: string) => void
  onConvert: (id: string) => void
  onArchive: (id: string) => void
}) {
  const sev = severityColors[gap.severity] || ''
  const icon = typeIcons[gap.type] || '📌'

  return (
    <div className="glass-card !rounded-xl p-4">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-lg">{icon}</span>
          <div>
            <div className="font-semibold text-sm">{gap.title}</div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className={`text-[10px] px-1.5 py-0.5 rounded border font-semibold ${sev}`}>{gap.severity.toUpperCase()}</span>
              <span className="text-[11px] text-muted-foreground">{gap.module}</span>
              <span className="text-[11px] text-muted-foreground">⏱ {gap.estimatedEffort}</span>
            </div>
          </div>
        </div>
        <div className="flex gap-1 flex-shrink-0">
          <button onClick={() => onConvert(gap.id)} className="btn-mini" title="创建任务">📋</button>
          <button onClick={() => onDismiss(gap.id)} className="btn-mini" title="忽略">✕</button>
          <button onClick={() => onArchive(gap.id)} className="btn-mini" title="归档">📁</button>
        </div>
      </div>
      <p className="text-xs text-muted-foreground mb-2">{gap.description}</p>
      <div className="text-[11px] text-primary font-medium">💡 {gap.suggestion}</div>
      <style>{`
        .btn-mini { background: none; border: 1px solid var(--border); border-radius: 4px; cursor: pointer; padding: 2px 4px; font-size: 11px; opacity: 0.5; }
        .btn-mini:hover { opacity: 1; background: var(--bg-secondary); }
      `}</style>
    </div>
  )
}
