# PAGE_ELEMENT_POSITION — sales / sales-order

> 从 SalesOrderPage.py + TECH_ANALYSIS 提取 | 2026-06-11

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 销售单号 | XPATH | `//input[@placeholder='销售单号']` | A | |
| 客户名称 | XPATH | `//input[@placeholder='客户名称']` | A | |
| 产品类型 | XPATH | `//div[contains(@class,'el-select')][.//input[@placeholder='产品类型']]` | B | |
| 开始日期 | XPATH | date-range-picker start | B | |
| 结束日期 | XPATH | date-range-picker end | B | |
| 查询 | XPATH | `//button[.//span[text()='查询']]` | A | |
| 重置 | XPATH | `//button[.//span[text()='重置']]` | A | |
| 新增销售 | XPATH | `//button[.//span[text()='新增销售']]` | A | |
| 单号(链接) | XPATH | `td:nth-child(1) .el-button` | B | 可点击 |
| 详情 | XPATH | `.//button[.//span[text()='详情']]` | A | |

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
