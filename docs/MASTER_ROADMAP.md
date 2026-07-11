# 统一修复路线图 — 全阶段规划

> **创建时间**: 2026-07-10  
> **基于**: 上个会话的决策 1-8 + 4 阶段事实收集  
> **累积问题**: 28 项（P0-P8）

> **真实状态校正（2026-07-11 更新）**：P7-1、P2-5、P2-8、P7-2 skill/evaluation 深度执行、P6-2 MCP API、P6-3 Plugin 初版集成和 P8 Parallel 节点执行已实现并有分项测试证据。Studio 的 Global Runs、Evaluations、Registry 与 Workflow Builder MVP 已完成。远程 Worker、计费治理、云端 Secret Provider、Plugin 安全治理、企业权限以及生产运维仍在 backlog。

---

## 执行原则

1. **先记录、后统一修复** — 所有问题先收集完毕，再制定统一方案
2. **按依赖关系排序** — P1-1（schema）和 P7-2（执行入口）是地基，必须先做
3. **向后兼容优先** — 旧端点保留 6 个月，新旧字段共存
4. **阶段内可并行** — 同一阶段的独立任务可以并行处理

---

## 7 个修复阶段

### ✅ 阶段 0 — 解除阻塞（已完成 100%）

| 问题 | 状态 | 修改文件 |
|------|------|---------|
| P0-1: ClaudeProvider 缺失 | ✅ | `aitest/adapters/llm/interface.py` |
| P0-2: Studio 22 个 TS 错误 | ✅ | 12 个 .tsx 文件 + `vite-env.d.ts` |
| P0-3: 产品定位文档冲突 | ✅ | `PRODUCT_SPEC_V1_ARCHIVED.md` |

**成果**: 测试和开发不再阻塞

---

### ✅ 阶段 1 — 地基统一（已完成 100%）

| 问题 | 状态 | 修改文件 |
|------|------|---------|
| P1-1: project.yaml schema 双轨 | ✅ | `ADR_001_TLO_DIRECTORY.md` |
| P1-2: 版本号混乱（2.5.0 vs 2.2） | ✅ | `agent-definitions.yaml` |
| P7-2: 执行入口未统一 | ✅ | 已在阶段 2 完成；skill/evaluation 深度执行已于 2026-07-11 完成 |

**成果**: schema 文档与代码统一，版本号对齐

---

### ✅ 阶段 2 — Run 资源体验（已完成）

**目标**: 统一执行入口，提升 Run 资源的用户体验

#### P7-2: 统一执行入口到 `POST /api/v1/runs`（5 个 Phase）

| Phase | 状态 | 说明 |
|-------|------|------|
| Phase 1: 新端点实现 | ✅ | `aitest/server/api/runs.py` + 设计文档 |
| Phase 2: 数据库扩展 | ✅ | RunModel 新增 5 字段 + 自动迁移 |
| Phase 3: 前端切换 | ✅ | 添加端点常量 + TypeScript 类型 + ExecutionView 使用 ENDPOINTS |
| Phase 4: 多类型支持 | ✅ | workflow/skill/evaluation（RunExecutor 分发器）|
| Phase 5: 旧端点废弃 | ✅ | execution_router 添加 deprecated=True |

**关键文件**:
```
aitest/server/api/runs.py          # 新端点 ★
aitest/server/api/run_executor.py  # Phase 4: 多类型执行分发器 ★
aitest/infra/models.py             # RunModel ★
aitest/platform/run.py             # Run dataclass ★
aitest/platform/run_store.py       # 迁移逻辑 ★
docs/api/POST_api_v1_runs.md      # 设计文档 ★
aitest/web/src/api/endpoints.ts    # 端点常量 ★
aitest/web/src/types/runs.ts       # TypeScript 类型 ★
```

**Phase 4 实现**:
- `RunExecutor` 根据 `target.type` 分发到不同执行逻辑
- `execute_agent()`: 复用现有 ExecutionService（完整实现）✅
- `execute_workflow()`: **完整实现 — WorkflowExecutor 执行引擎** ✅
- `execute_skill()`: **完整实现 — 复用 SDK 层 run_skill()** ✅ (2026-07-11)
- `execute_evaluation()`: **完整实现 — Dataset 遍历 + 结果聚合** ✅ (2026-07-11)

#### ✅ P7-1: API 路由资源化（已完成）

**任务**: 13 个 router 添加 `/api/v1/` 版本前缀

**迁移清单**:
```
✅ runs_router           → /api/v1/runs (已完成)
✅ quality_router        → /api/v1/quality (已完成)
✅ workflows_v1_router   → /api/v1/workflows (已完成)
✅ workspace_router      → /api/v1/workspaces
✅ agents_router         → /api/v1/agents
✅ workflows_router      → /api/v1/workflows
✅ bugs_router           → /api/v1/bugs
✅ audit_router          → /api/v1/audit
✅ kpi_router            → /api/v1/kpi
✅ kanban_router         → /api/v1/kanban
✅ terminal_router       → /api/v1/terminal
✅ obs_router            → /api/v1/observability
✅ chat_router           → /api/v1/chat
✅ sessions_router       → /api/v1/sessions
✅ onboarding_router     → /api/v1/onboarding
✅ integrations_router   → /api/v1/integrations
```

