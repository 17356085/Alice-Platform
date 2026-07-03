/**
 * WebSocket Event Definitions — shared contract between backend and frontend.
 *
 * v3.1: Defines all WS event types and their payload schemas.
 * Both terminal.py and kanban.py emit events matching these definitions.
 */

// ── Kanban WS Events ────────────────────────────────────────────────

export interface KanbanPhaseChangeEvent {
  type: 'phase_change'
  module: string
  phase: string
  status: 'running' | 'completed' | 'failed'
  progress: number
  message: string
  timestamp: string
}

export interface KanbanCardMovedEvent {
  type: 'card_moved'
  module: string
  from_stage: string
  to_stage: string
  timestamp: string
}

export interface KanbanConnectedEvent {
  type: 'connected'
  connections: number
  timestamp: string
}

export interface KanbanPongEvent {
  type: 'pong'
}

export type KanbanWSEvent =
  | KanbanPhaseChangeEvent
  | KanbanCardMovedEvent
  | KanbanConnectedEvent
  | KanbanPongEvent

// ── Terminal WS Events ──────────────────────────────────────────────

export interface TerminalObservationEvent {
  type: string  // ObservationEvent.type.value (skill_start, skill_complete, etc.)
  agent: string
  module: string
  page: string
  data: Record<string, unknown>
  timestamp: string
}

export type TerminalWSEvent = TerminalObservationEvent

// ── WS Event Type Constants ─────────────────────────────────────────

export const WS_EVENTS = {
  // Kanban
  PHASE_CHANGE: 'phase_change',
  CARD_MOVED: 'card_moved',
  CONNECTED: 'connected',
  PONG: 'pong',
} as const

// ── WS Action Types (client → server) ───────────────────────────────

export const WS_ACTIONS = {
  PING: 'ping',
  CARD_MOVE: 'card_move',
} as const
