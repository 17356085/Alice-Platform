# PAGE_ELEMENT_POSITION — sales / contract

> 从 ContractPage.py + TECH_ANALYSIS 提取 | 2026-06-11

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 合同编号搜索 | XPATH | `//input[@placeholder='合同编号']` | A | |
| 客户名称搜索 | XPATH | `//input[@placeholder='客户名称']` | A | |
| 产品类型下拉 | XPATH | `//div[contains(@class,'el-select')][.//input[@placeholder='产品类型']]` | B | |
| 有效期起 | XPATH | date-picker range start | B | |
| 有效期止 | XPATH | date-picker range end | B | |
| 合同状态下拉 | XPATH | `//div[contains(@class,'el-select')][.//input[@placeholder='合同状态']]` | B | |
| 查询 | XPATH | `//button[.//span[text()='查询']]` | A | |
| 重置 | XPATH | `//button[.//span[text()='重置']]` | A | |
| 新增合同 | XPATH | `//button[.//span[text()='新增合同']]` | A | |
| 进度条 | CSS | `.el-progress` (含3s CSS动画) | B | ⚠️ 等待动画完成 |
| 状态tag | CSS | `el-tag--danger=已终止, el-tag--success=已完成` | B | |
| 详情 | XPATH | `.//button[.//span[text()='详情']]` | A | per-row |
| 销售订单 | XPATH | `.//button[.//span[text()='销售订单']]` | A | per-row |

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
