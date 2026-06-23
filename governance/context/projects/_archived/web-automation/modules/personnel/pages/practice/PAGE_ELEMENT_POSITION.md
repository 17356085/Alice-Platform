# PAGE_ELEMENT_POSITION — personnel / practice

> 从 Selenium 实机分析提取（含真实数据 20 条） | 2026-06-12

## 筛选区

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 筛选状态下拉 | XPATH | `//div[contains(@class,"el-select")][.//span[normalize-space(.)="筛选状态"]]` | B |
| 筛选状态下拉(备) | CSS | `.el-select` (页面唯一的筛选下拉) | B |

## 表格（9 列，真实列名）

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 表格容器 | CSS | `.el-table` | A |
| 表头-序号 | CSS | `.el-table th:nth-child(1)` | A |
| 表头-练习类型 | CSS | `.el-table th:nth-child(2)` | A |
| 表头-练习名称 | CSS | `.el-table th:nth-child(3)` | A |
| 表头-开始时间 | CSS | `.el-table th:nth-child(4)` | A |
| 表头-用时 | CSS | `.el-table th:nth-child(5)` | A |
| 表头-正确率 | CSS | `.el-table th:nth-child(6)` | A |
| 表头-得分 | CSS | `.el-table th:nth-child(7)` | A |
| 表头-状态 | CSS | `.el-table th:nth-child(8)` | A |
| 表头-操作 | CSS | `.el-table th:nth-child(9)` | A |
| 数据行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | A |
| 空状态 | CSS | `.el-empty` | B |

## 行内操作按钮（按练习名称定位行）

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 已完成-开始练习 | XPATH | `//tr[.//td[contains(.,"{name}")]]//button[contains(.,"开始练习")]` | A |
| 未完成-继续练习 | XPATH | `//tr[.//td[contains(.,"{name}")]]//button[contains(.,"继续练习")]` | A |
| 查看成绩 | XPATH | `//tr[.//td[contains(.,"{name}")]]//button[contains(.,"查看成绩")]` | A |
| 删除 | XPATH | `//tr[.//td[contains(.,"{name}")]]//button[contains(.,"删除")]` | A |

## 删除确认弹窗

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 确认框 | CSS | `.el-message-box:not([style*="display: none"])` | A |
| 确定按钮 | XPATH | `//div[contains(@class,"el-message-box")]//button[.//span[normalize-space(.)="确定"]]` | A |
| 取消按钮 | XPATH | `//div[contains(@class,"el-message-box")]//button[.//span[normalize-space(.)="取消"]]` | A |

## 分页

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 分页容器 | CSS | `.el-pagination` | A |
| 总数 | CSS | `.el-pagination__total` | B |
| 每页条数 | CSS | `.el-pagination__sizes .el-select` | B |

<!-- status: confirmed | completed_by: ai-assistant | completed_at: 2026-06-12 -->
