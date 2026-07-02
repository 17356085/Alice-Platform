# Migration Map — 代码热力图 + 文件搬迁表

> 架构解耦分析 — 文档 7/7
> 核心问题: **从当前代码到目标四层架构，每一行属于哪里？**
> 前置文档: 05-REFINED_ARCHITECTURE.md (四层目标态)

## 1. 总览

```
当前 (7311 行, 18 文件)
        ↓ Phase 0: 热力图标注
        ↓ Phase 1: 物理搬迁 (只搬文件，不改逻辑)
        ↓ Phase 2: 局部接口提取 (LLM/Event)
        ↓ Phase 3: Workflow 抽象 (暂缓)
目标 (四层: Core 4 文件 / Runtime 7 文件 / Workflow 6 文件 / Adapter 8 文件)
```

## 2. agent_runner.py 代码热力图 (1370 行)

这是最关键的拆解对象。逐函数标注归属层。

### 2.1 类: AgentLoop (L70-1337)

| 行范围 | 函数/属性 | 归属层 | 理由 |
|--------|----------|--------|------|
| L70-93 | 类定义 + docstring | — | 会被拆散 |
| L94-224 | `__init__()` | **混合** | 见下方拆分 |
| L94-141 | `__init__` 基础属性 (agent_name, provider, context, skills, verbose, state) | **Core** (Task) | 任务定义和基础配置 |
| L142-151 | `__init__` abort signal, MCP clients, worktree | **Core** (Task) | 执行上下文生命周期 |
| L152-159 | `__init__` ReliableProvider, ContextWindowMonitor, SessionCompactor | **Runtime** (Retry) | 可靠性层初始化 |
| L160-163 | `__init__` capability_router, tool_calling flag | **Adapter** (LLM) | LLM 能力路由 |
| L165-178 | `__init__` model_tier, config.resolve_model_for_tier | **Runtime** (Config) | 模型配置解析 |
| L179-193 | `__init__` ReliableProvider 初始化 + ContextWindowMonitor 初始化 | **Runtime** (Retry) | 可靠性层 |
| L194-223 | `__init__` goal 构建 + TraceContext + AgentState 创建 | **Core** (Task) | 任务上下文构建 |
| L225-227 | `send_interaction()` | **Core** (Executor) | HITL 交互 |
| L231-245 | `skills`, `module`, `page` 属性 | **Core** (Task) | 任务属性 |
| L248-257 | `_resolve_model_for_provider()` | **Runtime** (Config) | 模型名解析 |
| L259-281 | `_get_capability_router()` | **Adapter** (LLM) | Capability Router 初始化 |
| L283-293 | `_emit_obs()` | **Adapter** (Event) | 事件发射 |
| L295-337 | `_log()`, `_slug_to_page_name()`, `_page_slug_to_underscore()`, `_resolve_artifact_path()`, `_resolve_path()` | **Runtime** (Paths) | 路径解析工具 |
| L339-426 | `_build_context_vars()` | **混合** | 见下方拆分 |
| L339-401 | `_build_context_vars` 基础部分 (module, page, memory, paths) | **Core** (Planner) | 上下文变量构建 |
| L402-426 | `_build_context_vars` ContextBuilder 部分 | **Adapter** (Knowledge) | 上下文发现 |
| L428-491 | `_build_user_input()` | **Core** (Planner) | Skill 用户输入构建 |
| L493-529 | `perceive()` | **Core** (Planner) | 环境感知 |
| L531-539 | `plan()` | **Core** (Planner) | 规划委托 |
| L541-615 | `act()` | **混合** | 见下方拆分 |
| L541-558 | `act` 特殊 Skill 分支 (code-consistency-checker) | **Core** (Executor) | 执行分派 |
| L559-597 | `act` 核心执行 (build_context → run_skill) | **Core** (Executor) | 核心执行 |
| L598-614 | `act` 窗口更新 + 消息历史 + 产出保存 | **Runtime** (ContextWindow) + **Core** (Executor) | 窗口管理 + 产出 |
| L617-619 | `_save_skill_output()` | **Core** (Executor) | 产出持久化 |
| L622-646 | `_act_mechanical_consistency_check()`, `_act_llm_consistency_review()` | **Core** (Executor) | 特殊 Skill 执行 |
| L648-739 | `_persist_skill_artifact()` | **Core** (Executor) | 产物持久化 |
| L741-880 | `observe()` | **混合** | 见下方拆分 |
| L741-758 | `observe` 基础 (Observation 构建) | **Core** (StateMachine) | 观察结果构建 |
| L759-772 | `observe` 安全检查 | **Runtime** (Security) | 安全审计 |
| L773-814 | `observe` 机械化 Skill 处理 | **Core** (StateMachine) | 状态判定 |
| L815-879 | `observe` 产出文件检查 | **Core** (StateMachine) | 产出验证 |
| L882-888 | `update()` | **Core** (StateMachine) | 状态更新委托 |
| L890-902 | `_emit_cache_summary()` | **Adapter** (Event) | 缓存统计事件 |
| L904-936 | `_do_continuation()` | **Runtime** (ContextWindow) | 上下文续传 |
| L938-994 | `run()` | **Core** (Executor) | 主循环 (含 continuation 包装) |
| L996-1107 | `_finalize_session()` | **混合** | 见下方拆分 |
| L996-1016 | `_finalize_session` 日志 + 缓存摘要 | **Core** (Executor) | 会话收尾 |
| L1017-1028 | `_finalize_session` OnlineMonitor | **Runtime** (Metrics) | 指标收集 |
| L1029-1060 | `_finalize_session` Worktree + MCP 清理 | **Core** (Executor) | 资源清理 |
| L1061-1107 | `_finalize_session` ArtifactLineage + OperationalMetrics | **Runtime** (Metrics) | 平台指标 |
| L1109-1329 | `_run_single_session()` | **Core** (Executor) | 单次会话主循环 |
| L1331-1337 | `run_interactive()` | **Core** (Executor) | 交互式主循环委托 |

