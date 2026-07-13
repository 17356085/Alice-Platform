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
  ONBOARDING_STATUS:   (sid: string) => `/api/v1/onboarding/${encodeURIComponent(sid)}/status`,
  ONBOARDING_CONFIRM:  (sid: string) => `/api/v1/onboarding/${encodeURIComponent(sid)}/confirm`,
  ONBOARDING_CANCEL:   (sid: string) => `/api/v1/onboarding/${encodeURIComponent(sid)}/cancel`,
  ONBOARDING_WS:       (sid: string) => `/api/v1/onboarding/ws/${encodeURIComponent(sid)}`,

  // WebSocket — migrated to v1
  WS_KANBAN:         '/api/v1/kanban/ws',

  // HITL Pause/Resume (Task 2 P0) — migrated to v1
  TASK_PAUSE_STATUS:  (tid: string) => `/api/v1/chat/tasks/${tid}/pause-status`,
  TASK_RESUME:        (tid: string) => `/api/v1/chat/tasks/${tid}/resume`,

  // Reports & Knowledge — migrated to v1
  KPI_SUMMARY:       '/api/v1/kpi/summary',
  KPI_PRODUCT:       '/api/v1/kpi/product',
  HEALTH:            '/health',

  // Runs (v1 API) — P7-2 Phase 3
  RUNS_CREATE:       '/api/v1/runs',
  RUNS_GET:          (runId: string) => `/api/v1/runs/${runId}`,
  RUNS_LIST:         '/api/v1/runs',

  // Global resource workbench
  EVALUATIONS_LIST:  '/api/v1/evaluations',
  REGISTRY:          '/api/v1/registry',

  // Phase 2 — Studio read models
  AGENTS_LIST:       '/api/v1/agents/list',
  AGENTS_RUN:        '/api/v1/agents/run',
  AGENTS_STATUS_ALL: '/api/v1/agents/status/all',
  WORKFLOWS_LIST:     '/api/v1/workflows',
  WORKFLOW_UPDATE:    (workflowId: string) => `/api/v1/workflows/${encodeURIComponent(workflowId)}`,
  WORKFLOW_DELETE:    (workflowId: string) => `/api/v1/workflows/${encodeURIComponent(workflowId)}`,
  WORKFLOW_VALIDATE:  (workflowId: string) => `/api/v1/workflows/${encodeURIComponent(workflowId)}/validate`,
  RUNS_HISTORY:      '/api/history',
  RUNS_INSPECTOR:    (runId: string) => `/api/runs/${runId}/inspector`,
  RUNS_TIMELINE:     (runId: string) => `/api/runs/${runId}/timeline`,
  RUNS_DEBUG:        (runId: string) => `/api/runs/${runId}/debug`,
  RUNS_REPORT:       (runId: string) => `/api/runs/${runId}/report`,
  OBSERVABILITY:     '/api/v1/observability/snapshot',
  MEMORY_STATS:      '/api/v1/memory/stats',
  MEMORY_SEARCH:     '/api/v1/memory/search',
  KNOWLEDGE_STATS:   '/api/v1/knowledge/stats',
  KNOWLEDGE_SEARCH:  '/api/v1/knowledge/search',
  ARTIFACTS_ALL:     (projectId: string) => `/api/v1/kpi/artifacts/${encodeURIComponent(projectId)}/all`,
  ARTIFACT_LINEAGE:  (projectId: string) => `/api/v1/kpi/artifacts/lineage/${encodeURIComponent(projectId)}`,
  BUGS_LIST:         '/api/v1/bugs/list',
  BUG_UPDATE:        (bugId: string) => `/api/v1/bugs/${encodeURIComponent(bugId)}`,
  KANBAN_OVERVIEW:   '/api/v1/kanban/overview',
  EXECUTION_CANCEL:  (requestId: string) => `/api/executions/${encodeURIComponent(requestId)}/cancel`,
  PROVIDERS_LIST:    '/api/v1/providers',
  NOTIFICATIONS:     '/api/v1/notifications',
  MODULES:           '/api/v1/modules',
  MODULE:            (moduleId: string) => `/api/v1/modules/${encodeURIComponent(moduleId)}`,
  MODULE_PAGES:      (moduleId: string) => `/api/v1/modules/${encodeURIComponent(moduleId)}/pages`,
  MODULE_PAGE:       (moduleId: string, pageId: string) => `/api/v1/modules/${encodeURIComponent(moduleId)}/pages/${encodeURIComponent(pageId)}`,
} as const
