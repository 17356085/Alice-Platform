# Phase 7 PR Backlog

Phase 7 目标：完成发布收口、SDK 独立发布边界收口，以及 Platform 与 SDK 共用统一执行内核。

## PH7-PR-7.1
- Status: Done
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
- Status: Done
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
- Status: Done
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
- Status: Done
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
  - 当前进展：
    - `platform_bridge` 已改为读取显式 `platform_ports` 注册表，不再动态 `import aitest.*`
    - `aitest/platform/sdk_ports.py` 已提供 Capability / Memory / Knowledge / MCP 的显式注入接线
    - `packages/alice-engine/tests/test_sdk_boundary.py` 已覆盖显式 Port 注入与 optional bridge 行为
    - `packages/alice-engine/tests/test_architecture.py` 已增加动态 `aitest` 导入回潮门禁
    - 本地补充清点已完成：SDK 运行时代码中未发现残余 `aitest` 直接导入或字符串动态导入，checkpoint / replay 路径保持为中性 runtime 接口
  - 剩余事项：
    - 无新的本地代码收口项；后续仅需在 7.5 / 7.6 联合验收时继续关注是否有线上环境特有的边界回潮

## PH7-PR-7.5
- Status: Done
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
  - 当前进展：
    - CI 已改为正式安装 `alice-governance`、`alice-discovery`、`alice-engine` 与根包 `aitest`
    - CI 已增加 workspace import smoke、`pytest --collect-only`、以及基础执行测试入口
    - Dockerfile 已复制并安装 `packages/`，不再只依赖手写第三方依赖列表
    - 本地按 CI 口径 `collect-only` 已达到 `1346 collected`
    - 本地完整 CI 风格测试已通过：`1344 passed, 2 skipped`
  - 验收结论：
    - Phase 7 已由用户确认全部走完，发布基线验收关闭
    - 后续不再围绕 7.5 重复做 CI / Docker 架构分析；若出现新失败，按普通回归处理

## PH7-PR-7.6
- Status: Done
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
  - 当前进展：
    - 新增 standalone boundary 测试，验证 `alice_governance` 缺失时 SDK 会回退到 `governance_default`
    - CI 已新增 `sdk-standalone` job：构建 `alice-engine` wheel，在不安装 `aitest` 的干净环境做 smoke
    - standalone smoke 已提升为 `Project + Engine + mock provider + injected InlineExecutionKernel` 级别
    - standalone smoke 脚本已与当前公开 Kernel 合同重新对齐，修正旧脚本读取 `request.request_id` 的漂移，改为 `request.context.request_id`
    - 本地 SDK / Platform 完整 CI 风格回归已通过：`1344 passed, 2 skipped`
    - 本地 SDK 核心边界/契约回归已通过：`test_architecture`、`test_sdk_boundary`、`test_kernel_contract`、`test_engine`
    - 本地 wheel 构建已通过：`python -m build --wheel packages/alice-engine`
    - 本地 installed-wheel smoke 已通过：临时 venv 安装 wheel 后，`import alice_engine`、`GovernanceRouter`、`platform_bridge`、`InlineExecutionKernel`、`Engine(..., kernel=...)` 可运行，且 smoke 过程未将 `aitest` 导入到 `sys.modules`
  - 验收结论：
    - Phase 7 已由用户确认全部走完，SDK 独立发布边界验收关闭
    - 下一阶段从 V2 模块治理和边界减重开始，不再重做 Phase 7 主线
