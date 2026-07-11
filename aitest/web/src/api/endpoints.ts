/** API endpoint constants — single source of truth.

Usage:
  import { ENDPOINTS } from '@/api/endpoints'
  const data = await api.get(ENDPOINTS.SOP_STATUS)
*/
export const ENDPOINTS = {
  // SOP & Kanban (migrated to v1)
  SOP_STATUS:        '/api/v1/kpi/sop-status',
  SOP_START:         '/api/v1/kanban/sop/start',

  // Chat (SSE-backed AI conversations) — migrated to v1
  CHAT_SESSIONS:     '/api/v1/chat/sessions',
  CHAT_MESSAGES:     (sid: string) => `/api/v1/chat/sessions/${sid}/messages`,
  CHAT_STREAM:       (sid: string, mid: string) => `/api/v1/chat/sessions/${sid}/stream/${mid}`,
  CHAT_HISTORY:      (sid: string) => `/api/v1/chat/sessions/${sid}/history`,
  CHAT_INTERACT:     (sid: string) => `/api/v1/chat/sessions/${sid}/interact`,

  // Onboarding — migrated to v1
  ONBOARDING_START:    '/api/v1/onboarding/start',
  ONBOARDING_VALIDATE: '/api/v1/onboarding/validate-path',
  ONBOARDING_STATUS:   (sid: string) => `/api/v1/onboarding/${sid}/status`,
  ONBOARDING_CONFIRM:  (sid: string) => `/api/v1/onboarding/${sid}/confirm`,
  ONBOARDING_CANCEL:   (sid: string) => `/api/v1/onboarding/${sid}/cancel`,
  ONBOARDING_WS:       (sid: string) => `/api/v1/onboarding/ws/${sid}`,

  // WebSocket — migrated to v1
  WS_KANBAN:         '/api/v1/kanban/ws',

  // HITL Pause/Resume (Task 2 P0) — migrated to v1
  TASK_PAUSE_STATUS:  (tid: string) => `/api/v1/chat/tasks/${tid}/pause-status`,
  TASK_RESUME:        (tid: string) => `/api/v1/chat/tasks/${tid}/resume`,

  // Reports & Knowledge — migrated to v1
  KPI_SUMMARY:       '/api/v1/kpi/summary',
  HEALTH:            '/health',

  // Runs (v1 API) — P7-2 Phase 3
  RUNS_CREATE:       '/api/v1/runs',
  RUNS_GET:          (runId: string) => `/api/v1/runs/${runId}`,
  RUNS_LIST:         '/api/v1/runs',

  // Global resource workbench
  EVALUATIONS_LIST:  '/api/v1/evaluations',
  REGISTRY:          '/api/v1/registry',
} as const
