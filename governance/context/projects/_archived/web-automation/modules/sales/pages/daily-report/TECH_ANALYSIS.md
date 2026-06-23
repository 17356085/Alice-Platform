# TECH_ANALYSIS — sales / daily-report

> 基于 DailyReportPage.py 已有代码反向提取 | 2026-06-12
> 页面路由: `#/sales/measurement` | PO: `page/sales_page/DailyReportPage.py` (41KB)
> 页面性质：**只读页面**，无弹窗CRUD

## 分析对象
- 模块：sales（销仓管理）
- 页面：销售日报表
- PO 规模：41KB，重点在汇总指标提取 + 明细表格数据校验 + 浮点精度处理

## Element Plus 组件识别

| 组件类型 | 用途 | 定位特点 |
|----------|------|----------|
| el-form--inline | 搜索区 | 日期选择器 + 产品下拉 + 查询/重置/导出按钮 |
| el-date-picker (daterange) | 日期范围选择 | placeholder含"开始日期"/"结束日期" |
| el-select | 产品筛选 | ⚠️ filterable + Teleport |
| el-statistic / 自定义卡片 | 汇总指标区 | 非BEM命名，CSS fallback 定位 |
| el-table | 明细表格 | 多列数据 |
| el-pagination | 分页器 | 标准 |
| el-button | 查询/重置/导出 | 导出按钮特殊处理（触发浏览器下载） |

## 定位器设计表（从 DailyReportPage.py 提取）

### 搜索区

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 开始日期 | CSS | `input[placeholder*="开始日期"], .el-date-editor input[placeholder*="开始"]` | B | 多选择器 fallback |
| 结束日期 | CSS | `input[placeholder*="结束日期"], .el-date-editor input[placeholder*="结束"]` | B | 多选择器 fallback |
| 日期范围选择器 | CSS | `.el-date-editor--daterange, .el-date-range-picker` | B | |
| 查询按钮(CSS) | CSS | `.search-form .el-button--primary, .el-form .el-button--primary` | B | 上下文限定 |
| 查询按钮(XPath) | XPATH | `//button[contains(@class,"el-button--primary")]//span[contains(normalize-space(.),"查询")]/parent::button` | A | 文本保底 |
| 重置按钮(CSS) | CSS | `.search-form .el-button--default, .el-form .el-button:not(.el-button--primary)` | B | |
| 重置按钮(XPath) | XPATH | `//button[contains(@class,"el-button")]//span[contains(normalize-space(.),"重置")]/parent::button` | A | 文本保底 |

### 汇总指标区

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 汇总卡片容器 | CSS | `.summary-wrapper, .stat-cards, .el-row.stat-row, .report-summary, [class*="stat-card"]` | B | 多选择器fallback，非BEM |
| 指标卡片项 | CSS | `.stat-card, .stat-item, .el-statistic, [class*="statistic-item"]` | B | 非BEM |
| 指标标签 | CSS | `.stat-card__label, .stat-item__label, .el-statistic__head` | B | 多命名风格 |
| 指标值 | CSS | `.stat-card__value, .stat-item__value, .el-statistic__content` | B | 核心断言目标 |

### 表格区

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 表格容器 | CSS | `.el-table` | A | |
| 表格行 | CSS | `.el-table__body-wrapper .el-table__row` | B | |
| 空数据 | CSS | `.el-table__empty-block` | B | |

### 分页区

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 分页器 | CSS | `.el-pagination` | A | |
| 总条数 | CSS | `.el-pagination__total` | B | |

## 已知技术难题

| 问题 | 影响 | 当前处理 |
|------|------|----------|
| 汇总卡片非BEM命名 | CSS定位不可靠，不同项目可能用不同class | 多选择器CSS fallback链（`.summary-wrapper, .stat-cards, ...`） |
| 浮点精度 | 汇总与明细求和可能有0.0001差异 | round(x, 4) 统一精度后比较 |
| el-date-picker range Teleport | 日期面板在body层渲染 | WebDriverWait for `.el-picker-panel` |
| time.sleep 存在于DailyReportPage.py | 违反代码红线 #3 | 需替换为 `wait_vue_stable()` / `WebDriverWait` |

## 异步等待策略

| 场景 | 等待条件 | 实现 |
|------|----------|------|
| 页面加载 | JS hash + 汇总卡片出现 | `driver.get(BASE_URL + "#/sales/measurement")` + `wait.until` for stat cards |
| 查询完成 | loading 消失 + 汇总刷新 | `wait_loading_disappear()` + 汇总值变化检测 |
| 日期面板打开 | el-picker-panel body层可见 | `WebDriverWait` for `.el-picker-panel` |
| 分页翻页 | 表格行更新 | `wait_loading_disappear()` |

## 自动化代码映射

- Page Object：`page/sales_page/DailyReportPage.py`（41KB，多选择器 fallback）
- 测试脚本：`test_daily_report.py` + `test_daily_report_display.py` + `test_daily_report_search.py` + `test_daily_report_pagination.py` + `test_daily_report_boundary.py` + `test_daily_report_data_integrity.py`（6文件，覆盖最广）
- conftest：`script/sales/conftest.py`

## ⚠️ 代码红线问题

| 违规项 | 位置 | 严重度 | 整改建议 |
|--------|------|--------|----------|
| `time.sleep` 硬等待 | DailyReportPage.py L22 | 🔴 #3 | 替换为 `WebDriverWait` / `wait_vue_stable()` |
| `print()` 调试输出 | test_daily_report.py L42-58 | 🔴 #4 | 替换为 `logger.info()` |

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 | next_phase: Phase 3.5 | next_agent: automation-agent -->