### 2.2 模块级函数 (L1340-1371)

| 行范围 | 函数 | 归属层 | 理由 |
|--------|------|--------|------|
| L1344-1360 | `run_agent()` | **Core** (Executor) | 兼容旧接口 |
| L1363-1366 | `list_agents()` | **Core** (Planner) | Agent 列表 |
| L1368-1371 | `list_dev_agents()` | **Core** (Planner) | 开发 Agent 列表 |

### 2.3 拆分统计

| 归属层 | 行数 | 占比 |
|--------|------|------|
| **Core** (Task/Planner/Executor/StateMachine) | ~920 | 67% |
| **Runtime** (Retry/ContextWindow/Security/Config/Metrics) | ~280 | 20% |
| **Adapter** (LLM/Event/Knowledge) | ~120 | 9% |
| **混合** (需要进一步拆分的边界代码) | ~50 | 4% |

## 3. 全量文件搬迁表

### 3.1 Layer 0: Core → `engine/`

| 源文件 | 行数 | 目标文件 | 搬迁内容 |
|--------|------|----------|----------|
| `agents/agent_runner.py` | 1370 | `engine/executor.py` | AgentLoop 核心: `run()`, `_run_single_session()`, `act()`, `perceive()`, `observe()`, `update()` |
| `agents/agent_runner.py` | — | `engine/task.py` | AgentLoop 基础属性: `__init__` 的 Task 部分, `skills`, `module`, `page`, `AgentState` |
| `agents/agent_runner.py` | — | `engine/planner.py` | `plan()`, `perceive()`, `_build_user_input()`, `list_agents()` |
| `agents/agent_runner.py` | — | `engine/state_machine.py` | `observe()` 的状态判定部分, `update()` |
| `agents/runner_state.py` | 215 | `engine/task.py` | `AgentState`, `Observation`, `AgentEvent`, `ArtifactRule` |
| `agents/task_state_machine.py` | 131 | `engine/state_machine.py` | `TaskState`, `TaskStateContext`, `VALID_TRANSITIONS` |
| `agents/plan_engine.py` | 302 | `engine/planner.py` | `plan_next_action()`, `_llm_decide()`, `check_skill_risk_level()`, HITL 确认逻辑 |
| `agents/state_updater.py` | 87 | `engine/state_machine.py` | `update_agent_state()`, `_emit_milestone()` |
| `agents/skill_executor.py` | 281 | `engine/executor.py` | `run_skill()`, `AGENT_SKILL_MAP`, `get_agent_definition()` |
| `llm/skill_loader.py` | 451 | `engine/planner.py` | `load_skill()`, Skill YAML 解析 |
| `graphs/state.py` | 550 | `engine/task.py` + `workflow/langgraph/state.py` | `SOPState` → workflow; `AgentResult`, `CANONICAL_PHASES` → core |

