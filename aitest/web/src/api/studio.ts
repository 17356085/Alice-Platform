import { api } from './client'
import { ENDPOINTS } from './endpoints'

export interface StudioRun {
  run_id: string
  status?: string
  workflow?: string
  module?: string
  agent?: string
  created_at?: string
  completed_at?: string
  total_tokens?: number
  total_cost?: number
  pages?: string[]
  [key: string]: unknown
}

export interface StudioSnapshot {
  projectId: string
  health: Record<string, unknown> | null
  productKpi: Record<string, any> | null
  runs: StudioRun[]
  agents: Record<string, string[]> | null
  moduleStatus: Record<string, string[]> | null
  workflows: Array<Record<string, any>>
  observability: Record<string, any> | null
  memory: Record<string, any> | null
  knowledge: Record<string, any> | null
  artifacts: Array<Record<string, any>>
  bugs: Array<Record<string, any>>
  kanban: Array<Record<string, any>>
  lineage: Record<string, any> | null
  providers: Array<Record<string, any>>
  sopStatus: Record<string, any> | null
}

export interface StudioNotification {
  id: string
  kind: string
  severity: string
  title: string
  message: string
  created_at?: string
  read?: boolean
  resource?: Record<string, any>
}

export interface StudioModulePage {
  id: string
  name: string
  module?: string
  description?: string
  url?: string
  config?: Record<string, unknown>
  locators?: Record<string, unknown>
  execution?: Record<string, unknown>
  enabled?: boolean
  persistent?: boolean
}

export interface StudioModulePageConfig {
  url?: string
  config?: Record<string, unknown>
  locators?: Record<string, unknown>
  execution?: Record<string, unknown>
  enabled?: boolean
}

function settledValue<T>(result: PromiseSettledResult<T>): T | null {
  return result.status === 'fulfilled' ? result.value : null
}

/**
 * Dashboard read model. Each source is independent: a missing optional API
 * must not blank the whole Studio shell while the backend is being upgraded.
 */
export async function loadStudioSnapshot(activeProjectId?: string): Promise<StudioSnapshot> {
  const projectId = activeProjectId || (typeof window !== 'undefined' ? window.localStorage.getItem('tlo-active-project') || '' : '')
  const sopQuery = projectId ? `?project=${encodeURIComponent(projectId)}` : ''
  // Project-scoped read models have no valid route without a project ID. Keep
  // the first render request-safe while the project selector is initializing.
  const artifactsRequest = projectId
    ? api.get<{ artifacts?: Array<Record<string, any>> }>(ENDPOINTS.ARTIFACTS_ALL(projectId))
    : Promise.resolve({ artifacts: [] as Array<Record<string, any>> })
  const lineageRequest = projectId
    ? api.get<Record<string, any>>(ENDPOINTS.ARTIFACT_LINEAGE(projectId))
    : Promise.resolve({})
  const kanbanRequest = api.get<{ modules?: Array<Record<string, any>> }>(
    `${ENDPOINTS.KANBAN_OVERVIEW}${projectId ? `?project_id=${encodeURIComponent(projectId)}` : ''}`,
  )
  const [health, productKpi, runsResponse, agentsResponse, modulesResponse, workflowsResponse, observability, memory, knowledge, artifactsResponse, bugsResponse, kanbanResponse, lineage, providersResponse, sopStatusResponse] =
    await Promise.allSettled([
      api.get<Record<string, unknown>>(ENDPOINTS.HEALTH),
      api.get<Record<string, any>>(ENDPOINTS.KPI_PRODUCT),
      api.get<{ runs?: StudioRun[] }>(`${ENDPOINTS.RUNS_LIST}?limit=10`),
      api.get<{ agents?: Record<string, string[]> }>(ENDPOINTS.AGENTS_LIST),
      api.get<{ modules?: Record<string, string[]> }>(ENDPOINTS.AGENTS_STATUS_ALL),
      api.get<{ workflows?: Array<Record<string, any>> }>(`${ENDPOINTS.WORKFLOWS_LIST}?limit=20`),
      api.get<Record<string, any>>(ENDPOINTS.OBSERVABILITY),
      api.get<Record<string, any>>(ENDPOINTS.MEMORY_STATS),
      api.get<Record<string, any>>(ENDPOINTS.KNOWLEDGE_STATS),
      artifactsRequest,
      api.get<{ bugs?: Array<Record<string, any>> }>(`${ENDPOINTS.BUGS_LIST}?limit=50`),
      kanbanRequest,
      lineageRequest,
      api.get<{ providers?: Array<Record<string, any>> }>(ENDPOINTS.PROVIDERS_LIST),
      api.get<Record<string, any>>(`${ENDPOINTS.SOP_STATUS}${sopQuery}`),
    ])

  return {
    projectId,
    health: settledValue(health),
    productKpi: settledValue(productKpi),
    runs: settledValue(runsResponse)?.runs ?? [],
    agents: settledValue(agentsResponse)?.agents ?? null,
    moduleStatus: settledValue(modulesResponse)?.modules ?? null,
    workflows: settledValue(workflowsResponse)?.workflows ?? [],
    observability: settledValue(observability),
    memory: settledValue(memory),
    knowledge: settledValue(knowledge),
    artifacts: settledValue(artifactsResponse)?.artifacts ?? [],
    bugs: settledValue(bugsResponse)?.bugs ?? [],
    kanban: settledValue(kanbanResponse)?.modules ?? [],
    lineage: settledValue(lineage),
    providers: settledValue(providersResponse)?.providers ?? [],
    sopStatus: settledValue(sopStatusResponse),
  }
}

