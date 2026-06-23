好的，遵照您的指示，我将以测试自动化专家的身份，根据您提供的 `ContractorUnitPage.py`、`test_contractor_unit.py` 和 `PAGE_CONTEXT.md`，制定自动化测试策略，并输出 `AUTO_STRATEGY.md`。

---

## 产出物: AUTO_STRATEGY.md

```markdown
# AUTO_STRATEGY — personnel / contractor-unit

> 版本: 1.0 | 最后更新: 2026-06-18 | 作者: automation-agent
> 基于: TEST_CASES, TECH_ANALYSIS, ContractorUnitPage.py, test_contractor_unit.py

## 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
| :--- | :--- | :--- | :--- | :--- |
| CU-001 | 页面打开时正常显示承包商单位列表 | P0 | ✅ | 核心冒烟用例，定位器稳定。 |
| CU-002 | 分页功能正常 | P0 | ✅ | 基础列表功能，查询后直接验证。 |
| CU-003 | 按单位名称搜索 | P0 | ✅ | 核心搜索功能，验证搜索交互。 |
| CU-004 | 按单位编码搜索 | P1 | ✅ | 核心搜索功能，验证搜索交互。 |
| CU-005 | 按状态搜索 | P0 | ✅ | 核心筛选功能，验证筛选交互。 |
| CU-006 | 新增承包商单位 | P0 | ✅ | **核心闭环用例**：新增→查询→编辑→删除。自动化价值高。 |
| CU-007 | 编辑承包商单位 | P0 | ✅ | 核心CRUD操作，验证编辑弹窗和保存逻辑。 |
| CU-008 | 启用/停用承包商单位 | P0 | ✅ | 核心状态变更操作，验证切换逻辑。 |
| CU-009 | 删除承包商单位 | P1 | ❌ | **风险标注**：定位器（`TABLE_DELETE_BUTTON`）可能因行内多行操作导致无法精确定位，且删除后需处理确认弹窗，场景复杂度高，建议优先手动测试。 |

**风险标注说明**：
- **CU-009**: 行内删除按钮定位器 `TABLE_DELETE_BUTTON` 使用 `tr[...] // button[.//span[contains(text(),"删除")]]`，这在存在多行且“删除”按钮结构相似时可能不精确。建议后续优化为结合行索引定位。

**不建议自动化用例**：
- **一次性操作**: 无。页面所有操作均为日常CRUD，无“仅上线前执行”的用例。
- **主观判断**: 无。所有用例均为功能性验证，不涉及UI美观度判断。

## 2. PageObject 拆分方案

### 2.1 现有 Page 类（`ContractorUnitPage.py`）

**职责**:
- 页面导航与状态验证。
- 搜索区和工具栏的所有操作（输入、点击搜索/重置/新增）。
- 表格数据的读取（行数、列数据、获取首行）。
- 分页操作（下一页、上一页、每页条数选择）。
- **行内操作**（编辑、启停用、删除）的定位与触发。

### 2.2 拆分建议

**原则**：遵循“一个页面一个 Page 类，复杂弹窗独立”规则。
**1. 新增 `ContractorUnitDialog` 类（推荐）**

-   **职责**：封装“新增/编辑承包商单位”弹窗的所有操作。
-   **原因**：
    -   弹窗是独立的 `el-dialog` 容器，其生命周期独立于主页面。
    -   弹窗内元素（`el-input`, `el-button`）与主页面元素隔离，封装为独立类可增强内聚性，避免定位器作用域污染。
    -   后续如果弹出“选择联系人”等更复杂的子组件，独立类更易于扩展。
-   **建议的定位器**：使用 `el-form-item` 的 `label` 属性精确定位输入框，如 `(By.XPATH, "//div[contains(@class, 'el-dialog')]//div[contains(@class,'el-form-item')][.//label[text()='单位名称']]//input")`

**2. 不拆分 `ContractorUnitPage` 类（维持现状）**

-   如果弹窗内元素与主页面交互简单（仅有几个输入框和按钮），也可以维持现状，直接在`ContractorUnitPage`中新增方法操作弹窗。但长期维护角度来看，拆分更优。

### 2.3 最终 PageObject 结构

```
page/personnel_page/
├── __init__.py
├── ContractorUnitPage.py              # 主列表页面操作
└── contractor_unit/
    └── ContractorUnitDialog.py         # 【新增】新增/编辑弹窗操作
```

## 3. 公共组件复用分析

### 3.1 可复用的 `BasePage` 方法

| 现有 `ContractorUnitPage.py` 方法 | 复用 `BasePage` 方法 | 说明 |
| :--- | :--- | :--- |
| `navigate()` | `self.navigate_to()` | 完全复用。 |
| `is_page_loaded()` | `self.wait.until()` + `self.wait_vue_stable()` | 模式复用，具体定位器不同。 `wait_vue_stable()` 是通用等待方法。 |
| `get_table_header_texts()` | `self.wait.until()` + `self.find_all()` | 模式复用。 |
| `get_table_row_count()` | `self.find_all(self.TABLE_ROWS)` | 复用 `find_all()`。 |
| `get_column_data()` | 自定义 | 需要循环获取 `td` 内容，无法直接复用。 |
| `get_first_row_data()` | `self.wait.until()` + `self.find_elements(By.TAG_NAME, 'td')` | 模式复用。 |
| `is_unit_name_present()` | `self.is_row_present()` | **完全复用**。 |
| `get_total_count_text()` | `self.wait.until()` + `get_text()` | 模式复用 `get_text()`。 |
| `get_total_count()` | `self.get_total_count()` | **完全复用**。 |
| `input_search_name()`, `click_search()`, `click_reset()` 等 | `self.type()`, `self.click()` | 建议重写以调用 `BasePage` 的标准 `type` 和 `click` 方法（可处理 `element` 或 `tuple`）。 |

