```yaml
---
source: ai
source_agent: tech-analysis
created: 2025-04-04
---

# 技术分析报告: 设备报警配置

## 1. Element Plus 组件识别

| 组件 | 用途 | 实例 | 备注 |
|------|------|------|------|
| `el-table` | 数据展示与操作 | 报警配置列表表格 | 存在 fixed-right 列（操作列），导致 DOM 克隆行 |
| `el-table-column` | 列定义 | 报警名称、类型、级别、触发值、状态、创建时间、操作（共9列） | - |
| `el-pagination` | 分页控制 | 表格底部 | 功能通过 `get_table_data()` 间接使用 |
| `el-input` | 文本输入 | 关键词搜索框（报警名称/设备名称） | placeholder 定位 |
| `el-select` | 下拉选择 | 报警类型、报警级别、状态（搜索区3个） | 透传 Teleport 渲染到 `<body>` |
| `el-button` | 按钮 | 查询、重置、新增配置、弹窗确定/取消 | - |
| `el-dialog` | 弹窗 | 新增/编辑/删除确认? | 实际弹窗表单尚未实现定位器（skip） |
| `el-message-box` (隐含) | 确认弹窗 | 删除确认 | 可能使用 `ElMessageBox.confirm` |
| `el-loading` | 加载遮罩 | 页面加载、表格刷新 | 通过 `_wait_loading_gone()` 等待 |
| `el-empty` | 空数据提示 | 表格无数据时 | 通过 `.el-table__empty-text` 定位 |
| `el-tag` (推测) | 状态标签 | 报警类型、报警级别、状态列 | 测试脚本中未直接使用，但 UI 通常使用 |
| `el-switch` (推测) | 开关 | 弹窗内状态控制 | 未在 PO 中定义，属于弹窗表单 |
| `el-input-number` (推测) | 数字输入 | 弹窗内触发值 | 未在 PO 中定义，属于弹窗表单 |
| `el-date-picker` (推测) | 日期范围 | 搜索区（未来可能） | 当前 PO 未定义，但常见于后台 |

> **Teleport 坑位**：`el-select` 的下拉面板（popper）渲染在 `<body>` 下，`is_displayed()` 可能失效（EP-001）。搜索区的 `el-select` 使用 XPath 索引定位，未直接触发下拉，但未来弹窗内 filterable el-select 会触发该问题（EP-002，已导致 `@skip`）。

## 2. DOM 结构分析

### 2.1 统计卡片（非标准布局）

- 结构：标签在下、数字在上（与常规顺序相反）
- 定位策略：`//*[contains(normalize-space(.),"{label}")]/preceding-sibling::*[1]`
- 风险点：DOM 结构易变，`preceding-sibling` 依赖相邻层级

### 2.2 搜索区

- 包裹在 `<form class='el-form--inline'>` 内
- `el-select` 组件通过重复的 `(el-select)[1]、[2]、[3]` 索引定位（脆弱）
- 按钮 `查询` 使用 `el-button--primary` 主按钮样式区分，`重置` 使用文本匹配

### 2.3 表格区

- 存在 fixed-right 列（操作列），导致 `el-table__body-wrapper` 内有两个 tbody（克隆行）
- `TABLE_ROWS` 使用 `tr.el-table__row` 会匹配到克隆行，需在 `get_table_data()` 中处理重复
- 表头由 `el-table__header-wrapper` 下的 `th .cell` 获取文本列表

### 2.4 弹窗区

- 定位器 `DIALOG_SAVE_BTN` / `DIALOG_CANCEL_BTN` 使用 `contains(@style,"display: none")` 排除隐藏弹窗
- 弹窗内具体表单元素（`el-input`、`el-select`、`el-switch`、`el-input-number`）尚未定义定位器
- 弹窗目前被 `@skip`，因为 filterable el-select 的交互存在稳定性问题

### 2.5 动态属性

- 无显式 `id` 或 `name` 属性（除了可能的 data-*）
- 定位主要依赖 CSS class 和 XPath 文本匹配
- Vue 动态 class（如 `el-table__row--striped`）不影响定位
- `el-select` dropdown 通过 Teleport 渲染，popper class 为 `.el-popper`

## 3. 定位器设计表（A/B/C 三级）