### 3.2 Layer 1: Runtime → `runtime/`

| 源文件 | 行数 | 目标文件 | 搬迁内容 |
|--------|------|----------|----------|
| `llm/reliable_provider.py` | 391 | `runtime/retry.py` | `ReliableProvider`, `get_reliable_provider()`, Retry/Fallback 逻辑 |
| `llm/context_window.py` | 316 | `runtime/context_window.py` | `ContextWindowMonitor`, `SessionCompactor`, `build_continuation_prompt()`, `ContextWindowExceededError` |
| `graphs/checkpoint.py` | 258 | `runtime/checkpoint.py` | `get_checkpointer()`, SQLite 持久化 |
| `infra/secure_subprocess.py` | 93 | `runtime/security.py` | `SecureSubprocess`, 安全 subprocess wrapper |
| `infra/security/command_validator.py` | ~100 | `runtime/security.py` | `CommandValidator`, 命令白名单 |
| `infra/error_logger.py` | ~100 | `runtime/error_handling.py` | 错误记录 + 分类 |
| `platform/paths.py` | ~170 | `runtime/paths.py` | `get_workstudy()`, `get_test_project_root()`, `get_context_modules()` |
| `platform/context.py` | ~300 | `runtime/context.py` | `ProjectContext`, 活跃项目管理 |
| `config.py` | ~200 | `runtime/config.py` | `.env` + YAML 配置 |
| `llm/governance_gate.py` | ~100 | `runtime/governance.py` | 生成前合规检查 |
| `llm/governance_connector.py` | ~100 | `runtime/governance.py` | Agent ↔ Governance 桥接 |

### 3.3 Layer 2: Workflow → `workflow/`

| 源文件 | 行数 | 目标文件 | 搬迁内容 |
|--------|------|----------|----------|
| `graphs/sop_graph.py` | 1509 | `workflow/langgraph/sop_graph.py` | `build_sop_graph()`, 全部节点函数, 路由逻辑, PreflightCache |
| `graphs/sop_runner.py` | 434 | `workflow/langgraph/runner.py` | `SOPRunner`, `run_interactive()`, AgentEvent 流包装 |
| `graphs/state.py` (LangGraph 部分) | — | `workflow/langgraph/state.py` | `SOPState`, `SOPMode`, `PhaseName`, `AgentName`, `GateResult` |
| `graphs/nodes.py` | 359 | `workflow/langgraph/nodes.py` | `make_agent_loop_node()`, `make_gate_node()`, `make_skill_node()` |
| `graphs/execution_graph.py` | 335 | `workflow/langgraph/execution.py` | execution/report/knowledge 子图 |
| `graphs/bug_analysis_graph.py` | ~300 | `workflow/langgraph/bug_analysis.py` | Bug 分析子图 |

### 3.4 Layer 3: Adapter → `adapters/`

| 源文件 | 行数 | 目标文件 | 搬迁内容 |
|--------|------|----------|----------|
| `llm/provider.py` | 79 | `adapters/llm/interface.py` | `LLMResponse`, `StreamEvent`, `get_provider()` 接口 |
| `llm/prompt_adapter.py` | 150 | `adapters/llm/prompt.py` | `PromptAdapter`, Provider 格式化 |
| `llm/context_injector.py` | ~200 | `adapters/llm/context.py` | `ContextInjector`, 上下文注入 |
| `audit_engine/event_bus.py` | ~100 | `adapters/event/interface.py` | `emit()` 函数, EventBus 接口 |
| `audit_engine/state_auditor.py` | ~200 | `adapters/audit/state.py` | `StateAuditor` |
| `audit_engine/sop_auditor.py` | ~200 | `adapters/audit/sop.py` | `SOPAuditor` |
| `discovery/browser_use.py` | ~200 | `adapters/browser/playwright.py` | Browser-Use 适配 |
| `knowledge/rag_engine.py` | ~200 | `adapters/knowledge/chromadb.py` | RAG 引擎 |
| `platform/testing_memory.py` | ~200 | `adapters/memory/chromadb.py` | ChromaDB 向量记忆 |

