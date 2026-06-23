# TECH_ANALYSIS — lab / gas-indicator

> **版本**: 2.0 | **日期**: 2026-06-18  
> **分析依据**: `GasIndicatorPage.py`, `test_gas_indicator.py`, `PAGE_CONTEXT.md`  
> **技术栈**: Vue 3 + Element Plus + Selenium 4.15.2 + pytest 7.4.4

---

## 1. Element Plus 组件识别

| 组件类型 | 出现位置 | 用途说明 |
|----------|----------|----------|
| `el-table` | 页面主区域 | 展示气体分析设计指标列表（23行，全量加载，无分页） |
| `el-table-column` | 表格内部 | 7列：序号 / 指标名称 / 分类 / 单位 / 规则 / 阈值 / 备注 |
| `el-dialog` | 新增/编辑操作 | 弹窗表单，用于录入指标字段 |
| `el-drawer` | 备用弹窗形式 | 若弹窗使用抽屉，则作为 `DIALOG_FALLBACK` 定位器 |
| `el-form` | 弹窗内部 | 承载6个表单项（指标名称、分类、单位、判断规则、阈值、备注） |
| `el-form-item` | 表单内部 | 每个字段对应的标签+输入框容器，标签文字为 `el-form-item__label` |
| `el-input` | 弹窗表单内 | 输入框（type=text），部分字段可能为 `textarea`（备注） |
| `el-button` | 表格上方 / 弹窗底部 | “新增指标”按钮（`el-button--primary`），“确定”/“取消”按钮 |
| `el-loading-mask` | 全局 | 加载遮罩，用于等待数据加载完成 |

> 未发现 `el-select` / `el-date-picker` / `el-pagination` / `el-upload` / `el-tree` 等组件。

---

## 2. DOM 结构分析

### 2.1 关键节点层级

```
#app
 └─ .app-main
     └─ .gas-indicator-container (或类似 div)
         ├─ .search-area? (不存在，当前页无搜索区)
         ├─ button.新增指标 (el-button--primary)
         ├─ .el-table
         │   ├─ .el-table__header-wrapper
         │   │   └─ thead (表头)
         │   └─ .el-table__body-wrapper
         │       └─ tbody
         │           └─ tr.el-table__row (数据行)
         └─ .el-table__empty-text (可选，无数据时)
 └─ .el-dialog / .el-drawer (弹窗渲染在 body 层)
     └─ .el-dialog__body
         └─ .el-form
             ├─ .el-form-item (指标名称)
             ├─ .el-form-item (指标分类)
             ├─ .el-form-item (单位)
             ├─ .el-form-item (判断规则)
             ├─ .el-form-item (阈值)
             └─ .el-form-item (备注)
```

### 2.2 稳定属性 vs 动态属性

| 属性类型 | 示例 | 说明 |
|----------|------|------|
| **稳定属性** | `class="el-dialog"` | Element Plus 基础类名，通常稳定 |
| 半稳定属性 | `class="el-button el-button--primary"` | 组合类名，可能随版本微调 |
| **动态属性** | `class="el-form-item__content"` | 内部类名较稳定 |
| 动态属性 | `data-v-xxxxx` | Vue 3 注入的 hash 属性，不可用于定位 |
| 动态属性 | `style="display: none;"` | v-if / v-show 控制，用于可见性判断 |
| 动态属性 | `tabindex="-1"` / 无 | aria 属性，不依赖 |

> **结论**：无 `data-testid` 或稳定 `id`，定位器必须依赖文本语义（A 级）或稳定 CSS 组合（B 级）。

### 2.3 v-if / v-show 控制元素

| 元素 | 控制方式 | 等待要点 |
|------|----------|----------|
| 弹窗 (`el-dialog`) | v-if (model-value) | 必须等待 DOM 出现且可见 |
| 表格行 (`el-table__row`) | v-for + 数据变化 | 等待行数 > 0 或行内文本可读 |
| 加载遮罩 (`el-loading-mask`) | v-show (loading 状态) | 等待消失 |
| 空数据文本 | v-if (数据为空) | 等待出现（有条件） |

---

## 3. 定位器设计表（A/B/C 三级）

