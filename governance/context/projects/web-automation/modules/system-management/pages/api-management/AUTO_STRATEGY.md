好的，作为 automation-agent，我将基于您提供的测试用例 (推断)、技术分析、页面上下文和 PO 代码，为 `system-management` 模块的 `api-management` 页面制定自动化测试策略，并输出 `AUTO_STRATEGY.md`。

根据输入，我推断您的测试用例设计 (TEST_CASES.md) 应包含以下典型场景，我将以此为基础进行分析：

**推断的测试用例 (基于 ApiManagementPage 功能和页面上下文):**
1.  TC-SEARCH-001: 输入 API 名称，点击搜索，验证表格仅显示匹配数据。 (P0)
2.  TC-SEARCH-002: 选择状态进行筛选，验证表格数据显示正确。 (P1)
3.  TC-RESET-001: 输入搜索条件后，点击重置，验证搜索条件清空并获取所有数据。 (P1)
4.  TC-ADD-001: 点击“新增”按钮，填写表单，点击确定，验证新增的 API 出现在列表中。 (P0)
5.  TC-EDIT-001: 选中一行数据，点击“编辑”，修改部分信息，点击确定，验证表格数据更新。 (P0)
6.  TC-DELETE-001: 选中一行数据，点击“删除”，点击确认弹窗的“确定”，验证数据从列表中移除。 (P0)
7.  TC-PAGINATION-001: 验证分页功能，点击下一页，验证表格数据正确切换。 (P1)
8.  TC-PAGINATION-002: 验证每页显示条数切换，验证表格数据刷新。 (P2)
9.  (假设) TC-CONFIG-001: 点击“配置权限”，弹窗出现，进行权限选择并保存。 (P2)
10. (假设) TC-BATCH_DELETE-001: 勾选多行，点击“批量删除”，确认删除。 (P1)

现在，我将生成 `AUTO_STRATEGY.md`。

## AUTO_STRATEGY.md

```yaml
---
source: ai
source_agent: automation-agent
created: 2026-06-18 10:54
module: system-management
page: api-management
---

# AUTO_STRATEGY.md — API 管理页面自动化策略

### 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 | 风险备注 |
|---|---|---|---|---|---|
| TC-SEARCH-001 | API名称搜索 | P0 | ✅ **必须** | 基础业务功能，定位器稳定（`placeholder`）。 | 无 |
| TC-SEARCH-002 | 状态筛选 | P1 | ✅ 推荐 | 常用操作，但 `el-select` 定位器相对稳定，可自动化。 | **中等风险**: `el-select` 下拉框通过 Teleport 渲染到 `<body>`，弹窗内元素需要特殊定位策略。 |
| TC-RESET-001 | 重置搜索条件 | P1 | ✅ 推荐 | 与搜索关联，自动化可覆盖回归。 | 无 |
| TC-ADD-001 | 新增API | P0 | ✅ **必须** | 核心CRUD操作，定位器稳定（按钮文本“新增”，弹窗内表单域稳定）。 | **低风险**: `el-dialog` 标题动态，建议使用类名或唯一表单域定位。 |
| TC-EDIT-001 | 编辑API | P0 | ✅ **必须** | 核心CRUD操作，定位器稳定（表格行内“编辑”按钮，弹窗复用新增表单）。 | **低风险**: 表格行内按钮需使用 `text()` 或 `contains` 定位。 |
| TC-DELETE-001 | 删除API | P0 | ✅ **必须** | 核心CRUD操作，需包含二次确认弹窗。 | **低风险**: 确认弹窗定位稳定（文本“确定”/“取消”）。 |
| TC-PAGINATION-001 | 分页翻页 | P1 | ✅ 推荐 | 高频操作，需验证正确性。`el-pagination` 结构稳定。 | 无 |
| TC-PAGINATION-002 | 每页条数切换 | P2 | ❌ 不建议 | 该操作手动执行频率低，且常通过 `el-select` 实现，定位器相对不稳定，维护成本可能大于收益。 | — |
| TC-CONFIG-001 | 配置权限 | P2 | ✅ 可选 | 功能重要，但弹窗内容可能复杂。如果权限管理是独立模块，可单独自动化。若弹窗内容稳定，可自动化。 | **中高等风险**: 弹窗内元素（如权限树）定位器可能复杂且不稳定。需评估ROI。 |
| TC-BATCH_DELETE-001 | 批量删除 | P1 | ✅ 推荐 | 重要功能，定位器稳定（表格行 `checkbox`）。 | **中等风险**: 需等待表格全选 `checkbox` 出现，`el-table` 的 `checkbox` 定位器相对稳定。 |

### 2. PageObject 拆分方案

建议将 `ApiManagementPage` 拆分为以下 Page 类：

```
page/
└── system_page/
    ├── api_management/
    │   ├── __init__.py
    │   ├── ApiManagementPage.py        # 主要 Page 类
    │   └── components/
    │       ├── __init__.py
    │       ├── SearchFormComponent.py   # (可选，复杂搜索表单)
    │       └── ApiDialogComponent.py    # (复杂弹窗，新增/编辑/配置权限)
    └── ...
