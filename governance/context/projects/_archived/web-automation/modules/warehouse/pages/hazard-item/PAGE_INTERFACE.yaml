好的，收到需求。基于您提供的 Page Object 代码和测试脚本，我对 `warehouse` 模块的 `hazard-item` 页面进行了分析。

由于没有提供页面截图或 HTML 源码，此次分析将主要从代码中推断页面结构、元素和交互逻辑，并据此生成 `PAGE_CONTEXT.md` 和 `PAGE_ELEMENT_POSITION.md`。定位器的设计将基于代码中已有的 XPath 进行优化和扩展，遵循既定的规则。

---

### PAGE_CONTEXT.md

```markdown
# 页面上下文: 环保物品管理 (Hazard Item)

| 元数据项 | 值 |
|---|---|
| 模块 | warehouse (库管管理) |
| 页面名称 | 环保物品管理 |
| 页面 URL | (待补充) |
| 访问路径 | 库管管理 → 环保危废管理 → 物品管理 |
| 页面类型 | 列表页 (CRUD) |
| 主要功能 | 查看、搜索、新增、删除、批量选择危废品 |

## 1. 页面整体结构

该页面是一个典型的后台管理列表页，主要分为以下几个区域：

1.  **顶部/导航**: 页面标题和面包屑导航 (由框架提供，非本页特有)。
2.  **搜索/筛选区 (Filter Area)**: 位于页面顶部，用于按条件筛选列表数据。
    -   包含：危废品名称输入框、查询按钮、重置按钮。
3.  **操作按钮区 (Action Area)**: 位于搜索区右侧或下方，包含业务操作入口。
    -   包含：新增按钮。
4.  **表格/列表区 (Table Area)**: 用于展示危废品数据列表。
    -   包含：多选框列、危废品名称列、其他数据列、操作列。
    -   操作列包含：删除按钮。
5.  **分页区 (Pagination Area)**: 位于表格底部，用于翻页和数据量统计。
6.  **弹窗/对话框 (Dialog)**: 用于新增危废品的表单操作。

## 2. 页面元素清单

### 2.1 搜索/筛选区

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `FILTER_ITEM_NAME` | 危废品名称搜索框 | `el-input` | 搜索区 | 用于按名称筛选列表 |
| `BTN_QUERY` | 查询按钮 | `el-button` | 搜索区 | 触发搜索 |
| `BTN_RESET` | 重置按钮 | `el-button` | 搜索区 | 重置搜索条件 |

### 2.2 表格/列表区

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `TABLE` | 数据表格容器 | `el-table` | 表格区 | 包含所有数据行 |
| `TABLE_HEADER` | 表头行 | `el-table__header-wrapper` | 表格区 | 包含列标题 |
| `TABLE_ROWS` | 所有数据行 | `el-table__row` | 表格区 | 用于获取行数 |
| `COL_CHECKBOX` | 多选框列（表头） | `el-checkbox` | 表格区 | 选择所有行 |
| `COL_ITEM_NAME` | 危废品名称列 | `el-table-column` | 表格区 | 文本显示 |
| `COL_ACTIONS` | 操作列 | `el-table-column` | 表格区 | 包含操作按钮 |
| `BTN_DELETE` | 删除按钮 | `el-button` | 表格区操作列 | 针对单行数据 |

### 2.3 分页区

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `PAGINATION` | 分页组件容器 | `el-pagination` | 分页区 | 包含分页所有子元素 |
| `TOTAL_COUNT` | 总条数显示 | `el-pagination__total` | 分页区 | 用于获取总数据量 |

### 2.4 弹窗/对话框 (新增)

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `DIALOG` | 新增表单弹窗 | `el-dialog` | 弹窗区 | 通用定位器，继承自BasePage |
| `DIALOG_TITLE` | 弹窗标题 | `el-dialog__title` | 弹窗区 | 通用定位器 |
| `FORM_ITEM_NAME` | 危废品名称输入框 | `el-input` | 弹窗区 | 用于输入新危废品名称 |
| `DIALOG_SAVE` | 保存按钮 | `el-button` | 弹窗区 | 通用定位器 |
| `DIALOG_CANCEL` | 取消按钮 | `el-button` | 弹窗区 | 通用定位器 |

## 3. 页面状态

| 状态 | 表现 | 交互/等待策略 |
|---|---|---|
| 加载中 | 表格区域出现 `el-loading-mask` 覆盖层 | 使用 `_wait_loading_gone()` 等待加载动画消失 |
| 空数据 | 表格区域显示空数据提示 | 搜索后应断言数据行数，或获取总数是否为0 |
| 错误状态 | 可能由后端接口返回，前端展示错误提示 | 依赖于 `el-message` 组件，由 BasePage 通用方法处理 |
| 弹窗打开 | `el-dialog` 出现，带有 `display: block` 样式 | 使用 `wait_dialog_open()` 等待弹窗动画完成 |

## 4. 权限点

根据测试脚本，未发现明显的权限控制点。所有测试用例均基于一个拥有完整访问权限的用户执行。所有可见元素（新增、删除、查询等）均可操作。如果未来引入权限控制，`新增`和`删除`按钮以及菜单入口将是潜在的权限控制点。

```

---

### PAGE_ELEMENT_POSITION.md

