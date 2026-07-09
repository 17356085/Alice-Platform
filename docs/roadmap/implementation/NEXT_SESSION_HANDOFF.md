# Next Session Handoff

> 更新时间：2026-07-08
> 适用对象：下一个继续实施本项目的会话
> 目标：不重复长对话，直接接手执行

## 1. 一句话结论

Phase 1 到 Phase 8 已经完成收口，且 `PH8-PR-8.1 ~ 8.7` gate 全部通过。下一个会话应切换到 Phase 9 规划，不要再重复 Phase 1-8 的架构分析。

## 2. 阶段映射

- `Phase 0`
  - 指最开始的架构尽调、Roadmap、Sprint 规划、PR Backlog、验收矩阵和主链路文档固化
  - 这是规划阶段，不是代码实施阶段
- `Phase 1`
  - 官方执行主链冻结与统一入口收口
- `Phase 2`
  - Capability / Tool / MCP / Memory / Knowledge / Replay 接入主链
- `Phase 3`
  - Governance / Security / Audit / Ownership 治理
- `Phase 4`
  - 插件化契约、扩展注册与边界清理
- `Phase 5`
  - Scheduler / Worker / Checkpoint / Resume / Async 执行
- `Phase 6`
  - Metrics / Trace / Performance / HA / Ecosystem 控制面
- `Phase 7`
  - 目标是“发布收口 + SDK 独立发布边界收口 + 统一执行内核”
  - 已由用户确认全部走完
- `Phase 8`
  - 当前建议进入的新阶段
  - 目标是“可治理模块化单体 + 边界减重 + 依赖门禁 + Runtime 合同固化”

## 3. 当前真实状态

已经具备的成果：

- `docs/architecture/OFFICIAL_EXECUTION_MAINLINE.md` 已固化官方执行主链。
- `docs/roadmap/implementation/phase-1~6-*` 文档已建立完整 PR Backlog 和验收矩阵。
- `docs/roadmap/implementation/Principle AI Engineer.md` 已按当前代码快照完成复审，并补入 SDK 独立发布分析。
- 平台主入口已经基本向 `ExecutionService` 收敛。
- Capability、Memory、Knowledge、Replay、Scheduler、Metrics、Trace 等能力已经有一轮改造和测试文件落位。

必须保持清醒的现实：

- `Phase 1~6` 文档里的 `Done`，代表该轮任务卡已落地，不等于整个项目已经达到稳定发布状态。
- 当前工作区存在大量未提交改动，属于“进行中的大快照”，不是干净发布基线。
- 公开 `ExecutionKernel` 已建立，`alice_engine.Engine.run()` 与 Platform `ExecutionService / EngineFactory` 已切到共享 Kernel 主链。
- `packages/alice-engine/alice_engine/platform_bridge.py` 已改为显式 Port 注册读取，不再字符串动态导入 `aitest.*`。
- 测试收集已恢复到可证明状态，本地按 CI 口径已可 `collect 1346`。
- 本地完整 CI 风格回归现已通过：`1344 passed, 2 skipped`（`pytest -x -q -p no:cacheprovider -m "not slow and not llm" packages/alice-engine/tests aitest/tests`，2026-07-07）。
- `alice-engine` wheel 已可在本机构建成功；并已在临时安装环境完成 installed-wheel smoke，确认 `import alice_engine`、`platform_bridge`、`GovernanceRouter`、`InlineExecutionKernel`、`Engine(..., kernel=...)` 最小 facade 路径可运行且不会把 `aitest` 导入进 `sys.modules`。
- `.github/workflows/ci.yml` 中 standalone smoke 已与当前公开 `KernelExecutionRequest` 合同重新对齐，修正了旧脚本仍读取 `request.request_id` 的漂移，现改为 `request.context.request_id`。
- CI / Docker / standalone wheel 验收已由用户确认全部走完，`PH7-PR-7.5 ~ 7.6` 已关闭。
- 当前工作区仍是 dirty snapshot；Phase 8 开始前仍要先看 `git status --short`，但不要擅自回退用户已有改动。
- Phase 8 的核心不是继续扩能力，而是治理已经接入主链的能力边界。
- `PH8-PR-8.1` 已落地 `tools/check_dependency_graph.py`、SCC 基线、CI 门禁与依赖回潮测试，并通过 gate。
- `PH8-PR-8.2` 已落地 Runtime Contract Pack、RunEvent 投影路径统一与硬 contract tests，并通过 gate。
- `PH8-PR-8.3` 已完成 `AgentLoop` 第一轮减重：`runtime_context_builder`、`ProviderRuntimeLifecycle`、`MCPClientLifecycle`、`ReplayStepSink`、`SessionLoopOrchestrator` 已接入主链，并通过 gate。
- `PH8-PR-8.4` 已完成第一轮组合根治理：server API、CLI、worker 解析路径统一，`aitest/llm/providers/*.py` 已标记 deprecated，并通过本机测试组。
- `PH8-PR-8.5` 已完成代码落地并通过 gate：`McpClientResult` 字段标注表达 async 语义、`sdk_ports._mcp_clients_factory` 事件循环冲突不再静默吞错（线程池 fallback + WARNING 日志）、新增 `AsyncToolProvider` Protocol、`test_mcp_client_degradation.py` 16 个测试全部通过；顺带修复两个阻塞验证的既有 bug（`path_utils.py` 向后兼容常量缺失、`aitest/mcp/__init__.py` 无条件 SDK 导入）。
- `PH8-PR-8.6` 已完成代码落地并通过 gate：SDK Provider 功能补齐（claude/openai/deepseek/mimo/ollama 全部支持 complete + stream + tool calling + 特殊功能如 Prompt Caching / reasoning_content），平台 adapter 改为委托实现（API key 注入 + trace 装饰器），设计文档完成（`docs/architecture/PH8-PR-8.6-PROVIDER-CONSOLIDATION.md`），测试文件已补齐（SDK 单元测试 + 平台 adapter 集成测试）。
- `PH8-PR-8.7` 已完成代码落地并通过 gate：所有必需测试文件已存在（`test_dependency_graph_guard.py`、`test_runtime_contract_pack.py`、`test_runtime_contract_projection.py`、`test_runtime_event_contracts.py`），统一 gate 脚本 `tools/phase8_gate.py` 集成全部 6 个 PR 的验收命令，文档与实际测试文件已完全对齐。

