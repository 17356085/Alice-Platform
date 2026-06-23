/** Settings Store — centralized app + project settings.

Replaces scattered localStorage reads across views.
Structure mirrors Aperant's settings-store.ts: app settings + per-project overrides.
*/
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const STORAGE_KEY = 'tlo-settings'

export interface ProviderAccount {
  id: string
  provider: 'claude' | 'openai' | 'deepseek' | 'ollama'
  label: string
  apiKey?: string
  model?: string
  baseUrl?: string
}

export interface AppSettings {
  // Appearance
  theme: string           // default | dusk | lime | ocean | retro | neo | forest
  darkMode: boolean
  language: string        // zh | en
  uiScale: number         // 75-200, default 100

  // Provider
  provider: string        // primary provider name
  fallbackChain: string[] // provider fallback order
  accounts: ProviderAccount[]

  // Agent
  defaultModel: string
  thinkingLevel: string   // low | medium | high

  // Audit
  auditInterval: number   // seconds
  costBudget: number      // USD monthly cap

  // Notifications
  notifyBuildComplete: boolean
  notifyRateLimit: boolean
}

export interface ProjectSettings {
  projectId: string
  provider?: string          // override global provider
  model?: string             // override global model
  maxParallel: number        // max parallel tasks
  mainBranch: string         // git main branch
  githubToken?: string
  githubRepo?: string
  gitlabToken?: string
  gitlabProject?: string
}

const defaults: AppSettings = {
  theme: 'default',
  darkMode: false,
  language: 'zh',
  uiScale: 100,
  provider: 'claude',
  fallbackChain: ['claude', 'deepseek', 'openai'],
  accounts: [],
  defaultModel: 'claude-sonnet-4-6',
  thinkingLevel: 'medium',
  auditInterval: 300,
  costBudget: 50,
  notifyBuildComplete: true,
  notifyRateLimit: true,
}

function load(): AppSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? { ...defaults, ...JSON.parse(raw) } : { ...defaults }
  } catch { return { ...defaults } }
}

export const useSettingsStore = defineStore('settings', () => {
  const app = ref<AppSettings>(load())
  const projectOverrides = ref<Record<string, ProjectSettings>>({})

  // Persist on change
  watch(app, (v) => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(v)) } catch { /* ignore */ }
  }, { deep: true })

  // ── App settings ────────────────────────────────────────────

  function updateApp(patch: Partial<AppSettings>) {
    Object.assign(app.value, patch)
  }

  function addAccount(account: ProviderAccount) {
    account.id = account.id || Date.now().toString(36)
    app.value.accounts.push(account)
  }

  function removeAccount(id: string) {
    app.value.accounts = app.value.accounts.filter(a => a.id !== id)
  }

  // ── Project settings ─────────────────────────────────────────

  function getProjectSettings(projectId: string): ProjectSettings {
    return projectOverrides.value[projectId] || { projectId, maxParallel: 4, mainBranch: 'main' }
  }

  function updateProject(projectId: string, patch: Partial<ProjectSettings>) {
    const current = getProjectSettings(projectId)
    projectOverrides.value[projectId] = { ...current, ...patch, projectId }
  }

  // ── Reset ───────────────────────────────────────────────────

  function resetApp() {
    app.value = { ...defaults }
  }

  return {
    app, projectOverrides,
    updateApp, addAccount, removeAccount,
    getProjectSettings, updateProject,
    resetApp,
  }
})
