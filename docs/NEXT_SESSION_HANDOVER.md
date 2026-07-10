# 下一轮会话交接文档 — 完成平台资源化最后 10%

> **创建时间**: 2026-07-11  
> **当前进度**: CLI MVP 100% 完成，整体平台 ~90%  
> **剩余工作**: 3 个任务（后端 API + 前端 IA + HITL 设计）

---

## 📊 当前状态

### 已完成（本次会话）

1. ✅ **P2-5: 多项目切换** — 智能别名 + 历史跟踪
2. ✅ **P2-8: 新增 CLI 命令** — workflow/quality/provider（10 个命令）
3. ✅ **P3-2: Run 记录查询优化** — 高级筛选 + 分页 + 导出
4. ✅ **P3-6: Agent 版本管理** — 版本列表 + diff 对比

**CLI v2 成果**:
- 27 个命令
- 100% 测试通过
- 生产就绪

### 待完成任务（下一轮会话）

根据 `docs/MASTER_ROADMAP.md`，还有 3 个任务：

1. ⏸️ **P7-1: API 路由资源化** — 13 个 router 添加 `/api/v1/` 前缀
2. ⏸️ **P2-6/P7-3: Studio IA 重组** — 19 个 Views 按 5-resource 模型合并
3. ⏸️ **P8-2: HITL 节点化** — WebSocket + 前端 UI（设计文档）

---

## 🎯 任务 1: P7-1 API 路由资源化

### 目标

将 13 个 FastAPI router 从各自的旧路径迁移到统一的 `/api/v1/` 前缀。

### 调研结果（已完成）

**13 个待迁移 Router**:

| Router | 文件 | 当前路径 | 目标路径 | 前端依赖 |
|--------|------|----------|----------|----------|
| workspace_router | `api/workspace.py` | `/api/platform/orgs/{org_id}/workspaces` | `/api/v1/workspaces` | 0 处 |
| agents_router | `api/agents.py` | `/api/agent` | `/api/v1/agents` | 0 处 |
| workflows_router | `api/workflows.py` | `/api/workflow` | `/api/v1/workflows` | 0 处 |
| bugs_router | `api/bugs.py` | `/api/bugs` | `/api/v1/bugs` | 0 处 |
| audit_router | `api/audit.py` | `/api/audit/*` | `/api/v1/audit` | 0 处 |
| kpi_router | `api/kpi.py` | `/api/kpi/*` | `/api/v1/kpi` | 3 处 ⚠️ |
| kanban_router | `api/kanban.py` | `/api/sop/*`, `/api/kanban/*` | `/api/v1/kanban` | 2 处 ⚠️ |
| terminal_router | `api/terminal.py` | `/ws/agent-terminal` | `/api/v1/terminal` | 1 处 ⚠️ |
| obs_router | `api/observability.py` | `/api/observability/*` | `/api/v1/observability` | 1 处 ⚠️ |
| chat_router | `api/chat.py` | `/api/chat/*` | `/api/v1/chat` | 10 处 ⚠️ |
| sessions_router | `api/sessions_api.py` | `/api/sessions/*` | `/api/v1/sessions` | 0 处 |
| onboarding_router | `api/onboarding.py` | `/api/onboarding/*` | `/api/v1/onboarding` | 5 处 ⚠️ |
| integrations_router | `api/integrations.py` | `/api/integrations/*` | `/api/v1/integrations` | 0 处 |

**前端依赖总计**: 22 处（主要集中在 chat/onboarding/kpi）

### 参考模式

已完成迁移的 3 个 router（runs/quality/workflows_v1）**直接使用新前缀，无向后兼容层**。

但 MASTER_ROADMAP.md 建议**保留旧端点 6 个月**向后兼容。

### 实施策略（建议）

**方案 1: 直接迁移（快速但有风险）**
- 修改 router prefix
- 同步修改前端 22 处引用
- 无向后兼容

**方案 2: 双路径兼容（推荐）**
- 新路径作为主路径
- 旧路径保留 6 个月，返回 deprecated warning
- 前端逐步迁移