### 3.5 保持原位 (不搬迁)

| 文件 | 理由 |
|------|------|
| `agents/output_persistence.py` | 工具模块，跟着 executor 走，搬到 `engine/output.py` |
| `agents/consistency_checks.py` | 工具模块，跟着 executor 走，搬到 `engine/consistency.py` |
| `agents/interactive_runner.py` | 交互式运行器，搬到 `engine/interactive.py` |
| `agents/context_agent.py` | 上下文优化，搬到 `engine/context_agent.py` |
| `platform/capability_router/` | Extension，不搬 |
| `platform/complexity/` | Extension，不搬 |
| `platform/testing_memory.py` | Extension，不搬 |
| `audit_engine/` (审计部分) | Extension，不搬 |
| `knowledge/` | Extension，不搬 |
| `server/`, `web/`, `chat/` | Platform，不搬 |

## 4. 依赖矩阵 (搬迁后)

### 4.1 允许的依赖方向

```
Core (Layer 0)  ──依赖──→  Workflow (Layer 2)
Core (Layer 0)  ──依赖──→  LLM Adapter (Layer 3, 接口)
Core (Layer 0)  ──依赖──→  Event Adapter (Layer 3, 接口)

Runtime (Layer 1)  ──包装──→  Core (Layer 0) 的 Executor/Planner

Workflow (Layer 2)  ──调用──→  Core (Layer 0) 的 Executor (通过节点工厂)

Adapter (Layer 3)  ──不依赖──→  Core/Runtime/Workflow (独立实现)
```

### 4.2 禁止的依赖

```
Core      ──✗──→  Runtime    (Core 不知道 Runtime 的存在)
Core      ──✗──→  Platform   (Core 不依赖平台)
Workflow  ──✗──→  Runtime    (Workflow 不直接包装)
Adapter   ──✗──→  Core       (Adapter 是独立实现)
```

### 4.3 当前违规 → 搬迁后修正

| 当前违规 | 位置 | 修正方式 |
|----------|------|----------|
| `agent_runner.py` 直接 import `ReliableProvider` | L31 | 搬迁后，Runtime 包装 Core 的 Executor |
| `agent_runner.py` 直接 import `ContextWindowMonitor` | L32-35 | 同上 |
| `agent_runner.py` 直接 import `PromptInjectionGuard` | L57 | 搬迁后，Runtime 的 Security 层 |
| `agent_runner.py` 直接 import `ObservationBus` | L58 | 搬迁后，通过 Event Adapter 接口 |
| `agent_runner.py` 直接 import `paths.py` | L61 | 搬迁后，Runtime 的 Paths 模块 |
| `sop_graph.py` 直接 import `audit_engine.event_bus.emit` | L59 | 搬迁后，通过 Event Adapter 接口 |
| `nodes.py` 直接 import `AgentLoop` | L44 | 搬迁后，Workflow 通过接口调用 Core |

## 5. Phase 0: 迁移执行计划

### Phase 0.1: 代码热力图标注 (1 天)

```bash
# 在每个函数上方添加归属注释
# [LAYER:Core/Task] [LAYER:Core/Planner] [LAYER:Runtime/Retry] ...
```

**产出**: 每个函数有明确的归属标注，代码内注释。

### Phase 0.2: 文件搬迁表 Review (0.5 天)

- 和团队 Review 这份搬迁表
- 确认每个文件的 source → target 映射
- 标记有争议的边界代码

**产出**: 签字确认的搬迁表。

### Phase 0.3: 创建目标目录结构 (0.5 天)

```bash
mkdir -p aitest/engine
mkdir -p aitest/runtime
mkdir -p aitest/workflow/langgraph
mkdir -p aitest/workflow/interface  # 预留，暂不实现
mkdir -p aitest/adapters/llm
mkdir -p aitest/adapters/event
mkdir -p aitest/adapters/audit
mkdir -p aitest/adapters/browser
mkdir -p aitest/adapters/knowledge
mkdir -p aitest/adapters/memory
```

每个目录放 `__init__.py`，暂时 re-export 原模块，保证零破坏。

### Phase 0.4: 依赖检查脚本 (0.5 天)