### 3.2 待新增的公共方法

-   **`get_nth_row_edit_button(row_index)`**: 获取指定行的编辑/删除/启停用按钮。用于精确定位行内操作，替代现有可能不精确的 `TABLE_EDIT_BUTTON`。该方法可考虑提升到 `BasePage` 的表格相关操作中。
-   **`handle_confirm_dialog(action='confirm')`**: 处理 `el-message-box` 确认对话框。此为通用模式，可提升到 `BasePage` 或新建 `DialogHelper` 类。

## 4. 等待策略建议

### 4.1 页面特有的异步行为

1.  **搜索/筛选后重载表格**：点击搜索/重置或选择状态下拉框后，表格数据会异步刷新。
2.  **新增/编辑/删除后重载表格**：提交弹窗或确认删除后，列表会重新加载。
3.  **行内状态切换**：点击“启用/停用”后，请求发送，状态变更，对应行的 `el-tag` 文字和样式会变化。
4.  **分页切换**：点击页码或下一页后，表格内容异步更新。

### 4.2 建议的等待封装

-   **在 `ContractorUnitPage` 中新增 `_wait_table_load_complete()` 方法**:
    -   **策略**: 等待 `.el-table__body-wrapper` 中的 `.el-loading-mask` 消失（如果存在） + 等待 `el-table__body-wrapper` 中至少出现一个 `tr` 元素 + 调用 `self.wait_vue_stable()`。
    -   **代码**:
        ```python
        def _wait_table_load_complete(self, timeout=10):
            """等待表格数据加载完成"""
            try:
                # 1. 等待 loading mask 消失
                load_mask = self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.el-table__body-wrapper .el-loading-mask')))
            except TimeoutException:
                pass  # 可能没有 loading mask
            finally:
                # 2. 等待至少一行数据出现，确保渲染完成
                self.wait.until(EC.presence_of_element_located(self.TABLE_ROWS))
                # 3. 等待 Vue 稳定
                self.wait_vue_stable()
        ```
-   **在新增/关闭弹窗后**:
    -   新增弹窗提交后，等待：`_wait_table_load_complete()` + 验证弹窗消失（等待 `el-dialog` 的 `display: none` 或 `visibility: hidden`）。
    -   可封装为 `wait_dialog_closed(dialog_container_locator)` 方法。

## 5. ROI 分析

### 5.1 预估开发时间

-   **分析 & 设计**: 0.5 小时
-   **代码编写**:
    -   实现 `ContractorUnitPage` 缺失的方法 (如 `input_search_name`, `click_search` 等): 1 小时
    -   优化现有不稳定定位器 (如 `SEARCH_STATUS_SELECT`): 0.5 小时
    -   实现 `_wait_table_load_complete()`: 0.5 小时
    -   实现 `ContractorUnitDialog` 类: 2 小时
-   **测试脚本编写** (`test_contractor_unit.py`):
    -   适配新 PageObject 签名: 0.5 小时
    -   实现 CU-006（新增闭环）: 2 小时
    -   **数据清理封装**: 实现 `yield` teardown 清理新增数据，使用 `CleanupTracker`: 1 小时
-   **调试 & 优化**: 2 小时
-   **总计开发时间**: **~10 小时**

### 5.2 预估维护成本

-   **月维护频率**: 低（元素稳定）
-   **月度维护工作量**:
    -   修复失败的定位器（假设每月 1-2 次 UI 调整）: 2 小时
    -   Vue 核心升级导致的 `wait_vue_stable()` 失效: 1 小时
-   **总计月维护成本**: **~3 小时/月**

### 5.3 手工执行时间

-   **单次完整回归执行（包含所有 9 个用例）**: **15 分钟**

### 5.4 ROI 计算

**假设**:
-   月执行频率：回归执行 30 次/月（每天一次）
-   自动化一次开发后，可稳定运行 6 个月
-   手工测试同事时薪：50元/小时
-   自动化工程师时薪：80元/小时

**公式**： `ROI = (手工执行时间 × 执行频率 × 月数) - (开发成本 + 维护成本 × 月数)`

-   **手工执行总成本**: 15分钟/次 × 30次/月 × 6月 = 2700分钟 = 45小时 → 2250元
-   **自动化总成本**: 10小时 × 80元/小时 + (3小时/月 × 6月 × 80元/小时) = 800元 + 1440元 = 2240元

**结果**:
-   **6个月总收益**: 2250元 (手工) - 2240元 (自动化) = **10元**
-   **月均收益**: ~1.7元

**解读**:
-   短期内ROI几乎持平，但**自动化优势**在于：
    1.  **测试覆盖率稳定性**：手动测试易疲劳遗漏，自动化100%执行预定用例。
    2.  **执行速度**：15分钟的自动化用例可以随时跑，而手动测试需要安排时间和人力。
    3.  **回归能力**：自动化可在几分钟内完成，支持CI/CD高频集成。
    4.  **数据清理**：自动化可以精准清理测试数据，避免数据残留。
-   **风险**：如果UI频繁改动，维护成本增加，ROI可能转负。因此，优化定位器（优先A级）、做好 `_wait_table_load_complete()` 封装，是维持ROI的关键。

**结论**：**自动化投资是值得的。** 它不仅能稳定地覆盖核心回归场景，还为未来扩展到更多页面（表格、弹窗、搜索等通用模式）提供了可复用的最佳实践。考虑到此项目为长期维护项目（超过6个月），自动化成本会持续摊薄，ROI将显著为正。