**策略**: 
- 逐个迁移，旧端点保留向后兼容（6 个月）
- 需要前后端协同更新 API 调用
- 建议在 P2-6（Studio IA 重组）后进行，避免重复修改

#### ✅ P2-6/P7-3: Studio IA 重组（MVP 完成）

**任务**: 19 个平铺 Views 按 5-resource 模型合并

**当前结构** (aitest/web/src/views/):
```
DashboardView.tsx
ProjectOverviewView.tsx
ExecutionView.tsx
RunInspectorView.tsx
AgentDetailView.tsx
AgentTerminalView.tsx
TimelineView.tsx
KanbanView.tsx
GapDiscoveryView.tsx
ReportsView.tsx
ArtifactsView.tsx
KnowledgeView.tsx
KnowledgeGraphView.tsx
ObservabilityView.tsx
SettingsView.tsx
ProjectSettingsView.tsx
StrategyPlannerView.tsx
IntelligenceChatView.tsx
OnboardingWizardView.tsx
```

**目标结构**:
```
全局导航:
  ProjectsView.tsx        # 项目列表
  GlobalRunsView.tsx      # 全局运行历史
  EvaluationsView.tsx     # 质量评估（新增）
  RegistryView.tsx        # Agent/Workflow/Skill 注册表（新增）
  SettingsView.tsx        # 全局设置

Project 内导航（选中项目后）:
  ProjectOverviewView.tsx # 概览（保留）
  BuildView.tsx           # 构建（合并 AgentDetail + StrategyPlanner）
  RunView.tsx             # 执行（合并 Execution + RunInspector + Terminal）
  QualityView.tsx         # 质量（合并 Reports + GapDiscovery + 新增 Dataset/Eval）
  AssetsView.tsx          # 资产（合并 Artifacts + Knowledge + KnowledgeGraph）
```

**当前实际状态**：目录和懒加载入口已迁移；`/runs`、`/evaluations`、`/registry` 已使用真实资源页，`/projects/:id/build` 使用 `BuildView`，支持 Workflow Draft 创建、校验与发布。图形画布与节点编辑器是后续增强，不阻塞 MVP。

#### ✅ P3-2: Multi-Run 对比（已完成）

**端点**: `GET /api/v1/runs/compare?run_ids=run1,run2,run3`

**实现**:
```python
@runs_router.get("/runs/compare")
async def compare_runs(run_ids: str):
    ids = run_ids.split(',')
    runs = [get_run_store().get_run(rid) for rid in ids]
    return {
        "runs": [r.to_dict() for r in runs if r],
        "diff": _compute_diff(runs)
    }
```

**前端**: 新增 `CompareRunsView.tsx`（侧边栏展示对比结果）

#### ✅ P3-3: Artifact blob API（已完成）

**端点**:
- `GET /api/v1/artifacts/:artifact_id/download` — 直接下载
- `GET /api/v1/artifacts/:artifact_id/url` — Signed URL（未来扩展）

**实现**:
```python
from fastapi.responses import FileResponse

@runs_router.get("/artifacts/{artifact_id}/download")
async def download_artifact(artifact_id: str):
    # artifact_id 格式: "project:module:page:filename"
    project, module, page, filename = artifact_id.split(':')
    store = ArtifactStore(project)
    path = store.path(module, page, filename)
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path)
```

---

### ✅ 阶段 3 — 质量闭环资源化（完成核心 P5-1）

**目标**: 把 EvalRunner/LMJudge/prompt_benchmark 包装成平台资源

#### ✅ P5-1: Dataset/Evaluation/Experiment 资源模型（已完成）

**新增数据库表**:
```sql
CREATE TABLE datasets (
    dataset_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- "test_cases" | "conversations" | "prompts"
    project_id TEXT,
    created_at TEXT,
    examples TEXT  -- JSONB
);

CREATE TABLE evaluations (
    evaluation_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    dataset_id TEXT NOT NULL,
    agent_version TEXT,
    evaluator_config TEXT,  -- JSONB (judge model, metrics)
    status TEXT,
    results TEXT,  -- JSONB (pass_rate, metrics)
    created_at TEXT
);

CREATE TABLE experiments (
    experiment_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    baseline_eval_id TEXT,
    candidate_eval_id TEXT,
    comparison TEXT,  -- JSONB (diff, winner)
    decision TEXT,    -- "promote" | "reject" | "pending"
    created_at TEXT
);
```

**API 端点**:
```
POST   /api/v1/datasets             # 创建 Dataset
GET    /api/v1/datasets/:id
POST   /api/v1/datasets/:id/examples  # 添加样本

POST   /api/v1/evaluations          # 运行 Evaluation
GET    /api/v1/evaluations/:id

POST   /api/v1/experiments          # 创建 Experiment（A/B 对比）
GET    /api/v1/experiments/:id
POST   /api/v1/experiments/:id/promote  # 提升候选版本
```

**闭环路径**:
```
failed Run
   ↓
extract_example() → Dataset
   ↓
modify Agent/Prompt
   ↓
run_evaluation() → Evaluation
   ↓
create_experiment() → Experiment (compare baseline vs candidate)
   ↓
promote() → AgentVersion deployed
```

#### ✅ P4-1: Skill 版本绑定（已完成）

**当前问题**: `agent-definitions.yaml` 引用裸 skill ID，无法得出 AgentVersion 锁定的 skill 版本

