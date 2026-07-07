# Phase 4 PR Backlog

Phase 4 目标：把新增能力从“改核心”转成“走契约、走注册、走插件”。

## PH4-PR-4.1
- Status: Done
- Tracking ID: PH4-PR-4.1
- Owner: Provider Owner
- ETA: 2 days
- 标题：定义 Provider 插件契约
- 目标：新增 provider 不再改核心内核
- 模块：`providers` `adapters` `packages/alice-engine`
- 风险：中
- 依赖：Phase 3 完成
- 完成标准：
  - provider 有统一能力声明
  - 注册与发现流程清晰
  - Provider registry 可按契约发现已知 provider

## PH4-PR-4.2
- Status: Done
- Tracking ID: PH4-PR-4.2
- Owner: Platform Owner
- ETA: 2 days
- 标题：定义 Tool / Capability 插件契约
- 目标：工具与能力可按契约扩展
- 模块：`tool layer` `capability_router` `governance`
- 风险：中
- 依赖：PH4-PR-4.1
- 完成标准：
  - tool / capability 可独立注册
  - 执行链无需改核心
  - router 可发现 capability contracts

## PH4-PR-4.3
- Status: Done
- Tracking ID: PH4-PR-4.3
- Owner: Graph Owner
- ETA: 3 days
- 标题：定义 Graph 插件契约
- 目标：新增 graph 走标准注册机制
- 模块：`graphs` `discovery` `runtime`
- 风险：高
- 依赖：PH4-PR-4.1
- 完成标准：
  - graph 元数据与装载协议明确
  - graph discovery 可工作
  - graph registry 可发现并构建 built-in graphs

## PH4-PR-4.4
- Status: Done
- Tracking ID: PH4-PR-4.4
- Owner: QA Reviewer
- ETA: 2 days
- 标题：建立扩展模板与契约测试
- 目标：提供 provider/tool/graph 扩展示例
- 模块：`packages/*/tests` 文档模板
- 风险：低
- 依赖：PH4-PR-4.1 PH4-PR-4.2 PH4-PR-4.3
- 完成标准：
  - 至少 1 套扩展示例
  - 契约测试可复用
  - 扩展模板文档可直接复用

## PH4-PR-4.5
- Status: Done
- Tracking ID: PH4-PR-4.5
- Owner: TL
- ETA: 2 days
- 标题：稳定 SDK 与平台主仓边界
- 目标：完成抽离后的边界清理
- 模块：`packages/alice-engine` `packages/alice-governance` `aitest`
- 风险：中
- 依赖：PH4-PR-4.4
- 完成标准：
  - 依赖方向清晰
  - 不再反向穿透
  - SDK 轻量导入
