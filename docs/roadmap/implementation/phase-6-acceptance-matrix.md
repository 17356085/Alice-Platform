# Phase 6 Acceptance Matrix

| Tracking ID | Status | ETA | 核心测试项 | 负责人 | Reviewer | 回滚点 |
|---|---|---|---|---|---|---|
| PH6-PR-6.1 | Done | 2 days | 指标采集测试、主链路 metrics smoke、指标缺失降级测试 | Audit Reviewer | TL, Runtime Owner | 回退 metrics 接线 |
| PH6-PR-6.2 | Done | 2 days | trace 关联测试、跨进程事件关联测试、replay 关联一致性测试 | Audit Reviewer | Infra Owner, TL | 回退 trace/id 体系 |
| PH6-PR-6.3 | Done | 2 days | 性能压测、回归基线对比、热点路径 profiling 检查 | Runtime Owner | TL, QA Reviewer | 回退单批性能优化 PR |
| PH6-PR-6.4 | Done | 3 days | worker 崩溃恢复测试、超时恢复测试、重复执行保护测试 | Infra Owner | Runtime Owner, QA Reviewer | 回退 HA/恢复策略改动 |
| PH6-PR-6.5 | Done | 2 days | 扩展控制面 smoke、版本兼容检查、CLI/UI 可见性测试 | Platform Owner | Governance Owner, Frontend Reviewer | 回退运营控制面功能 |
