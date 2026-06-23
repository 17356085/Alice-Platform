好的，这是针对 `personnel/entry-record` 页面的自动化测试策略。

---

# AUTO_STRATEGY — personnel / entry-record

> **生成日期**: 2026-06-18
> **依据**: EntryRecordPage.py, test_entry_record.py, PAGE_CONTEXT.md, BasePage API
> **Skill**: auto-strategy v1.0

## 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
|---------|------|--------|----------|------|
| **ER-001** | 页面打开时正常显示入场记录列表 | **P0** | ✅ | 核心冒烟，验证页面加载、表头、分页 | 
| **ER-002** | 分页功能正常 | **P0** | ✅ | 列表页核心交互，验证翻页数据变化 |
| **ER-003** | 按人员姓名搜索 | **P0** | ✅ | 核心搜索功能，快速定位数据 |
| **ER-004** | 按日期范围搜索 | **P0** | ✅ | 核心搜索功能，日期筛选 |
| ER-005 | 按承包商单位搜索 | P1 | ❌ | 输入无对应测试数据或接口，手动更灵活 |
| ER-006 | 搜索后重置条件 | P1 | ❌ | 集成测试，手动验证可快速检查UI状态 |
| ER-007 | 导出入场记录 | **P0** | ✅ * | 核心导出功能。**风险**: 需验证文件下载，跨浏览器兼容性 |
| ER-008 | 查看入场详情弹窗 | **P0** | ✅ | 核心只读交互，验证弹窗内容 |
| ER-009 | 切换每页显示条数 | P1 | ❌ | 数据量变化验证，手动或集成测试更有效 |
| ER-010 | 无数据时页面显示 | P2 | ❌ | 边界情况，可测试数据后手动验证 |
| ER-011 | 长时间页面不操作，刷新后页面正常 | P1 | ❌ | Session/权限测试，手动更可靠 |

> **注释**:
> *   `ER-007` 导出功能建议自动化，但需在 `AUTO_ARCHITECTURE` 或 `conftest.py` 中增加文件下载的处理（如设置 `download.default_directory` 并等待文件生成）。
> *   所有 **P1/P2** 用例，在自动化用例稳定后，可作为补充。
> *   **风险标注**: 所有搜索框的定位器（`XPath`）依赖于 `placeholder` 属性。如果前端修改了该属性值，定位器会失效。建议与开发约定，将 `placeholder` 固化或使用更稳定的 `data-testid` 属性。

---

## 2. PageObject 拆分方案

### 2.1 建议的 Page 类及职责

当前 `EntryRecordPage` 的设计已满足“一个页面一个 Page 类”的原则。**无需拆分**。

*   **`EntryRecordPage`**：负责入场记录页面的所有交互，包括：
    *   页面导航 (`navigate`)
    *   状态验证 (`is_page_loaded`, `get_table_header_texts`)
    *   搜索操作 (`input_search_name`, `click_search`, `click_reset` 等)
    *   数据提取 (`get_column_data`, `get_first_row_data`, `get_total_count` 等)
    *   分页操作 (`click_next_page`, `click_prev_page`, `select_page_size` 等)
    *   导出操作 (`click_export_btn`)
    *   详情弹窗操作 (`click_detail_btn`, `get_detail_dialog_content`, `close_detail_dialog`)

### 2.2 复杂组件独立化分析

*   **详情弹窗 (`el-dialog`)**: 虽然是一个独立组件，但其操作仅为“查看”（只读），且交互逻辑简单（打开 -> 读取内容 -> 关闭）。将该弹窗的操作封装在 `EntryRecordPage` 内部是合理的，无需为此新建一个独立的 Page 类。如果未来弹窗内的操作变得复杂（如包含表单编辑），则建议拆分为 `EntryRecordDetailDialog` 类。

---

## 3. 公共组件复用分析

### 3.1 可复用 BasePage 已有方法

当前 `EntryRecordPage` 已经很好地复用并扩展了 `BasePage` 的能力。以下是具体分析：

| 方法 | 来源 | 说明 |
|------|------|------|
| `navigate_to()` | `BasePage` | 用于实现 `navigate()` 方法。 |
| `wait_page_ready()` | `BasePage` | 用于处理页面整体加载等待。 |
| `_wait_loading_gone()` | `BasePage` | 用于等待 Element Plus 的 loading 动画消失。 |
| `wait_vue_stable()` | `BasePage` | 用于等待 Vue 的异步更新完成。 |
| `is_page_loaded()` | `PageObject` | `EntryRecordPage` 自定义实现，但复用了 `wait.until` 和 `EC.presence_of_element_located`。 |
| `get_total_count()` | `BasePage` | 直接复用。 |
| `TABLE_ROWS` | `BasePage` | `EntryRecordPage` 中没有重新声明，可以直接继承使用。 |
| `get_all_row_data()` | `BasePage` | `EntryRecordPage` 中没有，可以用 `find_all(self.TABLE_ROWS)` 实现。 |
| `find_all()`, `find()`, `wait_element_to_be_clickable()` 等 | `BasePage` | 所有底层元素定位和操作的基础方法。 |