| 元素 | 推荐定位策略 | 定位值 | 稳定性 | 备注 | 代码对应 |
|------|-------------|--------|--------|------|----------|
| 关键词搜索输入框 | CSS A | `input[placeholder="报警名称/设备名称"]` | A | 稳定属性 | `INPUT_KEYWORD` |
| 报警类型下拉(搜索区) | XPath B | `(//form[contains(@class,"el-form--inline")]//div[contains(@class,"el-select")])[1]` | B | 依赖索引，若组件重排会失效 | `SELECT_ALARM_TYPE` |
| 报警级别下拉(搜索区) | XPath B | `(//form[contains(@class,"el-form--inline")]//div[contains(@class,"el-select")])[2]` | B | 同上 | `SELECT_ALARM_LEVEL` |
| 状态下拉(搜索区) | XPath B | `(//form[contains(@class,"el-form--inline")]//div[contains(@class,"el-select")])[3]` | B | 同上 | `SELECT_STATUS` |
| 查询按钮 | XPath A | `//form[contains(@class,"el-form--inline")]//button[contains(@class,"el-button--primary")][contains(.,"查询")]` | A | 主按钮样式+文本 | `BTN_SEARCH` |
| 重置按钮 | XPath B | `//form[contains(@class,"el-form--inline")]//button[contains(.,"重置")]` | B | 文本匹配，可能和其他重置按钮冲突 | `BTN_RESET` |
| 新增配置按钮 | XPath A | `//button[contains(.,"新增配置")]` | A | 唯一文本 | `BTN_ADD` |
| 表头单元格 | CSS A | `.el-table__header-wrapper th .cell` | A | 固定结构 | `TABLE_HEADER_CELLS` |
| 表格数据行 | CSS A | `.el-table__body-wrapper tbody tr.el-table__row` | B | 注意 fixed-right 克隆行（需过滤） | `TABLE_ROWS` |
| 空数据提示 | CSS A | `.el-table__empty-text` | A | 表格无数据时出现 | `TABLE_EMPTY` |
| 统计卡片值(总/启/禁/今日) | XPath C | `//*[contains(normalize-space(.),"{label}")]/preceding-sibling::*[1]` | C | 依赖DOM结构，非标准组件 | `STAT_VALUE_XPATH` |
| 统计卡片容器 | CSS B | `.stat-value` | B | 可能与其他卡片混淆 | `STAT_CARD_CONTAINER` |
| 弹窗确定按钮 | XPath B | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[contains(@class,"el-button--primary")][contains(.,"确定")]` | B | 需排除隐藏弹窗 | `DIALOG_SAVE_BTN` |
| 弹窗取消按钮 | XPath B | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[contains(.,"取消")]` | B | 同上 | `DIALOG_CANCEL_BTN` |

> **稳定性说明**：
> - **A级** – 属性/文本足够稳定，极少变化。
> - **B级** – 依赖索引、CSS class 顺序或 DOM 层级，可能因改动影响。
> - **C级** – 依赖非常规 DOM 结构（如 preceding-sibling），脆弱。

## 4. Vue 异步等待策略

| 场景 | 等待条件 | 封装方法 | 实现说明 |
|------|---------|----------|----------|
| 页面加载 | `document.readyState == 'complete'` + loading 消失 + 表格 body 出现 | `_wait_page_ready(timeout=25)` → `wait_page_ready()` → `_wait_loading_gone()` → `wait_vue_stable()` | 三重等待确保 Vue 渲染完成 |
| 表格刷新的轻量等待 | 数据行或空状态提示出现 | `_wait_table_ready(timeout=5)` | 使用 `EC.presence_of_element_located` 或逻辑或 |
| 搜索完成 | loading 消失 + Vue 稳定 | 隐式在 `search_*` 方法后调用 `_wait_table_ready()`（测试脚本未展示完整，但推测存在） | - |
| 弹窗打开 | `el-dialog` 可见（非 display:none） | 未单独封装（当前弹窗交互全 skip） | 未来可借助 `wait_dialog_visible` 基类方法 |
| 弹窗关闭 | `el-dialog` 不可见 | 同上 | 基类 `wait_dialog_invisible` |
| 分页切换 | 表格重新渲染 | 隐式在 `get_table_data()` 中调用 `_wait_table_ready()` | - |
| Vue 响应式更新稳定 | 无 DOM 变化后的短暂空闲 | `wait_vue_stable()`（基类方法） | 使用 `setTimeout` + `requestAnimationFrame` 模式 |