```markdown
# 元素定位器: 环保物品管理 (Hazard Item)

> **版本**: v1.0
> **更新日期**: 2024-06-13
> **遵循标准**: Element Plus 页面元素定位器设计规范
>
> **定位器优先级**:
> - **A级 (推荐)**: 基于 `data-testid`, `id`, `name`, `placeholder` 等稳定属性。
> - **B级 (备用)**: 基于稳定 CSS 类组合的 CSS Selector。
> - **C级 (兜底)**: 基于文本或属性匹配的 XPath。

## 元素定位器设计

| 元素ID | 元素描述 | 定位策略 | 定位值 | 稳定性评级 | 备用方案 (C级) |
|---|---|---|---|---|---|
| `FILTER_ITEM_NAME` | 危废品名称搜索框 | **A级**: placeholder | `//input[@placeholder="请输入危废品名称"]` | ⭐⭐⭐ (依赖于文字不变) | `//div[contains(@class, 'filter-area')]//input[contains(@placeholder, '危废品名称')]` |
| `BTN_QUERY` | 查询按钮 | **B级**: CSS Selector | `button.el-button--primary:has(span:contains("查询"))` (此Selector不标准，建议用XPath) | ⭐⭐ (依赖于按钮文字和类名) | `//button[span[text()='查询']]` |
| `BTN_RESET` | 重置按钮 | **B级**: CSS Selector | `button.el-button:has(span:contains("重置"))` (此Selector不标准，建议用XPath) | ⭐⭐ (依赖于按钮文字和类名) | `//button[span[text()='重置']]` |
| `BTN_ADD` | 新增按钮 | **B级**: CSS Selector | `button.el-button--primary:has(span:contains("新增"))` (此Selector不标准，建议用XPath) | ⭐⭐ (依赖于按钮文字和类名) | `//button[span[text()='新增']]` |
| `TABLE_ROWS` | 表格所有数据行 | **C级**: XPath | `//div[contains(@class, 'el-table__body-wrapper')]//tr[contains(@class, 'el-table__row')]` | ⭐⭐⭐ (依赖Element Plus 结构) |
| `COL_ACTIONS_BTN_DELETE` | 某行删除按钮 | **C级**: XPath (动态) | `(//div[contains(@class, 'el-table__body-wrapper')]//tr[contains(@class, 'el-table__row')][{rowIndex}]//button[span[text()='删除']])[1]` | ⭐ (行号变化会导致定位失败) | 使用 `click_row_button(name, "删除")` 方法，通过遍历行文本定位。 |
| `TOTAL_COUNT` | 分页器总条数 | **C级**: XPath | `//span[contains(@class, 'el-pagination__total')]` | ⭐⭐⭐ (依赖Element Plus 结构) |

## 关键方法定位器说明

| 方法名 | 元素ID | 定位思路 | 备注 |
|---|---|---|---|
| `delete_item_by_name(name)` | `COL_ACTIONS_BTN_DELETE` | 1. 搜索元素。2. 遍历表格行，通过 `text()` 找到包含指定 `name` 的行。3. 在该行内查找删除按钮并点击。 | 这是一种更稳健的定位方式，避免了硬编码行索引。 |
| `fill_item_name(name)` | `FORM_ITEM_NAME` | 通过 `_fill_dialog_by_placeholder("危废品名称", value)` 实现。1. 找到可见的 `el-dialog`。2. 在其中查找 `placeholder` 包含 “危废品名称” 的输入框。3. 使用 JS 设置值。 | 通过 JavaScript 直接操作输入框，可以避免很多输入法、事件触发等与 Selenium 交互的问题，是一种推荐的稳健做法。 |
| `click_row_button` (来自 `BasePage`) | `COL_ACTIONS_BTN_DELETE` | 未知，但根据方法名，它会搜索表格行，找到包含指定文本的行，然后在该行内找到包含指定文本的按钮。 | 这是一个通用的稳健方法，避免了对 XPath 行号的依赖。 |

## 等待策略

| 等待场景 | 等待方式 | 实现方法 | 备注 |
|---|---|---|---|
| 页面初始加载 | 自旋等待 | `_wait_page_ready()` → `wait_vue_stable()` + `_wait_loading_gone()` | 确保页面和列表完全加载。 |
| 搜索/重置后 | 自旋等待 | `wait_vue_stable()` | 等待数据刷新和页面重新渲染。 |
| 弹窗打开 | 自旋等待 | `wait_dialog_open()` | 等待 `el-dialog` 的动画出现。 |
| 新增保存后 | 自旋等待 | `wait_vue_stable()` | 等待数据提交和列表刷新。 |
| 点击删除后 | 自旋等待 | `confirm_message_box()` (内部会处理等待) | 等待确认弹框出现、操作、并关闭。 |

## 注意事项 (Element Plus 相关)

1.  **XPath 的使用**: 代码中广泛使用 `contains(.,"文本")` 来定位按钮。这是一种有效但稍显脆弱的方式。优点是能精确匹配，缺点是一旦前端修改了按钮文字，所有相关定位器都将失效。测试脚本中已大量使用，这是一个现状。未来可以考虑向 `data-testid` 迁移。
2.  **动态行索引**: 对于表格行操作，应避免使用固定的 XPath 行号 `[{rowIndex}]`。应优先使用如 `click_row_button` 这样通过文本内容查找行的方案。
3.  **Teleported 组件**: 本项目涉及到的 `el-select`、`el-date-picker` 等组件的下拉面板通常通过 Teleport 渲染在 `<body>` 下。当前页面未使用此类组件，但如果未来添加，需要注意其定位器需使用 `body > .el-popper` 格式。
4.  **Vue 异步更新**: `wait_vue_stable()` 是确保任何 Vue 异步操作（如数据更新、DOM渲染）完成的关键等待方法，应在每个操作后适当调用。当前代码已很好遵循此实践。
```