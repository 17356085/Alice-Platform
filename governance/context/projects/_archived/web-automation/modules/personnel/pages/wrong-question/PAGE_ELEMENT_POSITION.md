# PAGE_ELEMENT_POSITION — personnel / wrong-question

> 从 Selenium 实机分析提取 | 2026-06-12
> 注意：侧边栏菜单名称为"错题集"，路由/页面名称为 wrong-question / 错题本

## 筛选区（8 个 el-form-item + 8 个 el-select — 最复杂）

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 查询按钮 | XPATH | `//button[.//span[normalize-space(.)="查询"]]` | A |
| 重置按钮 | XPATH | `//button[.//span[normalize-space(.)="重置"]]` | A |
| 筛选-课程 | XPATH | `//label[contains(.,"课程")]/following::div[contains(@class,"el-select")][1]` | B |
| 筛选-题型 | XPATH | `//label[contains(.,"题型")]/following::div[contains(@class,"el-select")][1]` | B |
| 筛选-来源 | XPATH | `//label[contains(.,"考试")]/following::div[contains(@class,"el-select")][1]` | B |
| 筛选-其他(5项) | XPATH | `//div[contains(@class,"search")]//div[contains(@class,"el-select")]` | B |
| 关键词搜索 | CSS | `input[placeholder*="搜索"]` | B |

## 表格

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 表格容器 | CSS | `.el-table` | A |
| 表头行 | CSS | `.el-table__header-wrapper th` | A |
| 数据行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | A |
| 空状态 | CSS | `.el-empty` | B |
| 行内-重新作答 | XPATH | `//tr[.//td[contains(.,"{question_text}")]]//button[contains(.,"作答") or contains(.,"重做")]` | B |
| 行内-查看解析 | XPATH | `//tr[.//td[contains(.,"{question_text}")]]//button[contains(.,"解析") or contains(.,"查看")]` | B |

## 重新作答弹窗

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 弹窗标题 | CSS | `.el-dialog:not([style*="display: none"]) .el-dialog__title` | A |
| 题目展示区 | CSS | `.el-dialog .question-content, .el-dialog [class*='question']` | B |
| 选项区 | CSS | `.el-dialog .el-radio, .el-dialog .el-checkbox` | B |
| 提交答案 | XPATH | `//div[contains(@class,"el-dialog")]//button[contains(.,"提交") or contains(.,"确定")]` | B |
| 关闭弹窗 | CSS | `.el-dialog__headerbtn` | B |

## 分页

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 分页容器 | CSS | `.el-pagination` | A |
| 总数 | CSS | `.el-pagination__total` | B |

> ⚠️ 检测到 3 个 el-pagination（可能错题列表 + 答题弹窗内分页 + 解析页分页），需录入错题数据后确认。
> ⚠️ 8 个 el-form-item 为三个未测试页面中筛选最复杂的，具体 label/维度需录入数据后提取确认。

<!-- status: scaffold | completed_by: ai-assistant | completed_at: 2026-06-12 -->