```python
# tools/check_layer_deps.py
# 扫描 import 语句，验证依赖方向合法性
# CI 中运行，防止违规依赖引入
```

**产出**: CI 可运行的依赖检查脚本。

### Phase 0 总计: 2.5 天

## 6. Phase 1: 物理搬迁 (只搬文件，不改逻辑)

### Phase 1.1: Runtime 层 (2 天)

按搬迁表把文件从原位置搬到 `runtime/`，原位置留 re-export：

```python
# aitest/llm/reliable_provider.py (搬迁后)
from aitest.runtime.retry import *  # re-export，零破坏
```

**搬迁顺序** (先搬被依赖少的):
1. `runtime/config.py` ← `config.py`
2. `runtime/paths.py` ← `platform/paths.py`
3. `runtime/context.py` ← `platform/context.py`
4. `runtime/security.py` ← `infra/secure_subprocess.py` + `infra/security/command_validator.py`
5. `runtime/error_handling.py` ← `infra/error_logger.py`
6. `runtime/retry.py` ← `llm/reliable_provider.py`
7. `runtime/context_window.py` ← `llm/context_window.py`
8. `runtime/checkpoint.py` ← `graphs/checkpoint.py`
9. `runtime/governance.py` ← `llm/governance_gate.py` + `llm/governance_connector.py`

每搬一个文件，跑一次 `pytest` 确认无回归。

### Phase 1.2: Adapter 层 (2 天)

**搬迁顺序**:
1. `adapters/llm/interface.py` ← `llm/provider.py` (仅接口定义)
2. `adapters/llm/prompt.py` ← `llm/prompt_adapter.py`
3. `adapters/llm/context.py` ← `llm/context_injector.py`
4. `adapters/event/interface.py` ← `audit_engine/event_bus.py`
5. `adapters/audit/state.py` ← `audit_engine/state_auditor.py`
6. `adapters/audit/sop.py` ← `audit_engine/sop_auditor.py`

Browser/Knowledge/Memory 是 Extension，暂不搬迁。

### Phase 1.3: Workflow 层 (2 天)

**搬迁顺序**:
1. `workflow/langgraph/state.py` ← `graphs/state.py` (LangGraph 部分)
2. `workflow/langgraph/nodes.py` ← `graphs/nodes.py`
3. `workflow/langgraph/sop_graph.py` ← `graphs/sop_graph.py`
4. `workflow/langgraph/runner.py` ← `graphs/sop_runner.py`
5. `workflow/langgraph/execution.py` ← `graphs/execution_graph.py`
6. `workflow/langgraph/bug_analysis.py` ← `graphs/bug_analysis_graph.py`

### Phase 1.4: Core 层 (3 天)

最复杂，因为需要拆分 `agent_runner.py`:

**拆分策略**: 不是一次性拆，而是先搬后拆。

1. 先把 `agent_runner.py` 整体搬到 `engine/executor.py`
2. 把 `runner_state.py` 搬到 `engine/task.py`
3. 把 `task_state_machine.py` 搬到 `engine/state_machine.py`
4. 把 `plan_engine.py` 搬到 `engine/planner.py`
5. 把 `state_updater.py` 搬到 `engine/state_machine.py` (合并)
6. 把 `skill_executor.py` 搬到 `engine/executor.py` (合并)
7. 从 `engine/executor.py` 中逐步提取:
   - Task 相关代码 → `engine/task.py`
   - Planner 相关代码 → `engine/planner.py`
   - StateMachine 相关代码 → `engine/state_machine.py`

**拆分顺序** (先提独立模块，再拆大文件):
```
Step 1: 提取 _build_context_vars() 的 ContextBuilder 部分 → 引用 Adapter
Step 2: 提取 _get_capability_router() → 引用 Adapter
Step 3: 提取 _emit_obs() → 引用 Event Adapter
Step 4: 提取 _do_continuation() → 引用 Runtime
Step 5: 提取 _finalize_session() 的 Metrics 部分 → 引用 Runtime
Step 6: 拆分 __init__() 的 Runtime 部分 → Runtime 包装
```

### Phase 1 总计: 9 天

## 7. Phase 2: 局部接口提取

### Phase 2.1: LLM Adapter 接口 (1 天)

