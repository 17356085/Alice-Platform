# PAGE_ELEMENT_POSITION — dcs / upload-log

> 基于 UploadLogPage.py (Selenium PO 实测) | 2026-06-22
> 日志列表页 — 统计卡片 + 多维筛选 + 详情弹窗

## 统计卡片区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 统计卡片容器 | CSS | `.stat-card, .el-statistic, .summary-card` | B | |
| 上传总数 | CSS | `.stat-total .el-statistic__content, .total-count` | B | |
| 成功数 | CSS | `.stat-success .el-statistic__content, .success-count` | B | |
| 失败数 | CSS | `.stat-fail .el-statistic__content, .fail-count` | B | |
| 异常数 | CSS | `.stat-abnormal .el-statistic__content, .abnormal-count` | B | |

## 时间/筛选区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 开始日期 | CSS | `.el-date-editor input:first-of-type` | A | 日期范围第一输入框 |
| 结束日期 | CSS | `.el-date-editor input:last-of-type` | A | 日期范围第二输入框 |
| 设备下拉 | CSS | `.el-select` | A | 第一个 el-select |
| 状态下拉 | CSS | `.el-select:nth-of-type(2), .status-filter .el-select` | A | 成功/失败/超时/异常 |
| 状态选项 | XPATH | `//li[contains(@class,"el-select-dropdown__item")]//span[text()="{status}"]` | B | |
| 设备选项 | XPATH | `//li[contains(@class,"el-select-dropdown__item")]//span[text()="{device}"]` | B | |
| 搜索输入框 | CSS | `input[placeholder*="点位名称" i], input[placeholder*="错误" i]` | A | |
| 搜索按钮 | XPATH | `//button[normalize-space(.//span)="搜索"]` | A | DOM 可能不匹配 |
| 重置按钮 | XPATH | `//button[normalize-space(.//span)="重置"]` | A | |

## 操作按钮

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 导出 | XPATH | `//button[normalize-space(.//span)="导出"] \| //button[.//span[text()="导出日志"]]` | A | 触发下载 |
| 刷新 | XPATH | `//button[normalize-space(.//span)="刷新"]` | A | |
| 清空 | XPATH | `//button[.//span[text()="清空"]] \| //button[.//span[text()="清空日志"]]` | B | 破坏性操作 |

## 数据表格 (Element Plus el-table)

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 表格容器 | CSS | `.el-table` | A | |
| 表格行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | B | |
| 加载遮罩 | CSS | `.el-loading-mask` | A | |
| 空数据提示 | CSS | `.el-table__empty-text` | B | |
| 行内详情按钮 | XPATH | `//tr[contains(@class,"el-table__row")]//td[contains(text(),"{text}")]/..//button[contains(.,"详情")]` | B | per-row |
| 行内重试按钮 | XPATH | `//tr[contains(@class,"el-table__row")]//td[contains(text(),"{text}")]/..//button[contains(.,"重试")]` | B | 仅失败行 |

## 分页 (Element Plus el-pagination)

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 分页器 | CSS | `.el-pagination` | A | |
| 总数 | CSS | `.el-pagination__total` | A | |

## 详情弹窗 (Element Plus el-dialog)

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 弹窗体内容 | CSS | `.el-dialog__body` | A | 日志详情内容 |
| 关闭按钮 | CSS | BasePage.DIALOG_CANCEL | A | 继承自 BasePage |

## 确认对话框

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 确定按钮 | XPATH | `//button[contains(@class,"el-button--primary")]//span[text()="确定"]` | A | message-box（清空确认） |

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-22 -->
