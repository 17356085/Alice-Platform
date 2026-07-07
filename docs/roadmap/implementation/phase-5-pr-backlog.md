# Phase 5 PR Backlog

Phase 5 目标：引入 Scheduler、Job Queue、Worker、恢复与重试，形成可调度可恢复的执行平台。

## PH5-PR-5.1
- Status: Done
- Tracking ID: PH5-PR-5.1
- Owner: Runtime Owner
- ETA: 2 days
- 标题：定义 Scheduler 核心数据模型
- 目标：明确 job、queue、lease、retry、state
- 模块：`runtime` `platform` `infra`
- 风险：高
- 依赖：Phase 4 完成
- 完成标准：
  - scheduler 数据模型冻结
  - 状态语义明确
  - 具备可复用的 job / lease / retry 基线

## PH5-PR-5.2
- Status: Done
- Tracking ID: PH5-PR-5.2
- Owner: Platform Owner
- ETA: 2 days
- 标题：引入异步执行入口
- 目标：从同步执行扩展到异步 job
- 模块：`server` `runtime` `platform`
- 风险：高
- 依赖：PH5-PR-5.1
- 完成标准：
  - 可创建异步 job
  - job 状态可查询
  - API 支持 async_mode 入口

## PH5-PR-5.3
- Status: Done
- Tracking ID: PH5-PR-5.3
- Owner: Runtime Owner
- ETA: 3 days
- 标题：持久化 checkpoint 与 resume 流程
- 目标：支持恢复执行
- 模块：checkpoint `runtime` `platform`
- 风险：高
- 依赖：PH5-PR-5.2
- 完成标准：
  - 关键状态可持久化
  - 可从中断点 resume
  - checkpoint thread id 可追踪

## PH5-PR-5.4
- Status: Done
- Tracking ID: PH5-PR-5.4
- Owner: Infra Owner
- ETA: 3 days
- 标题：Worker 执行面与控制面分离
- 目标：为分布式执行打基础
- 模块：`server` `runtime` `infra`
- 风险：高
- 依赖：PH5-PR-5.3
- 完成标准：
  - 控制面与执行面职责分开
  - worker 可独立消费任务

## PH5-PR-5.5
- Status: Done
- Tracking ID: PH5-PR-5.5
- Owner: Runtime Owner
- ETA: 2 days
- 标题：重试、幂等与并发控制
- 目标：提升运行稳定性
- 模块：`runtime` `platform` `audit`
- 风险：中
- 依赖：PH5-PR-5.4
- 完成标准：
  - retry 语义明确，失败任务可按策略回写 queued
  - 幂等与重复执行可控制，重复提交返回同一请求
  - worker 并发与租户容量约束可观测
  - next_retry_at / retry_count / max_retries 全链路可追踪
