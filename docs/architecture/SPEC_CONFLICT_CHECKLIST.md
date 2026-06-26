# 规范冲突清单 — APERANT_MIGRATION_PLAN.md vs 现有治理体系

> 审计日期: 2026-06-24 | 审计基准: CONSTITUTION.md v1.0 + source-of-truth.md + ADR-001 + shared-language.md
> 被审计对象: APERANT_MIGRATION_PLAN.md v1.1
> 方法论: 逐条对照 CONSTITUTION §1-§6、ADR-001 原则、source-of-truth 事实源分工

---

## 审查范围

| 治理文件 | 版本 | 关键约束 |
|---------|------|---------|
| [CONSTITUTION.md](CONSTITUTION.md) | v1.0 (2026-06-23) | 层级冻结、Python-free governance、Extension Point 优先、禁止清单 |
| [ADR_001_TLO_DIRECTORY.md](adr/ADR_001_TLO_DIRECTORY.md) | 已决议 (2026-06-23) | .tlo/ 跟随项目、知识 vs 派生分离 |
| [source-of-truth.md](../governance/context/source-of-truth.md) | — | 事实源分工、SOP 状态 SQLite 权威 |
| [shared-language.md](../governance/context/shared-language.md) | 2026-06-23 | 术语定义、歧义消除、ComplexityTier 已定义 |
| [testing_memory.py](../aitest/platform/testing_memory.py) | — | 8 类型枚举、BehaviorSignal、Confidence |

---

# 一、冲突项 (Migration Plan 与现有规范相抵触)

## 冲突 1 (P0): FROZEN 层文件变更未提及 Architecture Review

**规范依据**: CONSTITUTION §1.1 — Platform Core (`aitest/llm/`) 状态为 ❄️ FROZEN，任何变更须 Architecture Review 批准。§4.3 明确列出审批流程。

**Migration Plan 触及的 FROZEN 文件**:

| Migration Plan 引用 | 实际路径 | 所属层 | 冻结状态 |
|--------------------|---------|--------|---------|
| `aitest/llm/context_window.py` | [aitest/llm/context_window.py](d:/Desktop/Alice/aitest/llm/context_window.py) | Platform Core | ❄️ FROZEN |
| `aitest/llm/context_injector.py` | [aitest/llm/context_injector.py](d:/Desktop/Alice/aitest/llm/context_injector.py) | Platform Core | ❄️ FROZEN |
| `aitest/knowledge/rag_engine.py` | [aitest/knowledge/rag_engine.py](d:/Desktop/Alice/aitest/knowledge/rag_engine.py) | 未分类 | ⚠️ 需分类 |

**CONSTITUTION §1.2 Frozen 清单** 也锁定了:
- `aitest/agents/agent_runner.py` — `AgentLoop.run()` 签名不可变 (Migration Plan Task 5 包装调用)
- `aitest/server/main.py` — REST API 端点路径不可变 (Migration Plan Task 2 新增 `/api/tasks/{id}/resume`)

**风险**: 开发者直接修改 FROZEN 文件，违反 CONSTITUTION 审批流程。PR 被拒或引发架构治理债务。

**建议修订 APERANT_MIGRATION_PLAN.md**:
1. 在 Step 4 每个 Task 开头增加 `**审批要求**: Architecture Review Required for: <文件列表>` 字段
2. 在 Task 5 中明确 `agent_runner.py` 只添加 wrapper 调用，不修改 `AgentLoop.run()` 签名
3. 将 `rag_engine.py` 归类到具体层级（建议 Agent Runtime → STABLE）

---

## 冲突 2 (P0): `.tlo/` 用作平台执行状态存储，违反 ADR-001

**规范依据**: ADR-001 核心原则 1 — "项目上下文属于项目，不属于平台"。`.tlo/` 跟随 git clone，存放项目知识 (`knowledge/`) 和派生数据 (`cache/`, `graph.json`)。source-of-truth.md 明确 SOP 运行状态权威源是 `governance/.graph_state/checkpoints.sqlite`。

