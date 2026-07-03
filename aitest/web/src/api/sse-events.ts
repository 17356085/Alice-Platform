/**
 * SSE Event Name Constants — shared contract between backend and frontend.
 *
 * AUTO-GENERATED from aitest/platform/ui_projection.py UIEventType class.
 * Do NOT edit manually. Regenerate with:
 *   python -c "from aitest.platform.ui_projection import UIEventType; ..."
 *
 * v3.1: Eliminates hardcoded string coupling between Python backend and TypeScript frontend.
 */

export const SSE_EVENTS = {
  THINKING_STARTED: 'ui.thinking_started',
  THINKING_CHUNK: 'ui.thinking_chunk',
  THINKING_ENDED: 'ui.thinking_ended',
  SKILL_STARTED: 'ui.skill_started',
  SKILL_PROGRESS: 'ui.skill_progress',
  SKILL_ENDED: 'ui.skill_ended',
  OBSERVATION: 'ui.observation',
  PHASE_CHANGED: 'ui.phase_changed',
  MESSAGE: 'ui.message',
  INTERACTION: 'ui.interaction',
  DONE: 'ui.done',
  ERROR: 'ui.error',
} as const

export type SSEEventType = (typeof SSE_EVENTS)[keyof typeof SSE_EVENTS]