**方案 3: 分批迁移**
- 优先迁移零依赖的 7 个 router（workspace/agents/workflows/bugs/audit/sessions/integrations）
- 再迁移高依赖的 6 个 router（chat/onboarding/kpi/kanban/obs/terminal）

### 工作清单

1. **后端迁移** (13 个文件):
   ```
   aitest/server/api/workspace.py
   aitest/server/api/agents.py
   aitest/server/api/workflows.py
   aitest/server/api/bugs.py
   aitest/server/api/audit.py
   aitest/server/api/kpi.py
   aitest/server/api/kanban.py
   aitest/server/api/terminal.py
   aitest/server/api/observability.py
   aitest/server/api/chat.py
   aitest/server/api/sessions_api.py
   aitest/server/api/onboarding.py
   aitest/server/api/integrations.py
   ```

2. **前端同步** (22 处引用):
   ```
   aitest/web/src/api/endpoints.ts (15 处)
   aitest/web/src/api/client.ts (3 处)
   aitest/web/src/stores/kanban.ts (2 处)
   aitest/web/src/hooks/useOnboardingWS.ts (1 处)
   aitest/web/src/views/ObservabilityView.tsx (1 处)
   ```

3. **测试验证**:
   - 手动验证关键端点（无自动化测试）
   - 建议添加集成测试

### 预计工作量

- **后端**: 2-3 小时（修改 13 个 router prefix）
- **前端**: 1-2 小时（修改 22 处引用）
- **测试**: 1 小时（手动验证）
- **总计**: **4-6 小时**

---

## 🎯 任务 2: P2-6/P7-3 Studio IA 重组

### 目标

将 19 个平铺的 Views 重组为按 5-resource 模型（Projects/Runs/Quality/Registry/Assets）的层级结构。

### 当前结构（19 个平铺 Views）

```
aitest/web/src/views/
├── DashboardView.tsx
├── ProjectOverviewView.tsx
├── ExecutionView.tsx
├── RunInspectorView.tsx
├── AgentDetailView.tsx
├── AgentTerminalView.tsx
├── TimelineView.tsx
├── KanbanView.tsx
├── GapDiscoveryView.tsx
├── ReportsView.tsx
├── ArtifactsView.tsx
├── KnowledgeView.tsx
├── KnowledgeGraphView.tsx
├── ObservabilityView.tsx
├── SettingsView.tsx
├── ProjectSettingsView.tsx
├── StrategyPlannerView.tsx
├── IntelligenceChatView.tsx
├── OnboardingWizardView.tsx
└── (未完成: WorkflowBuilderView)
```

### 目标结构（5-resource 模型）

根据 MASTER_ROADMAP.md：

```
全局导航 (Global):
  ProjectsView.tsx              # 项目列表
  GlobalRunsView.tsx            # 全局运行历史
  EvaluationsView.tsx           # 全局质量评估
  RegistryView.tsx              # Agent/Workflow/Provider 注册中心
  SettingsView.tsx              # 全局设置

项目内导航 (Project Context):
  Overview                      # 项目概览 + 最近 Runs
    - ProjectOverviewView.tsx
    - DashboardView.tsx (合并)
    
  Build                         # 构建资源
    - WorkflowBuilderView.tsx   # Workflow 编辑器
    - StrategyPlannerView.tsx   # 策略规划
    
  Run                           # 执行资源
    - ExecutionView.tsx         # 执行面板
    - RunInspectorView.tsx      # Run 详情
    - TimelineView.tsx          # 时间线
    - KanbanView.tsx            # 看板
    
  Quality                       # 质量资源
    - GapDiscoveryView.tsx      # Gap 发现
    - ReportsView.tsx           # 质量报告
    
  Assets                        # 资产资源
    - AgentDetailView.tsx       # Agent 详情
    - AgentTerminalView.tsx     # Agent 终端
    - ArtifactsView.tsx         # 构件管理
    - KnowledgeView.tsx         # 知识库
    - KnowledgeGraphView.tsx    # 知识图谱

横向功能 (Cross-cutting):
  IntelligenceChatView.tsx      # AI 助手（全局悬浮）
  OnboardingWizardView.tsx      # 引导向导（首次进入）
  ObservabilityView.tsx         # 可观测性（独立入口）
  ProjectSettingsView.tsx       # 项目设置（独立入口）
```

