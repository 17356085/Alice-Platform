# PAGE_ELEMENT_POSITION — personnel / plan

> 从 TECH_ANALYSIS + TrainPlanPage.py (1528行) 提取 | 2026-06-11

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 搜索-名称 | XPATH | `//input[contains(@placeholder,'计划名称')]` | A |
| 搜索-类型下拉 | XPATH | 搜索区 el-select [1] | B |
| 搜索-状态下拉 | XPATH | 搜索区 el-select [2] | B |
| 搜索-发布下拉 | XPATH | 搜索区 el-select [3] | B |
| 搜索按钮 | XPATH | `//button[.//span[contains(text(),'查询') or contains(text(),'搜索')]]` | A |
| 重置按钮 | XPATH | `//button[.//span[contains(text(),'重置')]]` | A |
| 表格行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | A |

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