## 4. 下个会话不要再做什么

- 不要从头再做一遍架构分析。
- 不要再按 Phase 1 到 Phase 6 重新拆 Sprint。
- 不要再把 Phase 7 发布验收当作当前主线。
- 不要把“SDK 复用 Platform ExecutionService”当作目标。
- 不要直接做大重构式搬迁。
- 不要忽略当前 dirty worktree，尤其不要擅自回退用户已有改动。

## 5. 下个会话应该先读哪些文档

按顺序：

1. [NEXT_SESSION_HANDOFF.md](/D:/Desktop/Alice/docs/roadmap/implementation/NEXT_SESSION_HANDOFF.md)
2. [Principle AI Engineer.md](/D:/Desktop/Alice/docs/roadmap/implementation/Principle%20AI%20Engineer.md)
3. [phase-8-pr-backlog.md](/D:/Desktop/Alice/docs/roadmap/implementation/phase-8-pr-backlog.md)
4. [phase-8-acceptance-matrix.md](/D:/Desktop/Alice/docs/roadmap/implementation/phase-8-acceptance-matrix.md)
5. [OFFICIAL_EXECUTION_MAINLINE.md](/D:/Desktop/Alice/docs/architecture/OFFICIAL_EXECUTION_MAINLINE.md)

如需回看历史实施文档，再读：

- [README.md](/D:/Desktop/Alice/docs/roadmap/implementation/README.md)
- `phase-1~6-pr-backlog.md`
- `phase-1~6-acceptance-matrix.md`

## 6. 下个会话的主目标

下一个会话的主目标是 Phase 9 规划，不要再继续 Phase 8 的收尾。

## 7. 推荐执行顺序

建议严格按下面顺序推进：

1. 先做 Phase 9 规划与需求收敛
2. 再根据 Phase 9 目标拆分新的 PR / 验收矩阵
3. 保持 Phase 8 的 gate 状态不回退

## 8. 并行与串行关系

必须串行：

- `PH8-PR-8.1 -> PH8-PR-8.2` 建议串行
- `PH8-PR-8.2 -> PH8-PR-8.3` 已按顺序完成代码落地
- `PH8-PR-8.7` 必须最后做

可部分并行：

- `PH8-PR-8.4 ~ 8.6` 可以在当前合同和 AgentLoop 第一轮减重基础上部分并行
- 但每张 PR 都必须保持 Phase 7 发布回归可运行

## 9. 关键风险提示

- 当前仓库是 dirty worktree，下一会话开始前先看 `git status --short`，但不要擅自清理。
- `Phase 1~6` 文档中的 `Done` 不能直接当成“无需验证”。
- Phase 8 最大风险是把边界治理做成大重构；必须单 PR 单主题、小步可回滚。
- `aitest/platform/` 和 `alice_engine/core/executor.py` 是减重重点，但不能一次性大搬迁。
- 依赖图门禁初期应先设基线和防回潮，不要第一步就要求清零所有历史环。
- Provider、MCP、Replay、Context 合同变更会影响主执行链，必须有回归保护。

## 10. 建议的起手检查清单

- Phase 8 已验收完毕，下一会话优先进入 Phase 9 规划。

## 11. 本次交接物

本次会话已补齐以下交接文档：

- [NEXT_SESSION_HANDOFF.md](/D:/Desktop/Alice/docs/roadmap/implementation/NEXT_SESSION_HANDOFF.md)
- [phase-8-pr-backlog.md](/D:/Desktop/Alice/docs/roadmap/implementation/phase-8-pr-backlog.md)
- [phase-8-acceptance-matrix.md](/D:/Desktop/Alice/docs/roadmap/implementation/phase-8-acceptance-matrix.md)

这三份文件就是下一个会话的正式入口。