**解决方案**:
```yaml
agents:
  - id: page-observer
    version: "2.5.0"
    skills:
      - id: page-observe
        version: "1.2.0"        # ← 明确版本号
        sha256: "abc123..."     # ← 可选：内容哈希校验
```

**实现文件**:
- `packages/alice-engine/alice_engine/core/skill_ref.py` — SkillRef dataclass
- `packages/alice-engine/alice_engine/core/agent_definitions.py` — 解析 v1.0/v2.0 格式
- `docs/agent-definitions-v2-schema.md` — schema 设计文档

**向后兼容**:
- `get_skills()` 返回 `List[SkillRef]`
- `get_skills_legacy()` 返回 `List[str]`（向后兼容）
- `SkillRef.parse()` 自动识别 v1.0 (str) 和 v2.0 (dict) 格式

---

### ✅ 阶段 4 — Agent/Workflow Builder v1（已完成）

**目标**: Workflow 从 Python 代码变成 JSON schema 资源

#### ✅ P8-1: Workflow 图模型资源化 + 执行引擎（已完成）

**当前**: `sop_graph.py` 是 Python 代码实现

**目标**: JSON schema 可序列化图模型

**实现文件**:
- `aitest/platform/workflow.py` — WorkflowGraph/WorkflowNode/WorkflowEdge dataclass
- `aitest/platform/workflow_models.py` — WorkflowModel ORM
- `aitest/platform/workflow_store.py` — CRUD 操作
- `aitest/platform/workflow_executor.py` — **执行引擎（新增）** ★
- `aitest/server/api/workflows_v1.py` — REST API
- `aitest/server/api/run_executor.py` — **集成到 RunExecutor（已更新）** ★
- `migrations/add_workflow_tables_sqlite.sql` — 数据库迁移
- `docs/workflow_executor_design.md` — **执行引擎设计文档（新增）** ★
- `tests/test_workflow_executor.py` — **端到端测试（新增）** ★

**Schema 示例**:
```json
{
  "workflow_id": "test-automation-sop",
  "version": "1.0.0",
  "nodes": [
    {
      "node_id": "requirement-analysis",
      "type": "agent",
      "agent_id": "requirement-agent",
      "agent_version": "2.5.0",
      "retry_policy": {"max_attempts": 3, "backoff": "exponential"}
    },
    {
      "node_id": "hitl-review",
      "type": "human_gate",
      "prompt": "请审核需求分析结果",
      "timeout_seconds": 3600
    }
  ],
  "edges": [
    {
      "from": "requirement-analysis",
      "to": "hitl-review",
      "condition": "always"
    },
    {
      "from": "hitl-review",
      "to": "test-design",
      "condition": "approved"
    }
  ],
  "parallel_policy": {
    "parallel_nodes": ["page-1", "page-2", "page-3"],
    "max_concurrency": 3
  }
}
```

**数据库表**:
```sql
CREATE TABLE workflows (
    workflow_id TEXT PRIMARY KEY,
    name TEXT,
    version TEXT,
    graph_json TEXT,  -- JSON schema
    created_at TEXT
);

CREATE TABLE workflow_versions (
    workflow_id TEXT,
    version TEXT,
    graph_json TEXT,
    status TEXT,  -- "draft" | "published" | "archived"
    PRIMARY KEY (workflow_id, version)
);
```

**API**:
```
POST   /api/v1/workflows              # 创建工作流
GET    /api/v1/workflows/:id          # 获取工作流
GET    /api/v1/workflows              # 列出工作流
PUT    /api/v1/workflows/:id          # 更新工作流
POST   /api/v1/workflows/:id/publish  # 发布新版本
POST   /api/v1/workflows/:id/validate # 静态校验（基础实现）
```

**支持的节点类型**:
- `agent`: 执行 Agent（支持 retry_policy，复用 ExecutionService）✅
- `human_gate`: 人工审核（持久化 Gate、REST resolve、WebSocket 状态流、Studio 面板）✅
- `condition`: 条件分支（简单表达式求值，支持 node_outputs 访问）✅
- `parallel`: 并行执行（线程池路径与 LangGraph `Send()` 路径已实现）✅

**执行引擎特性**:
- **图构建**: 从 JSON 自动检测入口/出口节点，构建 LangGraph
- **状态管理**: WorkflowRuntime 管理 node_outputs 和 completed_nodes
- **重试逻辑**: 支持 exponential/linear/none 退避策略
- **条件路由**: 支持 always/approved/rejected/自定义表达式
- **错误处理**: 节点失败时更新 Run 状态，返回详细错误信息

**向后兼容**: 
- 旧的 `/api/workflow/*` 端点保留（基于 LangGraph）
- 新的 `/api/v1/workflows/*` 端点用于资源化管理

---

#### ✅ P8-2: HITL 节点化（已完成）

**当前**: 硬编码函数 `input("Continue? y/n")`

**目标**: JSON schema 声明式定义

```json
{
  "node_id": "hitl-review",
  "type": "human_gate",
  "prompt": "请审核需求分析结果",
  "form": [
    {"field": "approved", "type": "boolean"},
    {"field": "comment", "type": "text"}
  ],
  "timeout_seconds": 3600,
  "default_action": "reject"
}
```

**当前实现**: Gate 持久化、执行器阻塞/超时、REST resolve、WebSocket 状态流、Studio 审核面板和集成测试均已完成。

