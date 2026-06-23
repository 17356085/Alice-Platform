import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface PhaseStatus { [phase: string]: boolean }
interface ModuleInfo {
  status: string; stage: string; phase_status: PhaseStatus
  phases_done: number; phases_total: number
  pages: number; pages_list: string[]; artifacts: number
  failed: number; run_id: string; updated: string; note: string
  progress?: number; current_phase?: string; _kanban_stage?: string
}

// SOP column definitions — aligned with agent-definitions.yaml phases
const SOP_COLS: { key: string; label: string; icon: string; phases: string[] }[] = [
  { key: 'init', label: 'Init', icon: '🔰', phases: ['Preflight', 'Project Init'] },
  { key: 'design', label: 'Design', icon: '📝', phases: ['Requirement', 'Test Design'] },
  { key: 'automation', label: 'Automation', icon: '⚙️', phases: ['Automation'] },
  { key: 'execution', label: 'Execute', icon: '▶️', phases: ['Execute & Debug', 'Bug Analysis', 'Data Sanitization'] },
  { key: 'complete', label: 'Complete', icon: '✅', phases: ['Report', 'Knowledge'] },
]

function computeStage(info: ModuleInfo, running: Set<string>): string {
  if (running.has(info._kanban_stage || '') || info.stage === 'execution' && info.phases_done >= 5) return 'execution'
  if (info._kanban_stage) return info._kanban_stage
  if (info.stage === 'complete' || info.status === 'completed') return 'complete'
  if (info.stage === 'analysis' || info.status === 'completed_with_issues') return 'execution'
  if (info.stage === 'automation' || info.status === 'ready') return 'automation'
  if (info.phases_done >= 3) return 'design'
  return 'init'
}

export const useKanbanStore = defineStore('kanban', () => {
  const modules = ref<Record<string, ModuleInfo>>({})
  const loading = ref(false)
  const error = ref('')
  const running = ref<Set<string>>(new Set())
  const sopPhases = ref<string[]>([])

  const columns = computed(() => {
    const cols: Record<string, [string, ModuleInfo][]> = {}
    for (const c of SOP_COLS) cols[c.key] = []
    for (const [mod, info] of Object.entries(modules.value)) {
      const stage = computeStage(info, running.value)
      if (cols[stage]) cols[stage].push([mod, info])
    }
    return cols
  })

  const totalModules = computed(() => Object.keys(modules.value).length)

  async function fetchModules() {
    loading.value = true; error.value = ''
    try {
      const res = await fetch('/api/sop-status')
      const data = await res.json()
      modules.value = data.modules || {}
      sopPhases.value = data.sop_phases || []
    } catch (e: any) { error.value = e.message }
    finally { loading.value = false }
  }

  function moveCard(mod: string, toStage: string) {
    if (modules.value[mod]) modules.value[mod]._kanban_stage = toStage
  }

  function onPhaseChange(event: { module: string; phase: string; status: string; progress: number }) {
    const mod = modules.value[event.module]
    if (!mod) return
    mod.progress = event.progress
    mod.current_phase = event.phase
    mod.status = event.status === 'completed' ? 'completed' : 'in_progress'
    if (event.status === 'running') running.value.add(event.module)
    else if (event.status === 'completed') { running.value.delete(event.module); mod.phases_done = mod.phases_total }
  }

  async function startSOP(mod: string) {
    running.value.add(mod)
    try {
      await fetch('/api/sop/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ module: mod, mode: 'full' }) })
    } catch { running.value.delete(mod) }
  }

  return { modules, columns, loading, error, totalModules, running, sopPhases, SOP_COLS, fetchModules, moveCard, onPhaseChange, startSOP }
})