### 实施步骤

1. **设计新导航结构**
   - 绘制导航树（Global + Project Context）
   - 定义路由映射（URL schema）
   - 确定 Layout 组件层级

2. **创建脚手架**
   ```
   aitest/web/src/layouts/
   ├── GlobalLayout.tsx          # 全局布局（Projects/GlobalRuns/...）
   └── ProjectLayout.tsx         # 项目布局（Overview/Build/Run/...）
   
   aitest/web/src/views/
   ├── global/
   │   ├── ProjectsView.tsx
   │   ├── GlobalRunsView.tsx
   │   ├── EvaluationsView.tsx
   │   └── RegistryView.tsx
   └── project/
       ├── overview/
       ├── build/
       ├── run/
       ├── quality/
       └── assets/
   ```

3. **重构 SidebarNav**
   - `aitest/web/src/components/SidebarNav.tsx`
   - 新增 Context 感知（全局 vs 项目内）
   - 新增 Breadcrumb 导航

4. **迁移 Views**
   - 逐个移动现有 Views 到新目录
   - 更新路由配置
   - 更新导入路径

5. **更新路由配置**
   - `aitest/web/src/router/index.ts`
   - 定义新的嵌套路由
   - 保留旧路由重定向（兼容性）

### 工作清单

**设计阶段** (建议先完成):
- [ ] 绘制完整的导航树图
- [ ] 定义 URL schema（路由规则）
- [ ] 设计 Layout 组件 API

**实施阶段**:
- [ ] 创建 GlobalLayout.tsx
- [ ] 创建 ProjectLayout.tsx
- [ ] 重构 SidebarNav.tsx
- [ ] 创建新目录结构
- [ ] 迁移 19 个 Views（逐个）
- [ ] 更新 router/index.ts
- [ ] 更新所有 import 路径
- [ ] 测试导航流程

### 预计工作量

- **设计**: 2-3 小时（绘图 + 文档）
- **脚手架**: 3-4 小时（Layout + SidebarNav）
- **Views 迁移**: 6-8 小时（19 个 Views）
- **路由更新**: 2-3 小时
- **测试**: 2 小时
- **总计**: **15-20 小时**

---

## 🎯 任务 3: P8-2 HITL 节点化设计

### 目标

设计 Human-In-The-Loop (HITL) 节点的完整方案：
- WebSocket 实时推送
- 前端表单 UI
- 审核流程

### 当前状态

**已实现（基础版）**:
- `aitest/graphs_dev/workflow_builder.py` 中有 `human_gate` 节点类型
- 返回 `default_action`（无真实人工审核）

**需要设计**:
1. WebSocket 协议（Server → Studio）
2. 表单 Schema（动态表单定义）
3. 前端组件（审核 UI）
4. 审核状态管理（pending/approved/rejected）
5. 超时处理

### 设计文档大纲（建议）

创建 `docs/design/HITL_NODE_DESIGN.md`:

