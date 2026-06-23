# 页面上下文: 备品出库 (Spare Out Order)

## 1. 页面信息

| 属性 | 值 |
|------|-----|
| 页面名称 | 备品出库 |
| 模块 | warehouse（库管管理） |
| 导航路径 | 库管管理 > 备品备件管理 > 出库 |
| PO 类 | `SpareOutOrderPage` (文件: `page/warehouse_page/SpareOutOrderPage.py`) |
| 测试文件 | `script/warehouse/test_spare_out_order.py` |
| 审批链 | 备件出库审批链 (admin+chenqian 会签) |
| 技术栈 | Vue 3 + Element Plus |
| 测试框架 | Selenium 4 + pytest |

## 2. 搜索/筛选区

搜索区共 2 个筛选字段，使用标准 Element Plus 组件。

| 序号 | 元素名称 | 标签/Placeholder | 控件类型 | 精确 Locator | PO 常量 | 备注 |
|------|----------|-----------------|----------|--------------|---------|------|
| 1 | 经办人 | `请输入经办人` | `el-input` | `//input[@placeholder="请输入经办人"]` | `FILTER_HANDLER` | 文本输入，模糊搜索（中置信度，从搜索方法名推断） |
| 2 | 日期 | `选择日期` | `el-date-picker` | `//input[@placeholder="选择日期"]` | `FILTER_DATE` | 日期选择器，测试中未直接使用该字段（从 locator 定义推断） |

操作按钮:

| 按钮 | 精确 Locator | PO 常量 | 触发动作 | 备注 |
|------|-------------|---------|----------|------|
| 查询 | `//button[contains(.,"查询")]` | `BTN_QUERY` | 搜索 | 标准文本定位 |
| 重置 | `//button[contains(.,"重置")]` | `BTN_RESET` | 重置搜索条件 | 标准文本定位 |

## 3. 工具栏按钮

| 按钮 | 精确 Locator | PO 常量 | 触发动作 | 备注 |
|------|-------------|---------|----------|------|
| 新增 | `//button[contains(.,"新增")]` | `BTN_ADD` | 打开新增弹窗 | 工具栏按钮，触发 el-dialog |
| 备件查询 | `//button[contains(.,"备件查询")]` | `BTN_SPARE_QUERY` | 导航到备件查询页面 | **非弹窗操作**，导航到不同页面 |

## 4. 表格

表格使用 Element Plus `el-table` 组件。

- **表格行 locator**: `BasePage.TABLE_ROWS` (`.el-table__body-wrapper tbody tr.el-table__row`)
- **列数范围**: 8 <= headers <= 28（从测试 `test_columns_count` 断言推断）
- **业务列推断**: 包含 LY 单号列（点击链接跳转）、经办人列（搜索字段）、日期列、状态列等（中置信度，从 PO 方法名和业务领域推断）

已知的特殊列:

| 列名 | 类型 | 说明 |
|------|------|------|
| LY 单号 | 链接 (button) | 使用 CSS 类 `.el-button--primary.is-link`，文本以 `LY` 开头。通过 `click_ly_link(ly_number)` 点击，使用 XPath `//button[contains(.,"{ly_number}")]` |

操作列按钮:

| 按钮 | 精确 Locator | PO 常量 | 可见性 |
|------|-------------|---------|--------|
| 查看 | `//button[contains(.,"查看")]` | `BTN_VIEW` | 始终可见（中置信度，从 PO 定义推断） |
| 删除 | （通过 `click_row_button` 通用方法） | 无独立常量 | 草稿/待审批状态（中置信度，从 delete_by_handler 方法推断） |

## 5. 弹窗 (Dialog)

### 新增弹窗

- **触发方法**: `click_add()` (点击新增 -> 等待 `wait_dialog_open`)
- **关闭方法**: `click_dialog_cancel()` / `click_dialog_save()` (继承自 BasePage)
- **表单字段**:

| 字段 | Placeholder | PO 填充方法 | 类型 | 必填 |
|------|-------------|-------------|------|------|
| 经办人 | `经办人` | `fill_out_order_handler(name)` -> `_fill_dialog_by_placeholder("经办人", name)` | `el-input` | 是（中置信度，测试中填写后依赖此字段搜索验证） |

- **填充机制**: 使用 JavaScript 注入 `_fill_dialog_by_placeholder(placeholder_contains, value)`。遍历弹窗内所有非隐藏 `input`，匹配 placeholder 后设置 value 并触发 `input`/`change` 事件。无 fallback 逻辑，未匹配时仅打印警告。

### 查看弹窗

