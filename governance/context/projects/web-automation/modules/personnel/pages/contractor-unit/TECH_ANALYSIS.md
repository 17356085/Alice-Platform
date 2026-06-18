好的，遵照您的要求，我将以测试自动化专家的身份，分析您提供的 `ContractorUnitPage.py` 代码和 `PAGE_CONTEXT.md`，并输出 `TECH_ANALYSIS.md`。本分析将专注于识别 Element Plus 组件细节、优化定位器策略、制定异步等待策略，并识别自动化风险点。

---

## 产出物: TECH_ANALYSIS.md

```markdown
# TECH_ANALYSIS — personnel / contractor-unit

## 1. Element Plus 组件识别

| 组件 | 用途 | 出现位置 |
| :--- | :--- | :--- |
| `el-form` | 搜索区表单容器 | 搜索区 |
| `el-input` | 文本输入 | 搜索区 `search-name`/`search-code`、弹窗表单 `form-unit-code`/`form-unit-name`/`form-contact-person`/`form-contact-phone` |
| `el-select` | 状态筛选 | 搜索区 `search-status`、分页区 `page-size-select` |
| `el-button` | 操作触发 | 搜索按钮、重置按钮、新增按钮、行内编辑/启停用/删除按钮、弹窗确定/取消按钮 |
| `el-table` / `el-table-column` | 数据列表展示 | 列表区 |
| `el-pagination` | 分页控制 | 底部分页区 |
| `el-dialog` | 新增/编辑表单弹窗 | 弹窗区 |
| `el-tag` | 状态标签（启用/禁用） | 列表区 `col-status` |
| `el-switch` | *(可能需要)* 行内状态切换（替代按钮） | *(推断，某些实现可能使用)* |
| `el-message-box` | 删除确认对话框 | 删除操作触发时 |
| `el-option` | 下拉选项 | `el-select` 的子组件 |
| `el-table__row` | 数据行 | `el-table` 的子元素 |

## 2. DOM 结构分析

**关键节点层级结构（简化）**
```
div.page-container
├── div.search-area (或 el-form)
│   ├── el-input#search-name
│   ├── el-input#search-code
│   ├── el-select#search-status
│   ├── el-button#search-btn
│   └── el-button#reset-btn
├── div.table-toolbar
│   └── el-button#add-btn
├── div.table-container
│   └── el-table
│       ├── div.el-table__header-wrapper (表头)
│       │   └── table > thead > tr > th
│       └── div.el-table__body-wrapper (表体)
│           └── table > tbody > tr.el-table__row > td
├── div.pagination-container
│   └── el-pagination
│       ├── span.el-pagination__total (总条数)
│       ├── div.el-select__wrapper (每页条数)
│       ├── button.btn-prev
│       ├── ul.el-pager (页码按钮)
│       └── button.btn-next
└── el-dialog (新增/编辑弹窗)
    └── div.el-dialog__body
        └── el-form
            ├── el-form-item[label="单位编码"]
            │   └── el-input#form-unit-code
            ├── el-form-item[label="单位名称"]
            │   └── el-input#form-unit-name
            ├── el-form-item[label="联系人"]
            │   └── el-input#form-contact-person
            └── el-form-item[label="联系电话"]
                └── el-input#form-contact-phone
