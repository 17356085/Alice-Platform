# Phase 8 Acceptance Matrix

| Tracking ID | Status | ETA | 测试项 | 负责人 | Reviewer | 回滚点 |
| --- | --- | --- | --- | --- | --- | --- |
| PH8-PR-8.1 | Gate Passed | 2 days | 依赖图生成、SCC 基线、SDK 边界回潮门禁、CI 脚本验证 | TL | Runtime Owner, QA Reviewer | 回退依赖门禁脚本和 CI 检查 |
| PH8-PR-8.2 | Gate Passed | 3 days | Runtime Event / Context / Replay / Checkpoint / Artifact 合同测试 | Runtime Owner | Platform Owner, Replay Owner, TL | 回退合同导出和平台投影适配 |
| PH8-PR-8.3 | Gate Passed | 3 days | AgentLoop 主循环回归、Provider/Context/Tool/Replay 生命周期单测 | Runtime Owner | QA Reviewer, Provider Owner | 回退拆分出的内部服务，恢复旧 AgentLoop 接线 |
| PH8-PR-8.4 | Gate Passed | 3 days | Server/CLI composition root 集成测试、singleton 兼容测试、Run-scoped Context 测试 | Platform Owner | TL, Security Reviewer | 回退组合根接线，保留兼容 getter |
| PH8-PR-8.5 | Gate Passed | 2 days | ToolProvider / MCPProvider async 生命周期测试、缺依赖错误语义测试 | MCP Owner | Runtime Owner, QA Reviewer | 回退 MCP Provider 合同和 Adapter 接线 |
| PH8-PR-8.6 | Gate Passed | 2 days | Provider 配置、streaming、错误响应、兼容 facade 回归 | Provider Owner | Runtime Owner, Platform Owner | 回退 Provider facade 改动 |
| PH8-PR-8.7 | Gate Passed | 2 days | Phase 8 全套边界验收、CI 回归、文档命令一致性检查 | QA Reviewer | TL, Runtime Owner, Platform Owner | 回退 Phase 8 验收脚本和状态文档 |

## 阶段进入条件

- Phase 7 已全部走完，可信发布基线不再是当前主阻塞。
- `ExecutionKernel`、显式 Port 注入、SDK 独立发布边界已经成为当前基线。
- 下一阶段不扩展新业务能力，优先治理已经接入主链的能力边界。

## 阶段完成标准

- 依赖图和 SCC 有可重复报告，并在 CI 中阻止边界回潮。
- Runtime Contract Pack 至少覆盖 Event、Context、Replay、Checkpoint、Artifact。
- `alice_engine/core/executor.py` 第一轮减重完成，主循环行为兼容。
- Platform 组合根清楚，关键路径减少 singleton 和进程环境变量依赖。
- Tool/MCP async 生命周期有统一合同和测试。
- Provider 执行实现收敛到 SDK，`aitest.llm` 退为兼容 facade。
- Phase 8 验收命令、测试结果和文档状态一致。

## 当前真实状态

- `PH8-PR-8.1` 已落地依赖图脚本、SCC 基线、CI 门禁和回归测试，并已通过正式 gate。
- `PH8-PR-8.2` 已落地 Runtime Contract Pack、RunEvent 投影适配和硬 contract tests，并已通过正式 gate。
- `PH8-PR-8.3` 已完成第一轮 `AgentLoop` 边界减重，`Context / Provider / Tool-MCP / Replay / Session Orchestration` 均已抽成内部协作者，并已通过正式 gate。
- `PH8-PR-8.4` 已完成 Platform composition-root 治理并通过正式 gate：server API、CLI、worker 解析路径统一，`aitest/llm/providers/*.py` 已标记 deprecated。
- `PH8-PR-8.5` 已完成代码落地并通过本机 gate：`McpClientResult` 字段标注表达 async 语义、`sdk_ports._mcp_clients_factory` 事件循环冲突不再静默吞错（线程池 fallback + WARNING 日志）、新增 `AsyncToolProvider` Protocol、`test_mcp_client_degradation.py` 16 个测试全部通过；顺带修复两个阻塞验证的既有 bug（`path_utils.py` 向后兼容常量缺失、`aitest/mcp/__init__.py` 无条件 SDK 导入）。`tools/phase8_gate.py --pr 8.5` 在本机 `.venv` 环境通过，`aitest/tests/mcp/` 33/33 通过。
- `PH8-PR-8.6` 已完成代码落地并通过本机 gate：SDK Provider 功能补齐（claude/openai/deepseek/mimo/ollama 全部支持 complete + stream + tool calling + 特殊功能如 Prompt Caching / reasoning_content），平台 adapter 改为委托实现（API key 注入 + trace 装饰器），设计文档完成（`docs/architecture/PH8-PR-8.6-PROVIDER-CONSOLIDATION.md`），测试文件已补齐（SDK 单元测试 + 平台 adapter 集成测试）。
- `PH8-PR-8.7` 已完成代码落地并通过本机 gate：所有必需测试文件已存在（`test_dependency_graph_guard.py`、`test_runtime_contract_pack.py`、`test_runtime_contract_projection.py`、`test_runtime_event_contracts.py`），统一 gate 脚本 `tools/phase8_gate.py` 集成全部 6 个 PR 的验收命令，文档与实际测试文件已完全对齐。Phase 8 所有 PR gate 均已通过。