### 3.2 是否需要扩展 `ElementPlusHelper`

当前 `EntryRecordPage` 中对 `el-select`、`el-date-picker`、`el-pagination` 的操作都是通过 `BasePage` 的基本方法组合完成的。**建议扩展 `ElementPlusHelper`**，封装以下通用操作，以便其他页面复用：

*   `select_el_option_by_text(select_locator: tuple, option_text: str)`：选择一个 `el-select` 的选项。
*   `set_el_date_picker_value(picker_locator: tuple, date_value: str)`：设置日期选择器的值。`EntryRecordPage` 中的 `input_date_start` / `input_date_end` 方法可以演进为此通用方法。
*   `get_el_table_all_data(table_locator: tuple)`：获取表格所有行的数据，返回列表字典。
*   `click_el_pagination_page(page_number: int)`：点击分页器的指定页码。

---

## 4. 等待策略建议

### 4.1 页面特有的异步行为

基于 `EntryRecordPage` 代码推断，该页面存在以下异步行为：

1.  **表格数据加载**：页面加载、搜索、重置、翻页、切换每页条数后，表格区域会触发异步请求，并显示一个 `el-loading` 遮罩。
2.  **导航动画**：通过侧边栏导航到该页面时，可能存在 Vue Router 的转场动画，导致部分元素（如搜索框）短暂不可见。
3.  **下拉框/日期选择器弹出**：`el-select` 和 `el-date-picker` 的弹出层是动态添加到 `body` 下的，需要等待弹出完成才能进行操作。

### 4.2 建议的等待封装

当前 `EntryRecordPage` 的等待策略已经很优秀。可以在此基础上，为 `ElementPlusHelper` 添加更精细的等待方法：

*   **`wait_for_table_data_loaded()`**:
    *   **实现**: `<table>.wait_for_element_attribute_change("a", "class", "el-loading-parent--relative")` 或是 **`wait_for_element_to_be_stale`**，等待前一页的表格行元素变得陈旧。这是最稳定的等待方式。
*   **`wait_for_el_select_dropdown_visible(select_locator)`**:
    *   **实现**: 点击下拉框后，等待一个动态 `class` 为 `is-visible` 的 `el-select-dropdown` 元素出现。
*   **`wait_for_el_date_picker_dropdown_visible(picker_locator)`**:
    *   **实现**: 点击日期输入框后，等待一个 `class` 为 `el-date-picker` 的弹出面板元素出现。

> **建议**: 在 `EntryRecordPage` 的 `click_search()`, `click_reset()`, `click_next_page()`, `select_page_size()` 等会触发表格刷新的方法中，**显式**调用 `_wait_loading_gone()` 和 `wait_vue_stable()`，确保后续的数据提取操作能获取到最新页面状态。

---

## 5. ROI 分析

### 预估数据

| 项目 | 值 | 说明 |
|------|----|------|
| **完全自动化版本开发时间 (X)** | **5 小时** | 包括：为 5 个 P0 用例编写脚本、调试、准备测试数据风险处理、集成到 CI 流程。 |
| **预估月维护成本 (Y)** | **1 小时 / 月** | UI 变更（如添加/删除列，文案修改）导致的定位器调整；搜索逻辑变更的测试修复。 |
| **手工执行时间 (Z)** | **30 分钟 / 次** | 回归测试时，手工执行 P0 和 P1 用例的时间。 |
| **预计手工执行频率** | **40 次 / 月** | 约每天 2 次（每次代码提交或发布前）。 |

### ROI 计算

**月自动化收益** = `(手工执行时间 * 手工执行频率) - 月维护成本`

`= (30 分钟/次 * 40 次/月) - 1 小时/月`
`= 20 小时/月 - 1 小时/月`
`= 19 小时/月`

**净回本周期** = `自动化开发时间 / 月自动化收益`

`= 5 小时 / 19 小时/月`
`= 约 0.26 个月 ≈ 8 天`

### 结论

**ROI 极高**。自动化开发成本仅需约 8 天即可通过节省的手工测试时间收回。对于 10 次/月以上的回归频率，自动化是绝对推荐的。入场记录页面功能稳定，页面结构清晰，维护成本可控，非常适合自动化。