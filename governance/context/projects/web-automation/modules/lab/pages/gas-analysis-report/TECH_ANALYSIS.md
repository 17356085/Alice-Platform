# TECH_ANALYSIS — lab / gas-analysis-report

> 基于 GasAnalysisReportPage.py 逆向分析 | 2026-06-11

## Element Plus 组件识别
| 组件 | 用途 | 定位特点 |
|------|------|----------|
| 自定义Tab | 取样位置切换 | ⚠️ 非el-tabs，蓝色下划线标识选中，XPATH文本匹配 |
| el-date-picker | 日期筛选 | placeholder匹配，标准 |
| el-button | 查询/重置/新增/导出 | CSS+XPATH双降级 |
| el-table | 数据表格 | 兼容标准table，19列复杂表头 |
| el-dialog | 新增报告单 | 标准el-dialog，"保存报告"自定义文字 |
| el-input-number | 气体组分值 | 13项气体指标 |

## 定位器设计表（关键风险点）
| 元素 | 策略 | 定位值 | 稳定性 |
|------|------|--------|:--:|
| 取样位置Tab | XPATH | `//*[contains(normalize-space(.),"{text}")]` | B |
| 激活Tab | CSS | `.el-tabs__item.is-active, [class*="tab"][class*="active"]` | B |
| 日期输入 | CSS | `input[placeholder*="开始/结束日期"]` | A |
| 查询按钮 | CSS→XPATH降级 | `.el-button--primary` → 文本"查询" | A |
| 导出按钮 | CSS→XPATH→JS降级 | 三级降级确保成功率 | A |
| 表头提取 | JS | `querySelectorAll('thead th')` + 6次重试 | A |
| 统计行 | CSS | `tfoot tr, .el-table__footer-wrapper tr` | B |

## 等待策略
| 场景 | 策略 | 超时 |
|------|------|:--:|
| 页面导航 | JS hash路由 `_navigate_by_js_hash` | — |
| 表格加载 | `_wait_table_ready()` — JS轮询thead th | 15s |
| 弹窗打开 | `wait_dialog_open()` | 默认 |
| 弹窗保存 | `click_dialog_save()` → `wait_for_toast_text()` | 6s |
| 标签切换 | `click_location_tab()` → `_wait_table_ready()` | 15s |

## 已知坑位关联
- **EP-011**：多弹窗共存 → 定位器`not(contains(@style,'display:none'))`
- **FP-002**：get_table_headers 6次重试 + JS提取
- **UI-001**：自定义Tab非标准el-tabs → XPATH文本匹配保底