> **注意**：所有等待方法都继承自 `BasePage`，未在 `AlarmConfigPage.py` 中重新定义（除了 `_wait_page_ready` 和 `_wait_table_ready`）。上层用例无需直接调用。

## 5. 自动化风险点

| 风险 | 描述 | 影响 | 应对 |
|------|------|------|------|
| **fixed-right 列克隆** | `el-table` 固定列导致 DOM 中存在两个 tbody（原表 + 克隆） | `TABLE_ROWS` 定位器返回的行数是实际两倍，列索引偏移 | `get_table_data()` 中已处理：取前一半行作为真实数据行；避免基于列索引的直接 XPath 定位 |
| **filterable el-select 弹窗失效** | Element Plus 2.x 中 `filterable` 模式下 `is_displayed()` 对 Teleport 渲染的 popper 元素返回错误状态 | 导致 `Expected conditions` 失败，弹窗交互不可用 | 使用 `execute_script` 或 `ActionChains` 替代 `is_displayed()`；当前已 `@skip` |
| **统计卡片 DOM 结构不稳定** | 卡片标签与数值的排列顺序可能被前端改动 | `preceding-sibling` 定位器失效 | 添加备用定位策略（如 `.stat-value` 容器内的数字选择器） |
| **搜索区 el-select 索引依赖** | 搜索区下拉框位置依赖 `el-form--inline` 内 `el-select` 的出现顺序 | 若增加/删除搜索条件，索引偏移 | 考虑增加 `data-testid` 属性，或通过 `placeholder`/`label` 文本定位 |
| **弹窗表单元素缺失定位器** | 当前 PO 仅定义了弹窗的确定/取消按钮，未定义表单字段 | 无法编写弹窗交互测试 | 未来实现时需参考 Element Plus 最佳实践（如通过 `el-dialog` 作用域内的 `el-form-item` 的 label 定位） |
| **Vue 动态 class 与 CSS 选择器冲突** | `el-table__row` 的 class 在 Vue 渲染后可能有后缀或条件类（如 `--striped`） | 不影响当前 `tr.el-table__row` 选择，但需注意 CSS specificity | 保持使用 `.el-table__row` 类选择器，避免伪类 |
| **弹窗打开/关闭时序** | Vue 过渡动画导致 `is_visible` 判断滞后 | 可能获取到半透明或不可交互的弹窗 | 使用 `wait_dialog_visible` 和 `wait_vue_stable()`；对 `el-dialog` 的 `visible` 属性进行显式等待（通过基类） |
| **权限控制元素缺失** | 非 admin 用户可能看不到“新增配置”按钮或表格操作按钮 | 用例可能失败 | 测试脚本中已验证 admin 基线权限；未来可增加权限 fixture 控制 |
| **网络请求超时** | 后端响应慢导致 loading 持续 | 表格数据加载失败 | `_wait_page_ready` 使用 25s timeout，并可配置；`_wait_table_ready` 使用 5s 快速失败 |

## 6. 已知问题 & 已跳过测试

- **弹窗交互（新增/编辑/删除）**：全部标记为 `@skip`，原因见 EP-002（filterable el-select is_displayed 坑）。未来解决后需补充定位器和测试。
- **测试脚本中引用的 `is_search_input_visible`、`is_add_button_visible`**：方法未在提供的 PO 代码片段中展示，推测继承自 `BasePage` 或 PO 已存在（当前上下文可能不是完整文件）。需确认实际实现。

## 7. 扩展建议

- 为搜索区 `el-select` 增加 `data-testid` 属性以替代索引定位（提升稳定性）
- 为统计卡片引入标准 Element Plus 组件（如 `el-descriptions` 或 `el-card`）以简化定位
- 统一弹窗定位器，使用包含标题的 `el-dialog` 范围（如 `//div[@aria-label="新增报警配置"]`）
- 将 `_wait_page_ready` 中的特定等待（表格 body 出现）提取到 `BasePage` 的通用 `wait_table_loaded` 方法中（当前测试框架已声明存在该方法）

---

*此文档同时可作为 `PAGE_ELEMENT_POSITION.md` 使用，定位器设计表见第3节。*
```