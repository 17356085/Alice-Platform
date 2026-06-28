/** Kanban view — React port.
 *  Vue onMounted → useEffect([], []).
 *  Vue useRoute → React useParams + useSearchParams.
 *  Vue store access → Zustand selectors.
 */
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useKanbanStore, useSelectColumns, selectTotalModules, type ModuleInfo } from '@/stores/kanban'
import { useKanbanWS } from '@/hooks/useKanbanWS'
import { RefreshCw } from 'lucide-react'
import KanbanBoard from '@/components/KanbanBoard'
import ModuleDetailSheet from '@/components/ModuleDetailSheet'

export default function KanbanView() {
  const [searchParams] = useSearchParams()
  const projectId = searchParams.get('project') || ''

  const modules = useKanbanStore(s => s.modules)
  const loading = useKanbanStore(s => s.loading)
  const error = useKanbanStore(s => s.error)
  const running = useKanbanStore(s => s.running)
  const fetchModules = useKanbanStore(s => s.fetchModules)
  const moveCard = useKanbanStore(s => s.moveCard)
  const startSOP = useKanbanStore(s => s.startSOP)
  const columns = useSelectColumns()
  const totalModules = useKanbanStore(selectTotalModules)
  const { sendCardMove } = useKanbanWS()

  const [selectedMod, setSelectedMod] = useState('')
  const [selectedInfo, setSelectedInfo] = useState<ModuleInfo | null>(null)
  const [sheetOpen, setSheetOpen] = useState(false)

  useEffect(() => {
    fetchModules(projectId)
  }, [projectId, fetchModules])

  function onCardMove(mod: string, from: string, to: string) {
    moveCard(mod, to)
    sendCardMove(mod, from, to)
  }

  function onCardClick(mod: string, info: ModuleInfo) {
    setSelectedMod(mod)
    setSelectedInfo(info)
    setSheetOpen(true)
  }

  function onRun(mod: string) {
    startSOP(mod)
  }

  function refreshModules() {
    fetchModules(projectId)
  }

  return (
    <div>
      {/* Toolbar */}
      <div className="flex justify-between items-center mb-5">
        <div className="flex items-center gap-3">
          <div className="text-xs text-muted-foreground">{totalModules} modules</div>
          {running.size > 0 && (
            <div className="badge badge-info text-[10px] animate-pulse">{running.size} running</div>
          )}
        </div>
        <button onClick={refreshModules} className="btn-outline text-xs flex items-center gap-1.5">
          <RefreshCw size={13} strokeWidth={2} /> Refresh
        </button>
      </div>

      {/* Loading skeletons */}
      {loading && (
        <div className="flex gap-3 overflow-x-auto">
          {Array.from({ length: 9 }, (_, i) => (
            <div key={i} className="skeleton h-[200px] rounded-xl flex-shrink-0 w-[170px]" />
          ))}
        </div>
      )}

      {/* Error state */}
      {!loading && error && (
        <div className="text-center py-16 text-destructive text-sm">{error}</div>
      )}

      {/* Board */}
      {!loading && !error && totalModules > 0 && (
        <KanbanBoard
          columns={columns}
          running={running}
          onCardMove={onCardMove}
          onCardClick={onCardClick}
          onCardRun={onRun}
        />
      )}

      {/* Empty state */}
      {!loading && !error && totalModules === 0 && (
        <div className="text-center py-16 text-muted-foreground text-sm">
          No modules loaded — check server
        </div>
      )}

      {/* Detail sheet */}
      {sheetOpen && (
        <ModuleDetailSheet
          module={selectedMod}
          info={selectedInfo}
          open={sheetOpen}
          running={running.has(selectedMod)}
          onClose={() => setSheetOpen(false)}
          onRun={onRun}
          onReport={() => {}}
        />
      )}
    </div>
  )
}
