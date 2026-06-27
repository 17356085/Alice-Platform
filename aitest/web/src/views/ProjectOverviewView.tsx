/** Project Overview — module grid + SOP progress. shadcn/ui edition. */
import { useEffect, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useKanbanStore, selectColumns, SOP_COLS } from '../stores/kanban'
import { useProjectStore } from '../stores/project'
import { LayoutGrid, Play } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'

export default function ProjectOverviewView() {
  const { id } = useParams<{ id: string }>()
  const modules = useKanbanStore(s => s.modules)
  const loading = useKanbanStore(s => s.loading)
  const fetchModules = useKanbanStore(s => s.fetchModules)
  const setActive = useProjectStore(s => s.setActive)
  const activeProject = useProjectStore(s => s.activeProject())

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
    <div className="p-6 max-w-[1400px]">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <LayoutGrid size={22} />
          <h1 className="text-xl font-bold">{activeProject?.name || id || '项目概览'}</h1>
        </div>
        <Link to={`/projects/${id || 'default'}/kanban`}>
          <Button variant="gradient" size="sm" className="gap-1.5">
            <Play size={14} /> SOP 看板
          </Button>
        </Link>
      </div>

      {loading ? (
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 8 }, (_, i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
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
                <Card key={mod} className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-semibold text-sm">{mod}</span>
                    <Badge variant={
                      info.failed ? 'warning' :
                      info.phases_done >= info.phases_total ? 'success' : 'info'
                    } className="text-[10px]">
                      {info.failed ? '⚠️' : info.phases_done >= info.phases_total ? '✅' : '📝'} {info.phases_done}/{info.phases_total}
                    </Badge>
                  </div>
                  <Progress value={pct} className="mb-2 h-2" />
                  <div className="flex gap-3 text-[11px] text-muted-foreground">
                    <span>📄 {info.pages} pages</span>
                    <span>📦 {info.artifacts || 0} artifacts</span>
                  </div>
                </Card>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}

function StatBox({ label, value }: { label: string; value: number }) {
  return (
    <Card className="p-4 text-center">
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-[11px] text-muted-foreground mt-1">{label}</div>
    </Card>
  )
}
