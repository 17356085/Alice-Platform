# Page Context: reagent-fill (三剂消耗-装填管理)

## Page Information

| Field | Value |
|-------|-------|
| Page ID | reagent-fill |
| Chinese Name | 三剂消耗-装填管理 |
| Navigation Route | 库管管理 > 三剂消耗管理 > 装填管理 |
| PO Class | ReagentFillPage |
| Test File | test_reagent_fill.py |
| Module | warehouse |
| Package | ZJSN_Test-master526 |

---

## Search / Filter Fields

| 搜索字段 | 标签 | 类型 | 定位器 | 来源 |
|----------|------|------|--------|------|
| 三剂名称 | 请输入三剂名称 | el-input | `//input[@placeholder="请输入三剂名称"]` | PO代码 |

---

## Action Buttons

| 按钮 | 定位器 | 来源 |
|------|--------|------|
| 查询 (BTN_QUERY) | `//button[contains(.,"查询")]` | PO代码 |
| 重置 (BTN_RESET) | `//button[contains(.,"重置")]` | PO代码 |
| 新增 (BTN_ADD) | `//button[contains(.,"新增")]` | PO代码 |

---

## Table Columns

Table columns are not explicitly defined in the PO code. Column structure is inferred from test behavior and domain knowledge:

| # | 列名 | 推断依据 | 置信度 |
|---|------|----------|--------|
| 1 | 三剂名称 | 搜索字段/对话框字段 | 高 |
| - | (其他列) | 未在PO中定义 | 未知 |

- Table count assertions exist (via `is_row_present`)
- Pagination control is tested (`test_pagination_visible`)

---

## Dialogs

| 对话框 | 触发按钮 | 表单字段 | 来源 |
|--------|----------|----------|------|
| 新增装填记录 | BTN_ADD | 三剂名称 (el-input, placeholder="三剂名称") | PO代码 |

---

## Business Rules

| 规则 ID | 描述 | 验证点 | 置信度 |
|---------|------|--------|--------|
| BR-RF-01 | 三剂名称为必填项，提交空表单显示错误信息 | `assert error != ""` | 高 (测试脚本) |
| BR-RF-02 | 新增装填记录生成新数据行 | `after >= before + 1` | 高 (测试脚本) |
| BR-RF-03 | 删除装填记录移除对应数据行 | `not is_row_present` | 高 (测试脚本) |
| BR-RF-04 | 取消新增不生成数据行 | `not is_row_present` | 高 (测试脚本) |
| BR-RF-05 | 支持按三剂名称搜索过滤 | `search_by_item_name` | 高 (测试脚本) |
| BR-RF-06 | 重置按钮清除搜索条件 | `reset_search` | 高 (测试脚本) |
| BR-RF-07 | 数据名称使用时间戳前缀 `AUTO_装填_` 确保唯一性 | 测试数据 | 高 (测试脚本) |

---

## Test Scenario Mapping

| 测试函数 | 测试场景 | 验证要点 |
|----------|----------|----------|
| TestReagentFillLoad::test_page_loads | 页面加载 | 页面元素渲染，表格数据加载 |
| TestReagentFillLoad::test_pagination_visible | 分页控件可见 | 分页组件渲染 |
| TestReagentFillLoad::test_add_button_visible | 新增按钮可见 | 新增按钮渲染 |
| TestReagentFillSearch::test_search_by_item_name | 按名称搜索 | 输入搜索条件，触发查询 |
| TestReagentFillSearch::test_reset_search | 重置搜索 | 重置按钮清除搜索条件 |
| TestReagentFillInteraction::test_add_dialog_opens | 新增对话框打开 | 点击新增按钮弹出对话框 |
| TestReagentFillInteraction::test_add_dialog_has_form_fields | 对话框表单字段 | 对话框含三剂名称输入框 |
| TestReagentFillCRUD::test_add_item_success | 新增成功 | 行存在，count增加 |
| TestReagentFillCRUD::test_delete_created_item | 删除成功 | 行不再存在 |
| TestReagentFillCRUD::test_add_item_cancel | 取消新增 | 行不存在 |
| TestReagentFillCRUD::test_add_empty_required | 空提交验证 | 错误信息非空 |

---

## Public API Surface

| 方法 | 参数 | 用途 | 来源 |
|------|------|------|------|
| `navigate()` | - | 导航至页面 | PO代码 |
| `click_add()` | - | 点击新增按钮 | PO代码 |
| `search_by_item_name(name)` | str | 按名称搜索 | PO代码 |
| `reset_search()` | - | 重置搜索条件 | PO代码 |
| `fill_item_name(name)` | str | 在对话框填入名称 | PO代码 |
| `click_search()` | - | 点击查询按钮 | PO代码 |
| `delete_item_by_name(name)` | str | 按名称删除数据 | PO代码 |
| `_fill_dialog_by_placeholder(placeholder_contains, value)` | str, str | JS辅助填写对话框输入框 | PO代码（内部方法） |

---

## Test Data Constants

| 常量 | 格式 | 用途 |
|------|------|------|
| 新增测试数据 | `AUTO_装填_{timestamp}` | 新增CRUD测试 |
| 取消测试数据 | `AUTO_CANCEL_{timestamp}` | 取消操作测试 |

## Cleanup Strategy

- 主清理: `delete_item_by_name(name)` 在测试中直接调用
- 兜底清理: `cleanup_tracker` fixture 确保即使测试失败也清理残留数据
- 跨测试数据共享: 通过 `CREATED_NAME` 类变量（方法名推断）
