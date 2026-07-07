# Phase 6 PR Backlog

Phase 6 目标：进入企业级平台阶段，补齐观测、性能、分布式稳定性与生态运营能力。

## PH6-PR-6.1
- Status: Done
- Tracking ID: PH6-PR-6.1
- Owner: Audit Reviewer
- ETA: 2 days
- 标题：建立统一执行指标体系
- 目标：采集 latency、token、tool、retrieval、failure 等核心指标
- 模块：`audit` `metrics` `runtime` `server`
- 风险：中
- 依赖：Phase 5 完成
- 完成标准：
  - 指标定义明确
  - 主执行链可采集

## PH6-PR-6.2
- Status: Done
- Tracking ID: PH6-PR-6.2
- Owner: Audit Reviewer
- ETA: 2 days
- 标题：分布式事件追踪与关联 ID 体系
- 目标：打通执行、审计、回放、worker 观测链
- 模块：`event bus` `audit` `replay` `runtime`
- 风险：中
- 依赖：PH6-PR-6.1
- 完成标准：
  - trace / run / event 关联一致
  - 跨进程可追踪

## PH6-PR-6.3
- Status: Done
- Tracking ID: PH6-PR-6.3
- Owner: Runtime Owner
- ETA: 2 days
- 标题：性能基线与瓶颈治理
- 目标：建立热点路径性能基线并治理首批瓶颈
- 模块：`runtime` `provider` `knowledge` `memory`
- 风险：中
- 依赖：PH6-PR-6.1
- 完成标准：
  - 有性能基线
  - 至少解决一批关键瓶颈

## PH6-PR-6.4
- Status: Done
- Tracking ID: PH6-PR-6.4
- Owner: Infra Owner
- ETA: 3 days
- 标题：高可用与故障恢复策略
- 目标：建立 worker 崩溃、超时、重复执行场景恢复策略
- 模块：`runtime` `infra` `scheduler`
- 风险：高
- 依赖：PH6-PR-6.2
- 完成标准：
  - 关键故障场景有恢复策略
  - 故障不导致状态失真

## PH6-PR-6.5
- Status: Done
- Tracking ID: PH6-PR-6.5
- Owner: Platform Owner
- ETA: 2 days
- 标题：生态运营能力基线
- 目标：为插件、项目、租户、版本运营建立最小控制面
- 模块：`platform` `governance` `ui` `cli`
- 风险：中
- 依赖：PH6-PR-6.4
- 完成标准：
  - 可查看已注册扩展
  - 可识别版本与兼容关系
