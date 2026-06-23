好的，收到指令。我将严格按照模板要求，基于“personnel/qualification”页面的上下文（PAGE_CONTEXT.md）以及 Element Plus 的典型结构，生成一份详细的技术分析报告（TECH_ANALYSIS.md）。此报告将作为PAGE_ELEMENT_POSITION.md的输入。

---

## TECH_ANALYSIS.md

### 1. Element Plus 组件识别

| 组件类型 | 用途 | 出现位置 |
|----------|------|----------|
| `el-input` | 文本搜索（资质名称）、表单输入（资质名称/发证机关）、文本域（备注） | 搜索区、弹窗表单 |
| `el-select` | 下拉筛选（资质类型/状态）、表单选择（资质类型） | 搜索区、弹窗表单 |
| `el-date-picker` | 日期范围搜索、日期选择（获得/过期日期） | 搜索区、弹窗表单 |
| `el-button` | 触发操作（搜索/重置/新增/保存/取消/行内操作） | 搜索区、操作栏、弹窗底部、表格列 |
| `el-table` | 展示资质列表数据 | 主内容区 |
| `el-table-column` | 定义表格列（名称/类型/日期/状态/操作） | 表格内部 |
| `el-tag` | 展示资质类型和状态（颜色区分） | 表格列 |
| `el-dialog` | 新增/编辑/详情弹窗 | 弹窗层 |
| `el-pagination` | 分页控制 | 页面底部 |
| `el-upload` | 上传附件 | 弹窗表单 |
| `v-loading` | 表格数据加载/请求等待 | 表格容器 |

### 2. DOM 结构分析

页面将被解析为以下关键节点层级：

- **搜索区**
    - `.search-area` (父容器)
        - `el-input` → `.el-input` → `input[placeholder]`
        - `el-select` → `.el-select` → `.el-select__wrapper` → `.el-select__placeholder`
        - `el-date-picker` → `.el-date-editor--daterange` → `input[placeholder="开始日期"], input[placeholder="结束日期"]`
        - `el-button` → `.el-button` → `span` (文字)
- **操作栏**
    - `.operation-bar` (父容器)
        - `el-button` (btn-add) → 同上
- **表格区**
    - `.el-table`
        - `.el-table__header-wrapper`
        - `.el-table__body-wrapper`
            - `.el-table__row`
                - `.el-table_1_column_1` (动态哈希class)
        - `.el-table__empty-text` / `.el-empty` (空数据状态)
- **分页区**
    - `.el-pagination`
- **弹窗区**
    - `.el-overlay` (遮罩层)
        - `.el-dialog` (对话框容器)
            - `.el-dialog__header`
            - `.el-dialog__body`
                - `.el-form-item` (每个表单项)
            - `.el-dialog__footer`
                - `.el-button` (保存/取消)

**动态属性分析：**
- **动态Class:** `el-table_1_column_1`，`el-table_1_column_2` 等用于列的哈希class会随列定义变化，不能用于定位。
- **v-if控制的元素:** 空数据状态的 `.el-table__empty-text` 或 `.el-empty` 在数据存在时不存在；弹窗内容（`.el-dialog`）由 `v-model` 控制显示/隐藏。
- **稳定属性:** `placeholder`，`aria-label`, 按钮文字 `span` 文本，`el-dialog__title` 的 `title` 属性。

### 3. 定位器设计表（A/B/C 三级）

| 元素 | 推荐定位策略 | 定位值 | 稳定性 | 备注 |
|------|-------------|--------|--------|------|
| 资质名称搜索框 | CSS + placeholder | `input[placeholder*='请输入资质名称']` | A | 稳定标识 |
| 资质类型下拉筛选 | XPath（文字） + CSS | `//span[text()='全部']/ancestor::div[contains(@class,'el-select')]` | B | 利用“全部”文字定位父级，不依赖动态class |
| 日期范围搜索 | CSS + placeholder | `input[placeholder="开始日期"], input[placeholder="结束日期"]` | A | 多个匹配时按顺序取第一个 |
| 搜索按钮 | XPath（文字） | `//button[.//span[text()='搜索']]` | A | 文字定位，非常稳定 |
| 重置按钮 | XPath（文字） | `//button[.//span[text()='重置']]` | A | 同上 |
| 新增资质按钮 | XPath（文字） | `//button[.//span[text()='新增资质']]` | A | **注意：权限点**，若元素不存在需特殊处理 |
| 表格容器 | CSS | `.el-table` | A | 稳定元素 |
| 表格行 | CSS | `.el-table__body-wrapper .el-table__row` | B | 动态行，行数可能为0 |
| 行内编辑按钮 | XPath + 行索引 | `(.//button[.//span[text()='编辑']])[行索引]` | B | 需要与表格行上下文结合使用 |
| 行内删除按钮 | XPath + 行索引 | `(.//button[.//span[text()='编辑']])[行索引]` | B | 同上 |
| 分页器 | CSS | `.el-pagination` | A | 稳定元素 |
| 新增/编辑弹窗 | CSS | `.el-dialog` | A | 弹窗打开时可见 |
| 弹窗-资质名称输入 | CSS + placeholder | `.el-dialog input[placeholder*='请输入资质名称']` | A | 限定在弹窗上下文中 |
| 弹窗-资质类型选择 | XPath + 文字 | `//div[contains(@class,'el-dialog')]//span[text()='学历证书']/parent::*` | B | 先定位到对应的 el-select |
| 弹窗-保存按钮 | XPath（文字） | `//div[contains(@class,'el-dialog')]//button[.//span[text()='确 定']]` | A | **注意：Element Plus 按钮文字可能需要精确匹配，注意空格** |
| 弹窗-取消按钮 | XPath（文字） | `//div[contains(@class,'el-dialog')]//button[.//span[text()='取 消']]` | A | 同上 |
| Toast 提示 | CSS | `.el-message` | A | 全局 Toast |
| Loading 动画 | CSS | `.el-loading-mask` | B | v-loading 控制的遮罩层 |

