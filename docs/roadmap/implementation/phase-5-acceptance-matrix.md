# Phase 5 Acceptance Matrix

| Tracking ID | Status | ETA | 核心测试项 | 负责人 | Reviewer | 回滚点 |
|---|---|---|---|---|---|---|
| PH5-PR-5.1 | Done | 2 days | scheduler 模型单测、状态枚举测试 | Runtime Owner | TL, Infra Owner | 回退 scheduler 数据模型 |
| PH5-PR-5.2 | Done | 2 days | 异步 job 创建测试、job 查询测试、同步兼容回归 | Platform Owner | Runtime Owner, QA Reviewer | 回退异步执行入口 |
| PH5-PR-5.3 | Done | 3 days | checkpoint 持久化测试、resume 测试、中断恢复测试 | Runtime Owner | QA Reviewer, TL | 回退 checkpoint/resume 接线 |
| PH5-PR-5.4 | Done | 3 days | worker 消费测试、控制面/执行面边界测试 | Infra Owner | Runtime Owner, TL | 回退 worker 分离 |
| PH5-PR-5.5 | Done | 2 days | retry 测试、幂等测试、并发控制测试、请求去重测试、worker 回退测试 | Runtime Owner | Audit Reviewer, QA Reviewer | 回退 retry/幂等策略 |