**Migration Plan 方案**:
```python
# Migration Plan Task 2 + 风险缓解 1
pause_file = f".tlo/{task_id}/PAUSE"
resume_file = f".tlo/{task_id}/RESUME"
```

**冲突**: Pause/Resume 是**平台执行状态**（类似 LangGraph checkpoint），不是项目知识。放在 `.tlo/` 下会导致:
- `git clone` 项目后携带上一次执行的暂停状态（不应跟随项目）
- 与 ADR-001 的 `knowledge/` vs `cache/` 分层混淆
- 与 source-of-truth.md 的 SOP 状态 SQLite 权威源冲突

**正确位置应为**: `governance/.events/{task_id}/PAUSE` 或 `aitest/.graph_state/{task_id}/PAUSE`（与现有 `.graph_state/` 对齐）或 `governance/.data/{task_id}/PAUSE`

**建议修订 APERANT_MIGRATION_PLAN.md**:
1. 将所有 `.tlo/{task_id}/PAUSE` 替换为 `governance/.data/{task_id}/pause.json`
2. 在 Risk 1 缓解方案中引用 source-of-truth.md 的 SOP 状态分工
3. 增加 "不写入 .tlo/ 目录" 约束

---

## 冲突 3 (P1): WORKFLOW_RECIPE 类型重复定义

