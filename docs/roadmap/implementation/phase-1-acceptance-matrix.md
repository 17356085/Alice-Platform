# Phase 1 Acceptance Matrix

| Tracking ID | Status | ETA | 核心测试项 | 负责人 | Reviewer | 回滚点 |
|---|---|---|---|---|---|---|
| PH1-PR-1.1 | Done | 1 day | 架构文档评审、主链路走查、兼容层标记检查 | TL | Runtime Owner, Platform Owner | 直接回退文档变更 |
| PH1-PR-1.2 | Done | 1 day | context/result 占位结构检查、主路径 smoke | Runtime Owner | TL, QA Reviewer | 回退契约占位文件 |
| PH1-PR-2.1 | Done | 2 days | context 单测、字段完整性检查 | Runtime Owner | TL | 回退 context 模型定义 |
| PH1-PR-2.2 | Done | 1 day | Server context 注入测试、CLI context 注入测试、启动 smoke | Platform Owner | Runtime Owner, QA Reviewer | 回退入口适配层变更 |
| PH1-PR-2.3 | Done | 2 days | 执行器消费 context 集成测试、回归 smoke | Runtime Owner | TL, QA Reviewer | 回退 executor/workflow 变更 |
| PH1-PR-3.1 | Done | 2 days | result 结构单测、错误模型测试 | Runtime Owner | TL, Audit Reviewer | 回退 result 模型 |
| PH1-PR-3.2 | Done | 1 day | SSE 结果一致性、CLI 输出一致性、兼容字段回归 | Platform Owner | Frontend Reviewer, QA Reviewer | 回退 API/CLI 输出适配 |
| PH1-PR-3.3 | Done | 1 day | 生命周期枚举测试、状态映射测试 | Runtime Owner | TL, QA Reviewer | 回退状态枚举与映射 |
| PH1-PR-4.1 | Done | 1 day | cancel/abort/stop 行为测试、并发中止 smoke | Runtime Owner | TL, QA Reviewer | 回退控制接口与调用点 |
| PH1-PR-4.2 | Done | 2 days | 跨层访问消除回归、隐藏依赖扫描 | Platform Owner | TL | 回退封装层与调用重定向 |
| PH1-PR-5.1 | Done | 2 days | graph 执行集成测试、编排职责回归 | Graph Owner | Runtime Owner, QA Reviewer | 回退 graph 侧职责调整 |
| PH1-PR-5.2 | Done | 2 days | runtime 状态推进测试、异常路径测试 | Runtime Owner | TL, QA Reviewer | 回退 state/runtime 改动 |
| PH1-PR-5.3 | Done | 2 days | engine 调度测试、主链路集成测试 | Runtime Owner | TL, Platform Owner | 回退 engine 调度收口 |
| PH1-PR-6.1 | Done | 2 days | 状态 source of truth 测试、状态一致性检查 | Platform Owner | Runtime Owner, Audit Reviewer | 回退状态主来源切换 |
| PH1-PR-6.2 | Done | 1 day | 多入口统一执行测试、adapter 边界检查 | Platform Owner | TL, QA Reviewer | 回退入口适配化变更 |
| PH1-PR-6.3 | Done | 1 day | Phase 1 全量回归、文档与基线检查 | TL | 全体模块 Reviewer | 回退收口 PR，保留已验证子 PR |
