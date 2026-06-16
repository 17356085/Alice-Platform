# PAGE_ELEMENT_POSITION — personnel / employee

> 从 TECH_ANALYSIS + EmployeeManagePage.py 提取 | 2026-06-11

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 页面标题 | XPATH | `//h2[contains(text(),'员工') or contains(text(),'人员')]` | A |
| 搜索-姓名/工号 | XPATH | `//input[contains(@placeholder,'姓名') or contains(@placeholder,'工号')]` | A |
| 搜索-部门 | XPATH | `//input[contains(@placeholder,'搜索部门')]` | A |
| 表格行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | A |
| 表头 | XPATH | `//div[contains(@class,'el-table__header-wrapper')]//th//div[contains(@class,'cell')]` | A |
| 总条数 | CSS | `.el-pagination__total` | A |
| 下一页 | CSS | `.el-pagination .btn-next` | A |
| 上一页 | CSS | `.el-pagination .btn-prev` | A |
| 搜索按钮 | XPATH | `//button[.//span[contains(.,'查询') or contains(.,'搜索')]]` | A |
| 重置按钮 | XPATH | `//button[.//span[contains(.,'重置')]]` | A |

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
