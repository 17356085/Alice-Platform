# PAGE_ELEMENT_POSITION — personnel / study-record

> 从 Selenium 实机分析提取（含真实数据 9 条） | 2026-06-12
> ⚠️ 此页面以 admin 视角显示全员学习记录（非纯个人端）

## 筛选区

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 学员名称输入 | CSS | `input[placeholder*="请输入学员名称"]` | A |
| 课程名称输入 | CSS | `input[placeholder*="请输入课程名称"]` | A |
| 是否完成下拉 | XPATH | `//label[contains(.,"是否完成")]/following::div[contains(@class,"el-select")][1]` | B |
| 查询按钮 | XPATH | `//button[.//span[normalize-space(.)="查询"]]` | A |
| 重置按钮 | XPATH | `//button[.//span[normalize-space(.)="重置"]]` | A |

## 表格（9 列，含隐藏表头列）

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 表格容器 | CSS | `.el-table` | A |
| 表头-学员名称 | CSS | `.el-table th:nth-child(1)` | A |
| 表头-课程名称 | CSS | `.el-table th:nth-child(2)` | A |
| 表头-培训计划 | CSS | `.el-table th:nth-child(3)` | A |
| 表头-学习时长 | CSS | `.el-table th:nth-child(4)` | A |
| 表头-学习进度 | CSS | `.el-table th:nth-child(5)` | A |
| 列-状态 | CSS | `.el-table td:nth-child(6)` | B |
| 列-开始时间 | CSS | `.el-table td:nth-child(7)` | B |
| 列-结束时间 | CSS | `.el-table td:nth-child(8)` | B |
| 列-其他 | CSS | `.el-table td:nth-child(9)` | B |
| 数据行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | A |
| 空状态 | CSS | `.el-empty` | B |

> ⚠️ 列 6-9 的表头可能在 DOM 中未渲染或使用不同 class，定位器使用 `td:nth-child` 作为备选。
> ⚠️ 当前所有行第 9 列值为 "-"，该列用途待确认。

## 行内操作

当前无行内操作按钮（所有行最后一列为"-"）。若有点击课程名称跳转的行为，定位策略：

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 课程名称链接 | XPATH | `//tr[.//td[contains(.,"{course_name}")]]//td[2]` | B |

## 分页

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 分页容器 | CSS | `.el-pagination` | A |
| 总数 | CSS | `.el-pagination__total` | B |

<!-- status: confirmed | completed_by: ai-assistant | completed_at: 2026-06-12 -->
