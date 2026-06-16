# PAGE_ELEMENT_POSITION — personnel / course

> 从 TECH_ANALYSIS + CourseManagePage.py (570行) 提取 | 2026-06-11

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 搜索-名称 | XPATH | 课程名称输入框 | B |
| 搜索-分类下拉 | XPATH | `//div[contains(@class,'el-select')][1]` | B |
| 搜索-素材类型下拉 | XPATH | `//div[contains(@class,'el-select')][2]` | B |
| 搜索-发布状态下拉 | XPATH | `//div[contains(@class,'el-select')][3]` | B |
| 搜索按钮 | XPATH | `//button[.//span[text()='查询' or text()='搜索']]` | A |
| 重置按钮 | XPATH | `//button[.//span[text()='重置']]` | A |
| 新增课程 | XPATH | 含"新增"文字的 el-button | B |
| 课程卡片-查看 | XPATH | 课程卡片查看按钮 | B |
| 表格行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | A |

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