## 正式 Gate 命令

### PH8-PR-8.1

```powershell
python tools/check_dependency_graph.py
```

预期：

- 依赖图报告可输出
- 无 `alice_engine -> aitest` 静态或动态依赖回潮
- SCC 数量和最大 SCC 规模不超过已审查基线

### PH8-PR-8.2

```powershell
python -m pytest -q -p no:cacheprovider `
  packages/alice-engine/tests/test_runtime_contract_pack.py `
  aitest/tests/platform/test_runtime_contract_projection.py `
  aitest/tests/platform/test_runtime_event_contracts.py
```

预期：

- Runtime Contract Pack 合同测试通过
- `RuntimeEventEnvelope -> RunEvent` 投影测试通过
- `RunEvent` 核心事件字段 schema 与投影器表驱动一致性测试通过

### PH8-PR-8.3

```powershell
python -m pytest -q -p no:cacheprovider `
  packages/alice-engine/tests/test_architecture.py `
  packages/alice-engine/tests/test_provider_runtime_lifecycle.py `
  packages/alice-engine/tests/test_runtime_lifecycle.py `
  packages/alice-engine/tests/test_runtime_context_builder.py `
  packages/alice-engine/tests/test_session_loop_orchestrator.py `
  aitest/tests/agents/test_agent_runner.py `
  aitest/tests/integration/test_agent_loop.py
```

预期：

- `AgentLoop` 的 runtime context / context vars 组装由内部 collaborator 承接
- `Provider lifecycle` 由内部 collaborator 承接，最终 provider/model 解析路径冻结
- `Tool/MCP lifecycle` 与 replay step sink 由内部 collaborator 承接
- 单次 session 的 loop orchestration 从 `AgentLoop` 主体剥离，保留行为兼容
- 新拆内部协作者对 `executor` 的反向依赖由架构测试持续门禁
- 新增 runtime context 协作者单测通过，缓存与字段注入行为冻结
- 现有 AgentLoop 初始化与集成回归继续通过

### PH8-PR-8.5

```powershell
python -m pytest -q -p no:cacheprovider `
  aitest/tests/mcp/test_mcp_client_degradation.py `
  aitest/tests/mcp
```

预期：

- `McpClientResult.close` / `.call_tool` 类型标注通过 `Awaitable`/`Coroutine` 语义断言
- MCP SDK 缺失降级路径（`_connect_stdio` / `_connect_http` / `create_mcp_client` /
  `create_mcp_clients_for_agent`）全部返回空结果，不抛异常
- `sdk_ports._mcp_clients_factory` 在事件循环冲突时走线程池 fallback，非冲突
  `RuntimeError`/`Exception` 记录 WARNING 并带 agent 名称，不再静默吞错
- `AsyncToolProvider` Protocol 可导入、`runtime_checkable`、且声明的
  `call_tool_async` / `close_async` 均为 `async def`
- `aitest/tests/mcp/` 全目录无回归

### PH8-PR-8.6

```powershell
python -m pytest -q -p no:cacheprovider `
  packages/alice-engine/tests/providers/test_claude_provider.py `
  packages/alice-engine/tests/providers/test_openai_deepseek_provider.py `
  aitest/tests/platform/test_provider_adapter.py
```

预期：

- SDK Provider complete() + stream() + tool calling 通过单元测试
- Prompt Caching、reasoning_content、错误响应合同通过测试
- 平台 adapter 正确委托 SDK 层（API key 注入、trace 装饰器、base_url 注入）
- Legacy imports 兼容性保持
- 未知 provider 错误处理正确

### PH8-PR-8.7

```powershell
python tools/phase8_gate.py --all
```

或分步执行：

```powershell
python tools/check_dependency_graph.py
python -m pytest -q -p no:cacheprovider `
  packages/alice-engine/tests/test_dependency_graph_guard.py `
  packages/alice-engine/tests/test_runtime_contract_pack.py `
  aitest/tests/platform/test_runtime_contract_projection.py `
  aitest/tests/platform/test_runtime_event_contracts.py
```

预期：

- Phase 8 依赖门禁仍通过
- Runtime Contract Pack 与 RunEvent schema / 投影 gate 全部通过
- 文档中的 Phase 8 gate 命令与仓库实际测试文件一致

## 推荐执行顺序

1. 先做 `PH8-PR-8.1`，建立依赖图和边界门禁。
2. 再做 `PH8-PR-8.2`，冻结 Runtime Contract Pack。
3. 并行推进 `PH8-PR-8.3`、`PH8-PR-8.4`、`PH8-PR-8.5`、`PH8-PR-8.6`，但每张 PR 都必须保持主线测试可运行。
4. 最后用 `PH8-PR-8.7` 收束验收命令、CI 回归和下一阶段进入条件。