- **触发方法**: `click_view_first()` (点击第一行查看按钮 -> `wait_dialog_open`)
- **关闭方法**: `click_dialog_cancel()`

## 6. 业务规则 (从代码推断)

| 规则 | 描述 | 置信度 | 来源 |
|------|------|--------|------|
| 搜索流程 | 输入经办人名称 -> 点击查询 -> 等待 Vue 稳定 | 高 | `search_by_handler()` 方法体 |
| 重置流程 | 点击重置 -> 等待 Vue 稳定 | 高 | `reset_search()` 方法体 |
| 新增流程 | 点击新增 -> 弹窗打开 -> 填写表单 -> 保存/取消 | 高 | `test_add_out_order_success` / `test_add_out_order_cancel` |
| 删除流程 | 搜索记录 -> 点击行内删除按钮 -> 确认消息框 | 高 | `delete_by_handler()` 方法体 |
| LY 单号点击 | 按文本匹配 `button` 元素并点击 | 高 | `click_ly_link()` 方法体 |
| 备件查询导航 | 点击后跳转至其他页面，非弹窗 | 高 | `click_spare_query()` 方法体 |
| JS 弹窗填充 | 弹窗内按 placeholder 定位输入框并 JS 赋值 | 高 | `_fill_dialog_by_placeholder()` 方法体 |
| 新增后数据验证 | 搜索新建记录 -> 确认存在 -> 比较总数 | 高 | `test_add_out_order_success` |
| 取消后数据不存在 | 填写后取消 -> 搜索确认不存在 | 高 | `test_add_out_order_cancel` |
| 必填校验 | 空表单保存 -> 获取前端校验错误提示 | 中 | `test_add_empty_required` |
| 删除确认 | 删除需确认 MessageBox | 高 | `delete_by_handler()` 调用 `confirm_message_box()` |
| 清理兜底 | 删除失败时注册 CleanupTracker 回调 | 高 | `test_delete_created_out_order` |
| 列数范围 | 表头列数在 8-28 之间 | 中 | `test_columns_count` 断言 |
| 审批链 | 备件出库审批链，admin+chenqian 会签 | 高 | PO 类文档字符串 |

## 7. 测试场景映射

### TestSpareOutOrderLoad (5 个)

| 测试方法 | 场景描述 | 验证点 |
|----------|----------|--------|
| `test_page_loads` | 页面正常加载 | 表格行渲染，`len(rows) >= 0` |
| `test_columns_count` | 表格列数合理 | JS 获取 `th` 数量，断言 8 <= headers <= 28 |
| `test_pagination_visible` | 分页组件可见 | `TOTAL_COUNT` 元素存在 |
| `test_add_button_visible` | 新增按钮可见 | `BTN_ADD` 元素存在 |
| `test_spare_query_button_visible` | 备件查询按钮可见 | `BTN_SPARE_QUERY` 元素存在 |

### TestSpareOutOrderSearch (2 个)

| 测试方法 | 场景描述 | 验证点 |
|----------|----------|--------|
| `test_search_by_handler` | 按经办人搜索 | 搜索流程无异常 |
| `test_reset_search` | 重置搜索条件 | 重置流程无异常 |

### TestSpareOutOrderInteraction (5 个)

| 测试方法 | 场景描述 | 验证点 |
|----------|----------|--------|
| `test_add_dialog_opens` | 点击新增弹窗打开 | `is_dialog_visible()` 为 True |
| `test_add_dialog_has_form_fields` | 弹窗有表单输入项 | JS 检查弹窗内 input/textarea 数量 >= 1 |
| `test_ly_link_clickable` | LY 单号链接可点击 | 查找 `.el-button--primary.is-link` 文本以 LY 开头，点击无异常 |
| `test_spare_query_clickable` | 备件查询按钮可点击 | 点击后页面无异常（导航到其他页面） |
| `test_view_first_record` | 查看第一行记录 | 查看弹窗打开，`is_dialog_visible()` 为 True |

### TestSpareOutOrderCRUD (4 个)

| 测试方法 | 场景描述 | 验证点 |
|----------|----------|--------|
| `test_add_out_order_success` | 新增出库记录 | 创建后 `after_count >= before_count + 1` |
| `test_delete_created_out_order` | 删除刚创建的记录 | 删除后 `not is_row_present(handler)` |
| `test_add_out_order_cancel` | 新增取消 | 取消后 `not is_row_present(handler)` |
| `test_add_empty_required` | 必填校验 | 空表单保存，`get_form_error()` 返回错误信息或日志记录 |
