# RISK_MODEL — lab / gas-indicator + water-indicator

> Phase 1.5 | 2026-06-12 | 覆盖 gas-indicator & water-indicator

| 风险ID | 维度 | 描述 | 影响 | 等级 | 缓解 |
|--------|------|------|------|:--:|------|
| RISK-LI-B01 | 业务 | 设计指标值与实际标准不一致 | 判断基准错误 | P1 | 定期与标准文档核对 |
| RISK-LI-D01 | 数据 | 指标值被误修改(如页面含编辑功能) | 参考数据损坏 | P0 | 编辑权限控制+审计日志 |
| RISK-LI-U01 | UI/UX | 22-23行全部渲染无分页，数据多时性能 | 页面加载慢 | P2 | 前端虚拟滚动(如需) |