```

- **`ApiManagementPage`**:
    - **职责**: 管理 `api-management` 页面的主要UI组件，包括搜索表单（或委托给组件）、表格、分页。
    - **方法示例**:
        - `search_by_name(self, name: str) -> 'ApiManagementPage'`
        - `search_by_status(self, status: str) -> 'ApiManagementPage'`
        - `reset_search(self) -> 'ApiManagementPage'`
        - `click_add_button(self) -> 'ApiDialogComponent'`
        - `click_edit_button_by_name(self, api_name: str) -> 'ApiDialogComponent'`
        - `click_delete_button_by_name(self, api_name: str) -> 'ApiDialogComponent'`
        - `get_table_data(self) -> list[dict]`
        - `go_to_page(self, page_num: int) -> 'ApiManagementPage'`

- **`ApiDialogComponent`**:
    - **职责**: 封装 `el-dialog` 弹窗内的所有操作，包括新增、编辑、配置权限等。
    - **方法示例**:
        - `fill_form(self, **kwargs) -> 'ApiDialogComponent'`
        - `click_confirm(self) -> 'ApiManagementPage'`
        - `click_cancel(self)`
        - `select_permissions(self, permissions: list[str]) -> 'ApiDialogComponent'`

### 3. 公共组件复用分析

- **复用 BasePage 已有方法**:
    - `fill_input(locator, text)`: 适用于搜索输入框、弹窗内表单域的填写。
    - `click_button(locator)`: 适用于搜索、重置、新增、确定、取消等按钮。
    - `click_link(locator)`: 适用于表格内的“编辑”、“删除”等文字按钮。
    - `get_table_data(locator, header_mapping)`: 如果 BasePage 有，可用于获取表格数据。
    - `wait_for_element_visible(locator)`: 通用等待。

- **扩展 ElementPlusHelper**:
    - 需要扩展 `select_option_by_text(dropdown_locator, option_text)` 方法来处理 `el-select`。该方法应: 点击下拉框 -> 等待 `<body>` 下的 `el-select-dropdown` 出现 -> 点击包含 `option_text` 的 `el-option` 项。
    - 考虑增加 `wait_for_dialog_visible(dialog_locator, timeout=10)` 方法，封装对 `el-dialog` 的等待逻辑。
    - 增加 `click_table_checkbox(row_index)` 方法，用于操作 `el-table` 的 `checkbox`。

### 4. 等待策略建议

- **搜索后表格刷新**:
    - **特有行为**: 点击“搜索”或“重置”后，`el-table` 会重新加载数据，可能有 `v-loading` 覆盖层。
    - **建议**: 点击搜索按钮后，使用 `wait_until_element_disappears(table_loading_locator)` 或 `wait_for_element_visible(table_data_row_locator)` 等待数据渲染完成。建议封装为 `wait_for_table_loaded()` 方法。

- **弹窗出现**:
    - **特有行为**: `el-dialog` 在 `v-if`/`v-show` 为 `true` 时渲染。
    - **建议**: 使用 `wait_for_element_visible(dialog_panel_locator)`。定位器选择 `el-dialog` 的 `wrapper` 或 `panel` 类，而不是动态标题。

- **下拉菜单展开**:
    - **特有行为**: `el-select` 的下拉菜单通过 Teleport 渲染到 `<body>`，且不是 `option` 元素的直接父节点。
    - **建议**: 点击 `el-select` 后，使用 `wait_for_element_visible(el_select_dropdown_locator)` 等待 `<body>` 下的 `.el-select-dropdown` 出现，再进行选项选择。

### 5. ROI 分析

假设每周执行 **10 次** 回归测试。

| 用例类型 | 预估开发时间 (小时) | 预估月维护成本 (小时/月) | 手工执行时间 (分钟/次) | 自动化后执行时间 (分钟/次) | ROI 计算 (单月) |
|---|---|---|---|---|---|
| **P0 自动化 (TC-SEARCH-001, TC-ADD/EDIT/DELETE)** | 8 | 1 | 15 | 2 | `(15-2)*10 - (8/4周) + 1 = 130 - 3 = 127 分钟收益` |
| **P1 自动化 (TC-SEARCH-002, RESET, PAGINATION)** | 5 | 1 | 10 | 2 | `(10-2)*10 - (5/4周) + 1 = 80 - 2.25 = 77.75 分钟收益` |
| **所有推荐用例合计** | **13** | **2** | **25** | **4** | **`(25-4)*10 - (13/4周) + 2 = 210 - 5.25 = 204.75 分钟收益/月`** |

**结论**: 自动化覆盖 P0 和大部分 P1 用例后，每月可节省约 **3.4 小时** 的手工测试时间。预计 **2 个月内** 收回自动化开发成本。对于 P2 的 TC-PAGINATION-002 和 TC-CONFIG-001，建议在后续迭代中根据实际维护成本和执行频率再评估。

**建议**: 优先自动化 **P0** 的 CRUD 和搜索用例，确保核心业务链稳定。