```markdown
# HITL 节点设计文档

## 1. 架构概览
- Server 推送流程
- Studio 响应流程
- 状态同步机制

## 2. WebSocket 协议
### 2.1 消息格式
```json
{
  "type": "human_gate",
  "run_id": "run_123",
  "node_id": "hitl-review",
  "prompt": "请审核需求分析结果",
  "context": { ... },
  "options": ["approve", "reject", "request_changes"],
  "timeout_seconds": 3600
}
```

### 2.2 响应格式
```json
{
  "action": "approve",
  "comment": "LGTM",
  "timestamp": "2026-07-11T12:00:00Z"
}
```

## 3. 表单 Schema
- JSON Schema 定义
- 字段类型（text/select/checkbox/...）
- 验证规则

## 4. 前端组件
- `HumanGatePanel.tsx` — 审核面板
- `HumanGateForm.tsx` — 动态表单
- `HumanGateHistory.tsx` — 审核历史

## 5. 数据库表
```sql
CREATE TABLE human_gate_approvals (
    approval_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    status TEXT,  -- "pending" | "approved" | "rejected"
    action TEXT,
    comment TEXT,
    approver TEXT,
    created_at TEXT,
    resolved_at TEXT
);
```

## 6. API 端点
```
GET    /api/v1/runs/:run_id/human-gates        # 列出所有 HITL 节点
POST   /api/v1/runs/:run_id/human-gates/:node_id/resolve  # 提交审核
```

## 7. 实施计划
- Phase 1: 设计文档
- Phase 2: WebSocket 协议实现
- Phase 3: 前端 UI 实现
- Phase 4: 集成测试
```

### 工作清单

**本次会话（仅设计文档）**:
- [ ] 创建 `docs/design/HITL_NODE_DESIGN.md`
- [ ] 定义 WebSocket 协议
- [ ] 定义表单 Schema
- [ ] 设计数据库表
- [ ] 绘制交互流程图

**下次会话（实现）**:
- [ ] 实现 WebSocket 推送
- [ ] 实现前端组件
- [ ] 实现 API 端点
- [ ] 集成测试

### 预计工作量

- **设计文档**: 2-3 小时
- **实现**: 8-10 小时（下次会话）
- **总计**: **10-13 小时**

---

## 📁 关键文件清单

### 已完成的成果文件

**CLI v2 实现**:
```
aitest/cli/main.py                          # CLI 主入口（27 个命令）
aitest/cli/config.py                        # 配置管理（增强版）
aitest/cli/commands/
├── run/list.py                             # Run 查询优化（P3-2）
├── agent/versions.py                       # Agent 版本管理（P3-6）
├── project/switch.py                       # 多项目切换（P2-5）
├── workflow/                               # Workflow 命令组（P2-8）
├── quality/                                # Quality 命令组（P2-8）
└── provider/                               # Provider 命令组（P2-8）
```

**测试文件**:
```
test_p2_5_logic.py                          # P2-5 测试（4/4 通过）
test_p2_8_workflow.py                       # P2-8 Workflow（4/4 通过）
test_p2_8_quality_provider.py               # P2-8 Quality/Provider（5/5 通过）
test_p3_2_p3_6.py                           # P3-2 + P3-6（5/5 通过）
```

**文档**:
```
docs/SESSION_SUMMARY_2026-07-11_P2-5_MULTI_PROJECT.md
docs/SESSION_SUMMARY_2026-07-11_P2-8_WORKFLOW.md
docs/SESSION_SUMMARY_2026-07-11_P2-8_COMPLETE.md
docs/HANDOVER_SESSION_2026-07-11_FINAL_v3.md
docs/PROJECT_COMPLETION_100_PERCENT.md
docs/NEXT_SESSION_HANDOVER.md               # 本文档
```

### 待修改的核心文件

**P7-1 API 路由资源化**:
```
aitest/server/api/workspace.py              # 修改 prefix
aitest/server/api/agents.py                 # 修改 prefix
aitest/server/api/workflows.py              # 修改 prefix
aitest/server/api/bugs.py                   # 修改 prefix
aitest/server/api/audit.py                  # 修改 prefix
aitest/server/api/kpi.py                    # 修改 prefix
aitest/server/api/kanban.py                 # 修改 prefix
aitest/server/api/terminal.py               # 修改 prefix
aitest/server/api/observability.py          # 修改 prefix
aitest/server/api/chat.py                   # 修改 prefix
aitest/server/api/sessions_api.py           # 修改 prefix
aitest/server/api/onboarding.py             # 修改 prefix
aitest/server/api/integrations.py           # 修改 prefix

aitest/web/src/api/endpoints.ts             # 同步修改 15 处
aitest/web/src/api/client.ts                # 同步修改 3 处
aitest/web/src/stores/kanban.ts             # 同步修改 2 处
aitest/web/src/hooks/useOnboardingWS.ts     # 同步修改 1 处
aitest/web/src/views/ObservabilityView.tsx  # 同步修改 1 处
```

