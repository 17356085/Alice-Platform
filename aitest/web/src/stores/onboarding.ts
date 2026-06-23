import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api/client'
import { ENDPOINTS } from '@/api/endpoints'

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

export interface OnboardingState {
  session_id: string
  project_id: string
  base_url: string
  step: string
  progress: number
  current_page: string
  total_pages: number
  completed_pages: number
  menu_tree: MenuNode[]
  pages: PageInfo[]
  errors: string[]
  result: Record<string, any> | null
  started_at: string
  completed_at: string
}

const API = ENDPOINTS.ONBOARDING_START.replace('/start', '')

export const useOnboardingStore = defineStore('onboarding', () => {
  const sessionId = ref<string>('')
  const projectId = ref('')
  const baseUrl = ref('')
  const sourceType = ref<'url' | 'local'>('url')
  const projectPath = ref('')
  const step = ref('init')
  const progress = ref(0)
  const currentPage = ref('')
  const totalPages = ref(0)
  const completedPages = ref(0)
  const menuTree = ref<MenuNode[]>([])
  const pages = ref<PageInfo[]>([])
  const errors = ref<string[]>([])
  const result = ref<Record<string, any> | null>(null)
  const isRunning = ref(false)
  const wsConnected = ref(false)

  // Computed
  const stepIndex = computed(() => {
    const steps = ['init', 'validating', 'scanning_menu', 'confirm_menu', 'discovering_pages', 'observing_pages', 'generating_config', 'indexing', 'completed']
    return steps.indexOf(step.value)
  })

  const isMenuReady = computed(() =>
    step.value === 'confirm_menu' || stepIndex.value >= 3
  )

  const isComplete = computed(() => step.value === 'completed')
  const isFailed = computed(() => step.value === 'failed')

  // Actions
  async function start(url: string, pid: string, username: string, password: string) {
    isRunning.value = true
    errors.value = []
    projectId.value = pid
    baseUrl.value = url

    try {
      const data = await api.post<{ session_id: string; step: string }>(ENDPOINTS.ONBOARDING_START, {
        url: sourceType.value === 'url' ? url : '',
        project_id: pid,
        username, password,
        source_type: sourceType.value,
        project_path: sourceType.value === 'local' ? projectPath.value : '',
        observe_pages: sourceType.value === 'url',
        generate_page_objects: false,
      })
      sessionId.value = data.session_id
      step.value = data.step
      progress.value = 0
    } catch (e: any) {
      errors.value.push(`Start failed: ${e.message}`)
      isRunning.value = false
    }
  }

  async function pollStatus() {
    if (!sessionId.value) return
    try {
      const state = await api.get<OnboardingState>(ENDPOINTS.ONBOARDING_STATUS(sessionId.value))
      step.value = state.step
      progress.value = state.progress
      currentPage.value = state.current_page
      totalPages.value = state.total_pages
      completedPages.value = state.completed_pages
      if (state.menu_tree?.length) menuTree.value = state.menu_tree
      if (state.pages?.length) pages.value = state.pages
      if (state.errors?.length) errors.value = state.errors
      if (state.result) result.value = state.result
      if (['completed', 'failed', 'cancelled'].includes(state.step)) isRunning.value = false
    } catch (e: any) {
      errors.value.push(`Poll error: ${e.message}`)
    }
  }

  async function confirmMenu(editedMenu?: MenuNode[]) {
    if (!sessionId.value) return
    try {
      await api.post(ENDPOINTS.ONBOARDING_CONFIRM(sessionId.value), { menu_tree: editedMenu || null })
    } catch {
      errors.value.push('Confirm failed')
    }
  }

  async function cancel() {
    if (!sessionId.value) return
    try { await api.post(ENDPOINTS.ONBOARDING_CANCEL(sessionId.value)) } catch { /* ignore */ }
    isRunning.value = false
    step.value = 'cancelled'
  }

  function reset() {
    sessionId.value = ''
    projectId.value = ''
    baseUrl.value = ''
    step.value = 'init'
    progress.value = 0
    currentPage.value = ''
    totalPages.value = 0
    completedPages.value = 0
    menuTree.value = []
    pages.value = []
    errors.value = []
    result.value = null
    isRunning.value = false
    wsConnected.value = false
  }

  return {
    sessionId, projectId, baseUrl, sourceType, projectPath, step, progress,
    currentPage, totalPages, completedPages,
    menuTree, pages, errors, result,
    isRunning, wsConnected,
    stepIndex, isMenuReady, isComplete, isFailed,
    start, pollStatus, confirmMenu, cancel, reset,
  }
})
