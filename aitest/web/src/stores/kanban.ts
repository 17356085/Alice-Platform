/** Kanban Store — Zustand port from Pinia.
 *
 * Key difference from Vue: Zustand uses plain JS objects (no Proxies).
 * shallowRef concerns are irrelevant — React state is always plain.
 * Derived values (columns, totalModules) exposed as selectors for useMemo-like behavior.
 */
import { create } from 'zustand'
import { shallow } from 'zustand/shallow'
import { Flag, ClipboardList, FileText, Wrench, Play, Search, Brush, BarChart3, Brain } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { api } from '@/api/client'
import { ENDPOINTS } from '@/api/endpoints'
import { addTimelineEvent } from './timeline'

// ── Types ──────────────────────────────────────────────────────

interface PhaseStatus { [phase: string]: boolean }
export interface ModuleInfo {
  status: string; stage: string; phase_status: PhaseStatus
  phases_done: number; phases_total: number
  pages: number; pages_list: string[]; artifacts: number
  failed: number; run_id: string; updated: string; note: string
  progress?: number; current_phase?: string; _kanban_stage?: string
  // ── Task 4 (P1): Task FSM state ──
  task_state?: string  // "backlog" | "test_planning" | "plan_review" | "test_execution" | "result_validation" | "test_approval" | "done" | "error"
}

export interface KanbanColumn {
  key: string; label: string; icon: LucideIcon; idx: number
}

// ── Constants ──────────────────────────────────────────────────

export const SOP_COLS: KanbanColumn[] = [
  { key: 'Project Init', label: '1. Project Init', icon: Flag, idx: 0 },
  { key: 'Requirement', label: '2. Requirement', icon: ClipboardList, idx: 1 },
  { key: 'Test Design', label: '3. Test Design', icon: FileText, idx: 2 },
  { key: 'Automation', label: '4. Automation', icon: Wrench, idx: 3 },
  { key: 'Execute & Debug', label: '5. Execute', icon: Play, idx: 4 },
  { key: 'Bug Analysis', label: '6. Bug Analysis', icon: Search, idx: 5 },
  { key: 'Data Sanitization', label: '7. Sanitize', icon: Brush, idx: 6 },
  { key: 'Report', label: '8. Report', icon: BarChart3, idx: 7 },
  { key: 'Knowledge', label: '9. Knowledge', icon: Brain, idx: 8 },
]

// ── Helpers ────────────────────────────────────────────────────

export function computeStage(info: ModuleInfo, running: Set<string>): string {
  if (!info.phase_status || Object.keys(info.phase_status).length === 0) return 'Project Init'
  if (info.phases_done >= info.phases_total) return 'Knowledge'
  let current = 'Project Init'
  for (const [phase, done] of Object.entries(info.phase_status)) {
    if (done) current = phase
  }
  if (running.has(info._kanban_stage || '') && info.current_phase) {
    return info.current_phase in info.phase_status ? info.current_phase : current
  }
  return current
}

// ── Selectors (derived state) ──────────────────────────────────

export const selectColumns = (state: KanbanState) => {
  const cols: Record<string, [string, ModuleInfo][]> = {}
  for (const c of SOP_COLS) cols[c.key] = []
  for (const [mod, info] of Object.entries(state.modules)) {
    const stage = computeStage(info, state.running)
    if (cols[stage]) cols[stage].push([mod, info])
  }
  return cols
}

export const selectTotalModules = (state: KanbanState) => Object.keys(state.modules).length

/**
 * MEM-AUDIT: Stabilized columns selector.
 * Uses zustand/shallow to prevent re-render when columns content hasn't changed.
 * Replaces raw `useKanbanStore(selectColumns)` which created new objects every call.
 */
export function useSelectColumns() {
  return useKanbanStore(
    state => {
      const cols: Record<string, [string, ModuleInfo][]> = {}
      for (const c of SOP_COLS) cols[c.key] = []
      for (const [mod, info] of Object.entries(state.modules)) {
        const stage = computeStage(info, state.running)
        if (cols[stage]) cols[stage].push([mod, info])
      }
      return cols
    },
    shallow,
  )
}

// ── Store ──────────────────────────────────────────────────────

/** Paused task info from GET /api/v1/chat/tasks/{id}/pause-status */
export interface PausedTask {
  task_id: string
  reason: string
  skill_id: string
  risk_level: string
  paused_at: string
}

export interface KanbanState {
  modules: Record<string, ModuleInfo>
  loading: boolean
  error: string
  running: Set<string>
  sopPhases: string[]

  // ── HITL Pause/Resume (Task 2 P0) ──
  /** Tasks currently awaiting user approval (keyed by task_id) */
  pausedTasks: Record<string, PausedTask>
  /** Polling interval ID for pause status (for cleanup) */
  _pausePollTimer: ReturnType<typeof setInterval> | null

  fetchModules: (projectId?: string) => Promise<void>
  moveCard: (mod: string, toStage: string) => void
  onPhaseChange: (event: { module: string; phase: string; status: string; progress: number }) => void
  startSOP: (mod: string) => Promise<void>

