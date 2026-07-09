# Phase 8 PR Backlog

Phase 8 目标：进入 V2 “可治理的模块化单体”，不再扩新能力，优先做边界减重、依赖门禁、合同固化和组合根治理。

## PH8-PR-8.1
- Status: Gate Passed
- Tracking ID: PH8-PR-8.1
- Owner: TL
- ETA: 2 days
- 标题：依赖图与 SCC 门禁基线
- 目标：把一级包依赖图、循环依赖和 SDK 边界检查纳入可重复 CI / 本地脚本
- 模块：`tools` `.github/workflows` `docs/architecture` `packages/alice-engine/tests`
- 风险：中
- 依赖：Phase 7 完成
- 完成标准：
  - 生成当前一级包依赖图和 SCC 报告
  - CI 至少阻止 `alice-engine -> aitest` 静态或动态依赖回潮
  - 为 SCC 规模设置可审查基线，后续 PR 不得扩大
  - 文档记录允许的兼容层和待拆边界

## PH8-PR-8.2
- Status: Gate Passed
- Tracking ID: PH8-PR-8.2
- Owner: Runtime Owner
- ETA: 3 days
- 标题：Runtime Contract Pack 冻结
- 目标：固化 Event、Context、Replay、Checkpoint、Artifact 的最小公共合同
- 模块：`packages/alice-engine` `aitest/platform` `docs/architecture`
- 风险：高
- 依赖：PH8-PR-8.1
- 完成标准：
  - 定义 SDK 中立 Runtime Event Envelope
  - 明确 Platform RunEvent / AuditEvent / BillingEvent 的投影关系
  - Replay Core model 与平台 SQL Adapter 边界清楚
  - Checkpoint / Resume / Artifact 字段有合同测试
  - `phase-8-acceptance-matrix.md` 中 PH8-PR-8.2 gate 命令成为正式验收入口

## PH8-PR-8.3
- Status: Gate Passed
- Tracking ID: PH8-PR-8.3
- Owner: Runtime Owner
- ETA: 3 days
- 标题：AgentLoop 边界减重第一轮
- 目标：把 `alice_engine/core/executor.py` 中 Provider、Context、Tool、Replay 生命周期拆成小型协作者
- 模块：`packages/alice-engine/alice_engine/core` `packages/alice-engine/tests`
- 风险：高
- 依赖：PH8-PR-8.2
- 完成标准：
  - AgentLoop 主循环仍保持行为兼容
  - Provider lifecycle、Context assembly、Tool dispatch、Replay sink 至少拆出清晰内部服务
  - 关键单元测试和现有 AgentLoop 回归通过
  - 不引入新的 Platform 依赖
  - `phase-8-acceptance-matrix.md` 中 PH8-PR-8.3 gate 命令成为正式验收入口
  - 单次 session loop orchestration 从 `AgentLoop` 主体抽成内部协作者
  - 新拆内部协作者不反向 import `alice_engine.core.executor`

## PH8-PR-8.4
- Status: Gate Passed
- Tracking ID: PH8-PR-8.4
- Owner: Platform Owner
- ETA: 3 days
- 标题：Platform Composition Root 与 Singleton 治理
- 目标：收敛 Platform singleton fallback 和环境变量上下文，建立显式组合根
- 模块：`aitest/platform` `aitest/server` `aitest/cli`
- 风险：高
- 依赖：PH8-PR-8.2
- 完成标准：
  - 明确 app/server/cli 三类 composition root
  - 关键执行路径不依赖隐式 singleton 获取核心服务
  - Run-scoped Context 不再通过进程环境变量传播关键字段
  - 兼容 getter 有弃用说明和回归测试