#### ✅ P8-3: Workflow 静态校验（已完成）

**校验规则**:
1. 图拓扑：节点 ID 唯一性、边引用有效性
2. 循环检测：DFS 检测有向图环
3. 可达性检查：BFS 从入口节点检查所有节点可达
4. 孤立节点检测：无入边且无出边的节点
5. Agent 节点完整性：agent_id 非空

**实现文件**:
- `aitest/server/api/workflows_v1_validate.py` — 校验逻辑
- `POST /api/v1/workflows/:id/validate` — 返回 errors/warnings

**返回格式**:
```json
{
  "workflow_id": "wf_xxx",
  "valid": true,
  "errors": [],
  "warnings": ["Node X is isolated"]
}
```

---

### ✅ 阶段 5 — 外部依赖资源化（核心资源已完成）

**目标**: ModelProvider/MCP/Plugin/Environment/Secret 五个资源抽象

#### ✅ P6-1: ModelProvider 资源化（已完成）

**当前**: 直接读环境变量 `ANTHROPIC_API_KEY`

**目标**: Provider 资源管理

**实现文件**:
- `aitest/platform/model_provider.py` — ModelProvider/ProviderConfig dataclass
- `aitest/platform/model_provider_models.py` — ModelProviderModel ORM
- `aitest/platform/model_provider_store.py` — CRUD 操作
- `aitest/server/api/providers_v1.py` — REST API
- `aitest/adapters/llm/interface.py` — get_provider() 集成（支持 provider_id 参数）
- `aitest/infra/models.py` — RunModel.provider_id 字段（可选）
- `migrations/add_model_providers_table_sqlite.sql` — 数据库迁移
- `migrations/add_run_provider_id_sqlite.sql` — Run 表迁移
- `tests/test_model_provider.py` — 完整测试

**数据库表**:
```sql
CREATE TABLE model_providers (
    provider_id TEXT PRIMARY KEY,
    name TEXT,          -- "anthropic-prod" | "openai-dev"
    type TEXT,          -- "anthropic" | "openai" | "ollama" | "deepseek" | "mimo"
    config TEXT,        -- JSONB (api_key, base_url, default_model, max_tokens, timeout_seconds)
    status TEXT,        -- "active" | "inactive"
    org_id TEXT,
    created_by TEXT,
    created_at TEXT,
    updated_at TEXT
);
```

**API**:
```
POST   /api/v1/providers              # 创建 Provider
GET    /api/v1/providers              # 列出 Providers
GET    /api/v1/providers/:id          # 获取 Provider
PUT    /api/v1/providers/:id          # 更新 Provider
DELETE /api/v1/providers/:id          # 删除 Provider
POST   /api/v1/providers/test         # 测试连接
```

**集成**:
```python
# 方式 1: 使用 provider_id（从 ModelProviderStore 加载）
llm = get_provider("claude", provider_id="anthropic-prod")

# 方式 2: 传统方式（从环境变量加载，向后兼容）
llm = get_provider("claude")
```

**Run 关联**: `RunModel.provider_id` 字段（可选，向后兼容）

**向后兼容**:
- get_provider() 优先从 ModelProviderStore 加载，失败时 fallback 到环境变量
- 现有代码无需修改

#### ✅ P6-2: MCPServer 资源化（已完成）

**当前**: 硬编码 Python dict

**目标**: 动态管理 MCP 服务器

**实现文件**:
- `aitest/platform/mcp_server_store.py` — MCPServerStore CRUD + 环境变量解析
- `aitest/platform/mcp_server_manager.py` — MCPServerManager 进程管理 + 健康检查
- `aitest/mcp/registry.py` — 改造支持数据库加载（向后兼容）
- `aitest/mcp/mcp_client.py` — 改造支持数据库加载
- `migrations/017_mcp_servers.sql` — PostgreSQL 迁移
- `migrations/017_mcp_servers_sqlite.sql` — SQLite 迁移
- `tests/mcp/test_mcp_server_resource.py` — 完整测试（20 个用例）
- `docs/mcp_server_design.md` — 设计文档
- `docs/SESSION_SUMMARY_2026-07-11_MCP_SERVER.md` — 实现总结

**数据库表**:
```sql
CREATE TABLE mcp_servers (
    mcp_server_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    transport_type TEXT NOT NULL,  -- "stdio" | "http"
    command TEXT,
    args TEXT,  -- JSON 数组
    url TEXT,
    env TEXT,   -- JSON 对象（支持 secret_ref / environment_ref）
    tools TEXT, -- JSON 数组
    status TEXT DEFAULT 'stopped',
    process_id INTEGER,
    enabled_by_default INTEGER,
    org_id TEXT,
    created_by TEXT,
    created_at TEXT,
    updated_at TEXT,
    last_health_check TEXT
);

CREATE TABLE agent_mcp_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_type TEXT NOT NULL,
    mcp_server_id TEXT NOT NULL,
    allowed_tools TEXT,  -- JSON 数组
    org_id TEXT,
    created_at TEXT,
    UNIQUE(agent_type, mcp_server_id, org_id)
);
```

