/** Run API Types — /api/v1/runs (P7-2 Phase 3) */

export type RunTargetType = "agent" | "workflow" | "skill" | "evaluation"

export interface RunTarget {
  type: RunTargetType
  id: string
  version?: string
}

export interface RunParams {
  // type="agent"
  module?: string
  pages?: string[]

  // type="workflow"
  input?: Record<string, unknown>

  // type="skill"
  prompt?: string
  context?: Record<string, unknown>

  // type="evaluation"
  dataset_id?: string
  eval_config?: Record<string, unknown>
}

export interface RunRuntime {
  provider?: string
  model?: string
  temperature?: number
  max_tokens?: number
  environment_id?: string
}

export interface RunExecution {
  mode?: string
  priority?: number
  timeout_seconds?: number
  max_retries?: number
  async?: boolean
}

export interface RunMetadata {
  triggered_by?: string
  tags?: string[]
  idempotency_key?: string
  parent_run_id?: string
}

export interface CreateRunRequest {
  target: RunTarget
  params?: RunParams
  runtime?: RunRuntime
  execution?: RunExecution
  metadata?: RunMetadata
}

export interface RunArtifact {
  type: string
  path: string
  url?: string
}

export interface RunMetrics {
  duration_ms: number
  tokens_used: number
  cost_usd: number
}

export interface RunError {
  type: string
  message: string
  details?: Record<string, unknown>
}

export interface RunResult {
  status: "success" | "error"
  artifacts?: RunArtifact[]
  metrics?: RunMetrics
  error?: RunError
}

export type RunStatus = "pending" | "running" | "completed" | "failed" | "cancelled"

export interface CreateRunResponse {
  run_id: string
  status: RunStatus
  created_at: string
  target: RunTarget
  result?: RunResult
}

export interface GetRunResponse {
  run_id: string
  status: RunStatus
  agent: string
  module: string
  pages: string[]
  created_at: string
  completed_at?: string
  total_tokens?: number
  total_cost?: number
  error_message?: string
  // 其他字段根据需要扩展
}
