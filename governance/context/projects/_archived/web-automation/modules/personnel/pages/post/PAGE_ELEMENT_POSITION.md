# PAGE_ELEMENT_POSITION — personnel / post

> 从 TECH_ANALYSIS + PostManagePage.py (542行) 提取 | 2026-06-11

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 搜索-名称/编码 | XPATH | `//input[@placeholder='请输入岗位编码或名称']` | A |
| 搜索-部门下拉 | XPATH | `//div[contains(@class,'search-bar')]//div[contains(@class,'el-select')][1]` | B |
| 搜索-分类下拉 | XPATH | `//div[contains(@class,'search-bar')]//div[contains(@class,'el-select')][2]` | B |
| 搜索-状态下拉 | XPATH | `//div[contains(@class,'search-bar')]//div[contains(@class,'el-select')][3]` | B |
| 搜索按钮 | XPATH | `//button[.//span[contains(text(),'查询') or contains(text(),'搜索')]]` | A |
| 重置按钮 | XPATH | `//button[.//span[contains(text(),'重置')]]` | A |
| 新增按钮 | XPATH | `//button[contains(@class,'el-button--primary') and contains(.,'新增')]` | A |
| 表格行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | A |

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