| 编号 | 元素名称 | 控件类型 | 推荐定位策略 | 定位值 / 实现方式 | 备用定位器 | 稳定性 | 备注 |
|------|----------|----------|-------------|-------------------|-----------|--------|------|
| L01 | **页面加载遮罩** | `div.el-loading-mask` | B 级 CSS | `.el-loading-mask` | `(By.XPATH, "//div[contains(@class,'el-loading-mask')]")` | B | 用于等待表格加载完成 |
| L02 | **新增指标按钮** | `button` | A 级 JS 文本 | `driver.execute_script("...textContent.indexOf('新增指标')...")` | `(By.XPATH, "//span[text()='新增指标']/..")` | A 级（文本稳定） | 依赖产品文案，不可随意修改 |
| L03 | **表格行** | `tr.el-table__row` | B 级 CSS | `.el-table__body-wrapper tbody tr` | `(By.XPATH, "//tbody/tr")` | B | 数量动态变化，需等待加载 |
| L04 | **表格空数据文本** | `div.el-table__empty-text` | B 级 CSS | `.el-table__empty-text` | — | B | 仅无数据时出现 |
| L05 | **弹窗（主）** | `div.el-dialog` | B 级 CSS | `.el-dialog:not([style*="display: none"])` | — | B | 排除隐藏弹窗 |
| L06 | **弹窗（备用）** | `div.el-drawer` | B 级 CSS | `.el-drawer:not([style*="display: none"])` | — | B | 备用抽屉形式 |
| L07 | **弹窗确认按钮** | `button.el-button--primary` | A 级 JS 文本+CSS | `driver.execute_script("...querySelectorAll('button.el-button--primary')...")` | `(By.XPATH, "//div[contains(@class,'el-dialog')]//button[contains(@class,'el-button--primary')]")` | A | 弹窗内唯一 primary 按钮 |
| L08 | **表单字段（指标名称）** | `input` / `textarea` | A 级 JS 标签文本 | `_find_field_in_dialog("指标名称")` | 见备注 | A 级（依赖标签文本） | 标签文案变更会导致定位失败 |
| L09 | **表单字段（分类）** | `input` | A 级 JS 标签文本 | `_find_field_in_dialog("指标分类")` | 同上 | A | 同上 |
| L10 | **表单字段（单位）** | `input` | A 级 JS 标签文本 | `_find_field_in_dialog("单位")` | 同上 | A | 同上 |
| L11 | **表单字段（判断规则）** | `input` | A 级 JS 标签文本 | `_find_field_in_dialog("判断规则")` | 同上 | A | 同上 |
| L12 | **表单字段（阈值）** | `input` | A 级 JS 标签文本 | `_find_field_in_dialog("阈值")` | 同上 | A | 同上 |
| L13 | **表单字段（备注）** | `textarea` | A 级 JS 标签文本 | `_find_field_in_dialog("备注")` | 同上 | A | 可能使用 `textarea` |

> **说明**：  
> - A 级：文本定位（JS 或 XPath），稳定性依赖 UI 文案是否作为产品固定内容。  
> - B 级：CSS 组合类名，随 Element Plus 版本可能有微小变化，但通常稳定。  
> - C 级：当前未使用绝对 XPath 或索引，但列索引 `get_column_data(2)` 本质上是列顺序硬编码，可视为 C 级风险。

---

## 4. Vue 异步等待策略

| 场景 | 等待条件 | 具体实现 | 使用位置 |
|------|----------|----------|----------|
| **页面加载完成** | 表格主体出现 | `wait_page_ready(timeout=15)` (内部：等待 `#app` + 骨架消失) | `navigate()` |
| **表格数据加载** | 等待 loading 遮罩消失 | `_wait_loading_gone(timeout=10)` | `navigate()`, `click_add()` |
| **Vue 渲染稳定** | 等待所有 Vue 响应式更新完成 | `wait_vue_stable()` (内部：`await angular/custom`) | `navigate()`, `click_add()` |
| **弹窗打开** | 弹窗 DOM 出现且可见 | `WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(self.DIALOG))` | `click_add()` |
| **弹窗关闭** | 弹窗 DOM 消失 | `EC.invisibility_of_element_located(self.DIALOG)` | 可在测试中补充 |
| **表格刷新（新增后）** | 表格行数增加或行数据更新 | 自定义等待：轮询 `get_table_row_count()` 直到 > 原值 | 测试脚本中 |
| **表单字段可交互** | 输入框可点击/可聚焦 | `EC.element_to_be_clickable(el)` (在 `_clear_and_type` 之前) | `dialog_input_*` 内部 |

