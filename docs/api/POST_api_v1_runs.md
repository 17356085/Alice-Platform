# POST /api/v1/runs — 统一执行入口设计

> **状态**: RFC | **日期**: 2026-07-10 | **阶段**: Phase 2 (P7-2)

---

## 目标

统一所有执行类型（Agent/Workflow/Skill/Evaluation）到单一端点，替代当前的 `POST /api/workspaces/:ws_id/executions`。

## 设计原则

1. **向后兼容**: 保留旧端点，新端点为首选
2. **资源版本化**: 支持 `target.version` 指定执行对象的特定版本
3. **环境抽象**: 支持 `environment_id` 多环境部署
4. **类型统一**: Agent/Workflow/Skill/Evaluation 用同一个 `target.type` 区分

---

## Request Schema

```typescript
interface CreateRunRequest {
  // ── 执行目标（新增，替代旧的 module/pages/agent） ──
  target: {
    type: "agent" | "workflow" | "skill" | "evaluation";
    id: string;              // agent_id / workflow_id / skill_id / evaluation_id
    version?: string;        // "1.2.0" | "latest" | "agent-v3" (AgentVersion/WorkflowVersion)
  };

  // ── 执行参数（类型依赖的特定参数） ──
  params?: {
    // type="agent" 时:
    module?: string;         // 向后兼容旧参数
    pages?: string[];        // 向后兼容旧参数
    
    // type="workflow" 时:
    input?: Record<string, unknown>;  // workflow 输入变量
    
    // type="skill" 时:
    prompt?: string;         // skill 提示
    context?: Record<string, unknown>;
    
    // type="evaluation" 时:
    dataset_id?: string;
    eval_config?: Record<string, unknown>;
  };

  // ── 运行时配置 ──
  runtime?: {
    provider?: "claude" | "openai" | "deepseek" | "mimo";
    model?: string;          // 覆盖默认模型
    temperature?: number;
    max_tokens?: number;
    environment_id?: string; // 多环境支持（P6-4 Environment 资源）
  };

  // ── 执行策略 ──
  execution?: {
    mode?: "full" | "incremental" | "debug";  // 执行模式
    priority?: number;       // 0-10，默认5
    timeout_seconds?: number;
    max_retries?: number;    // 最大重试次数
    async?: boolean;         // 异步执行（后台运行）
  };

  // ── 元数据 ──
  metadata?: {
    triggered_by?: "manual" | "schedule" | "webhook" | "api";
    tags?: string[];
    idempotency_key?: string;
    parent_run_id?: string;  // 关联父 Run（用于多 Run 链式执行）
  };
}
```

---

## Response Schema

```typescript
interface CreateRunResponse {
  run_id: string;           // Run 唯一标识
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  created_at: string;       // ISO 8601
  
  // 执行目标回显
  target: {
    type: string;
    id: string;
    version: string;        // 解析后的实际版本（如 "latest" → "2.5.0"）
  };

  // 如果 async=true，立即返回；否则等待完成
  result?: {
    status: "success" | "error";
    artifacts?: Array<{
      type: string;
      path: string;
      url?: string;         // 下载链接（P3-3 Artifact blob API）
    }>;
    metrics?: {
      duration_ms: number;
      tokens_used: number;
      cost_usd: number;
    };
    error?: {
      type: string;
      message: string;
      details?: Record<string, unknown>;
    };
  };
}
```

---

## 向后兼容映射

旧端点 `POST /api/workspaces/:ws_id/executions` 内部转换为新格式：

```python
# 旧请求
{
  "module": "user_manage",
  "pages": ["user_list", "user_add"],
  "agent": "page-observer",
  "mode": "full",
  "provider": "claude"
}

# 映射到新格式
{
  "target": {
    "type": "agent",
    "id": "page-observer",
    "version": "latest"
  },
  "params": {
    "module": "user_manage",
    "pages": ["user_list", "user_add"]
  },
  "runtime": {
    "provider": "claude"
  },
  "execution": {
    "mode": "full"
  }
}
```

---

## 数据库扩展

`runs` 表需要新增字段（保持向后兼容）：

```sql
ALTER TABLE runs ADD COLUMN target_type VARCHAR(32) DEFAULT 'agent';
ALTER TABLE runs ADD COLUMN target_id VARCHAR(64) DEFAULT '';
ALTER TABLE runs ADD COLUMN target_version VARCHAR(64) DEFAULT 'latest';
ALTER TABLE runs ADD COLUMN environment_id VARCHAR(64) DEFAULT '';
ALTER TABLE runs ADD COLUMN parent_run_id VARCHAR(64) DEFAULT '';

-- 索引
CREATE INDEX idx_runs_target ON runs(target_type, target_id);
CREATE INDEX idx_runs_environment ON runs(environment_id);
CREATE INDEX idx_runs_parent ON runs(parent_run_id);
```

旧字段（`agent`, `module`, `pages`）保留，向后兼容旧查询。

---

## 实现计划

1. **Phase 1**: 新增 `/api/v1/runs` 路由，支持 `target.type="agent"` + 旧参数映射
2. **Phase 2**: 扩展 RunModel 数据库字段，迁移历史数据
3. **Phase 3**: Studio 前端切换到新端点
4. **Phase 4**: 支持 `target.type="workflow"` / `"skill"` / `"evaluation"`
5. **Phase 5**: 旧端点标记为 deprecated（保留 6 个月后废弃）

---

## 相关决策

- **决策7**: 统一 Control Plane，单一执行入口
- **P7-1**: API 路由资源化（`/api/v1/*` 版本前缀）
- **P6-4**: Environment 资源模型（`environment_id` 字段）
- **P8-1**: Workflow 图模型资源化（`target.type="workflow"`）
