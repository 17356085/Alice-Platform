/** Onboarding Store — Zustand port. Multi-step project discovery wizard.
 *  Pinia ref/reactive → Zustand plain state. No Proxy overhead.
 */
import { create } from 'zustand'
import { api } from '@/api/client'
import { ENDPOINTS } from '@/api/endpoints'

// ── Types ──────────────────────────────────────────────────────

export interface MenuNode {
  label: string
  route: string
  type: 'menu_group' | 'page'
  children?: MenuNode[]
  icon?: string
}

export interface PageInfo {
  id: string
  title: string
  route: string
  menu_path: string[]
  page_object?: string
  elements?: Record<string, any>
}

const MAX_ERRORS = 50

// ── Selectors ──────────────────────────────────────────────────

const STEPS = ['init', 'validating', 'scanning_menu', 'confirm_menu', 'discovering_pages', 'observing_pages', 'generating_config', 'indexing', 'completed']

export const selectStepIndex = (state: OnboardingState) => STEPS.indexOf(state.step)
export const selectIsMenuReady = (state: OnboardingState) => state.step === 'confirm_menu' || STEPS.indexOf(state.step) >= 3
export const selectIsComplete = (state: OnboardingState) => state.step === 'completed'
export const selectIsFailed = (state: OnboardingState) => state.step === 'failed'

// ── Store ──────────────────────────────────────────────────────

export interface OnboardingState {
  sessionId: string; projectId: string; baseUrl: string
  sourceType: 'url' | 'local'; projectPath: string
  step: string; progress: number
  currentPage: string; totalPages: number; completedPages: number
  menuTree: MenuNode[]; pages: PageInfo[]
  errors: string[]; result: Record<string, any> | null
  isRunning: boolean; wsConnected: boolean

  start: (url: string, pid: string, username: string, password: string) => Promise<void>
  pollStatus: () => Promise<void>
  confirmMenu: (editedMenu?: MenuNode[]) => Promise<void>
  cancel: () => Promise<void>
  reset: () => void
}

export const useOnboardingStore = create<OnboardingState>((set, get) => ({
  sessionId: '', projectId: '', baseUrl: '',
  sourceType: 'url', projectPath: '',
  step: 'init', progress: 0,
  currentPage: '', totalPages: 0, completedPages: 0,
  menuTree: [], pages: [],
  errors: [], result: null,
  isRunning: false, wsConnected: false,

  async start(url: string, pid: string, username: string, password: string) {
    set({ isRunning: true, errors: [], projectId: pid, baseUrl: url })
    const { sourceType, projectPath } = get()
    try {
      const data = await api.post<{ session_id: string; step: string }>(ENDPOINTS.ONBOARDING_START, {
        url: sourceType === 'url' ? url : '',
        project_id: pid,
        username, password,
        source_type: sourceType,
        project_path: sourceType === 'local' ? projectPath : '',
        observe_pages: sourceType === 'url',
        generate_page_objects: false,
      })
      set({ sessionId: data.session_id, step: data.step, progress: 0 })
    } catch (e: any) {
      set(state => ({
        errors: state.errors.length < MAX_ERRORS ? [...state.errors, `Start failed: ${e.message}`] : state.errors,
        isRunning: false,
      }))
    }
  },

  async pollStatus() {
    const { sessionId } = get()
    if (!sessionId) return
    try {
      const state = await api.get<any>(ENDPOINTS.ONBOARDING_STATUS(sessionId))
      set(s => {
        const updates: Partial<OnboardingState> = {
          step: state.step, progress: state.progress,
          currentPage: state.current_page, totalPages: state.total_pages, completedPages: state.completed_pages,
        }
        if (state.menu_tree?.length) updates.menuTree = state.menu_tree
        if (state.pages?.length) updates.pages = state.pages
        if (state.errors?.length) updates.errors = state.errors
        if (state.result) updates.result = state.result
        if (['completed', 'failed', 'cancelled'].includes(state.step)) updates.isRunning = false
        return updates as any
      })
    } catch (e: any) {
      set(s => ({
        errors: s.errors.length < MAX_ERRORS ? [...s.errors, `Poll error: ${e.message}`]
              : s.errors.length === MAX_ERRORS ? [...s.errors.slice(1), '⚠️ Error log full'] : s.errors,
      }))
    }
  },

  async confirmMenu(editedMenu?: MenuNode[]) {
    const { sessionId } = get()
    if (!sessionId) return
    try {
      await api.post(ENDPOINTS.ONBOARDING_CONFIRM(sessionId), { menu_tree: editedMenu || null })
    } catch {
      set(s => ({ errors: s.errors.length < MAX_ERRORS ? [...s.errors, 'Confirm failed'] : s.errors }))
    }
  },

  async cancel() {
    const { sessionId } = get()
    if (!sessionId) return
    try { await api.post(ENDPOINTS.ONBOARDING_CANCEL(sessionId)) } catch { /* ignore */ }
    set({ isRunning: false, step: 'cancelled' })
  },

  reset() {
    set({
      sessionId: '', projectId: '', baseUrl: '',
      step: 'init', progress: 0,
      currentPage: '', totalPages: 0, completedPages: 0,
      menuTree: [], pages: [],
      errors: [], result: null,
      isRunning: false, wsConnected: false,
    })
  },
}))
