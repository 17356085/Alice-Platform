/** Project Overview — module grid + SOP progress. */
import { useEffect, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useKanbanStore, selectColumns, SOP_COLS } from '../stores/kanban'
import { useProjectStore } from '../stores/project'
import { LayoutGrid, Play } from 'lucide-react'

export default function ProjectOverviewView() {
  const { id } = useParams<{ id: string }>()
  const modules = useKanbanStore(s => s.modules)
  const loading = useKanbanStore(s => s.loading)
  const fetchModules = useKanbanStore(s => s.fetchModules)
  const setActive = useProjectStore(s => s.setActive)
  const activeProject = useProjectStore(s => s.activeProject())
  const columns = useKanbanStore(selectColumns)

  useEffect(() => {
    if (id) { setActive(id); fetchModules(id) }
    else fetchModules()
  }, [id, setActive, fetchModules])

  const modList = useMemo(() => Object.entries(modules), [modules])
  const totalPhases = useMemo(() =>
    modList.reduce((sum, [, m]) => sum + m.phases_done, 0),
    [modList]
  )

  return (
    <div className="p-6 max-w-1400">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <LayoutGrid size={22} />
          <h1 className="text-xl font-bold">{activeProject?.name || id || '项目概览'}</h1>
        </div>
        <Link to={`/projects/${id || 'default'}/kanban`} className="btn-primary flex items-center gap-1.5">
          <Play size={14} /> SOP 看板
        </Link>
      </div>

      {loading ? (
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 8 }, (_, i) => <div key={i} className="skeleton h-28 rounded-xl" />)}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-4 gap-3 mb-6">
            <StatBox label="总模块" value={modList.length} />
            <StatBox label="总阶段" value={totalPhases} />
            <StatBox label="SOP 阶段" value={SOP_COLS.length} />
            <StatBox label="活跃项目" value={activeProject ? 1 : 0} />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {modList.map(([mod, info]) => {
              const pct = info.phases_total ? Math.round(info.phases_done / info.phases_total * 100) : 0
              return (
                <div key={mod} className="glass-card !rounded-xl p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-semibold text-sm">{mod}</span>
                    <span className={`badge ${info.failed ? 'badge-warn' : info.phases_done >= info.phases_total ? 'badge-ok' : 'badge-info'}`}>
                      {info.failed ? '⚠️' : info.phases_done >= info.phases_total ? '✅' : '📝'} {info.phases_done}/{info.phases_total}
                    </span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden mb-2">
                    <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${pct}%` }} />
                  </div>
                  <div className="flex gap-3 text-[11px] text-muted-foreground">
                    <span>📄 {info.pages} pages</span>
                    <span>📦 {info.artifacts || 0} artifacts</span>
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}
      <style>{`
        .btn-primary { display: inline-flex; align-items: center; gap: 4px; padding: 8px 16px; background: var(--accent); color: #fff; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 600; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 10px; font-weight: 600; }
        .badge-ok { background: #d4edda; color: #155724; }
        .badge-warn { background: #fff3cd; color: #856404; }
        .badge-info { background: var(--info-light); color: var(--info); }
      `}</style>
    </div>
  )
}

function StatBox({ label, value }: { label: string; value: number }) {
  return (
    <div className="glass-card !rounded-lg p-4 text-center">
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-[11px] text-muted-foreground mt-1">{label}</div>
    </div>
  )
}