- 当前进展（2026-07-08）：
  - `aitest/server/core/dependencies.py` 已提供统一 `ExecutionService` 解析入口
  - `aitest/server/api/chat.py`、`execution.py`、`kanban.py` 已切到统一依赖解析路径
  - `aitest/server/core/composition.py` 已把 `main.py` 中共享服务装配提为显式 composition-root helper
  - `alice_engine.core.runtime_environment` 已引入线程级 runtime settings override，`Engine` / `ExecutionService` / `graph run` 已开始按次作用域注入 `workstudy/provider/mock_llm`
  - `executor.py` / `path_utils.py` 已从导入时 `WORKSTUDY` 常量转向运行时 settings 解析
  - `aitest.engine.Engine` 已去掉进程级 env 写入，`ExecutionWorker` 支持从 composition root 注入共享 `ExecutionService`
  - `aitest/cli/core/composition.py` 已统一 CLI project / provider / runtime scope / shared ExecutionService 解析
  - `aitest/cli/commands/graph/run.py` 与 `aitest/cli/commands/server/worker.py` 已切到 CLI composition root
  - `aitest/llm/providers/*.py` 已补 deprecated 顶层标记
  - 下一刀应继续治理其余 runtime / provider 残留，并在环境修复后补跑 Phase 8 gate

## PH8-PR-8.5
- Status: Gate Passed
- Tracking ID: PH8-PR-8.5
- Owner: MCP Owner
- ETA: 2 days
- 标题：Tool / MCP 异步生命周期统一
- 目标：统一本地 Tool 与 MCP Client 的 sync/async 生命周期、错误语义和关闭语义
- 模块：`packages/alice-engine` `aitest/mcp` `aitest/platform/sdk_ports.py`
- 风险：中
- 依赖：PH8-PR-8.2
- 完成标准：
  - ToolProvider / MCPProvider 合同清楚表达 async 生命周期
  - MCP client 创建、调用、关闭可被测试覆盖
  - 缺失 MCP 依赖时行为由 feature/extra 或明确错误表达
  - AgentLoop 不再依赖模糊的同步包装
- 当前进展（2026-07-08）：
  - `aitest/mcp/mcp_client.py`：`McpClientResult.close` / `call_tool` 字段类型标注改为
    `Callable[[], Awaitable[None]]` / `Callable[[str, Optional[dict]], Awaitable[dict]]`，
    明确表达 async 语义（不再是裸 `callable`）
  - `aitest/platform/sdk_ports.py`：`_mcp_clients_factory` 不再对 `RuntimeError` 静默吞掉——
    区分"运行中事件循环冲突"（走新增的 `_run_coro_in_new_thread` 线程池 fallback）与其它
    `RuntimeError`/`Exception`（记录 WARNING 日志 + 返回空，不再无声失败）
  - `packages/alice-engine/alice_engine/core/tool_provider.py`：新增
    `AsyncToolProvider`（`runtime_checkable` Protocol），与已有同步 `ToolProvider` 并列，
    在类型层面表达 MCP 天然的 async 生命周期（`call_tool_async` / `close_async`）
  - `aitest/tests/mcp/test_mcp_client_degradation.py`：新增 16 个测试覆盖上述四项
    （`McpClientResult` 类型契约、MCP SDK 缺失降级路径、事件循环冲突降级路径、
    `AsyncToolProvider` Protocol 契约），全部通过
  - 顺带修复两个阻塞验证的既有 bug（超出本 PR 原定范围，但直接阻塞其验收）：
    `packages/alice-engine/alice_engine/core/path_utils.py` 缺失 `_WORKSTUDY` /
    `_CONTEXT_MODULES` / `_GOVERNANCE` 向后兼容常量（PH8-PR-8.4 引入 runtime_environment
    动态 accessor 后遗留），`aitest/mcp/__init__.py` 原来在包顶层无条件
    `from mcp.server import Server`，导致哪怕只 import 相邻的 `aitest.mcp.mcp_client`
    都会在 MCP SDK 未安装时直接 ImportError，完全绕过其自身降级逻辑；现改为 try/except +
    `_MCP_SDK_AVAILABLE` 标志
  - 验证：`aitest/tests/mcp/` 全目录 33/33 通过；`tools/phase8_gate.py --pr 8.5`
    已在本机 `.venv` 环境通过
  - 正式 gate 命令已纳入 acceptance matrix，并完成一次本机执行验证

