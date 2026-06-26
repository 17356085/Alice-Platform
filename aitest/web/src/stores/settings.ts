/** Settings Store — Zustand port. Centralized app + project settings.
 *
 * Persists to localStorage('tlo-settings') on every update.
 */
import { create } from 'zustand'

const STORAGE_KEY = 'tlo-settings'

// ── Types ──────────────────────────────────────────────────────

export interface ProviderAccount {
  id: string
  provider: 'claude' | 'openai' | 'deepseek' | 'ollama'
  label: string
  apiKey?: string
  model?: string
  baseUrl?: string
}

export interface AppSettings {
  theme: string           // default | dusk | lime | ocean | retro | neo | forest
  darkMode: boolean
  language: string        // zh | en
  uiScale: number         // 75-200, default 100

  provider: string        // primary provider name
  fallbackChain: string[] // provider fallback order
  accounts: ProviderAccount[]

  defaultModel: string
  thinkingLevel: string   // low | medium | high

  auditInterval: number   // seconds
  costBudget: number      // USD monthly cap

  notifyBuildComplete: boolean
  notifyRateLimit: boolean
}

export interface ProjectSettings {
  projectId: string
  provider?: string
  model?: string
  maxParallel: number
  mainBranch: string
  githubToken?: string
  githubRepo?: string
  gitlabToken?: string
  gitlabProject?: string
}

// ── Defaults ───────────────────────────────────────────────────

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

function persist(v: AppSettings) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(v)) } catch { /* ignore */ }
}

// ── State ──────────────────────────────────────────────────────

export interface SettingsState {
  app: AppSettings
  projectOverrides: Record<string, ProjectSettings>

  // App
  updateApp: (patch: Partial<AppSettings>) => void
  addAccount: (account: ProviderAccount) => void
  removeAccount: (id: string) => void

  // Project
  getProjectSettings: (projectId: string) => ProjectSettings
  updateProject: (projectId: string, patch: Partial<ProjectSettings>) => void

  // Reset
  resetApp: () => void
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  app: load(),
  projectOverrides: {},

  updateApp(patch: Partial<AppSettings>) {
    set(state => {
      const app = { ...state.app, ...patch }
      persist(app)
      return { app }
    })
  },

  addAccount(account: ProviderAccount) {
    set(state => {
      const a = { ...account, id: account.id || Date.now().toString(36) }
      const app = { ...state.app, accounts: [...state.app.accounts, a] }
      persist(app)
      return { app }
    })
  },

  removeAccount(id: string) {
    set(state => {
      const app = { ...state.app, accounts: state.app.accounts.filter(a => a.id !== id) }
      persist(app)
      return { app }
    })
  },

  getProjectSettings(projectId: string): ProjectSettings {
    return get().projectOverrides[projectId] || { projectId, maxParallel: 4, mainBranch: 'main' }
  },

  updateProject(projectId: string, patch: Partial<ProjectSettings>) {
    set(state => {
      const current = get().getProjectSettings(projectId)
      return {
        projectOverrides: {
          ...state.projectOverrides,
          [projectId]: { ...current, ...patch, projectId },
        },
      }
    })
  },

  resetApp() {
    const app = { ...defaults }
    persist(app)
    set({ app })
  },
}))
