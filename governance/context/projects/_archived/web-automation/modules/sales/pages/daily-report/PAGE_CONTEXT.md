# PAGE_CONTEXT — sales / daily-report

> 从 DailyReportPage.py 实际代码提取 | 2026-06-17 | 覆盖过期文档

## 页面信息
- **页面名称**: 销售日报表
- **路由**: `#/sales/measurement`
- **PO**: `page/sales_page/DailyReportPage.py` (继承 BasePage，无 ElementPlusHelper)
- **侧边栏导航**: `navigate_to("销售管理", "销售日报表")`
- **页面性质**: **只读页面**，无增删改操作

## 页面整体结构

顶部全局导航栏 → 左侧菜单 → 主内容区：
1. **搜索/筛选区**: 1 个 el-date-picker range + 2 个 el-button（查询/重置）— **无产品下拉，无导出按钮**
2. **汇总指标区**: 统计卡片，非 BEM 命名，多 CSS fallback 链定位
3. **明细表格区**: el-table 动态列，每行"明细"按钮展开子表
4. **分页区**: el-pagination

## 搜索/筛选区

| 元素ID | 描述 | 控件类型 | 定位器 | 等级 |
|:---|:---|:---|:---|:--:|
| `START_DATE` | 开始日期 | el-date-picker (readonly) | CSS: `input[placeholder*="开始日期"], .el-date-editor input[placeholder*="开始"]` | B |
| `END_DATE` | 结束日期 | el-date-picker (readonly) | CSS: `input[placeholder*="结束日期"], .el-date-editor input[placeholder*="结束"]` | B |
| `BTN_QUERY` | 查询 | el-button (primary) | `//button[contains(@class,"el-button--primary")]//span[contains(normalize-space(.),"查询")]/parent::button` | A |
| `BTN_RESET` | 重置 | el-button (default) | `//button[contains(@class,"el-button")]//span[contains(normalize-space(.),"重置")]/parent::button` | A |

> **注意**: 无"产品类型"下拉、无"导出"按钮。日期输入 readonly → 用 JS `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set` 绕过 + 完整事件链派发。兜底方案 `_set_date_range_via_input()` 使用 ActionChains Tab 键导航。

## 汇总指标区

⚠️ **非标准 CSS 类**（非 BEM 命名），定位脆弱，建议后端加 data-testid。

| 元素 | CSS 选择器 (fallback 链) | 等级 |
|:---|:---|:--:|
| 卡片容器 | `.summary-wrapper, .stat-cards, .el-row.stat-row, .report-summary, [class*="stat-card"]` | C |
| 卡片项 | `.stat-card, .stat-item, .el-statistic, [class*="statistic-item"]` | C |
| 标签 | `.stat-card__label, .stat-item__label, .el-statistic__head` | C |
| 数值 | `.stat-card__value, .stat-item__value, .el-statistic__number` | C |

关键方法:
- `get_summary_metrics()` → `dict` — CSS 定位 + 兜底遍历卡片容器文本两套提取逻辑
- `get_summary_value(name)` → `str`
- `get_summary_numeric_value(name)` → `float`
- `wait_summary_metrics_refresh(old, timeout)` — 等待汇总刷新

## 明细表格区

**动态列**，按表头文本部分匹配 `_get_column_index(header_text)` 查找列号。无固定 COL 常量。

| 元素 | 定位器 | 等级 |
|:---|:---|:--:|
| 表头 | CSS: `.el-table__header-wrapper th .cell` / XPATH 保底 | A |
| 数据行 | CSS: `.el-table__body-wrapper tbody tr.el-table__row` | A |
| 空数据 | CSS: `.el-table__empty-text, .el-table-empty` | A |
| 加载遮罩 | CSS: `.el-loading-mask, .el-table__body-wrapper .el-loading-mask` | A |
| 日期字体 | CSS: `span.font-medium` | B |
| 星期文本 | CSS: `span.text-gray-500` | C |

### 行操作: 明细下钻

| 元素 | 定位器 | 备注 |
|:---|:---|:---|
| 明细按钮 | CSS: `button.el-button--small.is-link` / XPATH: `//button[contains(normalize-space(.),"明细")]` | 每行 |
| 按日期定位明细 | `//tr[contains(@class,"el-table__row")][.//td[contains(normalize-space(.),"{date}")]]//button[contains(normalize-space(.),"明细")]` | — |
| 展开内表 | CSS fallback 链: `.el-table__expanded-cell .el-table, tr.el-table__row--level-1, .detail-table, .expanded-content, [class*="expanded"]` | C |

`get_expanded_detail_data()`: 轮询展开区域 + 兜底检查 `el-table__row--expanded` 类。

## 分页区

自有定位器，不引用 BasePage 通用分页定位器。

| 元素 | 定位器 | 等级 |
|:---|:---|:--:|
| 总条数 | CSS: `.el-pagination__total` | A |
| 下一页 | CSS: `.el-pagination .btn-next:not([disabled])` | A |
| 上一页 | CSS: `.el-pagination .btn-prev:not([disabled])` | A |
| 下一页禁用 | CSS: `.el-pagination .btn-next[disabled]` | A |
| 上一页禁用 | CSS: `.el-pagination .btn-prev[disabled]` | A |
| 每页条数 | CSS: `.el-pagination .el-select__wrapper, .el-pagination .el-select` | B |

## 核心业务规则
- **只读页面**: 无 CRUD
- **汇总 vs 明细一致性**: `verify_stat_vs_table(stat_name, col_header, tolerance=0.001)` — 明细列求和 = 汇总卡片值
- **浮点精度**: 容差 0.001（四舍五入到 4 位小数）
- **日期边界**: 无数据日期汇总显示 0 或 "--"，不显示 NaN

## 页面状态
- **加载中**: `_wait_table_ready()` — 最复杂实现：readyState + thead th offsetHeight + tbody + loading mask + 连续稳定性检测
- **空数据**: `get_table_empty_text()`
- **加载遮罩**: `_wait_loading_gone()` — 等待 `.el-loading-mask` 消失

## 技术难点
- ⚠️ 汇总卡片非 BEM 命名 — CSS fallback 链过长，建议后端加 `data-testid`
- el-date-picker readonly → JS native setter 绕过 + 完整事件链派发
- 明细展开区域 DOM 结构不固定 → 多选择器 fallback + 轮询
- `_wait_table_ready()` 实现最复杂（含连续稳定性检测）

## 测试文件
`script/sales/test_daily_report.py`, `test_daily_report_display.py`, `test_daily_report_search.py`, `test_daily_report_pagination.py`, `test_daily_report_boundary.py`, `test_daily_report_data_integrity.py`
