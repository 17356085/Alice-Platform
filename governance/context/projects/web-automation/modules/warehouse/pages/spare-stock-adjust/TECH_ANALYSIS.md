# 技术分析: 备品盘点调整

- **模块**: warehouse
- **页面**: spare-stock-adjust
- **Page Object**: `SpareStockAdjustPage`
- **技术栈**: Vue 3 + Element Plus + Selenium

## 1. Element Plus 组件识别

| 组件 | 用途 | 所在区域 | 备注 |
|------|------|----------|------|
| `el-input` | 物品编号输入框 | 搜索区 | 通过 `placeholder` 属性定位 |
| `el-date-picker` | 日期选择器 | 搜索区 | 单日选择器，非范围选择 |
| `el-button` | 查询 / 重置 | 搜索区 | 通过按钮文字内容定位 |
| `el-table` | 盘点调整记录列表 | 主内容区 | 表格数据行采用 `el-table__row` |
| `el-pagination` | 分页控制 | 表格底部 | 总记录数通过 `el-pagination__total` 获取 |
| `v-loading` (指令) | 表格加载遮罩 | 整个表格容器 | 需要等待其消失 |

## 2. DOM 结构分析

- **搜索区**: `el-form` 内部包含一个 `el-input`（物品编号）、一个 `el-date-picker`（日期）和两个 `el-button`（查询/重置）。物品编号输入框为 `<input placeholder="请输入物品编号">`，日期选择器输入框为 `<input placeholder="选择日期">`，均无唯一 `id`，依赖 `placeholder` 属性定位。
- **表格区**: `<div class="el-table">` → `<div class="el-table__body-wrapper">` → `<table class="el-table__body">` → `<tr class="el-table__row">`。表格行完全动态，无稳定属性，依赖 CSS 类选择器。
- **分页区**: `<div class="el-pagination">` 内包含 `<span class="el-pagination__total">` 显示总条数。
- **Teleport 元素**: `el-date-picker` 的下拉面板（日期选择弹窗）通过 `el-popper` 渲染到 `<body>` 层级。操作日期时需使用 `body > .el-picker-panel` 或 `body .el-popper` 定位面板内元素。
- **动态属性**: Vue 生成的哈希 class（如 `_v-xxxxx`）不用于定位；`v-loading` 控制 `el-loading-mask` 的显示/隐藏。

## 3. 定位器设计（A/B/C 三级）

### 页面自定义定位器

| 元素 | 优先策略 | 定位值（Selenium By 表达式） | 稳定性 | 备用方案 |
|------|----------|-------------------------------|--------|----------|
| 物品编号输入框 | B | `(By.XPATH, '//input[@placeholder="请输入物品编号"]')` | B | `(By.CSS_SELECTOR, 'input[placeholder="请输入物品编号"]')` |
| 日期选择器输入框 | B | `(By.XPATH, '//input[@placeholder="选择日期"]')` | B | `(By.CSS_SELECTOR, 'input[placeholder="选择日期"]')` |
| 查询按钮 | B | `(By.XPATH, '//button[contains(.,"查询")]')` | B | `(By.CSS_SELECTOR, 'button:has(span:contains("查询"))')` |
| 重置按钮 | B | `(By.XPATH, '//button[contains(.,"重置")]')` | B | `(By.CSS_SELECTOR, 'button:has(span:contains("重置"))')` |

### 从 BasePage 继承的通用定位器

| 元素 | 定位策略 | 定位值 | 稳定性 | 来源 |
|------|----------|--------|--------|------|
| 表格数据行 | CSS_SELECTOR | `.el-table__body-wrapper tbody tr.el-table__row` | B | `BasePage.TABLE_ROWS` |
| 分页总记录数 | CSS_SELECTOR | `.el-pagination__total` | A | `BasePage.TOTAL_COUNT` |
| 加载遮罩 | CSS_SELECTOR | `.el-loading-mask` | A | Element Plus `v-loading` |

**稳定性说明**:
- **A 级**: 框架定义且不随数据变化的类/属性（`.el-loading-mask`, `.el-pagination__total`）。
- **B 级**: 依赖文字内容或全局类名，在单一模块内可接受，有备用方案。
- **C 级**: 依赖 Teleport 层级和瞬态状态，仅在特殊操作中使用，需严格控制时序（本页面暂无 C 级定位器）。

## 4. Vue 异步等待策略

本页面无弹窗，主要等待场景为表格加载与搜索刷新。等待策略均使用 `BasePage` 已封装方法。

| 场景 | 等待条件 | 对应 BasePage 方法 |
|------|----------|--------------------|
| 页面加载 | Vue 渲染完成 + 加载遮罩消失 | `_wait_page_ready()` → `wait_vue_stable()` + `_wait_loading_gone()` |
| 搜索执行后 | 加载遮罩消失 + Vue 响应完成 | `search_by_item_code()` 内调用 `wait_vue_stable()` |
| 重置后 | 表格数据刷新（重新渲染） | `reset_search()` 内调用 `wait_vue_stable()` |
| 日期选择操作（若未来需要） | 下拉面板出现 | 需要自定义等待 `visibility_of_element_located(PICKER_PANEL)` |

## 5. 自动化风险点

| 风险 | 说明 | 应对 |
|------|------|------|
| **日期选择器 Teleport** | `el-date-picker` 下拉面板在 `<body>` 下，Selenium 可能无法通过常规父选择器定位 | 使用 `body > .el-popper`，操作前确保输入框已点击，面板已展开 |
| **Placeholder 国际化** | 若系统支持多语言，`placeholder="请输入物品编号"` 可能变为英文 | 考虑添加 `data-testid` 或使用 `el-form-item` 联动 label 定位 |
| **表格行过多导致懒加载** | `el-table` 默认虚拟滚动，不可见行不在 DOM 中 | 只能获取可见行；需要全量数据须借助分页循环 |
| **单日期选择器非范围** | `FILTER_DATE` 为单日选择器（非 `_START`/`_END` 成对出现），无法测试日期范围查询 | 测试日期搜索时仅使用单日过滤 |
| **无操作权限时元素隐藏** | 页面为只读，无 CRUD 按钮，权限风险低 | 若未来加入导出按钮，需使用 `is_element_present` 判断 |
| **Vue 动态 class 混淆** | 部分组件可能会额外生成组合类 | 坚持使用稳定类名，避免模糊匹配 |

## 6. 补充建议

- 当前定位器均为 **B 级**，建议与开发沟通在关键输入框上添加 `data-testid` 属性，可升级为 A 级。
- 单日期选择器的通用封装可在 `ElementPlusHelper` 中实现，处理 Teleport 面板的点击与日期选择。
- 页面无弹窗，等待策略简单；若后续增加"查看详情"对话框，需补充 `wait_dialog_visible` 等待。
- `search_by_item_code` 当前使用 `wait_vue_stable()` 而非 `_wait_page_ready()`，建议增加 `_wait_loading_gone()` 以确保加载遮罩完全消失。
