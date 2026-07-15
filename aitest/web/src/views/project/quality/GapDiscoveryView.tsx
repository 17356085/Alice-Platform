/** Gap Discovery View — full React port with real API scanner. */
import { useEffect } from 'react'
import { useGapScanner, type TestGap } from '@/hooks/useGapScanner'
import { Search, AlertTriangle, RefreshCw, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { EmptyState, PageHeader } from '@/components/shared'

const severityColors: Record<string, string> = {
  critical: 'bg-destructive/10 text-destructive border-destructive/20',
  high: 'bg-warning/10 text-warning border-warning/20',
  medium: 'bg-warning/10 text-warning border-warning/20',
  low: 'bg-info/10 text-info border-info/20',
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
    <div className="mx-auto flex max-w-6xl flex-col gap-5 p-4 sm:p-6">
      {/* Header */}
      <PageHeader title="缺口发现" description="扫描模块覆盖与失败模式，优先处理最影响质量闭环的测试缺口。" actions={<Button variant="outline" size="sm" onClick={() => void scan()} disabled={scanning}><RefreshCw data-icon="inline-start" className={scanning ? 'animate-spin' : ''} />{scanning ? '扫描中…' : '重新扫描'}</Button>} />

      {/* Stats */}
      {allGaps.length > 0 && (
        <div className="flex gap-4 mb-4 text-xs text-muted-foreground">
          <span>{stats.total} 个缺口</span>
          <span className="font-semibold text-destructive">{stats.critical} 严重</span>
          <span className="font-semibold text-warning">{stats.high} 高</span>
        </div>
      )}

      {/* Progress */}
      {scanning && (
        <div className="flex items-center gap-2 rounded-md bg-muted/50 px-3 py-2 text-sm text-muted-foreground">
          <RefreshCw size={14} className="animate-spin" /> {progress}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2 rounded-lg border border-border bg-card/50 p-3">
        <button onClick={() => setSelectedType('all')} className={`filter-chip ${selectedType === 'all' ? 'active' : ''}`}>全部</button>
        <button onClick={() => setSelectedType('missing_test')} className={`filter-chip ${selectedType === 'missing_test' ? 'active' : ''}`}>❌ 缺失测试</button>
        <button onClick={() => setSelectedType('missing_type')} className={`filter-chip ${selectedType === 'missing_type' ? 'active' : ''}`}>⚠️ 缺失类型</button>
        <button onClick={() => setSelectedType('low_coverage')} className={`filter-chip ${selectedType === 'low_coverage' ? 'active' : ''}`}>📉 覆盖不足</button>
        <button onClick={() => setSelectedType('flaky_test')} className={`filter-chip ${selectedType === 'flaky_test' ? 'active' : ''}`}>🔄 不稳定</button>
        <button onClick={() => setSelectedType('untested_component')} className={`filter-chip ${selectedType === 'untested_component' ? 'active' : ''}`}>🧩 未测组件</button>
        <div className="flex-1" />
          <label className="flex items-center gap-2 text-xs">
          <Checkbox checked={showDismissed} onCheckedChange={value => setShowDismissed(value === true)} />
          显示已忽略
        </label>
          <Button variant="ghost" size="sm" onClick={dismissAll} className="text-xs text-muted-foreground hover:text-destructive">全部忽略</Button>
      </div>

      {/* Gap list */}
      {gaps.length === 0 && !scanning ? (
        <EmptyState icon={AlertTriangle} title="未发现缺口" description="所有模块测试覆盖充足，或当前筛选条件没有结果。" />
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
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-lg">{icon}</span>
          <div>
            <div className="font-semibold text-sm">{gap.title}</div>
            <div className="flex items-center gap-2 mt-0.5">
              <Badge variant="outline" className={`text-[10px] ${sev}`}>{gap.severity.toUpperCase()}</Badge>
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
