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

// SOP 9 phases — one-to-one with agent-definitions.yaml full-sop orchestrator
// (Preflight + Quality Gate excluded — they are gates, not agent phases)
const SOP_COLS: { key: string; label: string; icon: string; idx: number }[] = [
  { key: 'Project Init', label: '1. Project Init', icon: '🔰', idx: 0 },
  { key: 'Requirement', label: '2. Requirement', icon: '📋', idx: 1 },
  { key: 'Test Design', label: '3. Test Design', icon: '📝', idx: 2 },
  { key: 'Automation', label: '4. Automation', icon: '⚙️', idx: 3 },
  { key: 'Execute & Debug', label: '5. Execute', icon: '▶️', idx: 4 },
  { key: 'Bug Analysis', label: '6. Bug Analysis', icon: '🔍', idx: 5 },
  { key: 'Data Sanitization', label: '7. Sanitize', icon: '🧹', idx: 6 },
  { key: 'Report', label: '8. Report', icon: '📊', idx: 7 },
  { key: 'Knowledge', label: '9. Knowledge', icon: '🧠', idx: 8 },
]

function computeStage(info: ModuleInfo, running: Set<string>): string {
  if (!info.phase_status || Object.keys(info.phase_status).length === 0) return 'Project Init'
  // If all phases done → Knowledge column
  if (info.phases_done >= info.phases_total) return 'Knowledge'
  // Find last completed phase
  let current = 'Project Init'
  for (const [phase, done] of Object.entries(info.phase_status)) {
    if (done) current = phase
  }
  if (running.has(info._kanban_stage || '') && info.current_phase) {
    return info.current_phase in info.phase_status ? info.current_phase : current
  }
  return current
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