**Schema**:
```json
{
  "mcp_server_id": "slack-connector",
  "name": "Slack MCP",
  "transport_type": "stdio",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-slack"],
  "env": {
    "SLACK_BOT_TOKEN": "secret:slack-bot-token",
    "WORKSPACE": "environment:SLACK_WORKSPACE"
  },
  "tools": ["slack_list_channels", "slack_post_message"],
  "status": "running",
  "process_id": 12345,
  "enabled_by_default": true
}
```

**核心功能**:
- MCPServerStore: CRUD 操作 + 环境变量解析（secret_ref / environment_ref）
- MCPServerManager: 启动/停止/重启/健康检查/自动重启
- Agent 映射: 支持限制 Agent 可用的 Tools
- 向后兼容: use_db=False 使用硬编码配置

#### ✅ P6-3: Plugin 完整机制（已完成 — 2026-07-11）

**当前**: ~~仅支持 Provider 注册~~ → **完整支持 Skill/CLI/API 扩展** ✅

**目标**: Skill/CLI/API 扩展 + 沙箱 + 签名（v2）

**实现文件**:
- `aitest/platform/plugin.py` — PluginManager 核心实现（+120 行）
- `packages/alice-engine/alice_engine/core/skill_loader.py` — Plugin Skill 加载支持（+30 行）
- `packages/alice-engine/alice_engine/core/skill_executor.py` — plugin_lookup_fn 参数注入（+5 行）
- `packages/alice-engine/alice_engine/core/agent_helpers.py` — plugin_lookup_fn 透传（+3 行）
- `aitest/server/api/run_executor.py` — Plugin Skill 查找函数注入（+8 行）
- `aitest/cli/main.py` — Plugin CLI 命令动态注册（+42 行）
- `aitest/server/main.py` — Plugin API 路由动态挂载（+28 行）
- `aitest/tests/platform/test_plugin_integration.py` — 集成测试（11 个用例）
- `docs/plugin_system_design.md` — 完整设计文档

**核心功能**:
- PluginInfo 扩展: skills/cli_commands/api_routes/author/homepage/dependencies 字段
- PluginManager 扩展: 3 个新注册表 + 9 个新方法
- **Skill 自动集成**: SkillLoader.load() 优先从 PluginManager 加载 Plugin Skills（通过 plugin_lookup_fn 回调）
- **CLI 自动集成**: CLI main.py 启动时从 PluginManager 动态注册 Plugin 命令（支持 create_command/create_typer 两种模式）
- **API 自动集成**: FastAPI main.py 启动时从 PluginManager 动态挂载 Plugin 路由（调用 create_router()）
- 手动注册 API: register_skill/cli_command/api_route
- 查询 API: get_skills/cli_commands/api_routes
- 向后兼容: v1.0 Plugin 继续工作

**Plugin 结构 (v2.0)**:
```yaml
name: my-plugin
version: 2.0.0
providers:
  - name: custom_browser
    class: my_plugin.providers:CustomBrowserProvider
skills:
  - name: custom-skill
    file: skills/custom_skill.md
cli_commands:
  - name: deploy
    class: my_plugin.cli:DeployCommand
api_routes:
  - prefix: /api/v1/custom
    class: my_plugin.api:CustomRouter
```

**待集成（明确 backlog）**:
- Skill 集成到 Skill Executor（设计完成，代码待实现）
- CLI 集成到 aitest CLI（设计完成，代码待实现）
- API 集成到 FastAPI（设计完成，代码待实现）

**未来扩展（v2）**:
- 沙箱隔离（权限模型）
- 签名验证（安全性）

#### ✅ P6-4: Environment 资源化（已完成）

**当前**: 混合在 `project.yaml` 的 `connection` 字段

**目标**: 独立 Environment 资源

**实现文件**:
- `aitest/platform/environment.py` — Environment dataclass
- `aitest/platform/environment_models.py` — EnvironmentModel ORM
- `aitest/platform/environment_store.py` — EnvironmentStore CRUD
- `aitest/server/api/environments_v1.py` — REST API（7 个端点）
- `migrations/add_environments_table_sqlite.sql` — 数据库迁移
- `migrations/add_run_environment_id_sqlite.sql` — Run 表迁移
- `tests/test_environment.py` — 完整测试（6 个场景）
- `docs/environment_design.md` — 设计文档

**数据库表**:
```sql
CREATE TABLE environments (
    environment_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    base_url TEXT NOT NULL,
    description TEXT,
    variables TEXT,  -- JSON 对象
    tags TEXT,       -- JSON 数组
    org_id TEXT,
    created_by TEXT,
    created_at TEXT,
    updated_at TEXT,
    is_default INTEGER DEFAULT 0
);
```

**API**:
```
POST   /api/v1/environments              # 创建 Environment
GET    /api/v1/environments              # 列出 Environments
GET    /api/v1/environments/:id          # 获取 Environment
PUT    /api/v1/environments/:id          # 更新 Environment
DELETE /api/v1/environments/:id          # 删除 Environment
POST   /api/v1/environments/:id/default  # 设置为默认
GET    /api/v1/environments/:id/resolved # 获取解析后的变量
```

**Schema**:
```json
{
  "environment_id": "staging",
  "name": "Staging Environment",
  "base_url": "https://staging.example.com",
  "variables": {
    "DB_HOST": "staging-db.example.com",
    "DB_PASSWORD": "secret:staging-db-password"
  },
  "tags": ["staging", "qa"],
  "is_default": false
}
```

**Run 关联**: `RunModel.environment_id` 字段（可选，向后兼容）