> **建议扩展**：在 `_find_field_in_dialog` 中，找到元素后增加 `wait.until(EC.visibility_of(el))`，避免元素隐藏导致操作失败。

---

## 5. 自动化风险点

| 风险编号 | 风险描述 | 影响等级 | 缓解措施 |
|----------|----------|----------|----------|
| R01 | **标签文本依赖**：所有表单字段通过 `el-form-item__label` 文本定位，文案一旦修改（如“指标分类”改为“类别”）即导致定位失败。 | 高 | 1. 推动开发添加 `data-testid` 属性；2. 与产品确认文案是否作为硬编码固定；3. 建立 UI 变更监控（每次发版时对比测试数据）。 |
| R02 | **列索引硬编码**：测试脚本中使用 `get_column_data(2)` 获取“指标名称”列，若开发在中间插入新列，索引偏移将获取错误数据。 | 中 | 1. 改用列名动态查找：先获取表头文本数组，计算目标列的索引。2. 在测试中定义列名常量字典。 |
| R03 | **弹窗 DOM 渲染位置**：`el-dialog` 通常渲染在 `<body>` 下而非页面内，若使用页面内范围查找可能找不到。 | 中 | 现有代码已使用 `driver.execute_script` 从 `body` 查找，但 `_get_dialog` 未指定 root，默认从 `driver` 查找（`body` 级别），正确。 |
| R04 | **Vue 异步竞争**：`wait_vue_stable()` 可能在数据未完全渲染前返回，导致表格行数不准确或表单字段不可交互。 | 中 | 在 `click_add` 弹窗打开后增加 `wait.until(EC.visibility_of_element_located(...))` 确保字段可见。表格加载后增加显式等待 `wait.until(lambda d: len(d.find_elements(*TABLE_ROWS)) > 0)`。 |
| R05 | **新增/编辑后表格数据未刷新**：页面无搜索区域，全量加载，若新增失败需校验数据是否新增。但现有代码无等待新行出现的断言。 | 低 | 测试脚本中建议调用 `wait_table_loaded()`（如果 BasePage 提供）或自定义等待行数变化。 |
| R06 | **JS 执行环境差异**：Firefox 与 Chrome 在 `execute_script` 中 `textContent` 行为一致，但某些跨域 iframe 可能禁止脚本。无 iframe 风险。 | 低 | 当前页面无 iframe，无此风险。 |

---

## 附录：BasePage / ElementPlusHelper 可用方法对照

| 方法 | 功能 | 在 gas-indicator 中使用情况 |
|------|------|---------------------------|
| `navigate_to(menu1, menu2)` | 菜单导航（侧栏） | 已使用 |
| `wait_page_ready(timeout)` | 等待页面骨架加载完成 | 已使用 |
| `_wait_loading_gone(timeout)` | 等待 loading 遮罩消失 | 已使用 |
| `wait_vue_stable()` | 等待 Vue 渲染稳定 | 已使用 |
| `click_element(locator)` | 点击元素（封装 scroll/click） | 未直接使用，但可通过 `driver.execute_script` 替代 |
| `input_text(locator, value)` | 清空并输入文本 | 未直接使用，使用自定义 `_clear_and_type` |
| `get_table_headers()` | 获取表头文本列表 | 测试中已使用 |
| `get_table_row_count()` | 获取表格行数 | 测试中已使用 |
| `get_column_data(col_index)` | 按列索引获取数据 | 测试中已使用 |
| `wait_dialog_visible(locator)` | 等待弹窗可见 | 未使用，直接手动 EC |
| `wait_table_loaded()` | 等待表格数据渲染 | 未使用，建议补充 |
| `select_option(...)` | 操作 el-select | 未用到 |

> **建议**：后续可考虑使用 `ElementPlusHelper.get_table_data()` 直接获取表格所有数据，避免硬编码列索引。

---

*结束*