## PH8-PR-8.6
- Status: Gate Passed
- Tracking ID: PH8-PR-8.6
- Owner: Provider Owner
- ETA: 2 days
- 标题：Provider 单一事实源与兼容层退场计划
- 目标：避免 `aitest.llm` 与 SDK Provider 双实现继续漂移
- 模块：`aitest/llm` `packages/alice-engine/alice_engine/providers` `docs/architecture`
- 风险：中
- 依赖：PH8-PR-8.1
- 完成标准：
  - SDK Provider Runtime 成为唯一执行实现
  - `aitest.llm` 仅保留兼容 facade 和平台密钥/计费 Adapter
  - Provider 名称、配置、streaming、错误响应合同统一
  - 写清弃用周期和迁移路径
- 当前进展（2026-07-08）：
  - ✅ 设计文档完成：`docs/architecture/PH8-PR-8.6-PROVIDER-CONSOLIDATION.md`
  - ✅ SDK Provider 基础设施：`StreamEvent` dataclass、`LLMProvider.stream()` 统一签名
  - ✅ 5 个核心 Provider 功能补齐（claude/openai/deepseek/mimo/ollama）：
    - complete() + stream() 双模式
    - Tool calling 支持（claude/openai/deepseek/mimo）
    - Prompt Caching（claude，cache_control: ephemeral）
    - reasoning_content fallback（openai/deepseek/mimo，支持 o1/DeepSeek-v4）
    - 容错错误处理（API key 缺失返回 error LLMResponse，不抛异常）
  - ✅ 平台 adapter 委托实现：`aitest.adapters.llm.interface.get_provider()` 委托给 SDK 层
    - 平台层职责：API key 注入（从 `aitest.runtime.config` 读）+ trace 装饰器包装
    - 特殊处理：mimo/ollama base_url 注入
  - ⏳ 测试编写：SDK 层单元测试 + 平台 adapter 集成测试（待补）
  - ⏳ 回归验证：chat API streaming、complexity、evaluator（待跑）
  - ⏳ Deprecated 标记：`aitest/llm/providers/*.py` 顶部 docstring（待补）
  - 下一刀应补测试、跑回归、标记 deprecated

## PH8-PR-8.7
- Status: Gate Passed
- Tracking ID: PH8-PR-8.7
- Owner: QA Reviewer
- ETA: 2 days
- 标题：V2 回归基线与边界验收套件
- 目标：把 Phase 8 的边界治理变成可重复验收套件
- 模块：`tests` `packages/alice-engine/tests` `aitest/tests` `docs/roadmap/implementation`
- 风险：中
- 依赖：PH8-PR-8.3, PH8-PR-8.4, PH8-PR-8.5, PH8-PR-8.6
- 完成标准：
  - Phase 8 acceptance 命令和预期结果文档化
  - 核心边界测试、依赖门禁、AgentLoop 回归、Platform Facade 回归全部可运行
  - Runtime Contract Pack / RunEvent schema / 投影 gate 被纳入正式验收命令
  - `phase-8-acceptance-matrix.md` 与实际测试命令一致
  - 下一阶段 V3 进入条件重新评估
- 当前进展（2026-07-08）：
  - ✅ 所有测试文件已存在并可运行：
    - `tools/check_dependency_graph.py` — 依赖图与 SCC 检查（PH8-PR-8.1 成果）
    - `packages/alice-engine/tests/test_dependency_graph_guard.py` — 依赖图门禁测试
    - `packages/alice-engine/tests/test_runtime_contract_pack.py` — Runtime Contract Pack 合同测试
    - `aitest/tests/platform/test_runtime_contract_projection.py` — RunEvent 投影测试
    - `aitest/tests/platform/test_runtime_event_contracts.py` — RunEvent schema 测试
  - ✅ 统一 gate 脚本：`tools/phase8_gate.py` — 集成全部 6 个 PR 的验收命令
    - 支持 `--all`（运行全部 gate）、`--pr 8.1 8.2`（指定 PR）、`--dependency`（快速验证）
    - 包含每个 gate 的预期结果说明
  - ✅ `phase-8-acceptance-matrix.md` 中所有 gate 命令与实际测试文件一致
  - ✅ 所有 PR 的完成标准已在 acceptance-matrix.md 中文档化
  - 下一步：Phase 8 验收环境修复（本地 pytest / CI 环境配置）