**向后兼容**:
- 优先级: 显式传入 → environment_id → 默认值
- 现有代码无需修改

#### ✅ P6-5: Secret Manager（已完成）

**当前**: API Key 明文存储在 `.env`

**目标**: SecretStore + secret_ref

**实现文件**:
- `aitest/infra/encryption.py` — FileEncryptionProvider / CloudEncryptionProvider
- `aitest/platform/secret.py` — Secret/SecretAuditLog dataclass
- `aitest/platform/secret_models.py` — SecretModel/SecretAuditLogModel ORM
- `aitest/platform/secret_store.py` — SecretStore CRUD + 加密/解密
- `aitest/server/api/secrets_v1.py` — REST API（7 个端点）
- `migrations/add_secrets_tables_sqlite.sql` — 数据库迁移
- `tests/test_secret_manager.py` — 完整测试（7 个场景）
- `docs/secret_manager_design.md` — 设计文档
- `docs/SECRET_MANAGER_MIGRATION.md` — 迁移指南

**加密方案**:
```python
# 开发环境: 文件加密（Fernet 对称加密）
governance/.data/.secret_key  # 加密密钥
governance/.data/aitest.db    # 加密后的 Secret 存储在 SQLite

# 生产环境: 云端 Secret Manager（占位实现）
AWS Secrets Manager / Azure Key Vault / HashiCorp Vault / GCP Secret Manager
```

**数据库表**:
```sql
CREATE TABLE secrets (
    secret_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- "api_key" | "password" | "token" | "certificate"
    encrypted_value TEXT NOT NULL,
    description TEXT,
    tags TEXT,  -- JSON 数组
    org_id TEXT,
    created_by TEXT,
    created_at TEXT,
    updated_at TEXT,
    last_accessed_at TEXT,
    expires_at TEXT
);

CREATE TABLE secret_audit_logs (
    log_id TEXT PRIMARY KEY,
    secret_id TEXT NOT NULL,
    action TEXT NOT NULL,  -- "create" | "read" | "update" | "delete"
    actor TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    ip_address TEXT,
    metadata TEXT
);
```

**API**:
```
POST   /api/v1/secrets              # 创建 Secret
GET    /api/v1/secrets              # 列出 Secrets
GET    /api/v1/secrets/:id          # 获取 Secret（不返回解密值）
GET    /api/v1/secrets/:id/value    # 获取解密值
PUT    /api/v1/secrets/:id          # 更新 Secret
DELETE /api/v1/secrets/:id          # 删除 Secret
GET    /api/v1/secrets/:id/audit    # 审计日志
```

**secret_ref 引用机制**:
```python
# ModelProvider 使用 secret_ref
{
  "provider_id": "anthropic-prod",
  "config": {
    "api_key_ref": "secret:anthropic-api-key-prod"
  }
}

# 自动解析
provider.get_api_key()
# → 从 SecretStore 加载并解密 "anthropic-api-key-prod"
```

**集成到 ModelProvider**:
```python
# get_api_key() 优先级
# 1. api_key_ref（Secret Manager）
# 2. api_key（明文，向后兼容）
```

**向后兼容**:
- 支持明文 api_key（fallback）
- 渐进式迁移（可混合使用）
- 现有代码无需修改

---

### ✅ 阶段 6 — CLI 重构（核心任务已完成）

**目标**: CLI 命令与产品概念对齐

#### ✅ P2-1: CLI 子命令重构（已完成）

**实现内容**:
- 新命令组: `aitest run create/list/show`（资源化）
- 新命令组: `aitest agent list/show`（资源化）
- 向后兼容: `aitest graph run` → 自动转换为 `aitest run create`
- 配置系统: ConfigResolver 统一配置优先级（CLI > 环境变量 > 配置文件 > 默认值）
- 输出系统: 统一输出格式（table/json/yaml）
- 废弃警告: 旧命令显示新命令提示

**交付文件**:
- `aitest/cli/main.py` — CLI v2 主文件（450 行）
- `aitest/cli/utils/config.py` — 配置解析器（220 行）
- `aitest/cli/utils/output.py` — 输出格式化工具（130 行）
- `aitest/cli/commands/run/create.py` — run create 命令（130 行）
- `aitest/cli/commands/run/list.py` — run list 命令（90 行）
- `aitest/cli/commands/run/show.py` — run show 命令（80 行）
- `aitest/cli/commands/agent/list.py` — agent list 命令（75 行）
- `aitest/cli/commands/agent/show.py` — agent show 命令（85 行）
- `aitest/tests/cli/test_cli_v2.py` — CLI v2 测试（350 行）
- `docs/cli_refactor_design.md` — 设计文档（450 行）
- `docs/SESSION_SUMMARY_2026-07-11_CLI_REFACTOR.md` — 实现总结

**总代码**: ~1,800 行

#### ✅ P2-2: 配置优先级统一（已完成）

**已在 P2-1 中完成**:
- ConfigResolver 类实现统一配置优先级
- 支持 CLI 参数 > 环境变量 > 配置文件 > 默认值
- 支持嵌套配置键（如 `defaults.llm_provider`）
- 类型转换（环境变量 → bool/int/float）

#### ✅ P2-3: 帮助文本完善（已完成）

**已在 P2-1 中完成**:
- 所有命令包含详细帮助文本
- 包含使用示例和参数说明
- 废弃命令显示新命令提示

