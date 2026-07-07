# Phase 2 PR Backlog

Phase 2 目标：把 Capability、Tool Calling、MCP、Memory、Knowledge、Replay 真正接入统一执行主链路。

## PH2-PR-2.1
- Status: Done
- Tracking ID: PH2-PR-2.1
- Owner: Platform Owner
- ETA: 2 days
- 标题：Capability Router 接入执行主链路
- 目标：让能力匹配成为正式执行步骤
- 模块：`aitest/platform/capability_router` `packages/alice-engine`
- 风险：中
- 依赖：Phase 1 完成
- 完成标准：
  - capability 决策进入主执行链
  - 无 capability 时有明确降级路径

## PH2-PR-2.2
- Status: Done
- Tracking ID: PH2-PR-2.2
- Owner: Runtime Owner
- ETA: 2 days
- 标题：统一 Tool Calling 契约
- 目标：统一工具注册、调用、返回结构
- 模块：`aitest/adapters` `packages/alice-engine` `aitest/platform`
- 风险：中
- 依赖：PH2-PR-2.1
- 完成标准：
  - tool 调用协议统一
  - agent 可真实调用 tool
  - 输出结构统一

## PH2-PR-2.3
- Status: Done
- Tracking ID: PH2-PR-2.3
- Owner: MCP Owner
- ETA: 2 days
- 标题：修复 MCP 生命周期并接入工具目录
- 目标：让 MCP 成为正式外部能力层
- 模块：`aitest/mcp` `packages/alice-engine`
- 风险：中
- 依赖：PH2-PR-2.2
- 完成标准：
  - MCP 会话生命周期正确
  - 工具目录可被执行器消费

## PH2-PR-2.4
- Status: Done
- Tracking ID: PH2-PR-2.4
- Owner: Memory Owner
- ETA: 2 days
- 标题：Memory 接入上下文构建主流程
- 目标：让 memory 不再是旁路系统
- 模块：`aitest/platform/testing_memory*` `context builder`
- 风险：中
- 依赖：Phase 1 完成
- 完成标准：
  - memory 查询可进入 context
  - 空结果有稳定降级策略

## PH2-PR-2.5
- Status: Done
- Tracking ID: PH2-PR-2.5
- Owner: Knowledge Owner
- ETA: 2 days
- 标题：Knowledge / RAG 接入统一上下文
- 目标：知识检索成为标准上下文构建步骤
- 模块：`knowledge` `governance` `platform/context`
- 风险：中
- 依赖：PH2-PR-2.4
- 完成标准：
  - knowledge 检索与 memory 协同
  - 可观测上下文来源

## PH2-PR-2.6
- Status: Done
- Tracking ID: PH2-PR-2.6
- Owner: Replay Owner
- ETA: 2 days
- 标题：Replay 正式进入执行生命周期
- 目标：录制与回放成为主链路能力
- 模块：`aitest/platform/replay*` `event bus` `execution service`
- 风险：中
- 依赖：PH2-PR-2.2 PH2-PR-2.4
- 完成标准：
  - 正常执行可录制
  - replay 可消费标准输入并重放
