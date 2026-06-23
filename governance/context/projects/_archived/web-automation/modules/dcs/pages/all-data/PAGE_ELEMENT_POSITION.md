# PAGE_ELEMENT_POSITION — dcs / all-data

> 基于 AllDataPage.py (Selenium PO 实测) | 2026-06-22
> 使用 Element Plus 标准 CSS 类 + 相对 XPath

## 搜索/筛选区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 搜索输入框 | CSS | `input[placeholder*="点位" i], input[placeholder*="点位名称" i]` | A | 大小写不敏感匹配 |
| 搜索按钮 | XPATH | `//button[normalize-space(.//span)="搜索"]` | A | |
| 重置按钮 | XPATH | `//button[normalize-space(.//span)="重置"]` | A | |
| 类型/状态下拉 | CSS | `.search-area .el-select, .filter-bar .el-select` | B | 可能多个，按位置取 |

## 操作按钮

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 新增 | XPATH | `//button[normalize-space(.//span)="新增"] \| //button[normalize-space(.//span)="新增点位"]` | A | 可能不存在（只读页） |
| 导入 | XPATH | `//button[normalize-space(.//span)="导入"]` | A | 触发文件选择 |
| 导出 | XPATH | `//button[normalize-space(.//span)="导出"]` | A | 触发下载 |
| 刷新 | XPATH | `//button[normalize-space(.//span)="刷新"]` | A | |
| 批量删除 | XPATH | `//button[.//span[text()="批量删除"]]` | B | 需先勾选行 |
| 批量启用 | XPATH | `//button[.//span[text()="启用"]]` | B | |
| 批量禁用 | XPATH | `//button[.//span[text()="禁用"]]` | B | |

## 数据表格 (Element Plus el-table)

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 表格容器 | CSS | `.el-table` | A | |
| 表格体 | CSS | `.el-table__body-wrapper` | A | |
| 表格行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | B | |
| 加载遮罩 | CSS | `.el-loading-mask` | A | 加载完消失 |
| 空数据提示 | CSS | `.el-table__empty-text` | B | |
| 复选框 | CSS | `.el-checkbox__input` | A | 行选择+全选 |
| 点位ID列 | CSS | `td:nth-child(2) .cell` | B | 按列索引 |
| 点位名称列 | CSS | `td:nth-child(3) .cell` | B | |
| 点位类型列 | CSS | `td:nth-child(4) .cell` | B | |
| 状态列 | CSS | `td:nth-child(7) .cell, td:nth-child(6) .cell` | B | 列索引可能变化 |
| 行内编辑按钮 | XPATH | `//tr[contains(@class,"el-table__row")]//td[contains(text(),"{text}")]/..//button[contains(.,"编辑")]` | A | per-row |
| 行内删除按钮 | XPATH | `//tr[contains(@class,"el-table__row")]//td[contains(text(),"{text}")]/..//button[contains(.,"删除")]` | A | per-row |
| 行内详情按钮 | XPATH | `//tr[contains(@class,"el-table__row")]//td[contains(text(),"{text}")]/..//button[contains(.,"详情")]` | A | per-row |

## 分页 (Element Plus el-pagination)

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 分页器 | CSS | `.el-pagination` | A | |
| 总数 | CSS | `.el-pagination__total` | A | "共N条" |
| 下一页 | CSS | `.el-pagination button.btn-next` | A | |
| 上一页 | CSS | `.el-pagination button.btn-prev` | A | |

## 弹窗表单 (Element Plus el-dialog)

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 名称输入 | CSS | `.el-dialog input[placeholder*="名称"]` | A | |
| ID输入 | CSS | `.el-dialog input[placeholder*="ID" i]` | B | |
| 类型下拉 | CSS | `.el-dialog .el-select` | B | 第一个 |
| 设备下拉 | CSS | `.el-dialog .el-select:nth-of-type(2)` | B | 第二个 |
| 确认删除 | XPATH | `//button[contains(@class,"el-button--primary")]//span[text()="确定"]` | A | message-box |

## 列索引映射

| 列索引 | 列名 | 备注 |
|:------:|------|------|
| 0 | Checkbox | 选择 |
| 1 | 点位ID | |
| 2 | 点位名称 | |
| 3 | 类型 | 模拟量/开关量/计数 |
| 4 | 单位 | |
| 5 | 采集周期 | |
| 6 | 状态 | 启用/禁用 |
| 7 | 上报率 | |
| 8 | 操作 | 编辑/删除/详情 |

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-22 -->
