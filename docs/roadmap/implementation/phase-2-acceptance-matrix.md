# Phase 2 Acceptance Matrix

| Tracking ID | Status | ETA | 核心测试项 | 负责人 | Reviewer | 回滚点 |
|---|---|---|---|---|---|---|
| PH2-PR-2.1 | Done | 2 days | capability 匹配测试、无匹配降级测试 | Platform Owner | TL, QA Reviewer | 回退 capability 接线 |
| PH2-PR-2.2 | Done | 2 days | tool 注册测试、tool 调用集成测试、错误返回测试 | Runtime Owner | Platform Owner, QA Reviewer | 回退 tool calling 契约层 |
| PH2-PR-2.3 | Done | 2 days | MCP 建连测试、工具目录读取测试、生命周期回归 | MCP Owner | Runtime Owner, QA Reviewer | 回退 MCP 生命周期改造 |
| PH2-PR-2.4 | Done | 2 days | memory 查询测试、context 注入测试、空 memory 降级测试 | Memory Owner | TL, QA Reviewer | 回退 memory 接线 |
| PH2-PR-2.5 | Done | 2 days | knowledge 检索测试、context 组装测试、检索失败降级测试 | Knowledge Owner | Governance Owner, QA Reviewer | 回退 knowledge 上下文接线 |
| PH2-PR-2.6 | Done | 2 days | replay 录制测试、回放测试、事件一致性测试 | Replay Owner | Audit Reviewer, TL | 回退 replay 主链路挂钩 |
