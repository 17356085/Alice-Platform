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
const SESSION_STORAGE_KEY = 'tlo-onboarding-session'

function saveSessionToStorage(state: Partial<OnboardingState>) {
  try {
    sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify({
      sessionId: state.sessionId,
      projectId: state.projectId,
      baseUrl: state.baseUrl,
      sourceType: state.sourceType,
      projectPath: state.projectPath,
      step: state.step,
      savedAt: Date.now(),
    }))
  } catch { /* quota exceeded */ }
}

function clearSessionFromStorage() {
  try { sessionStorage.removeItem(SESSION_STORAGE_KEY) } catch { /* */ }
}

export function getStoredSession(): { sessionId: string; projectId: string; baseUrl: string; sourceType: 'url' | 'local'; projectPath: string; step: string } | null {
  try {
    const raw = sessionStorage.getItem(SESSION_STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    // Expire after 2 hours (matches backend TTL)
    if (Date.now() - parsed.savedAt > 2 * 60 * 60 * 1000) {
      sessionStorage.removeItem(SESSION_STORAGE_KEY)
      return null
    }
    return parsed
  } catch { return null }
}

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
  checkpoint: Record<string, any> | null   // partial results from previous cancelled session

  start: (url: string, pid: string, username: string, password: string, outputPath?: string, resume?: boolean) => Promise<void>
  pollStatus: () => Promise<void>
  confirmMenu: (editedMenu?: MenuNode[]) => Promise<void>
  cancel: () => Promise<void>
  reset: () => void
  restore: (saved: { sessionId: string; projectId: string; baseUrl: string; sourceType: 'url' | 'local'; projectPath: string }) => void
}

export const useOnboardingStore = create<OnboardingState>((set, get) => ({
  sessionId: '', projectId: '', baseUrl: '',
  sourceType: 'url', projectPath: '',
  step: 'init', progress: 0,
  currentPage: '', totalPages: 0, completedPages: 0,
  menuTree: [], pages: [],
  errors: [], result: null,
  isRunning: false, wsConnected: false,
  checkpoint: null,

  async start(url: string, pid: string, username: string, password: string, outputPath: string = '', resume: boolean = false) {
    const { sourceType, projectPath } = get()
    set({ isRunning: true, errors: [], projectId: pid, baseUrl: url })
    try {
      const data = await api.post<{ session_id: string; step: string; progress: number; checkpoint: Record<string, unknown> | null }>(ENDPOINTS.ONBOARDING_START, {
        url: sourceType === 'url' ? url : '',
        project_id: pid,
        username, password,
        source_type: sourceType,
        project_path: sourceType === 'local' ? projectPath : '',
        output_path: outputPath,
        resume: resume,
        observe_pages: sourceType === 'url',
        generate_page_objects: false,
      })
      set(s => {
        const updates: Partial<OnboardingState> = {
          sessionId: data.session_id,
          step: data.step,
          progress: data.progress ?? 0,
          checkpoint: data.checkpoint ?? null,
        }
        saveSessionToStorage({ ...s, ...updates })
        return updates
      })
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e)
      set(state => ({
        errors: state.errors.length < MAX_ERRORS ? [...state.errors, `Start failed: ${msg}`] : state.errors,
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
        if (['completed', 'failed', 'cancelled'].includes(state.step)) {
          updates.isRunning = false
          clearSessionFromStorage()
        }
        // Persist step for refresh recovery
        if (!['completed', 'failed', 'cancelled'].includes(state.step)) {
          saveSessionToStorage({ ...s, ...updates })
        }
        return updates as Partial<OnboardingState>
      })
    } catch (e: unknown) {
      // 404 = session expired (server restart, TTL, etc.) → auto-reset
      const status = (e as { status?: number }).status
      const msg = e instanceof Error ? e.message : String(e)
      if (status === 404 || msg.includes('404')) {
        clearSessionFromStorage()
        set({ isRunning: false, step: 'failed', errors: ['Session expired — server may have restarted. Please try again.'] })
        return
      }
      set(s => ({
        errors: s.errors.length < MAX_ERRORS ? [...s.errors, `Poll error: ${msg}`]
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
    // Don't clear sessionStorage — keep checkpoint data for potential resume
    set(s => {
      saveSessionToStorage({ ...s, step: 'cancelled', isRunning: false })
      return { isRunning: false, step: 'cancelled' }
    })
  },

  restore(saved: { sessionId: string; projectId: string; baseUrl: string; sourceType: 'url' | 'local'; projectPath: string }) {
    set({
      sessionId: saved.sessionId,
      projectId: saved.projectId,
      baseUrl: saved.baseUrl,
      sourceType: saved.sourceType,
      projectPath: saved.projectPath,
      isRunning: true,
    })
  },

  reset() {
    clearSessionFromStorage()
    set({
      sessionId: '', projectId: '', baseUrl: '',
      step: 'init', progress: 0,
      currentPage: '', totalPages: 0, completedPages: 0,
      menuTree: [], pages: [],
      errors: [], result: null,
      isRunning: false, wsConnected: false,
      checkpoint: null,
    })
  },
}))
