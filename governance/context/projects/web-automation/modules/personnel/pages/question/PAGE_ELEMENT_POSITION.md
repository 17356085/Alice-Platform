# PAGE_ELEMENT_POSITION — personnel / question

> 从 TECH_ANALYSIS + QuestionBankPage.py (702行) 提取 | 2026-06-11

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 搜索-题干 | XPATH | `//input[contains(@placeholder,'题干')]` | A |
| 搜索-题型下拉 | XPATH | 搜索区 el-select [1] | B |
| 搜索-难度下拉 | XPATH | 搜索区 el-select [2] | B |
| 搜索按钮 | XPATH | `//button[.//span[contains(text(),'查询') or contains(text(),'搜索')]]` | A |
| 重置按钮 | XPATH | `//button[.//span[contains(text(),'重置')]]` | A |
| 新建试题 | XPATH | `//button[.//span[contains(text(),'新建试题') or contains(text(),'新建')]]` | A |
| 导入按钮 | XPATH | `//button[.//span[contains(text(),'导入')]]` | A |
| 批量删除 | XPATH | `//button[.//span[contains(text(),'批量删除')]]` | B |
| 表格行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | A |

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
