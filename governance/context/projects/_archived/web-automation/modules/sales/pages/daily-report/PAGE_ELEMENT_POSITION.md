# PAGE_ELEMENT_POSITION — sales / daily-report

> 从 DailyReportPage.py 实际定位器提取 | 2026-06-17

## 搜索/日期查询区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 开始日期 | CSS | `input[placeholder*="开始日期"], .el-date-editor input[placeholder*="开始"]` | B | readonly, JS native setter 绕过 |
| 结束日期 | CSS | `input[placeholder*="结束日期"], .el-date-editor input[placeholder*="结束"]` | B | readonly, JS native setter 绕过 |
| 日期范围选择器 | CSS | `.el-date-editor--daterange, .el-date-range-picker` | B | |
| 查询按钮 | CSS | `.search-form .el-button--primary, .el-form .el-button--primary` | B | 多选择器 fallback |
| 查询按钮 | XPATH | `//button[contains(@class,"el-button--primary")]//span[contains(normalize-space(.),"查询")]/parent::button` | A | 文本保底 |
| 重置按钮 | CSS | `.search-form .el-button--default, .el-form .el-button:not(.el-button--primary)` | B | 多选择器 fallback |
| 重置按钮 | XPATH | `//button[contains(@class,"el-button")]//span[contains(normalize-space(.),"重置")]/parent::button` | A | 文本保底 |

> 无产品下拉、无导出按钮。

## 日期输入方式

`_set_datepicker_value(locator, value)`:
1. JS `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set` 绕过 readonly
2. 派发 `input` + `change` + `compositionend` 事件链
3. 触发 Vue v-model 响应

兜底方案 `_set_date_range_via_input(start, end)`: ActionChains Tab 键切换字段 → send_keys 输入。

## 汇总指标区

⚠️ 非标准 CSS 类，定位脆弱。

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 卡片容器 | CSS | `.summary-wrapper, .stat-cards, .el-row.stat-row, .report-summary, [class*="stat-card"]` | C | 多选择器 fallback |
| 卡片项 | CSS | `.stat-card, .stat-item, .el-statistic, [class*="statistic-item"]` | C | |
| 标签 | CSS | `.stat-card__label, .stat-item__label, .el-statistic__head` | C | |
| 数值 | CSS | `.stat-card__value, .stat-item__value, .el-statistic__number` | C | |
| 按文本找标签 | XPATH (模板) | `//div[contains(@class,"stat-card")]//div[contains(@class,"label") and contains(normalize-space(.),"{text}")]` | B | |
| 按标签找数值 | XPATH (模板) | `//div[contains(@class,"stat-card")][.//div[contains(@class,"label") and contains(normalize-space(.),"{text}")]]//div[contains(@class,"value")]` | B | |

`get_summary_metrics()` 两套提取逻辑: CSS 定位优先 + 兜底遍历卡片容器文本。

## 明细表格区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 表头 | CSS | `.el-table__header-wrapper th .cell` | A | |
| 表头 | XPATH | `//div[contains(@class,"el-table__header-wrapper")]//th//div[@class="cell"]` | A | fallback |
| 数据行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | A | |
| 空数据 | CSS | `.el-table__empty-text, .el-table-empty` | A | |
| 加载遮罩 | CSS | `.el-loading-mask, .el-table__body-wrapper .el-loading-mask` | A | |
| 日期文本 | CSS | `span.font-medium` | B | |
| 星期文本 | CSS | `span.text-gray-500` | C | |

## 明细下钻

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 明细按钮 | CSS | `button.el-button--small.is-link, button.el-button.is-link` | B | 每行 |
| 明细按钮 | XPATH | `//button[contains(@class,"el-button") and contains(normalize-space(.),"明细")]` | B | |
| 按日期定位明细 | XPATH | `//tr[contains(@class,"el-table__row")][.//td[contains(normalize-space(.),"{date}")]]//button[contains(normalize-space(.),"明细")]` | B | 模板 |
| 展开内表 | CSS | `.el-table__expanded-cell, .el-table__expanded-cell .el-table, tr.el-table__row--level-1, .detail-table, .expanded-content, .expand-content, [class*="expanded"]` | C | fallback 链 |

`get_expanded_detail_data()`: 轮询展开区域 DOM + 兜底检查 `el-table__row--expanded` 类。

## 分页区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 总条数 | CSS | `.el-pagination__total` | A | |
| 下一页 | CSS | `.el-pagination .btn-next:not([disabled])` | A | |
| 上一页 | CSS | `.el-pagination .btn-prev:not([disabled])` | A | |
| 下一页禁用 | CSS | `.el-pagination .btn-next[disabled]` | A | |
| 上一页禁用 | CSS | `.el-pagination .btn-prev[disabled]` | A | |
| 每页条数 | CSS | `.el-pagination .el-select__wrapper, .el-pagination .el-select` | B | |
| 当前条数 | CSS | `.el-pagination .el-select .el-select__selected-item, .el-pagination .el-select__wrapper .el-select__selected-item` | B | |

自有定位器，不引用 BasePage 通用分页定位器。

## 交叉校验

`verify_stat_vs_table(stat_name, col_header, tolerance=0.001)`:
1. `get_summary_numeric_value(stat_name)` → 汇总值
2. `sum_detail_column_by_header(col_header)` → 明细求和
3. assert `abs(stat - sum) <= tolerance`

## 等待策略

| 场景 | 条件 | 超时 |
|:---|:---|:--:|
| 页面加载 | `_wait_page_ready()` → readyState + table + loading | 15s |
| 表格就绪 | `_wait_table_ready()` — 最复杂实现: readyState + thead th offsetHeight + tbody + loading mask + 连续稳定性检测 | 15s |
| 搜索刷新 | `wait_vue_stable()` + `_wait_table_ready()` | 10s |
| 明细展开 | `get_expanded_detail_data()` 轮询展开区域 | 10s |
| 汇总刷新 | `wait_summary_metrics_refresh(old, timeout)` | 10s |
| 加载遮罩消失 | `_wait_loading_gone()` | 10s |
| Toast | BasePage 通用 | 5s |