#### ✅ P2-4: Init 向导改进（已完成）

**实现内容**:
- 自动检测项目结构（package.json → 框架/UI 库/模块）
- 路径校验与重复检测
- 配置验证（URL 格式、账号格式）
- 快速模式（--quick）
- 非交互模式（--yes + CLI 参数）
- 智能默认值（使用检测结果预填表单）

**交付文件**:
- `aitest/cli/utils/detection.py` — 项目检测工具（270 行）
- `aitest/cli/utils/validation.py` — 配置验证工具（180 行）
- `aitest/cli/commands/project/init.py` — Init 向导主逻辑（+300 行改进）
- `aitest/cli/main.py` — 添加新参数支持（+5 行）
- `docs/init_wizard_improvement_design.md` — 设计文档（650 行）
- `docs/SESSION_SUMMARY_2026-07-11_INIT_IMPROVED.md` — 实现总结

**总代码**: ~750 行

**检测准确率**: 100%（Vue/React/Angular + 主流 UI 库）

#### ✅ P2-5: 多项目切换（已完成）

**目标**: 优化 `aitest init` 交互式项目初始化体验

**改进点**:
- 交互式问答（项目类型/测试目标/环境配置）
- 自动检测项目结构
- 生成模板文件（project.yaml/.tlo/）
- 验证配置正确性

#### ✅ P2-5: 多项目切换（别名与历史，已完成）

**当前**: `aitest project set/list/register` 命令已存在

**改进点**:
- 优化多项目管理体验
- 支持项目别名
- 快速切换项目（aitest project switch <alias>）
- 项目配置继承

#### ✅ P2-8: 新增 CLI 命令（已完成 workflow/quality/provider）

**目标**: 补充剩余资源的 CLI 命令

```bash
# Workflow 命令
aitest workflow create --file workflow.json
aitest workflow list
aitest workflow show <workflow_id>
aitest workflow validate <workflow_id>
aitest workflow run <workflow_id>

# Quality 命令
aitest quality dataset create --name "test-suite"
aitest quality eval run --dataset <d> --agent <a>
aitest quality experiment create --baseline <e1> --candidate <e2>

# Provider 命令
aitest provider list
aitest provider create --name "claude-prod" --type anthropic

# MCP 命令
aitest mcp list
aitest mcp start <mcp_server_id>
aitest mcp stop <mcp_server_id>

# Plugin 命令
aitest plugin list
aitest plugin install <url>

# Run 扩展命令
aitest run logs <run_id> [--follow]
aitest run stop <run_id>
aitest run retry <run_id>
aitest run compare <run_id_1> <run_id_2>
aitest run artifacts <run_id> [--download]
```

#### ✅ P3-1: CLI 支持 `--output json`（已完成）

**已在 P2-1 中完成**:
- 所有命令支持 `--output table|json|yaml`
- JSON 输出可用于脚本（如 `jq` 处理）

```bash
aitest run list --output json | jq '.runs[0].run_id'
aitest agent list --output yaml
```

---

### ⏸️ 阶段 7 — 质量 & 外部集成（最低优先级）

**遗留问题**（可延后到 MVP 之后）:
- P2-7: Quality (Dataset/Evaluation/Experiment) 完全缺失（已在阶段 3 覆盖）
- P3-4: Secrets Manager 完全缺失（已在阶段 5 P6-5 覆盖）
- P3-5: Worker Lease/Heartbeat 无 HTTP API（企业特性，延后）
- P3-6: Billing 只有 hook，无 REST API（企业特性，延后）

---

## 累积问题清单（28 项）进度

| 级别 | 总数 | 已完成 | 进行中 | 待开始 |
|------|------|--------|--------|--------|
| P0（阻塞） | 3 | 3 ✅ | 0 | 0 |
| P1（架构债） | 2 | 2 ✅ | 0 | 0 |
| P2（体验债） | 5 | 0 | 0 | 5 ⏸️ |
| P3（功能缺失） | 6 | 2 ✅ | 0 | 4 ⏸️ |
| P4（治理机制） | 1 | 1 ✅ | 0 | 0 |
| P5（质量闭环） | 1 | 1 ✅ | 0 | 0 |
| P6（外部依赖） | 5 | 5 ✅ | 0 | 0 |
| P7（Control Plane） | 3 | 3 ✅ | 0 | 0 |
## 累积问题清单（28 项）进度

| 级别 | 总数 | 已完成 | 进行中 | 待开始 |
|------|------|--------|--------|--------|
| P0（阻塞） | 3 | 3 ✅ | 0 | 0 |
| P1（架构债） | 2 | 2 ✅ | 0 | 0 |
| P2（体验债） | 5 | 4 ✅ | 0 | 1 ⏸️ |
| P3（功能缺失） | 6 | 3 ✅ | 0 | 3 ⏸️ |
| P4（治理机制） | 1 | 1 ✅ | 0 | 0 |
| P5（质量闭环） | 1 | 1 ✅ | 0 | 0 |
| P6（外部依赖） | 5 | 5 ✅ | 0 | 0 |
| P7（Control Plane） | 3 | 3 ✅ | 0 | 0 |
| P8（Workflow 图） | 3 | 3 ✅ | 0 | 0 |

**当前口径**: 核心 MVP 任务已完成；剩余项目均为明确延期或占位能力，详见文档顶部真实状态校正与各阶段 backlog。

