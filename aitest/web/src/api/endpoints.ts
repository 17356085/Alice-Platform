/** API endpoint constants — single source of truth.

Usage:
  import { ENDPOINTS } from '@/api/endpoints'
  const data = await api.get(ENDPOINTS.SOP_STATUS)
*/
export const ENDPOINTS = {
  // SOP & Kanban
  SOP_STATUS:        '/api/sop-status',
  SOP_START:         '/api/sop/start',

  // Chat (SSE-backed AI conversations)
  CHAT_SESSIONS:     '/api/chat/sessions',
  CHAT_MESSAGES:     (sid: string) => `/api/chat/sessions/${sid}/messages`,
  CHAT_STREAM:       (sid: string, mid: string) => `/api/chat/sessions/${sid}/stream/${mid}`,
  CHAT_HISTORY:      (sid: string) => `/api/chat/sessions/${sid}/history`,
  CHAT_INTERACT:     (sid: string) => `/api/chat/sessions/${sid}/interact`,

  // Onboarding
  ONBOARDING_START:    '/api/onboarding/start',
  ONBOARDING_VALIDATE: '/api/onboarding/validate-path',
  ONBOARDING_STATUS:   (sid: string) => `/api/onboarding/${sid}/status`,
  ONBOARDING_CONFIRM:  (sid: string) => `/api/onboarding/${sid}/confirm`,
  ONBOARDING_CANCEL:   (sid: string) => `/api/onboarding/${sid}/cancel`,
  ONBOARDING_WS:       (sid: string) => `/api/onboarding/ws/${sid}`,

  // WebSocket
  WS_KANBAN:         '/ws/kanban',

  // Reports & Knowledge
  KPI_SUMMARY:       '/api/kpi/summary',
  HEALTH:            '/health',
} as const
