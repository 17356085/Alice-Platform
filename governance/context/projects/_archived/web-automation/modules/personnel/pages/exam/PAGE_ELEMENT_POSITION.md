# PAGE_ELEMENT_POSITION — personnel / exam

> 从 TECH_ANALYSIS + ExamManagePage.py (856行) 提取 | 2026-06-11

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 搜索-名称 | XPATH | `//input[contains(@placeholder,'考试名称')]` | A |
| 搜索-状态下拉 | XPATH | `//div[contains(@class,'el-select')][.//label[contains(.,'状态')]]` | B |
| 搜索-发布状态下拉 | XPATH | `//div[contains(@class,'el-select')][.//label[contains(.,'发布状态')]]` | B |
| 搜索-日期 | XPATH | `//input[contains(@placeholder,'开始日期') or contains(@placeholder,'结束日期')]` | A |
| 搜索按钮 | XPATH | `//button[.//span[contains(text(),'查询') or contains(text(),'搜索')]]` | A |
| 重置按钮 | XPATH | `//button[.//span[contains(text(),'重置')]]` | A |
| 表格行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | A |
| 阅卷区 | XPATH | 考生答卷区 + 评分表单 | B |

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
