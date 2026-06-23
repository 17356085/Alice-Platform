/** Project Store — multi-project management + active project switching.

Enables workspace isolation: Dashboard (all projects) vs Workspace (active project context).
*/
import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { api } from '@/api/client'
import { ENDPOINTS } from '@/api/endpoints'

export interface ProjectInfo {
  id: string
  name: string
  path: string
  description?: string
  modules?: string[]
  status?: string
  updated_at?: string
}

const STORAGE_KEY = 'tlo-active-project'

function loadProjectId(): string {
  try { return localStorage.getItem(STORAGE_KEY) || '' } catch { return '' }
}
function saveProjectId(id: string) {
  try { localStorage.setItem(STORAGE_KEY, id) } catch { /* ignore */ }
}

export const useProjectStore = defineStore('project', () => {
  const projects = ref<ProjectInfo[]>([])
  const activeId = ref<string>(loadProjectId())
  const loading = ref(false)
  const error = ref('')

  const activeProject = computed(() =>
    projects.value.find(p => p.id === activeId.value) || null
  )
  const hasProjects = computed(() => projects.value.length > 0)
  const projectModules = computed(() => activeProject.value?.modules || [])

  // ── Fetch ───────────────────────────────────────────────────

  async function fetchProjects(projectId?: string) {
    loading.value = true; error.value = ''
    try {
      const pid = projectId || activeId.value
      const qs = pid ? `?project=${encodeURIComponent(pid)}` : ''
      // Use sop-status as project list proxy (each module maps to a project)
      const data = await api.get<{ modules: Record<string, any>; projects?: ProjectInfo[] }>(ENDPOINTS.SOP_STATUS + qs)
      if (data.projects) {
        projects.value = data.projects
      } else {
        // Fallback: derive from modules if no explicit project list
        const existing = new Set(projects.value.map(p => p.id))
        for (const [modId, info] of Object.entries(data.modules || {})) {
          if (!existing.has(modId)) {
            projects.value.push({
              id: modId, name: (info as any).name || modId, path: '',
              modules: (info as any).pages_list || [],
              status: (info as any).status,
              updated_at: (info as any).updated,
            })
          }
        }
      }
    } catch (e: any) { error.value = e.message }
    finally { loading.value = false }
  }

  // ── Actions ─────────────────────────────────────────────────

  function setActive(id: string) {
    activeId.value = id
    saveProjectId(id)
  }

  function addProject(project: ProjectInfo) {
    projects.value.push(project)
  }

  function removeProject(id: string) {
    projects.value = projects.value.filter(p => p.id !== id)
    if (activeId.value === id) {
      activeId.value = projects.value[0]?.id || ''
      saveProjectId(activeId.value)
    }
  }

  // ── Init ────────────────────────────────────────────────────

  // Auto-fetch on first access
  let _initialized = false
  function init() {
    if (!_initialized) {
      _initialized = true
      fetchProjects(activeId.value || undefined)
    }
  }

  return {
    projects, activeId, activeProject, hasProjects, projectModules, loading, error,
    fetchProjects, setActive, addProject, removeProject, init,
  }
})