export async function loadRunInspector(runId: string): Promise<Record<string, any>> {
  return api.get<Record<string, any>>(ENDPOINTS.RUNS_INSPECTOR(runId))
}

export async function loadRunsPage(limit = 10, offset = 0): Promise<{ runs: StudioRun[]; total: number }> {
  const data = await api.get<{ runs?: StudioRun[]; total?: number }>(
    `${ENDPOINTS.RUNS_LIST}?limit=${limit}&offset=${offset}`,
  )
  return { runs: data.runs ?? [], total: Number(data.total ?? data.runs?.length ?? 0) }
}

export async function cancelExecution(requestId: string): Promise<Record<string, any>> {
  return api.post<Record<string, any>>(ENDPOINTS.EXECUTION_CANCEL(requestId), {})
}

export async function createWorkflow(name: string, description: string): Promise<Record<string, any>> {
  return api.post<Record<string, any>>(ENDPOINTS.WORKFLOWS_LIST, {
    name,
    description,
    version: '1.0.0',
    graph: { nodes: [], edges: [] },
    status: 'draft',
  })
}

export async function publishWorkflow(workflowId: string, version = '1.0.0'): Promise<Record<string, any>> {
  return api.post<Record<string, any>>(`${ENDPOINTS.WORKFLOWS_LIST}/${encodeURIComponent(workflowId)}/publish`, { version })
}

export async function updateWorkflow(workflowId: string, payload: { name: string; description: string; status?: string }): Promise<Record<string, any>> {
  return api.put<Record<string, any>>(ENDPOINTS.WORKFLOW_UPDATE(workflowId), payload)
}

export async function deleteWorkflow(workflowId: string): Promise<Record<string, any>> {
  return api.delete<Record<string, any>>(ENDPOINTS.WORKFLOW_DELETE(workflowId))
}

export async function validateWorkflow(workflowId: string): Promise<Record<string, any>> {
  return api.post<Record<string, any>>(ENDPOINTS.WORKFLOW_VALIDATE(workflowId), {})
}

export async function replayWorkflow(workflowId: string, input: Record<string, any> = {}): Promise<Record<string, any>> {
  return api.post<Record<string, any>>(ENDPOINTS.RUNS_CREATE, {
    target: { type: 'workflow', id: workflowId, version: 'latest' },
    params: { input },
    execution: { mode: 'full', async_mode: false },
  })
}

export async function startSop(module: string, pages: string[] = [], provider = 'mock'): Promise<Record<string, any>> {
  return api.post<Record<string, any>>(ENDPOINTS.SOP_START, { module, pages, mode: 'full', provider })
}

export async function createModule(name: string, projectId = '', description = ''): Promise<Record<string, any>> {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : ''
  return api.post<Record<string, any>>(`${ENDPOINTS.MODULES}${query}`, { name, description })
}

export async function updateModule(moduleId: string, payload: { name?: string; description?: string }, projectId = ''): Promise<Record<string, any>> {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : ''
  return api.patch<Record<string, any>>(`${ENDPOINTS.MODULE(moduleId)}${query}`, payload)
}

