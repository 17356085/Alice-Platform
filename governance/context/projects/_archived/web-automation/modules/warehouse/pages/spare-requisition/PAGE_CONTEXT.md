# 页面上下文: 备品领用申请 (Spare Requisition)

## 1. 页面信息

| 属性 | 值 |
|------|-----|
| 页面名称 | 备品领用申请 |
| 模块 | warehouse（库管管理） |
| 导航路径 | 库管管理 > 备品备件管理 > 领用申请 |
| PO 类 | `SpareRequisitionPage` (文件: `page/warehouse_page/SpareRequisitionPage.py`) |
| 测试文件 | `script/warehouse/test_spare_requisition.py` |
| 审批链 | 备件领用申请审批链 (admin+chenqian -> tjw) |
| 技术栈 | Vue 3 + Element Plus |
| 测试框架 | Selenium 4 + pytest |

## 2. 搜索/筛选区

搜索区共 3 个筛选字段。注意搜索区使用自定义 `wh-filter-toolbar` 组件（非标准 Element Plus 搜索布局），流程状态下拉框定位依赖于该自定义容器的层级结构。

| 序号 | 元素名称 | 标签/Placeholder | 控件类型 | 精确 Locator | PO 常量 | 备注 |
|------|----------|-----------------|----------|--------------|---------|------|
| 1 | 申请人 | `请输入申请人` | `el-input` | `//input[@placeholder="请输入申请人"]` | `FILTER_APPLICANT` | 文本输入，模糊搜索 |
| 2 | 日期 | `选择日期` | `el-date-picker` | `//input[@placeholder="选择日期"]` | `FILTER_DATE` | 日期选择器，测试中未直接使用（从 locator 定义推断） |
| 3 | 流程状态 | 无 placeholder | `el-select`（在下拉触发器为 div） | `(//div[contains(@class,"wh-filter-toolbar")]//div[contains(@class,"el-select__wrapper")])[1]` | `FILTER_STATUS` | **注意**：使用自定义 `wh-filter-toolbar` 容器限定范围，定位器脆弱。测试中未直接使用该字段（从 locator 定义推断） |

操作按钮:

| 按钮 | 精确 Locator | PO 常量 | 触发动作 | 备注 |
|------|-------------|---------|----------|------|
| 查询 | `//button[contains(.,"查询")]` | `BTN_QUERY` | 搜索 | 标准文本定位 |
| 重置 | `//button[contains(.,"重置")]` | `BTN_RESET` | 重置搜索条件 | 标准文本定位 |

## 3. 工具栏按钮

| 按钮 | 精确 Locator | PO 常量 | 触发动作 | 备注 |
|------|-------------|---------|----------|------|
| 新增 | `//button[contains(.,"新增")]` | `BTN_ADD` | 打开新增弹窗 | 工具栏按钮 |

## 4. 表格与行内操作按钮

表格使用 Element Plus `el-table` 组件。

- **表格行 locator**: `BasePage.TABLE_ROWS` (`.el-table__body-wrapper tbody tr.el-table__row`)
- **列数范围**: 6 <= headers <= 14（从测试 `test_columns_count` 断言推断）
- **特殊列**: 流程状态列使用 `el-tag` 渲染（从 `get_first_row_status()` 方法推断，该方法读取第一行内的 `.el-tag` 文本）
- **业务列推断**: 包含申请人列（搜索字段）、日期列、流程状态列（el-tag）等（中置信度，从 PO 方法和业务领域推断）

### 行内操作按钮（按工作流状态动态显隐）

| 按钮 | 精确 Locator | PO 常量 | 可见性条件 | 触发动作 |
|------|-------------|---------|-----------|----------|
| 查看 | `//button[contains(.,"查看")]` | `BTN_VIEW` | 始终可见（中置信度） | 打开详情弹窗 |
| 编辑 | `//button[contains(.,"编辑")]` | `BTN_EDIT` | 仅草稿/待提交状态（中置信度，从工作流推断） | 打开编辑弹窗 |
| 提交 | `//button[contains(.,"提交")]` | `BTN_SUBMIT` | 仅草稿/待提交状态（中置信度，从工作流推断） | 提交审批，触发 Toast |
| 删除 | `//button[contains(.,"删除")]` | `BTN_DELETE` | 仅草稿/待提交状态（中置信度，从 delete_by_name 的 try/except 推断） | 删除确认弹窗 |

**注意**: 以上四个按钮为行内操作按钮，非工具栏按钮。可见性取决于该行数据的工作流状态。测试通过 `has_edit_button()`, `has_submit_button()`, `has_delete_button()` 三个方法进行存在性检测。

## 5. 弹窗 (Dialog)

### 新增/编辑弹窗

- **触发方法**: `click_add()` (点击新增 -> `wait_dialog_open()`) / `click_edit_first()` (点击编辑)
- **关闭方法**: `click_dialog_cancel()` / `click_dialog_save()` (继承自 BasePage)
- **表单字段**:

| 字段 | Placeholder | PO 填充方法 | 类型 | 必填 |
|------|-------------|-------------|------|------|
| 申请人 | `申请人` | `fill_requisition_applicant(name)` -> `_fill_dialog_by_placeholder("申请人", name)` | `el-input` | 是（中置信度，测试中填写后依赖此字段搜索验证） |

- **填充机制**: 使用 JavaScript 注入 `_fill_dialog_by_placeholder(placeholder_contains, value)`。遍历弹窗内所有非隐藏 `input`，匹配 placeholder 后设置 value 并触发 `input`/`change` 事件。无 fallback 逻辑，未匹配时仅打印警告。
- **测试验证方式**: `test_add_dialog_has_save_button` 检查弹窗内存在保存按钮（`DIALOG_SAVE`），而非检查表单字段数量。这与 spare-out-order 不同。