  /** Resume a paused task — user clicked approval button */
  resumeTask: (taskId: string) => Promise<void>
  /** Start polling for paused tasks (called when component mounts) */
  startPausePolling: () => void
  /** Stop polling for paused tasks (called on unmount) */
  stopPausePolling: () => void
}

export const useKanbanStore = create<KanbanState>((set, get) => ({
  modules: {},
  loading: false,
  error: '',
  running: new Set<string>(),
  sopPhases: [],

  // ── HITL Pause/Resume initial state ──
  pausedTasks: {},
  _pausePollTimer: null,

  async fetchModules(projectId?: string) {
    set({ loading: true, error: '' })
    try {
      const qs = projectId ? `?project=${encodeURIComponent(projectId)}` : ''
      const data = await api.get<{ modules: Record<string, ModuleInfo>; sop_phases: string[] }>(ENDPOINTS.SOP_STATUS + qs)
      set({ modules: data.modules || {}, sopPhases: data.sop_phases || [], loading: false })
    } catch (e: unknown) {
      set({ error: e instanceof Error ? e.message : String(e), loading: false })
    }
  },

  moveCard(mod: string, toStage: string) {
    set(state => {
      if (!state.modules[mod]) return state
      return {
        modules: {
          ...state.modules,
          [mod]: { ...state.modules[mod], _kanban_stage: toStage },
        },
      }
    })
  },

  onPhaseChange(event: { module: string; phase: string; status: string; progress: number }) {
    set(state => {
      const mod = state.modules[event.module]
      if (!mod) return state
      const newRunning = new Set(state.running)
      if (event.status === 'running') newRunning.add(event.module)
      else if (event.status === 'completed') { newRunning.delete(event.module) }

      // ── Timeline integration ──
      if (event.status === 'running') {
        addTimelineEvent({
          type: 'phase_start', module: event.module, phase: event.phase,
          message: `${event.module} — Phase ${event.phase} started`,
        })
      } else if (event.status === 'completed') {
        addTimelineEvent({
          type: 'phase_complete', module: event.module, phase: event.phase,
          message: `${event.module} — Phase ${event.phase} completed`,
          detail: `progress: ${event.progress}%`,
        })
      } else if (event.status === 'failed') {
        addTimelineEvent({
          type: 'error', module: event.module, phase: event.phase,
          message: `${event.module} — Phase ${event.phase} failed`,
        })
      }

      return {
        modules: {
          ...state.modules,
          [event.module]: {
            ...mod,
            progress: event.progress,
            current_phase: event.phase,
            ...(event.status === 'completed' ? { phases_done: mod.phases_total } : {}),
          },
        },
        running: newRunning,
      }
    })
  },

  async startSOP(mod: string) {
    set(state => ({ running: new Set([...state.running, mod]) }))
    addTimelineEvent({
      type: 'phase_start', module: mod,
      message: `SOP started for ${mod}`,
    })
    try {
      await api.post(ENDPOINTS.SOP_START, { module: mod, mode: 'full' })
    } catch {
      set(state => {
        const newRunning = new Set(state.running)
        newRunning.delete(mod)
        return { running: newRunning }
      })
    }
  },

  // ── HITL Pause/Resume (Task 2 P0) ──

  /** Resume a paused task — user clicked the approval button. */
  async resumeTask(taskId: string) {
    try {
      await api.post(ENDPOINTS.TASK_RESUME(taskId), {})
      // Optimistically remove from paused list
      set(state => {
        const next = { ...state.pausedTasks }
        delete next[taskId]
        return { pausedTasks: next }
      })
    } catch (e: unknown) {
      console.error(`[kanban] Failed to resume task ${taskId}:`, e)
    }
  },

  /**
   * Start polling for paused tasks. Polls every 3 seconds.
   * Call when kanban component mounts. Stops on unmount via stopPausePolling().
   *
   * Strategy: poll all running tasks for pause status.
   * A paused task has a corresponding pause.json on the backend.
   */
  startPausePolling() {
    const existing = get()._pausePollTimer
    if (existing) return // already polling

    const timer = setInterval(async () => {
      const { running } = get()
      if (running.size === 0) return

      // Check each running task for pause status
      // We don't know exact task_ids, so we check known running modules
      for (const mod of running) {
        try {
          const status = await api.get<{
            task_id: string; paused: boolean; reason: string
            skill_id: string; risk_level: string; paused_at: string
          } | null>(ENDPOINTS.TASK_PAUSE_STATUS(mod))
          if (status && status.paused) {
            set(state => ({
              pausedTasks: {
                ...state.pausedTasks,
                [status.task_id]: {
                  task_id: status.task_id,
                  reason: status.reason,
                  skill_id: status.skill_id,
                  risk_level: status.risk_level,
                  paused_at: status.paused_at,
                },
              },
            }))
          }
        } catch {
          // 404 means not paused — fine, skip
        }
      }
    }, 3000) // 3s polling interval

    set({ _pausePollTimer: timer })
  },

  /** Stop polling for paused tasks. Call on component unmount (useEffect cleanup). */
  stopPausePolling() {
    const timer = get()._pausePollTimer
    if (timer) {
      clearInterval(timer)
      set({ _pausePollTimer: null })
    }
  },
}))
