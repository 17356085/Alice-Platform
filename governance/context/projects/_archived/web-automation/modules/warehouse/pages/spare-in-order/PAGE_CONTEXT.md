# Page Context: spare-in-order (备品入库)

## Page Information

| Field | Value |
|-------|-------|
| Page ID | spare-in-order |
| Chinese Name | 备品入库 |
| Navigation Route | 库管管理 > 备品备件管理 > 入库 |
| PO Class | SpareInOrderPage |
| Test File | test_spare_in_order.py |
| Module | warehouse |
| Package | ZJSN_Test-master526 |

---

## Search / Filter Fields

| 搜索字段 | 标签 | 类型 | 定位器 | 来源 |
|----------|------|------|--------|------|
| 经办人 | 请输入经办人 | el-input | `//input[@placeholder="请输入经办人"]` | PO代码 |
| 日期 | 选择日期 | el-date-picker | `//input[@placeholder="选择日期"]` | PO代码 |

---

## Action Buttons

| 按钮 | 定位器 | 来源 |
|------|--------|------|
| 查询 (BTN_QUERY) | `//button[contains(.,"查询")]` | PO代码 |
| 重置 (BTN_RESET) | `//button[contains(.,"重置")]` | PO代码 |
| 新增入库 (BTN_ADD) | `//button[contains(.,"新增入库")]` | PO代码 |
| 查看 (BTN_VIEW) | `//button[contains(.,"查看")]` | PO代码 |

> Note: BTN_ADD uses non-standard button text "新增入库" (not "新增").

---

## Table Columns

Table has 8 columns (inferred from `test_columns_count: 6 <= headers <= 12`).

| # | 列名 | 推断依据 | 置信度 |
|---|------|----------|--------|
| 1-8 | (列名未在PO中定义) | 已知8列，具体列名未知 | 低 |

- Table count assertions exist (via `is_row_present`)
- Column count validated: `6 <= headers <= 12`
- Pagination control is tested (`test_pagination_visible`)

---

## Dialogs

| 对话框 | 触发按钮 | 表单字段 | 来源 |
|--------|----------|----------|------|
| 新增入库单 | BTN_ADD (新增入库) | 经办人 (el-input, placeholder="经办人") | PO代码 |

---

## Approval Chain

| 字段 | 值 |
|------|-----|
| 审批链名称 | 备件入库审批链 |
| 审批方式 | admin 会签 |
| 审批影响 | 新增入库单需审批通过后方可生效 |

---

## Business Rules

| 规则 ID | 描述 | 验证点 | 置信度 |
|---------|------|--------|--------|
| BR-SIO-01 | 经办人为必填项，空提交触发错误 | `test_add_empty_required` (error logged, dialog closed) | 高 (测试脚本) |
| BR-SIO-02 | 新增入库单生成新数据行 | `after >= before + 1` | 高 (测试脚本) |
| BR-SIO-03 | 删除入库单移除对应数据行 | `not is_row_present` | 高 (测试脚本) |
| BR-SIO-04 | 取消新增不生成数据行 | `not is_row_present` | 高 (测试脚本) |
| BR-SIO-05 | 支持按经办人搜索过滤 | `search_by_handler` | 高 (测试脚本) |
| BR-SIO-06 | 支持按日期搜索过滤 | `FILTER_DATE` 定位器存在 | 中 (定位器推断) |
| BR-SIO-07 | 重置按钮清除搜索条件 | `reset_search` | 高 (测试脚本) |
| BR-SIO-08 | 查看按钮可打开第一条记录的详情 | `click_view_first` | 中 (方法名推断) |
| BR-SIO-09 | 表格列数在6-12之间 | `6 <= headers <= 12` | 高 (测试脚本) |
| BR-SIO-10 | 数据名称使用时间戳前缀 `AUTO_IN_` 确保唯一性 | 测试数据 | 高 (测试脚本) |

---

## Test Scenario Mapping

| 测试函数 | 测试场景 | 验证要点 |
|----------|----------|----------|
| TestSpareInOrderLoad::test_page_loads | 页面加载 | 页面元素渲染，表格数据加载 |
| TestSpareInOrderLoad::test_columns_count | 表格列数 | 列头数量在6-12之间 |
| TestSpareInOrderLoad::test_add_button_visible | 新增入库按钮可见 | 新增入库按钮渲染 |
| TestSpareInOrderLoad::test_pagination_visible | 分页控件可见 | 分页组件渲染 |
| TestSpareInOrderSearch::test_search_by_handler | 按经办人搜索 | 输入搜索条件，触发查询 |
| TestSpareInOrderSearch::test_reset_search | 重置搜索 | 重置按钮清除搜索条件 |
| TestSpareInOrderInteraction::test_add_dialog_opens | 新增对话框打开 | 点击新增入库按钮弹出对话框 |
| TestSpareInOrderInteraction::test_add_dialog_has_form_fields | 对话框表单字段 | 对话框含经办人输入框 |
| TestSpareInOrderInteraction::test_view_first_record | 查看第一条记录 | 点击查看按钮浏览首行详情 |
| TestSpareInOrderCRUD::test_add_in_order_success | 新增成功 | 行存在，count增加 |
| TestSpareInOrderCRUD::test_delete_created_in_order | 删除成功 | 行不再存在 |
| TestSpareInOrderCRUD::test_add_in_order_cancel | 取消新增 | 行不存在，对话框关闭 |
| TestSpareInOrderCRUD::test_add_empty_required | 空提交验证 | 错误记录，对话框关闭 |

---

## Public API Surface

| 方法 | 参数 | 用途 | 来源 |
|------|------|------|------|
| `navigate()` | - | 导航至页面 | PO代码 |
| `click_add()` | - | 点击新增入库按钮 | PO代码 |
| `click_view_first()` | - | 查看第一条记录详情 | PO代码 |
| `search_by_handler(name)` | str | 按经办人搜索 | PO代码 |
| `reset_search()` | - | 重置搜索条件 | PO代码 |
| `fill_in_order_handler(name)` | str | 在对话框填入经办人 | PO代码 |
| `click_search()` | - | 点击查询按钮 | PO代码 |
| `delete_by_handler(name)` | str | 按经办人删除数据 | PO代码 |
| `_fill_dialog_by_placeholder(placeholder_contains, value)` | str, str | JS辅助填写对话框输入框（含降级策略） | PO代码（内部方法） |

---

## Test Data Constants

| 常量 | 格式 | 用途 |
|------|------|------|
| 新增测试数据 | `AUTO_IN_{timestamp}` | 新增CRUD测试 |
| 取消测试数据 | `AUTO_CANCEL_{timestamp}` | 取消操作测试 |

## Cross-Test Data Sharing

- `CREATED_HANDLER` 类变量在类级别共享，用于在新增和删除测试间传递数据

## Cleanup Strategy

- 主清理: `delete_by_handler(name)` 在测试中直接调用
- 兜底清理: `cleanup_tracker` fixture 确保即使测试失败也清理残留数据
