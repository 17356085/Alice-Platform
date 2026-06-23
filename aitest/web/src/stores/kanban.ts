import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface ModuleInfo {
  status: string
  phases: number
  pages: number
  failed: number
  updated: string
  progress?: number
  current_phase?: string
  _kanban_stage?: string
}

export const useKanbanStore = defineStore('kanban', () => {
  const modules = ref<Record<string, ModuleInfo>>({})
  const loading = ref(false)
  const error = ref('')
  const running = ref<Set<string>>(new Set())

  const columns = computed(() => {
    const cols: Record<string, [string, ModuleInfo][]> = {
      pending: [], planning: [], executing: [], analyzing: [], completed: [],
    }
    for (const [mod, info] of Object.entries(modules.value)) {
      const stage = info._kanban_stage || info.status
      if (stage === 'completed') cols.completed.push([mod, info])
      else if (stage === 'completed_with_issues' || stage === 'analyzing') cols.analyzing.push([mod, info])
      else if (stage === 'ready' || stage === 'planning' || stage === 'in_progress') {
        // In-progress/executing goes to executing column
        if (running.value.has(mod)) {
          cols.executing.push([mod, info])
        } else {
          cols.planning.push([mod, info])
        }
      }
      else cols.pending.push([mod, info])
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
    } catch (e: any) { error.value = e.message }
    finally { loading.value = false }
  }

  function moveCard(mod: string, toStage: string) {
    if (modules.value[mod]) modules.value[mod]._kanban_stage = toStage
  }

  // 🆕 SOP phase change handler (called by WebSocket)
  function onPhaseChange(event: { module: string; phase: string; status: string; progress: number; message: string }) {
    const { module, phase, status, progress, message } = event
    const mod = modules.value[module]
    if (!mod) return

    mod.progress = progress
    mod.current_phase = phase
    mod.status = status === 'completed' ? 'completed' : 'in_progress'

    if (status === 'running') {
      running.value.add(module)
      // Map phase to Kanban column
      const phaseToStage: Record<string, string> = {
        'Requirement': 'planning', 'Test Strategy': 'planning', 'Test Design': 'executing',
        'Automation': 'executing', 'Environment': 'executing', 'Execution': 'executing',
        'Bug Analysis': 'analyzing', 'Report': 'completed', 'Knowledge': 'completed',
      }
      mod._kanban_stage = phaseToStage[phase] || mod._kanban_stage
    } else if (status === 'completed') {
      running.value.delete(module)
      mod._kanban_stage = 'completed'
      mod.phases = 9
    }
  }

  // 🆕 Start SOP for a module
  async function startSOP(mod: string) {
    running.value.add(mod)
    try {
      await fetch('/api/sop/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ module: mod, mode: 'full' }),
      })
      ;(window as any).__tlo_toast?.add(`SOP started: ${mod}`, 'info')
    } catch {
      running.value.delete(mod)
      ;(window as any).__tlo_toast?.add(`Failed to start SOP: ${mod}`, 'error')
    }
  }

  return { modules, columns, loading, error, totalModules, running, fetchModules, moveCard, onPhaseChange, startSOP }
})
