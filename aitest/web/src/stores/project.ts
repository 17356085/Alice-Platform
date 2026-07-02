/** Project Store — Zustand port. Multi-project management + active switching.
 *
 * Zustand plain objects — no Vue deep-proxy overhead.
 */
import { create } from 'zustand'
import { api } from '@/api/client'
import { ENDPOINTS } from '@/api/endpoints'

// ── Types ──────────────────────────────────────────────────────

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

// ── State ──────────────────────────────────────────────────────

export interface ProjectState {
  projects: ProjectInfo[]
  activeId: string
  loading: boolean
  error: string

  // Derived
  activeProject: () => ProjectInfo | null
  hasProjects: () => boolean
  projectModules: () => string[]

  // Actions
  fetchProjects: (projectId?: string) => Promise<void>
  setActive: (id: string) => void
  addProject: (project: ProjectInfo) => void
  removeProject: (id: string) => void
  init: () => void
}

let _initialized = false

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  activeId: loadProjectId(),
  loading: false,
  error: '',

  activeProject: () => get().projects.find(p => p.id === get().activeId) || null,
  hasProjects: () => get().projects.length > 0,
  projectModules: () => get().activeProject()?.modules || [],

  async fetchProjects(projectId?: string) {
    set({ loading: true, error: '' })
    try {
      const pid = projectId || ''
      const qs = pid ? `?project=${encodeURIComponent(pid)}` : ''
      const data = await api.get<{
        modules: Record<string, any>
        projects?: Array<{ id: string; name: string; base_url: string; framework: string; test_path: string; module_count: number }>
      }>(ENDPOINTS.SOP_STATUS + qs)

      // Use projects field if available (v3: sop-status now returns registered projects)
      if (data.projects && data.projects.length > 0) {
        const projectList: ProjectInfo[] = data.projects.map(p => ({
          id: p.id,
          name: p.name || p.id,
          path: p.base_url || p.test_path || '',
          description: p.framework || '',
          modules: [],
          status: p.module_count > 0 ? 'discovered' : 'new',
        }))
        set({ projects: projectList, loading: false })
      } else {
        // Fallback: derive from module keys (legacy behavior)
        const arr = get().projects.slice()
        const existing = new Set(arr.map(p => p.id))
        for (const [key, info] of Object.entries(data.modules || {})) {
          const m = info as Record<string, unknown>
          const projId = (m.project_id as string) || key
          if (!existing.has(projId)) {
            arr.push({
              id: projId,
              name: (m.name as string) || projId,
              path: '',
              modules: (m.pages_list as string[]) || [],
              status: m.status as ProjectInfo['status'],
              updated_at: m.updated as string,
            })
          }
        }
        set({ projects: arr, loading: false })
      }
    } catch (e: unknown) {
      set({ error: e instanceof Error ? e.message : String(e), loading: false })
    }
  },

  setActive(id: string) {
    set({ activeId: id })
    saveProjectId(id)
  },

  addProject(project: ProjectInfo) {
    set(state => ({ projects: [...state.projects, project] }))
  },

  removeProject(id: string) {
    set(state => {
      const projects = state.projects.filter(p => p.id !== id)
      const activeId = state.activeId === id ? (projects[0]?.id || '') : state.activeId
      if (activeId !== state.activeId) saveProjectId(activeId)
      return { projects, activeId }
    })
  },

  init() {
    if (!_initialized) {
      _initialized = true
      get().fetchProjects(get().activeId || undefined)
    }
  },
}))
