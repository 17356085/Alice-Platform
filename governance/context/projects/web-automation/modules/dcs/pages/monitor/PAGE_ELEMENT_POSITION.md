# PAGE_ELEMENT_POSITION — dcs / monitor

> 基于 MonitorPage.py (Selenium PO 实测) | 2026-06-22
> 监控面板页 — 卡片网格 + 图表 + 可选表格视图

## 搜索/筛选区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 搜索输入框 | CSS | `input[placeholder*="参数" i], input[placeholder*="设备" i], input[placeholder*="点位名称" i]` | A | 多级 fallback；仪表盘可能无此控件 |
| 搜索按钮 | XPATH | `//button[normalize-space(.//span)="搜索"]` | B | 仪表盘可能无传统搜索栏 |
| 重置按钮 | XPATH | `//button[normalize-space(.//span)="重置"]` | B | 仪表盘可能无此按钮 |
| 状态下拉 | CSS | `.el-select` | B | 正常/告警/离线 |
| 状态选项 | CSS | `.el-select-dropdown__item` | B | |
| 状态选项按文本 | XPATH | `//li[contains(@class,"el-select-dropdown__item")]//span[text()="{text}"]` | B | |
| 日期选择器 | CSS | `.el-date-picker, .el-date-editor` | B | |

## 操作按钮

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 新增 | XPATH | `//button[normalize-space(.//span)="新增"] \| //button[normalize-space(.//span)="新增参数"]` | B | 仪表盘可能无此按钮 |
| 刷新 | XPATH | `//button[normalize-space(.//span)="刷新"]` | B | 数据可能自动推送 |
| 导出 | XPATH | `//button[normalize-space(.//span)="导出"]` | B | |

## 监控卡片区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 卡片容器 | CSS | `.monitor-cards, .card-grid, .el-row` | B | 多级 fallback |
| 参数卡片 | CSS | `.monitor-card, .param-card, .el-card` | B | 个数不固定，实时推送刷新 |
| 卡片名称 | CSS | `.card-title, .param-name` | B | |
| 卡片当前值 | CSS | `.card-value, .param-value` | B | 实时数值 |
| 状态标签 | CSS | `.el-tag, .status-badge` | B | 正常=绿/告警=红/离线=灰 |
| 趋势上箭头 | CSS | `.trend-up, .el-icon-top` | C | |
| 趋势下箭头 | CSS | `.trend-down, .el-icon-bottom` | C | |

## 图表区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 图表容器 | CSS | `.chart-container, [class*="chart"]` | B | ECharts/G2 canvas，验证困难 |

## 表格视图 (Element Plus el-table)

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 表格容器 | CSS | `.el-table` | A | 可选视图切换 |
| 表格行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | B | |
| 加载遮罩 | CSS | `.el-loading-mask` | A | |
| 行内编辑按钮 | XPATH | `//tr[contains(@class,"el-table__row")]//td[contains(text(),"{text}")]/..//button[contains(.,"编辑")]` | B | per-row |
| 行内删除按钮 | XPATH | `//tr[contains(@class,"el-table__row")]//td[contains(text(),"{text}")]/..//button[contains(.,"删除")]` | B | per-row |
| 行内详情按钮 | XPATH | `//tr[contains(@class,"el-table__row")]//td[contains(text(),"{text}")]/..//button[contains(.,"详情")]` | B | per-row |

## 分页 (Element Plus el-pagination)

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 分页器 | CSS | `.el-pagination` | A | |
| 总数 | CSS | `.el-pagination__total` | A | |

## 确认对话框

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 确定按钮 | XPATH | `//button[contains(@class,"el-button--primary")]//span[text()="确定"]` | A | message-box |

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-22 -->
