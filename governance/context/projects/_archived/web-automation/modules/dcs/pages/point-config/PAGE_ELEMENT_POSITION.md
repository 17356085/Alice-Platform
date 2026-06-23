# PAGE_ELEMENT_POSITION — dcs / point-config

> 基于 PointConfigPage.py (Selenium PO 实测) | 2026-06-22
> 使用 Element Plus 标准 CSS 类 + 相对 XPath，弹窗表单字段多

## 搜索/筛选区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 搜索输入框 | CSS | `input[placeholder*="点位" i], input[placeholder*="名称" i], input[placeholder*="点位名称" i]` | A | 多级 fallback |
| 搜索按钮 | XPATH | `//button[normalize-space(.//span)="搜索"]` | A | DOM 可能与 common-data 不同 |
| 重置按钮 | XPATH | `//button[normalize-space(.//span)="重置"]` | A | |
| 类型筛选下拉 | CSS | `.search-area .el-select, .filter-bar .el-select` | B | |

## 操作按钮

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 新增 | XPATH | `//button[normalize-space(.//span)="新增"] \| //button[normalize-space(.//span)="新增点位"]` | A | 可能不存在（只读页） |
| 导入 | XPATH | `//button[normalize-space(.//span)="导入"]` | A | |
| 导出 | XPATH | `//button[normalize-space(.//span)="导出"]` | A | |
| 批量删除 | XPATH | `//button[.//span[text()="批量删除"]]` | B | |
| 刷新 | XPATH | `//button[normalize-space(.//span)="刷新"]` | A | |

## 数据表格 (Element Plus el-table)

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 表格容器 | CSS | `.el-table` | A | |
| 表格行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | B | |
| 加载遮罩 | CSS | `.el-loading-mask` | A | |
| 复选框 | CSS | `.el-checkbox__input` | A | 行选择 |
| 按文本找行 | XPATH | `//tr[contains(@class,"el-table__row")]//td[contains(text(),"{text}")]/..` | B | |

## 分页 (Element Plus el-pagination)

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 分页器 | CSS | `.el-pagination` | A | |
| 总数 | CSS | `.el-pagination__total` | A | |

## 弹窗表单 (Element Plus el-dialog) — 字段多

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 名称输入 | CSS | `.el-dialog input[placeholder*="名称" i]` | A | |
| ID输入 | CSS | `.el-dialog input[placeholder*="ID" i]` | B | |
| 类型下拉 | CSS | `.el-dialog .el-select:nth-of-type(1)` | A | 模拟量/开关量/计数 |
| 设备下拉 | CSS | `.el-dialog .el-select:nth-of-type(2)` | B | |
| 采集周期输入 | CSS | `.el-dialog input[placeholder*="周期" i], .el-dialog input[placeholder*="ms" i]` | B | |
| 单位输入 | CSS | `.el-dialog input[placeholder*="单位" i]` | B | ℃/kPa/% 等 |
| 告警规则下拉 | CSS | `.el-dialog .el-select:nth-of-type(3)` | A | 无/上限/下限/双限 |
| 告警上限输入 | CSS | `.el-dialog input[placeholder*="上限" i]` | B | 选上限/双限时显示 |
| 告警下限输入 | CSS | `.el-dialog input[placeholder*="下限" i]` | B | 选下限/双限时显示 |
| 启用开关 | CSS | `.el-dialog .el-switch` | B | |

## 下拉选项（按文本定位）

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 类型选项 | XPATH | `//li[contains(@class,"el-select-dropdown__item")]//span[text()="{type}"]` | B | 模拟量/开关量/计数 |
| 告警规则选项 | XPATH | `//li[contains(@class,"el-select-dropdown__item")]//span[text()="{rule}"]` | B | 无/上限/下限/双限 |

## 确认对话框

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 确定按钮 | XPATH | `//button[contains(@class,"el-button--primary")]//span[text()="确定"]` | A | message-box |

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-22 -->
