好的，收到。我将遵循 `tech-analysis` 技能定义，基于你提供的 `HazardIoRecordPage` Page Object 代码、测试脚本和已知的 Element Plus 技术栈（无 HTML 源码），生成 **TECH_ANALYSIS.md** 和 **PAGE_ELEMENT_POSITION.md**（合并输出）。

---

## TECH_ANALYSIS / PAGE_ELEMENT_POSITION — 环保出入库明细表

### 1. Element Plus 组件识别

| 组件 | 用途 | 所在区域 | 备注 |
|------|------|----------|------|
| `el-date-picker` | 开始/结束日期选择 | 搜索区 | 通过 `placeholder` 定位输入框 |
| `el-button` | 查询 / 重置 | 搜索区 | 通过文字内容定位 |
| `el-table` | 出入库明细列表 | 主内容区 | 表格数据行采用 `el-table__row` |
| `el-pagination` | 分页控制 | 表格底部 | 总记录数通过 `el-pagination__total` 获取 |
| `v-loading` (指令) | 表格加载遮罩 | 整个表格容器 | 需要等待其消失 |

### 2. DOM 结构分析

- **搜索区**：`el-form` 内部两个 `el-date-picker` + 两个 `el-button`。日期选择器输入框为 `<input placeholder="开始日期">` 和 `<input placeholder="结束日期">`，无唯一 `id`，局部稳定。
- **表格区**：`<div class="el-table"> → <div class="el-table__body-wrapper"> → <table class="el-table__body"> → <tr class="el-table__row">`。表格行完全动态，无稳定属性，依赖 CSS 类选择器。
- **分页区**：`<div class="el-pagination">` 内包含 `<span class="el-pagination__total">` 显示总条数。
- **Teleport 元素**：`el-date-picker` 的下拉面板（日期选择弹窗）通过 `el-popper` 渲染到 `<body>` 层级，使用 `body > .el-picker-panel` 或 `body .el-popper` 定位。
- **动态属性**：Vue 生成的哈希 class（如 `_v-xxxxx`）不用于定位；`v-loading` 控制 `el-loading-mask` 的显示/隐藏。

### 3. 定位器设计表（A/B/C 三级）

| 元素 | 优先策略 | 定位值（Selenium By 表达式） | 稳定性 | 备注 |
|------|----------|-------------------------------|--------|------|
| 开始日期输入框 | B | `(By.XPATH, '//input[@placeholder="开始日期"]')` | B | 依赖文字，国际化可能变更；可考虑 `(By.CSS_SELECTOR, 'input[placeholder="开始日期"]')` 同等级 |
| 结束日期输入框 | B | `(By.XPATH, '//input[@placeholder="结束日期"]')` | B | 同上 |
| 查询按钮 | B | `(By.XPATH, '//button[contains(.,"查询")]')` | B | 文字稳定度高；备用 `(By.CSS_SELECTOR, 'button:has(span:contains("查询"))')` |
| 重置按钮 | B | `(By.XPATH, '//button[contains(.,"重置")]')` | B | 同上 |
| 表格数据行 | B | `(By.CSS_SELECTOR, '.el-table__body-wrapper .el-table__row')` | B | 通用选择器，多行时返回列表 |
| 分页总记录数 | B | `(By.CSS_SELECTOR, '.el-pagination__total')` | B | 通用选择器，单一元素 |
| 表格加载遮罩 | A | `(By.CSS_SELECTOR, '.el-loading-mask')` | A | 由 `v-loading` 控制，稳定出现与消失 |
| 日期选择下拉面板 | C | `(By.CSS_SELECTOR, 'body > .el-picker-panel')` | C | 面板瞬态，仅在点击输入框后出现；需配合等待 |

**稳定性说明**：
- **A 级**：框架定义且不随数据变化的类/属性（`.el-loading-mask`, `.el-pagination__total`）。
- **B 级**：依赖文字内容或全局类名，在单一模块内可接受，有备用方案。
- **C 级**：依赖 Teleport 层级和瞬态状态，仅在特殊操作中使用，需严格控制时序。

### 4. Vue 异步等待策略

本页面无弹窗，主要等待场景为表格加载与搜索刷新。等待策略均使用 `BasePage` 已封装方法。

| 场景 | 等待条件 | WebDriverWait 示例（伪码） | 对应 BasePage 方法 |
|------|----------|----------------------------|--------------------|
| 页面加载 | 表格行至少出现 1 条（或加载遮罩消失） | `wait.until(EC.presence_of_element_located(TABLE_ROWS))` | `_wait_page_ready()` → `wait_vue_stable()` + `_wait_loading_gone()` |
| 搜索执行后 | 加载遮罩消失 + Vue 响应完成 | `wait.until(EC.invisibility_of_element_located(LOADING_MASK))` | `_wait_loading_gone()` + `wait_vue_stable()` |
| 重置后 | 表格数据刷新（行数变化或重新渲染） | 可配合 `wait_vue_stable()` 等待，无需显式等待行数变化 | `wait_vue_stable()` |
| 日期选择操作（若未来需要） | 下拉面板出现 | `wait.until(EC.visibility_of_element_located(PICKER_PANEL))` | 自定义等待（本页面未使用） |

### 5. 自动化风险点

| 风险 | 说明 | 应对 |
|------|------|------|
| **日期选择器 Teleport** | 下拉面板在 `<body>` 下，Selenium 可能无法通过常规父选择器定位 | 使用 `body > .el-popper`，操作前确保输入框已点击，面板已展开 |
| **Placeholder 国际化** | 若系统支持多语言，`placeholder="开始日期"` 可能变为英文 | 考虑添加 `data-testid` 或使用索引定位；或优先 CSS 类 `el-date-editor` 结合位置 |
| **表格行过多导致懒加载** | `el-table` 默认虚拟滚动，不可见行不在 DOM 中 | 只能获取可见行；需要全量数据须借助分页循环或禁用虚拟滚动 |
| **无操作权限时元素隐藏** | 页面为只读，无需处理；但若未来加入导出按钮，需检查权限 | 使用 `is_element_present` 判断 |
| **Vue 动态 class 混淆** | 部分组件可能会额外生成 `el-table--fit` 等组合类，但不影响基础选择器 | 坚持使用稳定类名，避免使用 `contains(@class, 'el-table')` 这种模糊匹配 |

### 6. 补充建议

- 当前定位器均为 **B 级**，建议与开发沟通在关键输入框（如日期）上添加 `data-testid` 属性，可升级为 A 级。
- 如需测试日期范围搜索，建议在 `ElementPlusHelper` 中封装 `pick_date_range` 方法，处理 Teleport 面板的点击与日期选择。
- 页面无弹窗，因此等待策略简单；若后续增加导出对话框，需补充 `wait_dialog_visible` 等待。