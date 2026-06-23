好的，Agent。收到任务。基于您提供的 `TEST_CASES.md`（推断）、`TECH_ANALYSIS.md` 草案、`PAGE_CONTEXT.md` 草案和现有的 `ExamRecordPage` 代码，我将产出 `AUTO_STRATEGY.md`。我将严格遵循 `Skill: auto-strategy` 的规则和模板。

---

## AUTO_STRATEGY.md

# 自动化策略 — 考试记录 (ExamRecordPage)

> **模块**: `personnel`
> **页面**: `exam-record`
> **版本**: 1.0
> **策略基于**: `PAGE_CONTEXT.md` (预测结构), `TECH_ANALYSIS.md` (待验证定位器)
> **状态**: 草案，需要在实际DOM上验证后定稿

## 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由与风险 |
| :--- | :--- | :--- | :--- | :--- |
| **TC-001** | 按人员姓名搜索 | P0 | ✅ | 核心功能，定位器稳定 (`input[placeholder]`)。 |
| **TC-002** | 按日期范围搜索 | P0 | ✅ | 核心功能，但`el-date-picker`的日期选择（时间面板）自动化成本高，建议仅做输入值 + 搜索验证。 |
| **TC-003** | 按考试类型搜索 | P0 | ✅ | 核心功能，`el-select`操作已有公共方法。 |
| **TC-004** | 按状态搜索 | P0 | ✅ | 核心功能，`el-select`操作已有公共方法。 |
| **TC-005** | 组合搜索（姓名+类型+状态） | P0 | ✅ | 验证组合逻辑，功能稳定。 |
| **TC-006** | 不填写任何条件，直接搜索 | P1 | ❌ | 返回所有数据，意义不大。可转为`TC-001`的前置条件或删除。 |
| **TC-007** | 搜索后，点击重置按钮 | P0 | ✅ | 验证重置功能，定位器稳定。 |
| **TC-008** | 查看某条考试记录的详情 | P0 | ✅ | 核心功能，弹窗定位器`DIALOG_DETAIL`基于XPath，需**验证稳定性**。 |
| **TC-009** | 分页功能：点击下一页 | P0 | ✅ | `el-pagination`定位器稳定，是通用组件。 |
| **TC-010** | 分页功能：切换每页显示条数 | P1 | ❌ | P1用例，自动化收益与成本比不高。 |
| **TC-011** | 点击导出按钮 | P0 | ❌ | **不建议自动化**。浏览器文件下载行为（路径、重命名、弹窗）跨浏览器兼容性极差，自动化稳定性差，维护成本高。 |
| **TC-012** | 查看空数据状态 | P2 | ❌ | P2用例，自动化成本高（需要构造空数据环境）。 |
| **TC-013** | 搜索后，表格数据与搜索条件匹配 | P0 | ✅ | 业务逻辑验证核心，需与`get_table_data`方法配合。 |
| **TC-014** | 输入特殊字符进行搜索 | P2 | ❌ | 通常由单元测试覆盖，UI自动化成本高且容易因XSS过滤规则变化而失败。 |
| **TC-015** | 分页边界值测试（首页、末页） | P1 | ❌ | 自动化收益不高，手动测试更灵活。 |

## 2. PageObject 拆分方案

```
pages/
└── exam_record/
    ├── __init__.py                   # 模块导出
    ├── exam_record_page.py           # 主Page类
    └── exam_record_detail_dialog.py  # 独立的详情弹窗Page类
```

### 2.1 `ExamRecordPage` (主Page类)
- **职责**: 搜索区、表格、操作按钮（导出）、分页的所有操作。
- **合并建议**: 现有 `exam_record_page.py` 代码结构良好。建议将 `_fill_input` 和 `_select_by_label` 这样的通用辅助方法迁移到 `BasePage` 中，使 `ExamRecordPage` 更专注于业务操作。
- **待移除/修改的方法**: `get_table_data` 方法中的 CSS 选择器 `td.el-table__cell` 在 Element Plus 不同版本可能不同（可能是 `td.el-table__cell` 或 `td .cell`），需要在`TECH_ANALYSIS.md`中**验证**。

### 2.2 `ExamRecordDetailDialog` (详情弹窗Page类)
- **职责**: 封装“考试记录详情”弹窗的所有操作，如等待弹窗可见、读取弹窗数据、点击确定关闭。
- **理由**: 弹窗是一个独立的视觉组件，有自己完整的生命周期和元素集合，独立成类可以避免主Page类过于臃肿，提高可维护性。
- **示例代码框架**:
    ```python
    class ExamRecordDetailDialog(BasePage):
        DIALOG = (By.XPATH, "//div[contains(@class,'el-dialog') and .//span[text()='考试记录详情']]")
        CONFIRM_BTN = (By.XPATH, ".//button[.//span[text()='确定']]")
        # 其他只读控件...

        def is_visible(self) -> bool:
            return self.is_element_visible(self.DIALOG)

        def click_confirm(self) -> "ExamRecordDetailDialog":
            self.click(self.CONFIRM_BTN)
            self.wait_for_invisible(self.DIALOG)
            return self
    ```

