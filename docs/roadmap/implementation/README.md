# Implementation Roadmap Docs

本目录用于承载 Agent 平台未来几个月的实施计划文档。

目标：

- 把 Roadmap 落成可执行的 PR Backlog
- 把每个 PR 对应的验收项、负责人、评审人、回滚点显式化
- 保证每个阶段都可小步提交、可单独 Review、可单独回滚
- 保证每个阶段结束后系统保持可运行

## 文档说明

- `phase-N-pr-backlog.md`
  - 记录该阶段的 PR 任务卡
  - 每张卡包含 `Status / Tracking ID / Owner / ETA / 风险 / 依赖 / 完成标准`
- `phase-N-acceptance-matrix.md`
  - 记录该阶段每个 PR 的 `Tracking ID / Status / ETA / 测试项 / 负责人 / Reviewer / 回滚点`
- `NEXT_SESSION_HANDOFF.md`
  - 提供给下一个会话的正式交接说明
  - 记录当前真实进度、阶段映射、剩余主线、执行顺序和风险边界
- `docs/architecture/OFFICIAL_EXECUTION_MAINLINE.md`
  - 平台官方执行主链路文档
  - 作为 Phase 1 的架构冻结基线

## 当前阶段说明

- `Phase 0`
  - 指“分析、建模、Roadmap、PR Backlog 和验收矩阵固化”
  - 不对应业务代码交付
- `Phase 1` 到 `Phase 6`
  - 已完成一轮实施与文档落地
  - 但这不等于发布基线已经完全收口
- `Phase 7`
  - 用于承接当前改造后的收口工作
  - 重点解决 SDK 独立发布、统一执行内核、发布基线和测试收集问题

## 角色约定

- TL: Technical Lead
- Runtime Owner: Runtime / Engine 负责人
- Platform Owner: Platform / API 负责人
- Governance Owner: Governance / Skills / Policy 负责人
- Infra Owner: 基础设施 / DB / Deploy 负责人
- Security Reviewer: 安全评审
- QA Reviewer: 测试与回归评审
- Frontend Reviewer: 前端 / SSE / UI 协同评审
- Graph Owner: Graph / Workflow 负责人
- Memory Owner: Memory 负责人
- Knowledge Owner: Knowledge / RAG 负责人
- MCP Owner: MCP 集成负责人
- Replay Owner: Replay 负责人
- Provider Owner: Provider / Model 接入负责人
- Audit Reviewer: Audit / Observability 评审

## 通用 PR 规则

- 单 PR 单主题
- 尽量少跨模块
- 合并后系统可运行
- 必须有回滚方案
- 必须说明兼容性影响
- 必须说明验证方式

## 当前约定

- 新增任务默认 `Status: Todo`
- `ETA` 以 1 到 3 天为单位估算
- `Tracking ID` 采用 `PH{N}-PR-{M}` 格式
- `Owner` 负责推进，不代表必须单人完成