### 4. Vue 异步等待策略

| 场景 | 等待条件 | WebDriverWait 示例 (使用 BasePage 封装) |
|------|---------|----------------------------------------|
| 页面加载 | 表格可见 | `wait_table_loaded()` 或 `wait.until(EC.presence_of_element_located(TABLE))` |
| 搜索完成（表格刷新） | Loading 消失, 表格数据变化 | `wait_loading_disappear()` 或自定义等待，如 `wait.until(EC.staleness_of(旧行))` |
| 弹窗打开 | 弹窗可见 | `wait_dialog_visible()` (BasePage 封装) |
| 弹窗关闭 | 弹窗不可见 | `wait_dialog_closed()` (BasePage 封装) |
| 下拉选项展开 | Select 下拉框可见 | 通过 `ElementPlusHelper.select_option` 内部处理，等待 `body > .el-popper` 可见 |
| 表单提交响应 | Toast 出现 | `wait.until(EC.presence_of_element_located(TOAST))` |

### 5. 自动化风险点与 Element Plus 已知坑位

- **Teleport 渲染 (EP-001):** `el-select` 的下拉选项列表渲染在 `<body>` 下，不在 `.el-dialog` 内部，因此使用 `.el-dialog` 作为父级限定会定位不到。必须使用 `body > .el-popper`。
- **动态哈希 Class (如 `el-table_1_column_1`):** 绝对不能用于定位。需要依赖列内元素的稳定属性（如文本内容）或表格的整体结构。
- **v-if 控制元素:** 对于“新增”按钮（权限点）这类元素，自动化脚本需要先判断元素是否存在，避免直接定位导致的`NoSuchElementException`。
- **`is_displayed()` 失效 (EP-001):** 对于 Teleport 元素，`is_displayed()` 可能返回 `False`。需要检查元素的 `offsetParent` 属性或直接等待其可见。
- **组件状态与交互时序（如EP-002）:** `filterable el-select` 的交互时序可能与标准 `el-select` 不同。建议统一使用 `ElementPlusHelper.select_option()` 方法，该方法已处理这些差异。
- **权限适配:** 自动化脚本必须能处理“新增”、“编辑”、“删除”按钮因权限缺失而不在 DOM 中的情况。可使用 `wait.until(EC.presence_of_element_located)` 来判断。
- **表格行数据变化:** 搜索、翻页、增删改操作后，表格行会完全重新渲染（新DOM对象）。等待旧行元素失效（staleness_of）是确保数据已刷新的最可靠方法。

---

## 输出：PAGE_ELEMENT_POSITION.md（定位器补充设计）

基于以上分析，为弹窗内部的特定组件提供更精准的定位器，以覆盖之前未详细说明的难点元素：

| 元素 | 推荐定位策略 | 定位值 | 稳定性 | 备注 |
|------|-------------|--------|--------|------|
| 弹窗-资质类型选择器（触发） | XPath | `//div[contains(@class,'el-dialog')]//label[text()='资质类型']/following-sibling::div[1]//input` | C | 利用label文字向后定位。这是间接定位 |
| 弹窗-获得日期 | CSS + placeholder | `.el-dialog input[placeholder="选择日期"]` | B | 如果有多个日期picker，推荐结合index |
| 弹窗-上传附件 | CSS | `.el-dialog .el-upload .el-upload__input` | B | 实际触发文件选择的隐藏input |
| 弹窗-备注 (textarea) | CSS + placeholder | `.el-dialog textarea[placeholder*='请输入备注']` | A | placeholder稳定 |

---

等待备用方案：若 `wait_table_loaded()` 失效，使用 `wait.until(EC.presence_of_element_located(...))` 并检查表格的 `_data` 属性（BasePage 的 `get_table_data` 方法内部处理）。若 `wait_dialog_visible()` 失效，等待 `.el-dialog` 的 `display` 属性变为非 `none`。