**P2-6/P7-3 Studio IA 重组**:
```
aitest/web/src/layouts/
├── GlobalLayout.tsx                        # 新增
└── ProjectLayout.tsx                       # 新增

aitest/web/src/components/SidebarNav.tsx    # 重构

aitest/web/src/views/                       # 重组目录结构
├── global/                                 # 新增
└── project/                                # 新增

aitest/web/src/router/index.ts              # 重构路由
```

**P8-2 HITL 节点化**:
```
docs/design/HITL_NODE_DESIGN.md             # 新增设计文档
aitest/server/api/human_gates.py            # 新增 API
aitest/web/src/components/HumanGatePanel.tsx # 新增组件
```

---

## 🚀 启动下一轮会话

### 推荐的任务顺序

**方案 1: 快速完成后端（推荐）**
1. P7-1 API 路由资源化（4-6 小时）
2. P8-2 HITL 设计文档（2-3 小时）
3. P2-6/P7-3 Studio IA 重组（15-20 小时，分多次会话）

**方案 2: 用户可见优先**
1. P2-6/P7-3 Studio IA 重组（先做设计 2-3 小时）
2. P7-1 API 路由资源化（4-6 小时）
3. P8-2 HITL 设计文档（2-3 小时）

### 启动命令

**直接继续（推荐）**:
```
继续完成剩余 3 个任务：
1. P7-1: API 路由资源化（13 个 router）
2. P2-6/P7-3: Studio IA 重组（19 个 Views）
3. P8-2: HITL 节点化设计

优先做 P7-1，参考 docs/NEXT_SESSION_HANDOVER.md
```

**单独完成某个任务**:
```
完成 P7-1: API 路由资源化
参考 docs/NEXT_SESSION_HANDOVER.md 中的调研报告和工作清单
```

---

## 📝 重要提醒

### 1. 向后兼容

**P7-1 API 路由迁移时**，建议保留旧路径 6 个月：
```python
# 新路径（主要）
@router.get("/api/v1/chat/sessions")
async def list_sessions():
    ...

# 旧路径（兼容）
@router.get("/api/chat/sessions", deprecated=True)
async def list_sessions_deprecated():
    # 返回 Warning header
    response.headers["X-API-Deprecated"] = "Use /api/v1/chat/sessions"
    return await list_sessions()
```

### 2. 前端同步

**P7-1 修改后端路径时**，必须同步修改前端 22 处引用，否则会导致功能失效。

### 3. 测试验证

13 个 router **无自动化测试**，迁移后需要：
- 手动验证关键端点
- 或添加集成测试（推荐）

### 4. Studio IA 重组影响面大

**P2-6/P7-3** 涉及 19 个 Views 和整个导航系统，建议：
- 先完成设计文档和评审
- 分批迁移（按资源类型）
- 每批迁移后充分测试

---

## 🎯 预期最终成果

完成这 3 个任务后：

1. ✅ **API 统一** — 所有端点使用 `/api/v1/` 前缀
2. ✅ **导航清晰** — 5-resource 模型导航（Global + Project Context）
3. ✅ **HITL 就绪** — 设计文档完成，可随时实施

**整体平台完成度**: 90% → **100%** ✅

---

## 📞 联系上下文

### 本次会话成果

- ✅ CLI v2 完整实现（27 个命令）
- ✅ 4 个任务完成（P2-5/P2-8/P3-2/P3-6）
- ✅ 18 个测试全部通过
- ✅ 5 个总结文档

### 下次会话目标

- ⏸️ 完成剩余 3 个任务
- ⏸️ 平台 100% 完成
- ⏸️ 生产部署就绪

---

**准备就绪，随时可以启动下一轮会话！** 🚀