```

**稳定属性与动态属性**
- **稳定属性**:
  - `placeholder` 属性 (搜索输入框)
  - `el-form-item` 的 `label` 属性 (弹窗表单字段的标识)
  - `class="el-table"`, `class="el-pagination"`, `class="el-dialog"` 等 Element Plus 固定类名
  - `v-text` / `text()` (按钮文本 "新增", "编辑", "搜索" 等)
  - 列索引 `td:nth-child(1)` 等 (相对稳定的结构正确定位器)
  - `.el-table__body-wrapper` (等待表格内容加载)
  - `.el-loading-mask` (等待 loading 消失)

- **动态/潜在不稳定属性**:
  - Vue 生成的 `data-v-xxxxxx` 属性 (极罕见，Vite 可能不生成，但 Vue CLI 可能的产物)
  - 动态绑定的 `class` (如 `is-active`, `is-disabled`)
  - 表格行高亮类 (如 `hover-row`, `current-row`)

## 3. 定位器设计表 (A/B/C 三级)

本表基于从技术栈推断的最佳实践设计，假设页面 UI 遵循 Element Plus 典型结构。

| 元素 | 推荐定位策略 | 定位值 | 稳定性 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| **单位名称搜索框** | CSS `placeholder` | `input[placeholder*="单位名称"]` | **A** | 推荐替换原 `contains` XPath |
| **单位编码搜索框** | CSS `placeholder` | `input[placeholder*="单位编码"]` | **A** | 推荐替换原 XPath |
| **状态下拉框** | CSS (el-form + el-select) | `.el-form .el-select` | **B** | 或使用 `el-select` 后 `ElSelectWrapper` 操作 |
| **搜索按钮** | XPath `button` + `span` | `//button[.//span[text()='搜索']]` | **A** | 文本稳定可靠 |
| **重置按钮** | XPath `button` + `span` | `//button[.//span[text()='重置']]` | **A** | |
| **新增按钮** | XPath `button` + `span` | `//button[.//span[text()='新增']]` | **A** | |
| **表格容器** | CSS | `.el-table` | **A** | 页面加载首要等待元素 |
| **表格数据行** | CSS | `.el-table__body-wrapper .el-table__row` | **B** | 动态渲染，但结构稳定 |
| **表头文本(验证)** | XPath | `//div[contains(@class,"el-table__header-wrapper")]//th[.//div[contains(@class,"cell")]]` | **B** | 用于获取列名，原定位器合理 |
| **分页组件容器** | CSS | `.el-pagination` | **A** | |
| **总条数文本** | CSS | `.el-pagination__total` | **A** | 推荐替代原 XPath |
| **下一页** | CSS + class | `.el-pagination .btn-next:not(.is-disabled)` | **A** | 利用 `is-disabled` 判断是否可用 |
| **上一页** | CSS + class | `.el-pagination .btn-prev:not(.is-disabled)` | **A** | |
| **当前激活页码** | CSS | `.el-pagination .is-active` | **B** | `is-active` 动态 class |
| **行内编辑按钮(第N行)** | XPath (行索引) | `(//tr[contains(@class,"el-table__row")])[N]//button[.//span[text()='编辑']]` | **B** | 需配合行索引定位特定行 |
| **行内启停用按钮(第N行)** | XPath (行索引) | `(//tr[contains(@class,"el-table__row")])[N]//button[.//span[text()='启用' or text()='停用']]` | **B** | 需处理动态文本 |
| **行内删除按钮(第N行)** | XPath (行索引) | `(//tr[contains(@class,"el-table__row")])[N]//button[.//span[text()='删除']]` | **B** | |
| **弹窗容器** | CSS | `.el-dialog[aria-label*="承包商单位"]` | **A** | Element Plus v2+ 自动生成 `aria-label`，非常稳定 |
| **弹窗表单 - 单位编码** | XPath (label) | `//div[contains(@class,"el-dialog")]//*[label[contains(text(),"单位编码")]]//input` | **A** | 通过 `el-form-item` label 关联 |
| **弹窗表单 - 单位名称** | XPath (label) | `//div[contains(@class,"el-dialog")]//*[label[contains(text(),"单位名称")]]//input` | **A** | 同上 |
| **弹窗表单 - 联系人** | XPath (label) | `//div[contains(@class,"el-dialog")]//*[label[contains(text(),"联系人")]]//input` | **A** | |
| **弹窗表单 - 联系电话** | XPath (label) | `//div[contains(@class,"el-dialog")]//*[label[contains(text(),"联系电话")]]//input` | **A** | |
| **弹窗确定按钮** | XPath (dialog + button) | `//div[contains(@class,"el-dialog")]//button[.//span[text()='确 定']]` | **A** | 注意 `el-button` 可能会在 `span` 内加空格 |
| **弹窗取消按钮** | XPath (dialog + button) | `//div[contains(@class,"el-dialog")]//button[.//span[text()='取 消']]` | **A** | |
| **删除确认按钮** | XPath (el-message-box) | `//div[contains(@class,"el-message-box")]//button[.//span[text()='确定']]` | **B** | `el-message-box` 挂载在 `body` 下 |

## 4. Vue 异步等待策略

| 场景 | 等待条件 | 示例代码 (WebDriverWait) |
| :--- | :--- | :--- |
| **页面加载** | 表格出现 | `wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.el-table')))` |
| **搜索/刷新完成** | Loading 遮罩消失 (或新行出现) | `wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.el-loading-mask')))` |
| **新增/编辑弹窗打开** | `el-dialog` 可见 | `wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.el-dialog[aria-label*="承包商单位"]')))` |
| **弹窗表单加载** | 表单输入框可交互 | `wait.until(EC.element_to_be_clickable((By.XPATH, '//div[contains(@class,"el-dialog")]//*[label[contains(text(),"单位名称")]]//input')))` |
| **弹窗关闭** | `el-dialog` 不可见 | `wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.el-dialog[aria-label*="承包商单位"]')))` |
| **表格行变化 (增/删/改后)** | 获取新行数据并验证行内容 | `def table_row_count_changed(old_count): ...` 自定义等待 lambda |
| **分页切换** | 下一页/上一页按钮 `is-disabled` 状态变化 + 表格行重绘 | `wait.until(EC.staleness_of(old_row))` 或 `wait.until(EC.presence_of_all_elements_located(TABLE_ROWS))` |
| **下拉选项展开** | `el-select-dropdown` 出现 | `wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.el-select-dropdown')))` |
| **确认对话框 (删除)** | `el-message-box` 可见 | `wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.el-message-box')))` |
| **Vue 内部状态稳定** | (可选) 使用 `page.wait_vue_stable()` | `page.wait_vue_stable()` |