```python
# aitest/adapters/llm/interface.py
from typing import Protocol

class LLMAdapter(Protocol):
    def chat(self, messages: list, model: str = None, **kwargs) -> dict: ...
    def chat_stream(self, messages: list, model: str = None, **kwargs): ...

class LLMResponse:
    content: str
    model: str
    finish_reason: str
    token_usage: dict
```

**验证**: Core 代码只 import `adapters.llm.interface`，不 import 具体 Provider。

### Phase 2.2: Event Adapter 接口 (1 天)

```python
# aitest/adapters/event/interface.py
from typing import Protocol

class EventBus(Protocol):
    def emit(self, event_type: str, **kwargs) -> None: ...

class NoopEventBus:
    def emit(self, event_type: str, **kwargs) -> None:
        pass

class PlatformEventBus:
    def emit(self, event_type: str, **kwargs) -> None:
        # → ObservationBus → Hooks → Metrics → Webhooks
        ...
```

**验证**: Core 代码通过 `EventBus` 接口发射事件，不知道具体实现。

### Phase 2.3: Runtime 装饰器模式 (2 天)

```python
# aitest/runtime/__init__.class Runtime:
    def wrap_executor(self, executor: Executor) -> Executor:
        """包装 Executor，加入 Retry/Checkpoint/Security 等增强。"""
        reliable = ReliableProvider(...)
        window = ContextWindowMonitor(...)

        class EnhancedExecutor:
            def execute(self, skill_id, context):
                # 1. 窗口检查
                window.check()
                # 2. 执行 (带 Retry)
                result = reliable.complete(...)
                # 3. 窗口更新
                window.add_usage(...)
                return result

        return EnhancedExecutor()
```

### Phase 2 总计: 4 天

## 8. Phase 3: Workflow 抽象 (暂缓)

**条件**: 当有第二个 Workflow 引擎需求时才做。

**如果做**:
```python
# aitest/workflow/interface.py
from typing import Protocol

class WorkflowEngine(Protocol):
    def build(self, definition: dict) -> object: ...
    def execute(self, workflow: object, initial_state: dict) -> dict: ...
```

**当前不做**。只做物理隔离 (`workflow/langgraph/` 目录)。

## 9. 验收标准

### Phase 0 验收
- [ ] 所有函数有 `[LAYER:...]` 归属注释
- [ ] 文件搬迁表签字确认
- [ ] 目录结构创建完成
- [ ] 依赖检查脚本 CI 通过

### Phase 1 验收
- [ ] 所有文件搬到目标目录
- [ ] 原位置 re-export 正常
- [ ] 全量 pytest 通过 (零回归)
- [ ] `python demo.py --module equipment --mock-llm` 正常运行

### Phase 2 验收
- [ ] Core 代码不直接 import Runtime 模块
- [ ] Core 代码不直接 import 具体 Adapter 实现
- [ ] LLM Adapter 接口提取完成
- [ ] Event Adapter 接口提取完成
- [ ] Runtime 装饰器模式验证通过

## 10. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 搬迁后 import 断裂 | 高 | 高 | 原位置留 re-export，逐文件验证 |
| 拆分 agent_runner.py 引入 bug | 中 | 高 | 先搬后拆，每步跑 pytest |
| 循环依赖 | 中 | 中 | 依赖检查脚本 CI 把关 |
| 团队对搬迁表有分歧 | 低 | 中 | Phase 0.2 专门做 Review |

## 11. 时间线

```
Week 1:  Phase 0 (2.5天) — 热力图 + 搬迁表 + 目录 + 依赖检查
Week 2:  Phase 1.1-1.2 (4天) — Runtime + Adapter 物理搬迁
Week 3:  Phase 1.3-1.4 (5天) — Workflow + Core 物理搬迁
Week 4:  Phase 2 (4天) — LLM/Event 接口提取 + Runtime 装饰器
```

**总计: 15.5 天 (~3 周)**

## 12. 与 05-REFINED_ARCHITECTURE.md 的关系

05 定义了**目标态** (四层架构)。
本文档定义了**迁移路径** (从当前代码到目标态)。

```
05: "Core 只有 4 个文件: task.py, planner.py, executor.py, state_machine.py"
07: "agent_runner.py 的 L94-141 属于 task.py, L493-529 属于 planner.py, ..."
```

没有 07，05 是空中楼阁。
有了 07，05 才是可执行的工程计划。
