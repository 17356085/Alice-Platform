# Phase 7 PR Backlog

Phase 7 目标：完成发布收口、SDK 独立发布边界收口，以及 Platform 与 SDK 共用统一执行内核。

## PH7-PR-7.1
- Status: Todo
- Tracking ID: PH7-PR-7.1
- Owner: TL
- ETA: 1 day
- 标题：固化公开 ExecutionKernel 契约
- 目标：在 `alice-engine` 内定义公开、稳定、可测试的 `ExecutionKernel` 接口与最小输入输出模型
- 模块：`packages/alice-engine` `docs/architecture`
- 风险：中
- 依赖：无
- 完成标准：
  - Kernel 公共接口明确
  - 与 Platform Facade、Standalone Facade 的职责边界清晰
  - 不引入 `aitest -> sdk -> aitest` 反向依赖

## PH7-PR-7.2
- Status: Todo
- Tracking ID: PH7-PR-7.2
- Owner: Runtime Owner
- ETA: 2 days
- 标题：让 Standalone SDK Engine 改为调用公开 Kernel
- 目标：去掉 `alice_engine.Engine.run()` 对 `_internal.graph` 的直接依赖
- 模块：`packages/alice-engine`
- 风险：高
- 依赖：PH7-PR-7.1
- 完成标准：
  - Standalone `Engine` 通过公开 Kernel 执行
  - `_internal.graph` 不再是公开行为根基
  - SDK 基础执行回归通过

## PH7-PR-7.3
- Status: Todo
- Tracking ID: PH7-PR-7.3
- Owner: Platform Owner
- ETA: 2 days
- 标题：让 Platform ExecutionService 与 SDK 共用同一 Kernel
- 目标：统一 Platform Facade 与 Standalone Facade 下方执行语义
- 模块：`aitest/platform` `packages/alice-engine`
- 风险：高
- 依赖：PH7-PR-7.2
- 完成标准：
  - `ExecutionService / EngineFactory` 调用同一公开 Kernel
  - CLI、Server、Chat 主路径语义保持不变
  - 不把租户、RunStore、Audit 语义硬塞进 SDK

## PH7-PR-7.4
- Status: Todo
- Tracking ID: PH7-PR-7.4
- Owner: Runtime Owner
- ETA: 3 days
- 标题：移除动态 Platform Bridge，改为显式 Port 注入
- 目标：逐步替换 `platform_bridge` 中对 `aitest.*` 的动态加载
- 模块：`packages/alice-engine` `aitest/platform` `aitest/mcp`
- 风险：高
- 依赖：PH7-PR-7.3
- 完成标准：
  - Capability / Memory / Knowledge / Replay / MCP 通过显式 Port 或受控 Adapter 注入
  - SDK 不再依赖字符串动态导入 `aitest.*`
  - 最小安装行为可预测

## PH7-PR-7.5
- Status: Todo
- Tracking ID: PH7-PR-7.5
- Owner: Infra Owner
- ETA: 2 days
- 标题：发布基线收口与 workspace package 安装验证
- 目标：把测试收集、CI、Docker、workspace package 安装链拉到可证明状态
- 模块：`pyproject.toml` `packages/*` `docs/architecture` `CI/Docker`
- 风险：中
- 依赖：PH7-PR-7.3
- 完成标准：
  - workspace packages 安装链清晰
  - 关键测试可收集并可执行
  - Docker/CI 不再遗漏核心 package

## PH7-PR-7.6
- Status: Todo
- Tracking ID: PH7-PR-7.6
- Owner: QA Reviewer
- ETA: 2 days
- 标题：SDK 独立发布验证与边界契约测试
- 目标：在不安装 `aitest` 的环境中验证 `alice-engine` 可以独立安装和运行
- 模块：`packages/alice-engine/tests` `CI` `release docs`
- 风险：中
- 依赖：PH7-PR-7.4, PH7-PR-7.5
- 完成标准：
  - clean env wheel 安装通过
  - import `alice_engine` 不触发 `aitest` 依赖
  - Kernel Contract Test 与最小 Mock Provider 执行通过
