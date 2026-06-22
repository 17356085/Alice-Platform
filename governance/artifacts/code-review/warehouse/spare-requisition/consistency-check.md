# Code Consistency Check — warehouse/spare-requisition

**Module**: warehouse
**Page**: spare-requisition
**PO Class**: SpareRequisitionPage
**PO File**: `ZJSN_Test-master526/page/warehouse_page/SpareRequisitionPage.py`
**Test File**: `ZJSN_Test-master526/script/warehouse/test_spare_requisition.py`

## 1. PO 方法覆盖审计

| 方法 | 调用者（测试方法） | 覆盖状态 | 备注 |
|------|-------------------|----------|------|
| `navigate()` | fixture: `spare_requisition_page` | 间接覆盖 | fixture 中调用 |
| `_wait_page_ready()` | `test_page_loads`, `test_view_first_record`, `test_first_row_action_buttons_exist`, `test_edit_dialog_opens`, `test_first_row_status_readable`, `test_submit_button_triggers_toast` | 完全覆盖 | 6 处调用，所有测试入口 |
| `search_by_applicant(name)` | `test_search_by_applicant`, `test_reset_search`, `test_add_requisition_success`, `test_delete_created_requisition`, `test_add_requisition_cancel` | 完全覆盖 | |
| `reset_search()` | `test_reset_search` | 完全覆盖 | |
| `click_search()` | 无直接测试调用 | **未覆盖** | 方法存在但未被测试调用；`search_by_applicant` 内部自行调用点击查询 |
| `click_add()` | `test_add_dialog_opens`, `test_add_dialog_has_save_button`, `test_add_requisition_success`, `test_add_requisition_cancel`, `test_add_empty_required` | 完全覆盖 | |
| `click_view_first()` | `test_view_first_record` | 完全覆盖 | |
| `click_edit_first()` | `test_edit_dialog_opens` | 完全覆盖 | |
| `click_submit_first()` | `test_submit_button_triggers_toast` | 完全覆盖 | |
| `click_delete_first()` | 无直接测试调用 | **未覆盖** | 方法存在但未被测试直接调用；`delete_by_name` 内部使用 `click_row_button` 定位删除，而非调用 `click_delete_first` |
| `has_edit_button()` | `test_first_row_action_buttons_exist`, `test_edit_dialog_opens` | 完全覆盖 | |
| `has_submit_button()` | `test_first_row_action_buttons_exist`, `test_submit_button_triggers_toast` | 完全覆盖 | |
| `has_delete_button()` | `test_first_row_action_buttons_exist` | 完全覆盖 | |
| `get_first_row_status()` | `test_first_row_status_readable` | 完全覆盖 | |
| `_fill_dialog_by_placeholder(placeholder, value)` | 间接: `fill_requisition_applicant` -> 测试 | 间接覆盖 | |
| `fill_requisition_applicant(name)` | `test_add_requisition_success`, `test_add_requisition_cancel` | 完全覆盖 | |
| `delete_by_name(name)` | `test_delete_created_requisition` | 完全覆盖 | |

**发现**:
1. `click_search()` 方法未被测试直接调用，与 `search_by_applicant()` 冗余。
2. `click_delete_first()` 方法存在但未被测试直接调用。删除测试通过 `delete_by_name` 内部使用 `click_row_button(name, "删除")` 实现，而非调用 `click_delete_first()`。这说明 `click_delete_first()` 和 `delete_by_name()` 是两套删除路径：前者操作第一行，后者通过名称搜索定位。

## 2. Locator 命名约定

| PO 常量 | 命名模式 | 合规 (UPPER_SNAKE) | 前缀规范 |
|---------|----------|-------------------|----------|
| `FILTER_APPLICANT` | `FILTER_` + 字段名 | 合规 | 搜索区字段 |
| `FILTER_DATE` | `FILTER_` + 字段名 | 合规 | 搜索区字段 |
| `FILTER_STATUS` | `FILTER_` + 字段名 | 合规 | 搜索区字段 |
| `BTN_QUERY` | `BTN_` + 动作 | 合规 | 按钮 |
| `BTN_RESET` | `BTN_` + 动作 | 合规 | 按钮 |
| `BTN_ADD` | `BTN_` + 动作 | 合规 | 按钮 |
| `BTN_VIEW` | `BTN_` + 动作 | 合规 | 按钮 |
| `BTN_EDIT` | `BTN_` + 动作 | 合规 | 按钮 |
| `BTN_SUBMIT` | `BTN_` + 动作 | 合规 | 按钮 |
| `BTN_DELETE` | `BTN_` + 动作 | 合规 | 按钮 |

**结果**: 所有 locator 常量符合 UPPER_SNAKE_CASE 命名规范，前缀使用一致的 `FILTER_`/`BTN_` 模式。

