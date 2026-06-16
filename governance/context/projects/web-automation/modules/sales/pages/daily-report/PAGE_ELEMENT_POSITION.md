# PAGE_ELEMENT_POSITION — sales / daily-report

> 从 DailyReportPage.py + TECH_ANALYSIS 提取 | 2026-06-11

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 日期起 | XPATH | date-range-picker start input | B | |
| 日期止 | XPATH | date-range-picker end input | B | |
| 查询 | XPATH | `//button[.//span[text()='查询']]` | A | |
| 导出 | XPATH | `//button[.//span[text()='导出']]` | B | |
| 汇总卡片 | CSS | `.summary-card .stat-value` | B | |
| 明细表格 | CSS | `.el-table` | A | |

## 断言策略: 汇总指标与明细合计一致性(浮点数容差0.01)

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
