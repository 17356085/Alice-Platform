import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface ModuleInfo {
  status: string
  phases: number
  pages: number
  failed: number
  updated: string
  _kanban_stage?: string
}

export const useKanbanStore = defineStore('kanban', () => {
  const modules = ref<Record<string, ModuleInfo>>({})
  const loading = ref(false)
  const error = ref('')

  const columns = computed(() => {
    const cols: Record<string, [string, ModuleInfo][]> = {
      pending: [], planning: [], executing: [], analyzing: [], completed: [],
    }
    for (const [mod, info] of Object.entries(modules.value)) {
      const stage = info._kanban_stage || info.status
      if (stage === 'completed') cols.completed.push([mod, info])
      else if (stage === 'completed_with_issues' || stage === 'analyzing') cols.analyzing.push([mod, info])
      else if (stage === 'ready' || stage === 'planning') cols.planning.push([mod, info])
      else if (stage === 'in_progress' || stage === 'executing') cols.executing.push([mod, info])
      else cols.pending.push([mod, info])
    }
    return cols
  })

  const totalModules = computed(() => Object.keys(modules.value).length)

  async function fetchModules() {
    loading.value = true
    error.value = ''
    try {
      const res = await fetch('/api/sop-status')
      const data = await res.json()
      modules.value = data.modules || {}
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  function moveCard(mod: string, toStage: string) {
    if (modules.value[mod]) {
      modules.value[mod]._kanban_stage = toStage
    }
  }

  return { modules, columns, loading, error, totalModules, fetchModules, moveCard }
})
