# Phase 5 Regression Checklist

这份清单用于回归 PH5-PR-5.1 ~ PH5-PR-5.5 的完整链路，重点覆盖：

- Scheduler / Request / Run 的状态语义
- Async 提交与 worker 消费
- checkpoint / resume
- worker 控制面与执行面分离
- retry / idempotency / concurrency control

## 1. 请求生命周期

- [ ] `ExecutionRequest` 默认字段兼容旧数据
- [ ] `queue()` 只允许 `created -> queued`
- [ ] `dispatch()` 会写入 `run_id`
- [ ] `complete()` / `fail()` / `cancel()` 会清理 `next_retry_at`
- [ ] `schedule_retry()` 会增加 `retry_count`
- [ ] `schedule_retry()` 会把状态回写为 `queued`
- [ ] `schedule_retry()` 会生成未来的 `next_retry_at`

## 2. 持久化与回放

- [ ] `execution_requests` 表能正确保存 `agent`
- [ ] `execution_requests` 表能正确保存 `idempotency_key`
- [ ] `execution_requests` 表能正确保存 `next_retry_at`
- [ ] 老数据库可通过 best-effort migration 兼容新字段
- [ ] `RunStore.load_request()` 能反序列化新字段
- [ ] `RunStore.save_request()` 的插入/更新列数一致
- [ ] `claim_next_request()` 只领取可执行请求
- [ ] `claim_next_request()` 会跳过未到期的 retry 请求

## 3. 幂等语义

- [ ] 相同 `idempotency_key` 的重复提交返回同一 `request_id`
- [ ] 幂等查询会受 `workspace_id` / `org_id` 限定
- [ ] terminal 请求再次提交不会生成新 request
- [ ] async submit 与 sync execute 行为保持一致

## 4. Retry 语义

- [ ] 可重试错误会触发 backoff
- [ ] 非可重试错误不会重排到 queued
- [ ] `retry_count` 不超过 `max_retries`
- [ ] retry 后请求不会被过早领取
- [ ] worker 失败重试与 service 失败重试一致

## 5. Worker / 并发控制

- [ ] worker 只消费 `queued` 请求
- [ ] worker 启动前后状态可见
- [ ] tenant capacity 超限时不会误标记为业务失败
- [ ] worker 的 `retried` / `throttled` 统计可观测
- [ ] worker 异常不会破坏 request 持久化

## 6. 可观测性

- [ ] `/metrics` 可返回文本格式指标
- [ ] `/health` 能暴露 execution worker 统计
- [ ] completion / failure 事件包含足够的执行结果信息
- [ ] `MetricsConsumer` 能汇总运行结果
- [ ] `operational_metrics` 能被正常查询

## 7. 回滚检查

- [ ] 回滚 `PH5-PR-5.5` 相关逻辑后，Phase 5 其他 PR 仍可运行
- [ ] 旧数据库不因新增字段失效
- [ ] worker 退回同步执行路径后，控制面仍可正常提交请求
- [ ] 幂等降级时，系统仍以 request_id 为主键可运行