**规范依据**: [testing_memory.py:42](d:/Desktop/Alice/aitest/platform/testing_memory.py#L42) 已定义 `WORKFLOW_RECIPE = "workflow_recipe"`。shared-language.md §TestingMemory 已声明 8 种类型含 `workflow_recipe`。

**Migration Plan 方案**:
```
Migration Plan Task 3b: 增加 DEAD_END, WORKFLOW_RECIPE, DECISION, TASK_CALIBRATION 记忆类型
```

**冲突**: `WORKFLOW_RECIPE` 已存在。Migration Plan 应表述为"扩展已有枚举"，而非"新增"。此外 `DECISION` 与现有 `HISTORICAL_FAILURE` 有语义重叠（失败后的决策 vs 失败模式本身）。

**建议修订 APERANT_MIGRATION_PLAN.md**:
1. Task 3b 改为 "扩展 MemoryType 枚举: 新增 3 个类型 (DEAD_END, TASK_CALIBRATION, DECISION), WORKFLOW_RECIPE 已存在于行 42"
2. 在 shared-language.md 的 TestingMemory 条目中追加新类型定义

---

## 冲突 4 (P2): 前端技术栈在多个治理文件中不一致

**背景**: 这是**已有治理漂移**，Migration Plan 继承了正确状态但需显式记录。

| 文件 | 声明 | 实际代码 |
|------|------|---------|
| CONSTITUTION.md §5 | "Vue 3 + Pinia" | ❌ 过时 |
| FRONTEND_REBUILD_PLAN_A.md | "保留 Vite + Vue 3.5 技术栈" | ❌ 与代码冲突 |
| [package.json](d:/Desktop/Alice/aitest/web/package.json) | React 18 + Zustand + React Router | ✅ 当前事实 |
| APERANT_MIGRATION_PLAN.md | 引用 `kanban.ts` (Zustand store) | ✅ 匹配代码 |

**Migration Plan 正确使用了 Zustand stores**，但 CONSTITUTION.md 声明的 "Vue 3 + Pinia" 会在执行时造成混淆。

**建议修订 CONSTITUTION.md (独立修复,非 Migration Plan 范围)**:
1. §5 技术栈基线: "Vue 3 + Pinia" → "React 18 + Zustand"
2. UI 组件: "Radix Vue + Tailwind CSS" → "Radix UI + Tailwind CSS + Lucide React"
3. `governance/context/shared-language.md` 中 "Vue 3 Teleport" → 删除或在歧义表中标注 "仅适用于被测系统前端"

---

## 冲突 5 (P2): REST API 端点变更触及 FROZEN 清单

**规范依据**: CONSTITUTION §1.2 Frozen 清单 — `aitest/server/main.py` REST API 端点路径不可变。

**Migration Plan 方案**: Task 2 新增 `POST /api/tasks/{id}/resume`

**分析**: 新增端点（非修改已有端点）在 §4.2 属于"轻审批"范围。但 Migration Plan 未标注审批要求。

**建议修订 APERANT_MIGRATION_PLAN.md**: Task 2 增加 `**审批要求**: Light Review (新增端点，不修改已有路径)` 标注。

---

# 二、一致项 (现有规范支持迁移计划)

| # | 规范 | Migration Plan 对齐点 | 证据 |
|---|------|---------------------|------|
| C1 | `aitest/infra/` STABLE 层可增加模块 | Task 2 新建 `pause_handler.py` | CONSTITUTION §1.1: infra "可增不可删" |
| C2 | `aitest/mcp/` STABLE 层可增加模块 | Task 6 新建 `mcp_client.py` | CONSTITUTION §1.1: mcp "可增不可删" |
| C3 | ComplexityTier 术语已定义 | Task 1 使用 SIMPLE/STANDARD/COMPLEX | shared-language.md §ComplexityRouting |
| C4 | Extension Point 模式 | Agent 定义走 `agent-definitions.yaml`, Skill 走 `governance/skills/` | CONSTITUTION P6 |
| C5 | ChromaDB 技术基线 | Task 3b 复用现有 ChromaDB | CONSTITUTION §5 |
| C6 | `ObservationBus` 事件订阅 | Task 3b 订阅 `SKILL_FAILED` 事件 | testing_memory.py 已有 `BehaviorSignal` |
| C7 | `MemoryType` 枚举扩展模式 | Task 3b 在现有 `class MemoryType(Enum)` 上增加成员 | [testing_memory.py:34](d:/Desktop/Alice/aitest/platform/testing_memory.py#L34) |
| C8 | Agent 定义声明式 | 新 agent type (planner/coder/qa_reviewer) 应在 YAML 定义 | CONSTITUTION P3 |
| C9 | `governance/` Python-free | Migration Plan 未提议在 governance/ 写 Python 代码 | CONSTITUTION P2 |
| C10 | `.tlo/knowledge/` 作为项目知识源 | Memory types 与 `.tlo/knowledge/modules/` 互补 | ADR-001 原则 2 |

---

# 三、缺失项 (Migration Plan 需要但现有规范未覆盖)

## 缺失 1: 平台执行状态 vs 项目知识边界定义

**问题**: 现有规范定义了 `.tlo/`（项目）和 `governance/context/`（平台配置）的边界，但未定义**运行时执行状态**（pause/resume、session checkpoint、agent 中间状态）的存储位置。

**现状**: 
- source-of-truth.md 指定 SOP 状态 → `governance/.graph_state/checkpoints.sqlite` (LangGraph)
- `governance/.events/` 存在但无规范文件说明用途
- `governance/.data/` 未在任何规范文件中出现

**Migration Plan 需要**: 明确的 "平台执行状态目录" 存储 sentinel 文件、agent session state、task FSM 状态。

**建议** (修订 CONSTITUTION.md 或 source-of-truth.md):
1. 新增条目: "平台执行状态: `governance/.data/{task_id}/` — 运行时 pause/resume、session checkpoint、agent 状态。不跟随项目 git。"
2. 与 `.graph_state/` 的关系: `.graph_state/` = LangGraph 专用 checkpoint; `.data/` = 通用执行状态

---

## 缺失 2: 新 Agent Type 的声明式定义规范

**问题**: Migration Plan 引入 4 个新 agent type (planner, coder, qa_reviewer, qa_fixer)，但未指定如何在 `governance/agents/agent-definitions.yaml` 中注册。

**CONSTITUTION P3** 要求 Agent 定义声明式。如果 Migration Plan 执行时只在 Python 代码中硬编码，将违反 CONSTITUTION。

**建议** (修订 APERANT_MIGRATION_PLAN.md 或新增 agent-definitions.yaml 条目):
1. 在 Task 1 和 Task 4 中增加 "agent-definitions.yaml 变更" 文件清单
2. 示例 agent definition entry:
```yaml
- name: planner
  phase: planning
  skills: [complexity-assessment, task-decomposition, implementation-planning]
  capabilities: [file_search, context_building, memory_query]
  boundaries: "只产出计划，不执行代码变更"
  mcp_servers: [auto-claude]
```

---

## 缺失 3: SOP Phase 扩展与 CANONICAL_PHASES 的对齐

**问题**: Migration Plan 引入新 phase (`plan_review`, `human_review`, `qa_review`, `qa_fixing`)，但 CONSTITUTION §1.2 将 SOP Phase 枚举列为 FROZEN。shared-language.md 定义 Phase 为 "Phase 0-9, CANONICAL_PHASES 定义"。

**风险**: 新 phase 需要插入 CANONICAL_PHASES 或作为 Phase 间子状态，但现有规范未说明如何扩展。

**建议** (修订 CONSTITUTION.md 或 shared-language.md):
1. 定义 Phase 扩展规则: "子 Phase (如 plan_review) 作为 Phase 间 guard 状态，不进入 CANONICAL_PHASES 枚举，由 task_state_machine.py 管理"
2. 或在 CONSTITUTION §1.2 中明确: "SOP Phase 枚举可增不可删/改"

---

## 缺失 4: Extension Point 评估记录

**问题**: CONSTITUTION P6 和 §8 决策框架要求: 任何新能力优先评估 Extension Point (Plugin → Skill → MCP Server → Config)，只有四种方式都无法满足时才改 Core。

**Migration Plan 未记录**对各 Task 的 Extension Point 评估结果。例如:
- Task 1 (pipeline_router.py) → 能否用 Config/Skill 实现？
- Task 3a (context_builder.py) → 能否用 MCP Server 实现？
- Task 4 (task_state_machine.py) → 能否用 Plugin 实现？

**建议** (修订 APERANT_MIGRATION_PLAN.md):
1. 在 Step 2 每个 P0/P1 条目增加 `**Extension Point 评估**: <Plugin/Skill/MCP/Config> — <可行/不可行> — <原因>`
2. 示例: "P0-1 pipeline_router.py — EP 评估: Config 不可行 (需要运行时动态路由，YAML 静态配置不足); MCP 不可行 (路由是内部编排逻辑); Plugin 可行但过度设计 → 直接实现为 Agent Runtime 层模块"

---

## 缺失 5: 前端状态管理规范

**问题**: CONSTITUTION.md 声明 "Vue 3 + Pinia" 但实际代码是 React 18 + Zustand。Migration Plan 正确使用了 Zustand stores 但未涉及此外治理漂移。

此外，Migration Plan Task 2 和 Task 4 涉及前端 `kanban.ts` store 修改，但无前端架构规范（store 设计原则、API 调用规范、组件结构）作为依据。

**建议** (修订 CONSTITUTION.md):
1. 修正 §5 技术栈为 React 18 + Zustand
2. 增加前端架构约束: "Zustand stores 按领域分离 (task/kanban/chat/settings), store 间通过 subscribe 通信, API 调用统一通过 api/client.ts"

---

## 🆕 缺失 6 (审阅增补): "代码生成 vs 测试执行" 语义映射未审计

**问题**: Aperant 的 Phase-Agent 流水线 (`planning → coding → qa_review → qa_fixing`) 是面向**代码生成**（创建新代码）的。aitest 是面向**测试执行**（验证现有系统）的。两个目标在语义上根本不同:

| Aperant 语义 | aitest 应有语义 | 风险 |
|-------------|---------------|------|
| `planner` → 拆解需求，生成"实现计划" | `test_planner` → 制定"测试策略/测试计划" | 直接移植会尝试创建代码而非执行测试 |
| `coder` → 写代码实现功能 | `test_executor` → 执行测试 Skill/用例 | `coder` agent 会误读测试 Skill 为"待实现功能" |
| `qa_reviewer` → 审查代码质量 | `result_validator` → 验证测试结果正确性 | QA 标准错位：代码覆盖率 vs 测试覆盖率 |
| `qa_fixer` → 修复代码缺陷 | `issue_retry` → 失败用例重试+策略调整 | 修复范围错位：改被测代码 vs 改测试策略 |
| `human_review` → 审批 PR 合并 | `test_approval` → 审批测试报告/放行 | 审批对象错位：代码 diff vs 测试报告 |

**Migration Plan 未做此映射**。如果直接按 Aperant 术语移植，会导致:
- `plan_engine.py` 的决策逻辑在测试场景下产生误判（例如: 把"测试失败"视为"代码需修改"）
- Agent prompt 使用代码生成领域语言，与测试执行任务不匹配

**建议** (修订 APERANT_MIGRATION_PLAN.md):
1. 在 Step 1 "机制 1: 多角色规划-执行-合并流水线" 增加语义映射表:
```markdown
### Aperant → aitest 语义映射

| Aperant Phase | Aperant Agent | aitest Phase | aitest Agent | 职责重新定义 |
|--------------|---------------|-------------|-------------|------------|
| planning | planner | test_planning | test_planner | 制定测试策略，选择测试 Skill，非生成实现计划 |
| coding | coder | test_execution | test_executor | 执行测试 Skill/用例，非编写应用代码 |
| qa_review | qa_reviewer | result_validation | result_validator | 验证测试结果，非代码审查 |
| qa_fixing | qa_fixer | issue_retry | issue_retry | 失败重试+策略调整，非修复被测代码 |
| human_review | N/A | test_approval | N/A | 审批测试报告/放行，非 PR 合并 |
```
2. 在 `pipeline_router.py` 和 `task_state_machine.py` 中使用 aitest 重新命名的 phase，避免术语污染
3. 在 `agent-definitions.yaml` 新条目中使用 `test_planner` / `test_executor` 等名称

---

## 🆕 缺失 7 (审阅增补): MCP Client 外部工具集成的协议约束未审计

**问题**: 现有 [aitest/mcp/](d:/Desktop/Alice/aitest/mcp/) 是成熟的 MCP **Server** 端实现（`protocol.py`、`tools/`、`browser_server.py`），向外部 AI 暴露工具。Migration Plan Task 6 引入 MCP **Client** 端能力（让 aitest agent 调用外部 MCP Server，如 Playwright MCP、数据库 MCP），这会引入新的能力边界。

**未审计的风险**:

| 维度 | 现有 MCP Server 规范 | Task 6 MCP Client 需要 | 缺口 |
|------|---------------------|----------------------|------|
| 协议约束 | `mcp/protocol.py` 定义 Server↔Client 消息格式 | Client 端须遵循相同协议规范 | 无 — 协议本身双向 |
| 安全审计 | `mcp/audit.py` 审计外部调用 | 外部工具调用是否纳入审计？ | **缺**: 外部 MCP 调用审计规则 |
| 错误分类 | `mcp/error_taxonomy.py` 错误分类 | 外部工具调用失败如何分类？ | **缺**: 远程 MCP 错误 vs 本地 tool 错误 |
| 频率限制 | `mcp/rate_limit.py` 限制外部请求频率 | 向外调用的频率限制？ | **缺**: outbound rate limiting |
| 术语定义 | shared-language.md 未定义 "MCP Client" | 需区分 MCP Server (对外暴露) vs MCP Client (调用外部) | **缺**: MCP 双向术语 |

**建议** (修订 shared-language.md + CONSTITUTION.md):
1. shared-language.md 新增术语:
```markdown
**MCP Server**:
aitest 向外部 AI 暴露的工具端点。实现 `mcp/protocol.py` 协议，注册在 `mcp/tools/`。
_避免_: "MCP 服务"、"工具服务"

**MCP Client**:
aitest Agent 调用外部 MCP Server 的客户端。通过 `mcp/mcp_client.py` 管理连接生命周期。
_避免_: "远程工具调用"、"外部工具"
```
2. CONSTITUTION.md 或 `mcp/` 下新增文件 `mcp/client_security.py` — 外部工具调用审计 + outbound rate limiting
3. APERANT_MIGRATION_PLAN.md Task 6 增加安全审计验收标准

---

# 四、修订建议汇总

## 对 APERANT_MIGRATION_PLAN.md 的修订 (7 项,原 5 + 新增 2)

| # | 位置 | 修订内容 | 优先级 |
|---|------|---------|--------|
| 1 | Step 4 每个 Task | 增加 `**审批要求**` 字段 (Architecture Review / Light Review / 免审批) | P0 |
| 2 | Task 2 + Risk 1 | `.tlo/{task_id}/PAUSE` → `governance/.data/{task_id}/pause.json` | P0 |
| 3 | Task 3b | WORKFLOW_RECIPE 改为 "扩展已有枚举"，新增仅 3 类型 (DEAD_END, TASK_CALIBRATION, DECISION) | P1 |
| 4 | Task 1 + Task 4 | 增加 `governance/agents/agent-definitions.yaml` 到涉及文件清单 | P1 |
| 5 | Step 2 每个 P0/P1 条目 | 增加 `**Extension Point 评估**` 字段 | P2 |
| 6 | Step 1 机制 1 | 增加 "Aperant → aitest 语义映射表" (code-gen → test-execution)，重命名 phase/agent | P0 |
| 7 | Task 6 + shared-language.md | MCP Client 安全审计规范: outbound rate limiting + 术语定义 + audit 覆盖 | P1 |

## 对 CONSTITUTION.md 的修订 (3 项,独立于 Migration Plan)

| # | 位置 | 修订内容 | 优先级 |
|---|------|---------|--------|
| 6 | §5 技术栈基线 | "Vue 3 + Pinia" → "React 18 + Zustand"; "Radix Vue" → "Radix UI + Lucide React" | P0 (已有治理漂移) |
| 7 | §1.2 Frozen 清单 | 明确 SOP Phase 枚举变更规则: "可增不可删/改" | P1 |
| 8 | 新增 §3.1 | 平台执行状态目录: `governance/.data/{task_id}/` — 平台运行时状态，不跟随项目 git | P0 |

## 对 source-of-truth.md 的修订 (1 项)

| # | 位置 | 修订内容 | 优先级 |
|---|------|---------|--------|
| 9 | 事实源分工表 | 新增行: "平台执行状态 (pause/resume/session)" → `governance/.data/` | P0 |

---

# 五、执行前置检查清单

在启动 Migration Plan Task 1 编码前，须完成:

- [ ] CONSTITUTION.md §5 技术栈修正为 React 18 + Zustand (冲突 4)
- [ ] APERANT_MIGRATION_PLAN.md 增加审批要求标注 (冲突 1)
- [ ] APERANT_MIGRATION_PLAN.md sentinel 路径修正 (冲突 2)
- [ ] APERANT_MIGRATION_PLAN.md 增加语义映射表 (缺失 6)
- [ ] APERANT_MIGRATION_PLAN.md 增加 MCP Client 安全审计验收标准 (缺失 7)
- [ ] source-of-truth.md 新增平台执行状态条目 (缺失 1)
- [ ] shared-language.md 新增 "MCP Server" / "MCP Client" 术语定义 (缺失 7)
- [ ] `governance/.data/` 目录创建 + README 说明 (缺失 1)
- [ ] agent-definitions.yaml 规划新 agent type 条目 (缺失 2)
- [ ] CONSTITUTION.md 新增 `.data/` 执行状态目录定义 (缺失 1)

**未完成上述检查即开始编码的风险**: CLAUDE.md 加载 CONSTITUTION → Agent 读取 Migration Plan → 规则冲突 → Agent 执行时产生不可预期行为 (跳过审批、写错路径、用错技术栈)。
