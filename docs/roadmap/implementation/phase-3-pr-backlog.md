# Phase 3 PR Backlog

Phase 3 目标：夯实多租户、安全、审计、治理与生产可控性。

## PH3-PR-3.1
- Status: Done
- Tracking ID: PH3-PR-3.1
- Owner: Platform Owner
- ETA: 2 days
- 标题：关键 API 加入租户与归属校验
- 目标：补齐 run / workspace / org 边界
- 模块：`aitest/server/api` `aitest/platform/ownership.py`
- 风险：中
- 依赖：Phase 2 完成
- 完成标准：
  - 关键读写接口有归属校验
  - 非法访问被拒绝
  - 执行 / 审计 / Webhook / 报表 / 用量关键接口通过访问控制回归

## PH3-PR-3.2
- Status: Done
- Tracking ID: PH3-PR-3.2
- Owner: Audit Reviewer
- ETA: 2 days
- 标题：执行审计链闭环
- 目标：建立 run 级别审计可追踪性
- 模块：`aitest/audit_engine` `event bus` `replay`
- 风险：中
- 依赖：PH3-PR-3.1
- 完成标准：
  - 关键执行事件可追踪
  - run 与 event 可关联
  - replay session / audit / run-event 可聚合查询

## PH3-PR-3.3
- Status: Done
- Tracking ID: PH3-PR-3.3
- Owner: Infra Owner
- ETA: 2 days
- 标题：统一安全策略入口
- 目标：整合 tool / provider / prompt 安全策略
- 模块：`aitest/infra/security.py` `providers` `tool layer`
- 风险：中
- 依赖：PH3-PR-3.1
- 完成标准：
  - 安全策略统一挂载
  - 危险行为可被阻断或审计
  - prompt / provider / tool 执行前经过统一 SecurityHook

## PH3-PR-3.4
- Status: Done
- Tracking ID: PH3-PR-3.4
- Owner: Governance Owner
- ETA: 2 days
- 标题：统一 Governance 资产加载来源
- 目标：避免运行时在多个 governance 来源之间漂移
- 模块：`packages/alice-governance` 运行时加载逻辑
- 风险：中
- 依赖：Phase 2 完成
- 完成标准：
  - governance source of truth 明确
  - 兼容层有迁移说明
  - engine / executor / project 统一走 governance pack 解析器

## PH3-PR-3.5
- Status: Done
- Tracking ID: PH3-PR-3.5
- Owner: Governance Owner
- ETA: 2 days
- 标题：配置与策略版本化
- 目标：为治理、审计、安全建立版本边界
- 模块：`governance` `platform/config` `audit`
- 风险：中
- 依赖：PH3-PR-3.2 PH3-PR-3.4
- 完成标准：
  - 配置版本可识别
  - 运行记录能标识使用的策略版本
  - 执行结果 / run events / audit query 可回溯版本来源
