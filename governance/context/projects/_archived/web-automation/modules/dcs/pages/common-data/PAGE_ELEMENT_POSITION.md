# PAGE_ELEMENT_POSITION — dcs / common-data

> 基于 CommonDataPage.py (Selenium PO 实测) | 2026-06-22
> 卡片面板页 — 使用 Element Plus + 自定义卡片组件

## 搜索/筛选区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 搜索输入框 | CSS | `input[placeholder*="点位名称" i], input[placeholder*="点位" i], input[placeholder*="名称" i]` | A | 多级 fallback |
| 搜索按钮 | XPATH | `//button[normalize-space(.//span)="搜索"]` | A | |
| 重置按钮 | XPATH | `//button[normalize-space(.//span)="重置"]` | A | |
| 设备下拉 | CSS | `.search-area .el-select` | B | |

## 操作按钮

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 新增 | XPATH | `//button[normalize-space(.//span)="新增"] \| //button[.//span[text()="添加常用点位"]]` | A | 打开点位选择弹窗 |
| 导出 | XPATH | `//button[normalize-space(.//span)="导出"]` | A | |
| 删除所有 | XPATH | `//button[.//span[text()="删除所有"]] \| //button[.//span[text()="清空"]]` | B | 破坏性 |
| 恢复默认 | XPATH | `//button[.//span[text()="恢复默认"]]` | B | |
| 刷新 | XPATH | `//button[normalize-space(.//span)="刷新"]` | A | |

## 卡片网格区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 卡片容器 | CSS | `.card-grid, .el-row, .common-data-cards` | B | 多级 fallback |
| 点位卡片 | CSS | `.point-card, .data-card, .el-card` | B | 个数不固定 |
| 卡片标题 | CSS | `.el-card__header, .card-title, .point-name` | B | |
| 卡片内容 | CSS | `.el-card__body, .card-body` | B | |
| 卡片数值 | CSS | `.card-value, .point-value` | B | 实时数值 |
| 状态标签 | CSS | `.el-tag, .status-badge` | B | 自定义组件 |
| 拖拽手柄 | CSS | `.drag-handle, .el-icon-rank` | B | 需 JS DataTransfer |

## 右键菜单 (Element Plus el-dropdown)

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 菜单项 | CSS | `.el-dropdown-menu__item, [role="menuitem"]` | B | 编辑/删除/置顶/移至末尾 |
| 按文本定位菜单项 | XPATH | `//li[contains(@class,"el-dropdown-menu__item")]//span[text()="{item}"] \| //div[@role="menuitem" and contains(text(),"{item}")]` | B | |

## 表格备选视图 (Element Plus el-table)

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 表格容器 | CSS | `.el-table` | A | 备用视图 |
| 表格行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | B | |
| 加载遮罩 | CSS | `.el-loading-mask` | A | |

## 弹窗 (点位选择)

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 确认添加 | XPATH | `//button[.//span[text()="添加选中"]] \| //button[.//span[text()="确定"]]` | A | |
| 点位复选框 | XPATH | `//label[contains(@class,"el-checkbox")]//span[contains(text(),"{name}")]` | B | per-item |

## 确认对话框

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 确定按钮 | XPATH | `//button[contains(@class,"el-button--primary")]//span[text()="确定"]` | A | message-box |

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-22 -->
