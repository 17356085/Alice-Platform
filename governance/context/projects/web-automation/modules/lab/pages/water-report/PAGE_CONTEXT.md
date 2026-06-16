# PAGE_CONTEXT — lab / water-report

> Phase 1 | 2026-06-12 | Selenium | 模板: gas-analysis-report

## 页面信息
- 页面ID: water-report | 页面名称: 水质分析报告单
- 路由: #/lab/water/report | 菜单: 化验室取样→水质分析→水质分析报告单
- UI: Element Plus + 自定义 report-table

## 页面职责
展示水质分析报告单，支持取样位置切换、日期筛选、新增/导出。

## 核心元素

### 搜索区
| 元素 | 控件 | 定位 |
|------|------|------|
| 开始日期 | el-date-picker | placeholder=开始日期 |
| 结束日期 | el-date-picker | placeholder=结束日期 |
| 下拉筛选 | el-select | |
| 查询/重置/新增/导出 | el-button | |

### 表格
自定义 report-table（非el-table），多行表头。

### 新增弹窗
检验员* / 复核员* / 日期 / 取样时间 / 取样位置 / 水质指标 / 保存/取消

## 与气体分析报告单差异
- 指标：水质指标(pH/COD/氨氮/...) vs 气体组分(13项)
- 取样位置：水质取样点 vs 22个气体取样点
