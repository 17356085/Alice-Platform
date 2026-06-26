/** Observability — timeline + metrics + logs. */
import { useState, useEffect } from 'react'
import { Clock, Activity, FileText } from 'lucide-react'

interface MetricEvent { ts: string; type: string; message: string; color: string }

export default function ObservabilityView() {
  const [events] = useState<MetricEvent[]>([])
  const [activeTab, setActiveTab] = useState<'timeline' | 'metrics' | 'logs'>('timeline')

  return (
    <div className="p-6">
      <h1 className="text-xl font-bold mb-6 flex items-center gap-2"><Clock size={20} /> 可观测性</h1>
      <div className="flex gap-2 mb-4">
        {(['timeline', 'metrics', 'logs'] as const).map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${
              activeTab === tab ? 'bg-primary text-primary-foreground border-primary' : 'bg-card border-border hover:bg-accent'
            }`}>
            {tab === 'timeline' ? '时间线' : tab === 'metrics' ? '指标' : '日志'}
          </button>
        ))}
      </div>
      {events.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground text-sm">
          <Activity size={48} className="mx-auto mb-4 opacity-20" />
          暂无事件 — 运行 SOP 后将显示可观测数据
        </div>
      ) : (
        <div className="space-y-2">
          {events.map((e, i) => (
            <div key={i} className="flex items-center gap-3 p-3 bg-card border border-border rounded-lg text-xs">
              <span className="text-muted-foreground font-mono">{e.ts}</span>
              <span className="font-semibold" style={{ color: e.color }}>{e.type}</span>
              <span>{e.message}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
