# RISK_MODEL — lab / gas-analysis-report

> 6维度风险识别 | 2026-06-11 | 基于 PAGE_CONTEXT.md + 代码分析

| # | 风险 | 维度 | 等级 | 触发条件 | 缓解措施 |
|:--:|------|------|:--:|----------|----------|
| R1 | 取样位置Tab非标准组件，22个点位硬编码列表可能过期 | 功能 | P1 | 新增/删除点位后列表不更新 | `get_all_location_names()` 兜底遍历已知列表 + 定期同步 |
| R2 | 多行表头（19列复杂结构），`get_table_headers` 取最后一行可能遗漏 | 数据 | P1 | 表头结构调整 | 6次重试 + 取`thead tr:last-child` |
| R3 | 导出按钮无确认弹窗时返回True但实际未触发 | 功能 | P2 | 导出逻辑变更 | 增加Toast文案多关键词匹配 |
| R4 | 取样位置切换后表格异步加载，快速连续点击可能冲突 | 稳定性 | P1 | 连续快速切换 | `_wait_table_ready()` 15s超时 + thead轮询 |
| R5 | 新增报告单弹窗多弹窗共存（El-Plus已知坑EP-011） | 兼容性 | P2 | 未关闭弹窗再次打开 | `:not([style*="display:none"])` 排除隐藏弹窗 |
| R6 | 统计行`is_displayed()`检测在`El-Plus 2.x`下可能失效 | 兼容性 | P2 | 统计行Teleport渲染 | 双策略：el-table footer + 标准tfoot |
