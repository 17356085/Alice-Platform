# Next Session Handoff

> 更新时间：2026-07-06
> 适用对象：下一个继续实施本项目的会话
> 目标：不重复长对话，直接接手执行

## 1. 一句话结论

Phase 1 到 Phase 6 的结构化改造和文档化工作已经完成一轮，但项目当前仍处于“主链已接通、发布基线未收口”的状态。下一个会话不应再重复宏观规划，而应进入收口执行。

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
  - 当前建议进入的新阶段
  - 目标是“发布收口 + SDK 独立发布边界收口 + 统一执行内核”

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
- SDK 和 Platform 还没有共享同一个公开、稳定、可发布的 `ExecutionKernel`。
- `alice_engine.Engine.run()` 仍走 `_internal.graph`，与 Platform `ExecutionService` 下方主链并未完全统一。
- `packages/alice-engine/alice_engine/platform_bridge.py` 仍通过动态加载 `aitest.*` 维持能力接线，这不满足真正的 SDK 独立发布要求。
- 测试、镜像、workspace package 安装链是否完全收口，仍需下个会话继续验证。

## 4. 下个会话不要再做什么

- 不要从头再做一遍架构分析。
- 不要再按 Phase 1 到 Phase 6 重新拆 Sprint。
- 不要把“SDK 复用 Platform ExecutionService”当作目标。
- 不要直接做大重构式搬迁。
- 不要忽略当前 dirty worktree，尤其不要擅自回退用户已有改动。

## 5. 下个会话应该先读哪些文档

按顺序：

1. [NEXT_SESSION_HANDOFF.md](/D:/Desktop/Alice/docs/roadmap/implementation/NEXT_SESSION_HANDOFF.md)
2. [Principle AI Engineer.md](/D:/Desktop/Alice/docs/roadmap/implementation/Principle%20AI%20Engineer.md)
3. [OFFICIAL_EXECUTION_MAINLINE.md](/D:/Desktop/Alice/docs/architecture/OFFICIAL_EXECUTION_MAINLINE.md)
4. [phase-7-pr-backlog.md](/D:/Desktop/Alice/docs/roadmap/implementation/phase-7-pr-backlog.md)
5. [phase-7-acceptance-matrix.md](/D:/Desktop/Alice/docs/roadmap/implementation/phase-7-acceptance-matrix.md)

如需回看历史实施文档，再读：

- [README.md](/D:/Desktop/Alice/docs/roadmap/implementation/README.md)
- `phase-1~6-pr-backlog.md`
- `phase-1~6-acceptance-matrix.md`

## 6. 下个会话的主目标

下一个会话的主目标不是继续横向扩能力，而是完成以下三件事：

1. 统一 SDK 与 Platform 下方的执行内核。
2. 收口 SDK 独立发布边界，逐步移除动态 `aitest.*` Bridge。
3. 把测试收集、workspace package 安装、镜像/CI 验证拉到可证明状态。

## 7. 推荐执行顺序

建议严格按下面顺序推进：

1. 先做 `PH7-PR-7.1`
   - 明确公开 `ExecutionKernel` 契约
   - 不先搬代码，先固定边界
2. 再做 `PH7-PR-7.2`
   - 让 standalone SDK `Engine` 改为调用公开 Kernel
3. 再做 `PH7-PR-7.3`
   - 让 Platform `ExecutionService / EngineFactory` 也调用同一 Kernel
4. 再做 `PH7-PR-7.4`
   - 用显式 Port 注入替代 `platform_bridge` 的动态 `aitest.*` 加载
5. 然后做 `PH7-PR-7.5`
   - 收口 workspace package 安装、Docker/CI 发布基线、测试收集问题
6. 最后做 `PH7-PR-7.6`
   - 在未安装 `aitest` 的前提下，验证 SDK wheel / 独立运行 / 边界契约

## 8. 并行与串行关系

必须串行：

- `PH7-PR-7.1 -> PH7-PR-7.2 -> PH7-PR-7.3 -> PH7-PR-7.4`
- `PH7-PR-7.6` 必须等待 `PH7-PR-7.4` 完成

可部分并行：

- `PH7-PR-7.5` 可以在 `PH7-PR-7.3` 后半段开始准备
- 但 `PH7-PR-7.5` 的最终验收，需要在 `PH7-PR-7.4` 之后再跑完整回归

## 9. 关键风险提示

- 当前仓库是 dirty worktree，下一会话开始前先看 `git status --short`，但不要擅自清理。
- `Phase 1~6` 文档中的 `Done` 不能直接当成“无需验证”。
- `platform_bridge` 的存在会导致静态依赖图与真实运行依赖不一致。
- 若直接推进新功能而不先收口内核，会继续放大 Platform 与 SDK 的双执行语义问题。
- 若未先固定 Kernel 契约就直接删兼容层，极容易引入入口行为漂移。

## 10. 建议的起手检查清单

- 查看 `docs/roadmap/implementation/Principle AI Engineer.md` 中“当前关键偏差”和“SDK 独立发布与能力归属分析”两节。
- 核对 `packages/alice-engine/alice_engine/engine.py` 当前是否仍走 `_internal.graph`。
- 核对 `aitest/platform/execution_service.py` 与 `aitest/platform/engine_factory.py` 是否已经可以承接公共 Kernel。
- 核对 `packages/alice-engine/alice_engine/platform_bridge.py` 里有哪些 `aitest.*` 动态加载点仍存在。
- 先收集测试/安装/镜像阻断项，再进入 Phase 7 第一张 PR 卡。

## 11. 本次交接物

本次会话已补齐以下交接文档：

- [NEXT_SESSION_HANDOFF.md](/D:/Desktop/Alice/docs/roadmap/implementation/NEXT_SESSION_HANDOFF.md)
- [phase-7-pr-backlog.md](/D:/Desktop/Alice/docs/roadmap/implementation/phase-7-pr-backlog.md)
- [phase-7-acceptance-matrix.md](/D:/Desktop/Alice/docs/roadmap/implementation/phase-7-acceptance-matrix.md)

这三份文件就是下一个会话的正式入口。