## 3. 测试覆盖缺口

| PO 功能 | 测试覆盖? | 风险等级 | 说明 |
|---------|----------|----------|------|
| 日期搜索 (`FILTER_DATE`) | ❌ 未覆盖 | 中 | locator 已定义但测试未使用日期搜索 |
| 流程状态搜索 (`FILTER_STATUS`) | ❌ 未覆盖 | 中 | locator 已定义但测试未使用状态筛选 |
| 重置后搜索条件验证 | ⚠️ 部分覆盖 | 低 | `test_reset_search` 仅验证无异常 |
| 分页翻页 | ❌ 未覆盖 | 中 | `test_pagination_visible` 仅验证存在 |
| 行内删除按钮 (`click_delete_first`) | ❌ 未覆盖 | 低 | 方法存在但测试通过其他路径实现删除 |
| 编辑后保存 | ❌ 未覆盖 | 中 | `test_edit_dialog_opens` 仅验证弹窗打开 |
| 提交后状态变更 | ❌ 未覆盖 | 中 | `test_submit_button_triggers_toast` 仅验证 Toast |
| 废除行数据验证 | ❌ 未覆盖 | 低 | 删除后 `is_row_present` 验证存在 |
| wh-filter-toolbar 自定义组件 | ❌ 未覆盖 | 中 | 搜索组件布局未做兼容性测试 |

## 4. 治理文档完整性

| 文档类型 | 路径 | 状态 |
|----------|------|------|
| PAGE_CONTEXT.md | `governance/context/.../spare-requisition/PAGE_CONTEXT.md` | 完整 |
| PAGE_INTERFACE.yaml | `governance/context/.../spare-requisition/PAGE_INTERFACE.yaml` | 完整 |
| TECH_ANALYSIS.md | `governance/context/.../spare-requisition/TECH_ANALYSIS.md` | 完整 |
| AUTO_STRATEGY.md | `governance/context/.../spare-requisition/AUTO_STRATEGY.md` | 完整 |
| RISK_MODEL.md | `governance/context/.../spare-requisition/RISK_MODEL.md` | 完整（含 BUSINESS_SCENARIOS） |
| TEST_CASES.md | `governance/context/.../spare-requisition/TEST_CASES.md` | 完整 |
| consistency-check.md | `governance/artifacts/code-review/warehouse/spare-requisition/` | 完整 |

## 5. Risk-to-Test Mapping (P0 风险)

| P0 风险 | 覆盖测试 | 状态 |
|---------|----------|------|
| BUSK-SRQ-001 (申请人信息不实/库存异常占用) | TC-SRQ-014, TC-SRQ-015, TC-SRQ-016, TC-SRQ-017 | 完全覆盖 |
| PERM-SRQ-001 (未授权 URL 访问) | 无 | 缺口（需安全测试） |
| PERM-SRQ-004 (已审批记录删除按钮未隐藏) | 无 | 缺口（需在不同状态行验证） |
| API-SRQ-003 (Token 过期) | 无 | 缺口（需 Mock） |

## 6. 特殊说明

1. **`wh-filter-toolbar` 定位器脆弱性**: `FILTER_STATUS` 使用 `(//div[contains(@class,"wh-filter-toolbar")]//div[contains(@class,"el-select__wrapper")])[1]`，依赖自定义容器类名 `wh-filter-toolbar` 和索引 `[1]`。这是一个非标准 Element Plus 组件，若搜索区布局重构，该定位器会失效。

2. **`_fill_dialog_by_placeholder` 无 fallback**: 与 spare-out-order 相同，纯 JS 填充无 fallback，未匹配 placeholder 时仅打印 warning。

3. **`click_delete_first` vs `delete_by_name` 两套删除路径**: `click_delete_first()` 直接操作第一行；`delete_by_name()` 通过搜索名称再点击行内按钮。前者更高效但依赖于行序，后者更精确但依赖搜索功能。测试中使用 `delete_by_name` 确保删除的是自己创建的数据。

4. **按钮可见性预检模式**: PO 提供了 `has_edit_button()`, `has_submit_button()`, `has_delete_button()` 三个方法，测试在操作前先检查按钮是否存在（`pytest.skip` 跳过），这种模式避免了因工作流状态导致的测试不稳定。这是一个正面的设计模式，建议推广。

5. **`get_first_row_status` 的 el-tag 依赖**: 方法通过 `.el-tag` CSS 选择器读取状态文本。若 el-tag 在表格行中用于其他目的（如类型标签），状态读取可能返回错误的值。当前测试仅验证返回类型为 string，未验证内容正确性。

6. **`click_search` 冗余**: 同 spare-out-order，未被测试直接调用。