## 3. 公共组件复用分析

| 操作 | 复用建议 | 说明 |
| :--- | :--- | :--- |
| `navigate()` | ✅ **复用** `SidebarNavigator.navigate_to()` | 直接调用，无需修改。 |
| `search()` 中的 `_fill_input` | 🔜 **建议迁移** 到 `BasePage.type_and_slowly()` | 让 `BasePage` 的方法更通用，`ExamRecordPage` 只需调用 `self.type_slowly(locator, value)`。 |
| `search()` 中的 `_select_by_label` | 🔜 **建议迁移** 到 `ElementPlusHelper.select_by_label_text()` | 这是 Element Plus 组件的通用操作，扩展 `ElementPlusHelper` 是非常好的实践。 |
| `reset_search()` | ✅ **复用** `BasePage.click` | 无特殊操作。 |
| `get_table_data()` | ❌ **不直接复用** | 表格数据提取逻辑高度定制（需表头映射）。可以创建一个通用的 `_parse_table` 方法，但仍然需要在每个Page类中调用。 |
| `view_detail()` | ✅ **复用** 新创建的 `ExamRecordDetailDialog` | 主Page类只需调用 `dialog = ExamRecordDetailDialog(self.driver)`。 |
| `get_pagination_info()` | ✅ **复用** `BasePage.get_pagination_text()` | 建议确认 `BasePage` 中是否存在此方法。 |

## 4. 等待策略建议

该页面存在以下异步行为：

1.  **导航加载**: `navigate()` 后，表格数据和分页信息需要时间渲染。
    - **等待方式**: `wait_vue_stable()` 或等待表格容器 `.el-table` 可见。
2.  **搜索/重置**: 点击按钮后，表格会重新加载数据。
    - **等待方式**: 在 `wait_vue_stable()` 后，增加一个小的硬等待（如 `sleep(0.5s)`），以确保前端DOM更新完成。**更优方案**：监听一个特定元素的文本内容变化（如分页总数），或等待加载状态（如 V-loading 指令）消失。
3.  **弹窗出现/消失**:
    - **等待方式**: 使用显式等待 `wait_for_visible(LOCATOR)` 和 `wait_for_invisible(LOCATOR)`，这比硬等待更可靠。
4.  **日期选择器联动**: `el-date-picker` 展开和选择有过渡动画。
    - **等待方式**: 建议在每次点击时间面板的“确定”按钮前，增加对日期面板是否已展开的显式等待。

**建议**: 扩展 `BasePage` 或创建 `ExamRecordPage` 的私有方法 `_wait_for_table_to_load`，封装通用的等待逻辑，避免在测试用例中散落各种等待代码。

## 5. ROI 分析

此部分为估算，基于一个熟练的自动化工程师。

| 项目 | 预估 |
| :--- | :--- |
| **开发成本** | `ExamRecordPage` 细化: 4 小时<br>`ExamRecordDetailDialog` 创建: 2 小时<br>测试用例编写 (预计5个自动化用例): 2 小时<br>总计: **8 小时** |
| **手工执行时间** | 执行所有功能用例（P0-P1）: **15 分钟/次** |
| **手工执行频率** | 每日执行 2 次（主要回归） | 30 分钟/天 |
| **维护成本** | **2 小时/月** (定位器因版本升级变更，约为开发成本的 25%) |
| **月度收益** | (30 分钟/天 × 22 天/月) - 2 小时 = 11 小时 - 2 小时 = **9 小时/月** |
| **月度纯收益(时间)** | 每月节约 **9 小时** 的人工执行时间。 |
| **回本周期** | 8 小时 (开发) / 1.1 小时 (日均收益) ≈ **7-8 个工作日** |

**结论**: ROI 非常正面，自动化方案值得投资。自动化后，测试人员可以从重复的手工回归中解放出来，专注于探索性测试和边界值测试。

---

### 定位器风险标注

| 定位器 | 稳定性 | 风险说明 |
| :--- | :--- | :--- |
| `SEARCH_DATE_RANGE` | B 级 | `el-date-editor--daterange` 是动态class，若Element Plus升级或界面样式微调，此class可能变化。**建议**：在TECH_ANALYSIS中确认是否存在更稳定的ID或固定class。 |
| `DIALOG_DETAIL` | B 级 | XPath 路径较长，若弹窗标题变更或DOM结构有微小调整，可能导致定位失败。**建议**：检查是否可以通过部分class或 aria-label 定位。 |
| `SEARCH_EXAM_TYPE_SELECT` | A 级 | `label` 文本稳定的情况下，XPath路径可靠。 |

---
<!-- ⚠️ AUTO-GENERATED FOOTER BEGIN: skill-footer -->
**版本**: 1.0 | **分类**: automation | **注册**: skill-registry.yaml
**元数据版本**: 1.0 | 更新时间: 2026-06-18 10:54
<!-- ⚠️ AUTO-GENERATED FOOTER END: skill-footer -->