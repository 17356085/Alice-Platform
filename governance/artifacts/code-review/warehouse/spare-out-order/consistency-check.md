# Code Consistency Check — warehouse/spare-out-order

**Module**: warehouse
**Page**: spare-out-order
**PO Class**: SpareOutOrderPage
**PO File**: `ZJSN_Test-master526/page/warehouse_page/SpareOutOrderPage.py`
**Test File**: `ZJSN_Test-master526/script/warehouse/test_spare_out_order.py`

## 1. PO 方法覆盖审计

| 方法 | 调用者（测试方法） | 覆盖状态 | 备注 |
|------|-------------------|----------|------|
| `navigate()` | fixture: `spare_out_order_page` | 间接覆盖 | fixture 中调用 |
| `_wait_page_ready()` | `test_page_loads`, `test_ly_link_clickable`, `test_view_first_record` | 直接覆盖 | |
| `click_add()` | `test_add_dialog_opens`, `test_add_dialog_has_form_fields`, `test_add_out_order_success`, `test_add_out_order_cancel`, `test_add_empty_required` | 完全覆盖 | 5 处调用 |
| `click_spare_query()` | `test_spare_query_clickable` | 完全覆盖 | |
| `click_view_first()` | `test_view_first_record` | 完全覆盖 | |
| `click_ly_link(ly_number)` | `test_ly_link_clickable` | 完全覆盖 | |
| `search_by_handler(name)` | `test_search_by_handler`, `test_add_out_order_success`, `test_delete_created_out_order`, `test_add_out_order_cancel` | 完全覆盖 | |
| `reset_search()` | `test_reset_search` | 完全覆盖 | |
| `_fill_dialog_by_placeholder(placeholder, value)` | 间接调用: `fill_out_order_handler` -> 测试调用 | 间接覆盖 | |
| `fill_out_order_handler(name)` | `test_add_out_order_success`, `test_add_out_order_cancel` | 完全覆盖 | |
| `click_search()` | 无直接测试调用 | **未覆盖** | 方法存在但未被任何测试直接调用；`search_by_handler` 内部自行调用点击查询 |
| `delete_by_handler(name)` | `test_delete_created_out_order` | 完全覆盖 | |

**发现**: `click_search()` 方法未被任何测试直接调用。此方法与 `search_by_handler()` 中的查询点击冗余——`search_by_handler` 内部已包含 `self.click(self.BTN_QUERY)`。`click_search()` 可能是为外部独立调用提供的接口，但测试始终通过 `search_by_handler` 执行搜索。

## 2. Locator 命名约定

| PO 常量 | 命名模式 | 合规 (UPPER_SNAKE) | 前缀规范 |
|---------|----------|-------------------|----------|
| `FILTER_HANDLER` | `FILTER_` + 字段名 | 合规 | 搜索区字段 |
| `FILTER_DATE` | `FILTER_` + 字段名 | 合规 | 搜索区字段 |
| `BTN_QUERY` | `BTN_` + 动作 | 合规 | 按钮 |
| `BTN_RESET` | `BTN_` + 动作 | 合规 | 按钮 |
| `BTN_ADD` | `BTN_` + 动作 | 合规 | 按钮 |
| `BTN_SPARE_QUERY` | `BTN_` + 动作 | 合规 | 按钮 |
| `BTN_VIEW` | `BTN_` + 动作 | 合规 | 按钮 |

**结果**: 所有 locator 常量符合 UPPER_SNAKE_CASE 命名规范，前缀使用一致的 `FILTER_`/`BTN_` 模式。

## 3. 测试覆盖缺口

| PO 功能 | 测试覆盖? | 风险等级 | 说明 |
|---------|----------|----------|------|
| 日期搜索 (`FILTER_DATE`) | ❌ 未覆盖 | 中 | locator 定义了日期筛选字段但测试未使用 |
| 重置后搜索条件验证 | ⚠️ 部分覆盖 | 低 | `test_reset_search` 仅验证点击重置无异常，未验证搜索条件是否清空 |
| 分页翻页 | ❌ 未覆盖 | 中 | `test_pagination_visible` 仅验证分页存在 |
| 表单字段填写后校验 | ❌ 未覆盖 | 低 | `fill_out_order_handler` 后无填写成功校验 |
| `click_search()` 方法 | ❌ 无测试 | 低 | 方法存在但未被测试直接调用 |
| 空数据状态 | ❌ 未覆盖 | 低 | 未验证空表时 UI 表现 |
| LY 链接无数据时的容错 | ⚠️ 已处理 | 低 | 测试中有 skip 逻辑 |
| 多弹窗叠加场景 | ❌ 未覆盖 | 中 | JS fill 在多弹窗时可能出错 |

## 4. 治理文档完整性

| 文档类型 | 路径 | 状态 |
|----------|------|------|
| PAGE_CONTEXT.md | `governance/context/.../spare-out-order/PAGE_CONTEXT.md` | 完整 |
| PAGE_INTERFACE.yaml | `governance/context/.../spare-out-order/PAGE_INTERFACE.yaml` | 完整 |
| TECH_ANALYSIS.md | `governance/context/.../spare-out-order/TECH_ANALYSIS.md` | 完整 |
| AUTO_STRATEGY.md | `governance/context/.../spare-out-order/AUTO_STRATEGY.md` | 完整 |
| RISK_MODEL.md | `governance/context/.../spare-out-order/RISK_MODEL.md` | 完整（含 BUSINESS_SCENARIOS） |
| TEST_CASES.md | `governance/context/.../spare-out-order/TEST_CASES.md` | 完整 |
| consistency-check.md | `governance/artifacts/code-review/warehouse/spare-out-order/` | 完整 |

## 5. Risk-to-Test Mapping (P0 风险)

| P0 风险 | 覆盖测试 | 状态 |
|---------|----------|------|
| BUSK-SOO-001 (出库数量错误/库存偏差) | TC-SOO-013, TC-SOO-014, TC-SOO-015, TC-SOO-016 | 完全覆盖 |
| BUSK-SOO-003 (未遵循审批链) | 无直接测试（无法在 UI 层绕过审批链） | 不适用（后端逻辑） |
| PERM-SOO-001 (未授权 URL 访问) | 无 | 缺口（需安全测试） |
| PERM-SOO-002 (越权操作) | 无 | 缺口（需在不同角色下执行） |
| API-SOO-003 (Token 过期) | 无 | 缺口（需 Mock） |
| DATA-SOO-002 (SQL 注入/XSS) | 无 | 缺口（需安全测试） |

## 6. 特殊说明

1. **`_fill_dialog_by_placeholder` 无 fallback**: 方法使用纯 JS 方式填充弹窗输入框，未匹配时仅记录 warning 不抛出异常。这意味着如果 placeholder 改变或弹窗结构变化，测试可能静默通过但实际未填写表单。建议在 `fill_out_order_handler` 后增加填写验证步骤。

2. **`click_search` 冗余**: PO 中有 `click_search()` 和 `search_by_handler()` 两个方法，前者仅点击查询按钮，后者包含输入+点击。`click_search()` 未被测试调用，可能应标记为 `@property` 或移除。

3. **日期筛选未覆盖**: `FILTER_DATE` locator 已定义但测试中未使用日期搜索功能。

4. **LY 链接行内定位**: `click_ly_link` 使用 `//button[contains(.,"{ly_number}")]` 全局定位而非行内定位，若表格中存在多个 LY 单号，点击行为可能不确定。
