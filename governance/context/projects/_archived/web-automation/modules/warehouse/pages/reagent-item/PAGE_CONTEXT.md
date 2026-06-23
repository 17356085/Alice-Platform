# 页面上下文: 三剂消耗-物品管理 (Reagent Item)

| 元数据项 | 值 |
|---|---|
| 模块 | warehouse (库管管理) |
| 页面名称 | 三剂消耗-物品管理 |
| 访问路径 | 库管管理 → 三剂消耗管理 → 物品管理 |
| Hash 路由 | `#/warehouse/reagent/item` (从 conftest.py 推断) |
| 页面类型 | 列表页 (CRUD + 导入导出 + 批量选择) |
| 主要功能 | 查看、搜索、新增、删除、导入导出、批量选择三剂物品 |
| 审批流 | 无 |

## 1. 页面整体结构

该页面是一个典型的后台管理列表页，主要分为以下几个区域：

1. **顶部/导航**: 页面标题和面包屑导航（由框架提供，非本页特有）。
2. **搜索/筛选区 (Filter Area)**: 位于页面顶部，用于按条件筛选列表数据。
   - 包含：物品名称输入框、查询按钮、重置按钮。
3. **操作按钮区 (Action Area)**: 位于搜索区右侧或下方，包含业务操作入口。
   - 包含：新增按钮（从PO代码`BTN_ADD`推断）。
4. **表格/列表区 (Table Area)**: 用于展示三剂物品数据列表。
   - 包含：多选框列、物品名称列、其他数据列、操作列。
   - 操作列包含：删除按钮（从 `delete_item_by_name` 方法推断）。
5. **分页区 (Pagination Area)**: 位于表格底部，用于翻页和数据量统计。
6. **弹窗/对话框 (Dialog)**: 用于新增物品的表单操作。

## 2. 页面元素清单

### 2.1 搜索/筛选区

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `FILTER_ITEM_NAME` | 物品名称搜索框 | `el-input` | 搜索区 | placeholder="请输入物品名称" |
| `BTN_QUERY` | 查询按钮 | `el-button` | 搜索区 | 触发搜索 |
| `BTN_RESET` | 重置按钮 | `el-button` | 搜索区 | 重置搜索条件 |

### 2.2 操作按钮区

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `BTN_ADD` | 新增按钮 | `el-button` | 操作区 | 打开新增弹窗 |

### 2.3 表格/列表区

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `TABLE` | 数据表格容器 | `el-table` | 表格区 | 包含所有数据行 |
| `TABLE_HEADER` | 表头行 | `el-table__header-wrapper` | 表格区 | 包含列标题 |
| `TABLE_ROWS` | 所有数据行 | `el-table__row` | 表格区 | 继承自 BasePage |
| `COL_CHECKBOX` | 多选框列（表头） | `el-checkbox` | 表格区 | 选择所有行，从方法推断 |
| `COL_ITEM_NAME` | 物品名称列 | `el-table-column` | 表格区 | 文本显示，从搜索字段推断 |
| `COL_ACTIONS` | 操作列 | `el-table-column` | 表格区 | 包含"删除"按钮 |
| `BTN_DELETE` | 删除按钮 | `el-button` | 表格区操作列 | 针对单行数据，从 `delete_item_by_name` 推断 |

### 2.4 分页区

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `PAGINATION` | 分页组件容器 | `el-pagination` | 分页区 | 包含分页所有子元素 |
| `TOTAL_COUNT` | 总条数显示 | `el-pagination__total` | 分页区 | 继承自 BasePage |

### 2.5 弹窗/对话框 (新增)

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `DIALOG` | 新增表单弹窗 | `el-dialog` | 弹窗区 | 通用定位器，继承自BasePage |
| `DIALOG_TITLE` | 弹窗标题 | `el-dialog__title` | 弹窗区 | 通用定位器 |
| `FORM_ITEM_NAME` | 物品名称输入框 | `el-input` | 弹窗区 | placeholder="物品名称"，通过JS动态查找 |
| `DIALOG_SAVE` | 保存按钮 | `el-button` | 弹窗区 | 通用定位器，继承自BasePage |
| `DIALOG_CANCEL` | 取消按钮 | `el-button` | 弹窗区 | 通用定位器，继承自BasePage |

## 3. 页面状态

| 状态 | 表现 | 交互/等待策略 |
|---|---|---|
| 加载中 | 表格区域出现 `el-loading-mask` 覆盖层 | 使用 `_wait_loading_gone()` 等待加载动画消失 |
| 空数据 | 表格区域显示空数据提示 | 搜索后应断言数据行数，或获取总数是否为0 |
| 错误状态 | 可能由后端接口返回，前端展示错误提示 | 依赖于 `el-message` 组件，由 BasePage 通用方法处理 |
| 弹窗打开 | `el-dialog` 出现，带有 `display: block` 样式 | 使用 `wait_dialog_open()` 等待弹窗动画完成 |
| 弹窗表单校验 | 保存时若必填项为空，输入框下方显示错误提示 | 使用 `get_form_error()` 获取校验信息 |

## 4. 权限点

根据测试脚本，未发现明显的权限控制点。所有测试用例均基于一个拥有完整访问权限的用户执行。如果未来引入权限控制，新增、删除按钮以及页面菜单入口将是潜在的权限控制点。

## 5. 业务规则（从代码推断）

| ID | 规则描述 | 来源 |
|---|---|---|
| BR-RI-001 | 物品名称不能为空。保存时若为空，弹窗内显示必填校验错误信息 | 从 `test_add_empty_required` 测试推断 |
| BR-RI-002 | 物品名称在同一系统内应唯一（从功能逻辑推断） | 从功能逻辑推断 |
| BR-RI-003 | 已关联消耗记录的物品不允许删除（从通用仓库业务逻辑推断） | 从业务逻辑推断 |
| BR-RI-004 | 取消新增后，不创建任何数据 | 从 `test_add_item_cancel` 测试推断 |

## 6. 测试场景映射

| 测试类 | 测试方法 | 覆盖场景 |
|---|---|---|
| TestReagentItemLoad | test_page_loads | 页面正常加载验证 |
| TestReagentItemLoad | test_pagination_visible | 分页组件可见性验证 |
| TestReagentItemLoad | test_add_button_visible | 新增按钮可见性验证 |
| TestReagentItemSearch | test_search_by_item_name | 按物品名称搜索冒烟 |
| TestReagentItemSearch | test_reset_search | 重置搜索条件冒烟 |
| TestReagentItemInteraction | test_add_dialog_opens | 点击新增弹窗弹出验证 |
| TestReagentItemInteraction | test_add_dialog_has_form_fields | 弹窗表单字段存在性验证 |
| TestReagentItemCRUD | test_add_item_success | 新增物品成功 — 正向链路 |
| TestReagentItemCRUD | test_delete_created_item | 删除刚创建的物品 — 逆向链路 |
| TestReagentItemCRUD | test_add_item_cancel | 新增物品取消操作 |
| TestReagentItemCRUD | test_add_empty_required | 必填校验验证 |