**关键建议**:
- **等待策略应优先选择**:
  1.  **目标元素可见/可点击**: 最直接，避免 `sleep`。
  2.  **Loading 消失**: 全局 Loading 组件消失是页面稳定重要信号。
  3.  **内容变化**: 表格行 `staleness` 或 `presence` 变化。
- **自定义等待函数**: 对于账号增删改的闭环测试，应实现类似 `wait_for_table_data_update` 的函数，它利用 `get_table_row_count` 或 `get_first_row_data` 对比旧数据，结合 `wait.until` 循环等待直到出现新预期行。

## 5. 自动化风险点

| 风险点 | 严重程度 | 说明 | 应对策略 |
| :--- | :--- | :--- | :--- |
| **弹窗 `aria-label` 不唯一** | 中 | 如果页面存在多个 `el-dialog`，`aria-label` 可能重复。 | 使用更具体的选择器，如 `//div[contains(@class,"el-dialog")][.//*[contains(text(),"新增")]]` |
| **按钮文本动态加载** | 低 | 按钮文本在 UI 配置化系统中可能通过 API 动态获取。 | 使用 `contains` 结合稳定文本部分，或使用 `data-*` 属性 (如 `data-testid`)。 |
| **表单组件挂载层级** | 中 | `el-select`、`el-date-picker` 的下拉面板 (`el-select-dropdown`) 挂载在 `<body>` 层，而非弹窗内。 | 定位下拉选项时，应使用 **`document.querySelector('body .el-select-dropdown')` 策略**，而不是在弹窗内查找。 |
| **删除确认 `el-message-box`** | 中 | `el-message-box` 同样挂载在 `<body>` 下。 | 定位器需要是全局的，而不是页面根元素内的。 |
| **虚拟滚动表格 (性能)** | 高 | 如果表格数据量非常大 (数千行)，Element Plus 可能开启虚拟滚动，此时 DOM 中只有可视区域的表格行。 | 获取所有行时，`find_all` 不会返回所有数据。**对于搜索功能，不依赖遍历所有行，而是通过搜索验证结果即可。** 对于数据抓取，需要调用 `get_table_data` (如果是虚拟滚动，这个函数需特殊实现)。 |
| **`el-table` 动态列** | 低-中 | 如果列顺序通过配置动态改变，依赖硬编码列索引 (`td:nth-child(2)`) 的定位会失效。 | 优先使用列 header 文本或 `data-col-id` 属性定位列，避免依赖索引。 |
| **`el-table__row` 中的隐藏元素** | 中 | 某些操作按钮可能根据权限、状态实现 `v-if` 或 `v-show`。 | 在定位行内按钮前，验证其可见性 (`is_displayed`)。例如，只有启用状态的承包商才有“停用”按钮。 |

## 6. 代码层面改进建议 (针对 `ContractorUnitPage.py`)

1.  **优化 `SEARCH_NAME_INPUT`**: 从 `contains` XPath 改为 `input[placeholder*="单位名称"]` CSS 选择器，更高效稳定。 **(A级)**
2.  **优化 `PAGE_SIZE_OPTION`**: 该定位器是动态字符串模板，但在当前 `BasePage` API 中未体现使用方式。建议在代码中提供一个 `_select_page_size(size)` 方法，内部解析该模板。
3.  **修复 `CURRENT_PAGE`**: 当前 XPath 试图定位带 `is-active` 的按钮，但页码元素是 `li` 或 `button`。更正为 `CSS: .el-pagination .is-active` 更准确。
4.  **添加“弹窗”相关定位器常量**: 当前代码完全没有弹窗内表单元素的定位器。建议新增：
    - `DIALOG_CONTAINER`
    - `FORM_UNIT_CODE_INPUT`
    - `FORM_UNIT_NAME_INPUT`
    - `FORM_CONTACT_PERSON_INPUT`
    - `FORM_CONTACT_PHONE_INPUT`
    - `FORM_SUBMIT_BUTTON`
    - `FORM_CANCEL_BUTTON`
5.  **添加“确认框”相关定位器常量**:
    - `CONFIRM_DIALOG`
    - `CONFIRM_OK_BUTTON`
    - `CONFIRM_CANCEL_BUTTON`
6.  **移除冗余方法**: `is_unit_name_present` 调用父类 `is_row_present`，其自身定位器 `ROW_BY_TEXT` 可能不存在，应删除或正确实现父类方法。