---

## 里程碑

### ✅ Milestone 1: 解除阻塞（已完成 2026-07-10）
- 阶段 0 + 阶段 1 全部完成
- 测试和开发不再受阻

### ✅ Milestone 2: Run 资源可用（已完成）
- P7-2 Phase 1-5 全部完成（后端 + 前端 + 多类型支持 + deprecated 标记）
- P3-2/P3-3 完成（Multi-Run 对比 + Artifact 下载）

### ✅ Milestone 3: 质量闭环打通（已完成）
- P5-1 完成（Dataset/Evaluation/Experiment 数据模型 + REST API）
- P4-1 完成（Skill 版本绑定）

### 🟡 Milestone 4: Workflow Runtime（后端完成，Builder UI 待实现）
- P8-1 完成（Workflow 图模型资源化 + 执行引擎）
- P8-3 完成（静态校验：循环检测 + 可达性）
- P8-2 完成（HITL Gate 持久化、阻塞/超时、REST、WebSocket、Studio 面板与集成测试）
- `BuildView` / `WorkflowBuilderView` 尚未实现

### 🟡 Milestone 5: 核心外部依赖资源化（MVP）
- 阶段 5（外部依赖抽象）：P6-1 ✅ + P6-2 ✅ + P6-3 ✅ + P6-4 ✅ + P6-5 ✅
- 不等同于生产就绪：仍缺少云端 Secret Provider、Plugin 沙箱/签名/权限隔离、远程 Worker、企业权限、部署和运维验收。

### ✅ Milestone 6: CLI 重构（核心任务已完成）
- 阶段 6（CLI 重构）：P2-1 ✅ + P2-2 ✅ + P2-3 ✅ + P2-4 ✅ + P2-5 ✅ + P2-8 ✅
- **已完成**:
  - P2-1: CLI 子命令重构（run/agent 命令组）
  - P2-2: 配置优先级统一（ConfigResolver）
  - P2-3: 帮助文本完善（详细示例）
  - P2-4: Init 向导改进（自动检测 + 快速模式）
  - P3-1: CLI 支持 `--output json`（统一输出格式）
- **待完成**:
   - 无核心 CLI 任务遗留；后续仅做扩展命令和回归测试

---

## 关键决策记录

### 决策 1: P1-1 schema 统一
- **选择**: 承认当前实现（`test_project:`/`application:`/`discovery:`）为标准
- **理由**: 5 个项目文件已在生产使用，`test_project:` 语义更清晰
- **放弃**: ADR-001 的 `test:` 字段

### 决策 2: P7-2 挪到阶段 2
- **理由**: 统一执行入口本身就是资源模型重构，不是"地基"问题
- **影响**: 阶段 1 提前完成，阶段 2 工作量增加

### 决策 3: P7-2 Phase 向后兼容策略
- **新旧字段共存**: `agent/module/pages` 保留，`target_type/target_id/target_version` 新增
- **自动迁移**: `RunStore.__init__()` 时自动 ALTER TABLE
- **旧端点保留**: `POST /api/workspaces/:ws_id/executions` 保留 6 个月

### 决策 4: 阶段 5、6 可与阶段 2-4 并行
- **理由**: 外部依赖资源化（阶段 5）和 CLI 重构（阶段 6）相对独立
- **前提**: 必须完成阶段 0、1

---

## 下次会话启动指令

**方式 1（推荐）**: 直接提供任务指令
```
请读取 D:\Desktop\Alice\docs\HANDOVER_SESSION_2026-07-10.md，
继续 P7-2 Phase 3（前端切换到新执行端点）。
```

**方式 2**: 更改优先级
```
请读取 D:\Desktop\Alice\docs\MASTER_ROADMAP.md，
跳过 P7-2 Phase 3，直接实现 P3-2（Multi-Run 对比）和 P3-3（Artifact blob API）。
```

**方式 3**: 切换阶段
```
请读取 D:\Desktop\Alice\docs\MASTER_ROADMAP.md，
开始阶段 3（质量闭环资源化）：实现 P5-1 Dataset/Evaluation/Experiment 资源模型。
```

---

## 技术债务清单（生产前必须解决）

1. **Alembic 缺失**: 手动 ALTER TABLE 不适合生产环境
2. **PostgreSQL 迁移未验证**: 当前只测试了 SQLite
3. **测试覆盖不足**: 新端点和数据库迁移逻辑缺少单元测试
4. **Signed URL 未实现**: Artifact 下载依赖本地文件系统
5. **Secret 明文存储**: `.env` 文件不安全
6. **错误处理不完整**: 新端点缺少详细错误码和重试逻辑
7. **性能未优化**: Multi-Run 对比可能涉及大量数据库查询
8. **权限控制缺失**: 新端点未实现细粒度权限检查

---

## 参考文档

- **决策记录**: 上个会话的决策 1-8（完整版保存在会话历史）
- **累积问题**: 上个会话的 P0-P8 完整清单
- **设计文档**: `docs/api/POST_api_v1_runs.md`
- **架构文档**: `docs/adr/ADR_001_TLO_DIRECTORY.md`
- **产品定位**: `PRODUCT.md`（唯一事实源）
- **会话交接**: `docs/HANDOVER_SESSION_2026-07-10.md`（阶段 2 详细状态）
