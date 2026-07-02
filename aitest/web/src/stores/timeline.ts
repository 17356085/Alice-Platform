/** Timeline event store — client-side event log from WS + store changes.
 *  Persisted to localStorage.
 */
import { create } from 'zustand'

export type TimelineEventType =
  | 'phase_start' | 'phase_complete'
  | 'artifact_created' | 'artifact_updated'
  | 'error' | 'warning' | 'retry'
  | 'checkpoint' | 'memory_hit' | 'info'

const ICON: Record<string, string> = {
  phase_start: '🟢', phase_complete: '✅', artifact_created: '📄', artifact_updated: '📄',
  error: '🔴', warning: '🟡', retry: '🔄', checkpoint: '💾', memory_hit: '🧠', info: 'ℹ️',
}
const COLOR: Record<string, string> = {
  phase_start: 'info', phase_complete: 'success', artifact_created: 'gold',
  artifact_updated: 'secondary', error: 'destructive', warning: 'warning',
  retry: 'info', checkpoint: 'secondary', memory_hit: 'gold', info: 'secondary',
}

export interface TimelineEvent {
  id: string
  ts: number
  type: TimelineEventType
  module: string
  phase?: string
  agent?: string
  message: string
  detail?: string
  icon?: string
  color?: string
  tokensIn?: number
  tokensOut?: number
  cost?: number
  duration?: number
  output?: string
}

const STORAGE_KEY = 'tlo-timeline'
const MAX_EVENTS = 500
let seq = 0

function makeEvent(e: Omit<TimelineEvent, 'id' | 'ts'>): TimelineEvent {
  return {
    ...e,
    id: `${Date.now()}-${seq++}`, ts: Date.now(),
    icon: e.icon || ICON[e.type] || 'ℹ️',
    color: e.color || COLOR[e.type] || 'secondary',
  }
}

function load(): TimelineEvent[] {
  try { const raw = localStorage.getItem(STORAGE_KEY); return raw ? JSON.parse(raw) : [] }
  catch { return [] }
}
function save(events: TimelineEvent[]) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(events.slice(-MAX_EVENTS))) }
  catch { /* quota */ }
}

interface TimelineState {
  events: TimelineEvent[]
  add: (e: Omit<TimelineEvent, 'id' | 'ts'>) => void
  clear: () => void
  byModule: (mod: string) => TimelineEvent[]
  recent: (n?: number) => TimelineEvent[]
}

export const useTimelineStore = create<TimelineState>((set, get) => ({
  events: load(),

  add: (e) => {
    const event = makeEvent(e)
    set(state => { const events = [...state.events, event]; save(events); return { events } })
  },

  clear: () => { localStorage.removeItem(STORAGE_KEY); set({ events: [] }) },

  byModule: (mod) => get().events.filter(e => e.module === mod),

  recent: (n = 20) => get().events.slice(-n).reverse(),
}))

export function addTimelineEvent(e: Omit<TimelineEvent, 'id' | 'ts'>) {
  useTimelineStore.getState().add(e)
}