### 查看弹窗

- **触发方法**: `click_view_first()` (点击第一行查看按钮 -> `wait_dialog_open()`)
- **关闭方法**: `click_dialog_cancel()`

## 6. 业务规则 (从代码推断)

| 规则 | 描述 | 置信度 | 来源 |
|------|------|--------|------|
| 搜索流程 | 输入申请人名称 -> 点击查询 -> 等待 Vue 稳定 | 高 | `search_by_applicant()` 方法体 |
| 重置流程 | 先搜索 -> 点击重置 -> 等待 Vue 稳定 | 高 | `test_reset_search` 测试体 |
| 新增流程 | 点击新增 -> 弹窗打开 -> 填写表单 -> 保存/取消 | 高 | `test_add_requisition_success` / `test_add_requisition_cancel` |
| 编辑流程 | 点击编辑 -> 弹窗打开（仅当有编辑按钮时） | 高 | `test_edit_dialog_opens` 测试体 |
| 提交流程 | 点击提交 -> Toast 提示（仅当有提交按钮时） | 高 | `test_submit_button_triggers_toast` + `click_submit_first()` |
| 删除流程 | 点击删除 -> 确认消息框 -> Toast 提示 | 高 | `click_delete_first()` 方法体 |
| 删除兜底 | 已审批记录不允许删除，try/except 捕获异常仅警告 | 高 | `delete_by_name()` 的 try/except 逻辑 |
| 动态按钮可见性 | 查看/编辑/提交/删除按钮按工作流状态动态显隐 | 高 | `has_*_button()` 方法 + 测试断言 |
| 流程状态读取 | 第一行状态通过 `.el-tag` 读取 | 高 | `get_first_row_status()` 方法体 |
| JS 弹窗填充 | 弹窗内按 placeholder 定位输入框并 JS 赋值 | 高 | `_fill_dialog_by_placeholder()` 方法体 |
| 新增后数据验证 | 搜索新建记录 -> 确认存在 -> 比较总数 | 高 | `test_add_requisition_success` |
| 取消后数据不存在 | 填写后取消 -> 搜索确认不存在 | 高 | `test_add_requisition_cancel` |
| 必填校验 | 空表单保存 -> 获取前端校验错误提示 | 中 | `test_add_empty_required` |
| 列数范围 | 表头列数在 6-14 之间 | 中 | `test_columns_count` 断言 |
| 审批链 | 备件领用申请审批链，admin+chenqian -> tjw | 高 | PO 类文档字符串 |
| 自定义搜索组件 | wh-filter-toolbar 自定义容器包裹搜索区域 | 高 | `FILTER_STATUS` locator 使用 wh-filter-toolbar 类限定 |
| 提交含 Toast | `click_submit_first` 内部调用 `wait_for_toast_text` | 高 | `click_submit_first()` 方法体 |
| 删除含 Toast | `click_delete_first` 调用 `confirm_message_box` + `wait_for_toast_text` | 高 | `click_delete_first()` 方法体 |

## 7. 测试场景映射

### TestSpareRequisitionLoad (4 个)

| 测试方法 | 场景描述 | 验证点 |
|----------|----------|--------|
| `test_page_loads` | 页面正常加载 | 表格行渲染，`len(rows) >= 0` |
| `test_columns_count` | 表格列数合理 | JS 获取 `th` 数量，断言 6 <= headers <= 14 |
| `test_add_button_visible` | 新增按钮可见 | `BTN_ADD` 元素存在 |
| `test_pagination_visible` | 分页组件可见 | `TOTAL_COUNT` 元素存在 |

### TestSpareRequisitionSearch (2 个)

| 测试方法 | 场景描述 | 验证点 |
|----------|----------|--------|
| `test_search_by_applicant` | 按申请人搜索 | 搜索流程无异常 |
| `test_reset_search` | 重置搜索条件 | 先搜索 -> 重置 -> 流程无异常 |

### TestSpareRequisitionInteraction (3 个)

| 测试方法 | 场景描述 | 验证点 |
|----------|----------|--------|
| `test_add_dialog_opens` | 点击新增弹窗打开 | `is_dialog_visible()` 为 True |
| `test_add_dialog_has_save_button` | 弹窗有保存按钮 | `DIALOG_SAVE` 元素存在 |
| `test_view_first_record` | 查看第一行记录 | 查看弹窗打开，`is_dialog_visible()` 为 True |

### TestSpareRequisitionRowActions (4 个)

| 测试方法 | 场景描述 | 验证点 |
|----------|----------|--------|
| `test_first_row_action_buttons_exist` | 第一行至少有一个操作按钮 | `has_view or has_edit or has_submit or has_delete` |
| `test_edit_dialog_opens` | 编辑按钮打开编辑弹窗 | `is_dialog_visible()` 为 True |
| `test_first_row_status_readable` | 第一行流程状态可读取 | `isinstance(status, str)` |
| `test_submit_button_triggers_toast` | 提交按钮触发 Toast | `click_submit_first` 内部 `wait_for_toast_text` 无异常 |

### TestSpareRequisitionCRUD (4 个)

| 测试方法 | 场景描述 | 验证点 |
|----------|----------|--------|
| `test_add_requisition_success` | 新增领用申请 | 创建后 `after_count >= before_count + 1` |
| `test_delete_created_requisition` | 删除刚创建的记录 | 删除后 `not is_row_present(applicant)` |
| `test_add_requisition_cancel` | 新增取消 | 取消后 `not is_row_present(applicant)` |
| `test_add_empty_required` | 必填校验 | 空表单保存，`get_form_error()` 返回错误信息或日志记录 |