export async function deleteModule(moduleId: string, projectId = ''): Promise<Record<string, any>> {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : ''
  return api.delete<Record<string, any>>(`${ENDPOINTS.MODULE(moduleId)}${query}`)
}

export async function listModulePages(moduleId: string, projectId = ''): Promise<{ pages: StudioModulePage[]; total: number }> {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : ''
  const data = await api.get<{ pages?: StudioModulePage[]; total?: number }>(`${ENDPOINTS.MODULE_PAGES(moduleId)}${query}`)
  return { pages: data.pages ?? [], total: Number(data.total ?? data.pages?.length ?? 0) }
}

export async function createModulePage(moduleId: string, name: string, description = '', projectId = '', config: StudioModulePageConfig = {}): Promise<Record<string, any>> {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : ''
  return api.post<Record<string, any>>(`${ENDPOINTS.MODULE_PAGES(moduleId)}${query}`, { name, description, ...config })
}

export async function updateModulePage(moduleId: string, pageId: string, payload: { name?: string; description?: string } & StudioModulePageConfig, projectId = ''): Promise<Record<string, any>> {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : ''
  return api.patch<Record<string, any>>(`${ENDPOINTS.MODULE_PAGE(moduleId, pageId)}${query}`, payload)
}

export async function deleteModulePage(moduleId: string, pageId: string, projectId = ''): Promise<Record<string, any>> {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : ''
  return api.delete<Record<string, any>>(`${ENDPOINTS.MODULE_PAGE(moduleId, pageId)}${query}`)
}

export async function listNotifications(limit = 20, scope = ''): Promise<{ notifications: StudioNotification[]; total: number; unread: number }> {
  const query = new URLSearchParams({ limit: String(limit) })
  if (scope) query.set('scope', scope)
  const data = await api.get<{ notifications?: StudioNotification[]; total?: number; unread?: number }>(
    `${ENDPOINTS.NOTIFICATIONS}?${query.toString()}`,
    { timeoutMs: 5000 },
  )
  return { notifications: data.notifications ?? [], total: Number(data.total ?? 0), unread: Number(data.unread ?? 0) }
}

export async function markNotificationRead(notificationId: string, scope = ''): Promise<Record<string, any>> {
  const query = scope ? `?scope=${encodeURIComponent(scope)}` : ''
  return api.patch<Record<string, any>>(`${ENDPOINTS.NOTIFICATIONS}/${encodeURIComponent(notificationId)}/read${query}`, {})
}

export async function runAgent(agent: string, module = 'studio', provider = 'mock', mode = 'full'): Promise<Record<string, any>> {
  return api.post<Record<string, any>>(ENDPOINTS.AGENTS_RUN, {
    agent,
    module,
    page: '',
    provider,
    mode,
  })
}

export async function updateBug(bugId: string, status: string): Promise<Record<string, any>> {
  return api.patch<Record<string, any>>(ENDPOINTS.BUG_UPDATE(bugId), { status })
}

export async function searchMemory(query: string, collection = ''): Promise<Record<string, any>[]> {
  const params = new URLSearchParams({ query })
  if (collection) params.set('collection', collection)
  const data = await api.get<{ results?: Record<string, any>[] }>(`${ENDPOINTS.MEMORY_SEARCH}?${params.toString()}`)
  return data.results ?? []
}

export async function searchKnowledge(query: string, collection = 'all'): Promise<Record<string, any>[]> {
  const params = new URLSearchParams({ query, collection })
  const data = await api.get<{ results?: Record<string, any>[] }>(`${ENDPOINTS.KNOWLEDGE_SEARCH}?${params.toString()}`)
  return data.results ?? []
}

export function normalizeRunStatus(status?: string): 'success' | 'warning' | 'failed' | 'running' | 'idle' {
  const normalized = (status || '').toLowerCase()
  if (['completed', 'success', 'succeeded'].includes(normalized)) return 'success'
  if (['failed', 'error', 'timed_out'].includes(normalized)) return 'failed'
  if (['running', 'started', 'pending'].includes(normalized)) return 'running'
  if (['cancelled', 'warning', 'paused'].includes(normalized)) return 'warning'
  return 'idle'
}
