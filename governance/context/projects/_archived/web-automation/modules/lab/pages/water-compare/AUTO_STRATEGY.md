好的，收到您的输入。我将基于提供的 `WaterComparePage` 代码、`test_water_compare.py` 测试脚本以及 `PAGE_CONTEXT.md` 中的技术分析，为您制定该页面的自动化测试策略。

---

# AUTO_STRATEGY — lab / water-compare

> Phase 2 | 页面: water-compare | 自动化策略 | 2026-06-18

## 1. 自动化覆盖矩阵

| 用例 ID | 标题 | 优先级 | 是否自动化 | 理由 |
|:---|:---|:---|:---|:---|
| TC-WC-01 | 正常显示水质分析对比页面 | P0 | ✅ 是 | 基础冒烟，验证页面核心元素加载，定位器稳定(B级)，执行频率高。 |
| TC-WC-02 | 日期范围查询 | P0 | ✅ 是 | 核心业务功能，验证查询流程与结果加载，定位器稳定(B级)。 |
| (建议新增) | 查询后数据对比表格显示 | P1 | ✅ 是 | 验证查询结果的展示，与TC-WC-02耦合度高，可在同一测试方法中验证。 |
| (建议新增) | 选择取样位置并查询 | P1 | ✅ 是 | 验证双位置选择的交互与查询联动，属于核心功能。(⚠️ 需先实现 `el-select` 定位器) |
| (建议新增) | 点击重置按钮 | P1 | ❌ 建议手动 | 重置行为的预期结果(如清空表单、表格数据清空)模糊，手动验证更可靠，避免频繁维护。 |
| (建议新增) | 空数据状态显示 | P2 | ❌ 建议手动 | 验证UI层面的“暂无数据”提示，手动检查一次即可。 |
| (建议新增) | 日期格式校验 | P2 | ❌ 建议手动 | 等价类/边界值校验，自动化的维护成本高于其收益，且手动测试更灵活。 |

## 2. PageObject 拆分方案

当前 `WaterComparePage` 已经是一个结构合理的 Page Object，符合“一个页面一个 Page 类”的原则。**无需拆分**。

**职责**: `WaterComparePage` 负责封装水质分析对比页面的所有交互操作，包括：
-   页面导航与加载状态等待
-   日期输入框的设置 (`set_start_date`, `set_end_date`)
-   查询/重置按钮的点击 (`click_query`, `click_reset`)
-   页面加载状态验证 (`is_page_loaded`)
-   表格数据读取 (`get_table_row_count`)

**建议优化**：
-   `_js_click_search_or_reset` 方法是通用的，可以考虑将其迁移至 `BasePage` 或 `ElementPlusHelper` 作为公共方法，减少代码重复。

## 3. 公共组件复用分析

-   **BasePage复用**: `navigate_to`, `wait_page_ready`, `_wait_loading_gone`, `wait_vue_stable` 这四个方法是复用 `BasePage` 的，代码正确。
-   **ElementPlusHelper 扩展**:
    -   `set_start_date` 和 `set_end_date` 方法中的 `clear()`后`send_keys()`模式，可以提取为 `BasePage` 或 `ElementPlusHelper` 的 `fill_input_by_placeholder(placeholder, value)` 方法，提高代码复用性。
    -   `_js_click_search_or_reset` 方法可以提取为 `BasePage` 的 `_js_click_button_by_text(text)` 方法，供所有需要JS点击按钮的页面类使用。

## 4. 等待策略建议

1.  **异步行为分析**:
    -   `click_query` 和 `click_reset` 会触发数据请求。
    -   请求完成后，表格数据可能会重新渲染，期间会显示 `el-loading` 遮罩。

2.  **建议的等待封装**:
    -   **查询/重置后**: 现有的 `_wait_loading_gone(timeout=10)` 是处理 Element Plus 表格加载遮罩的**首选方案**，应保持使用。
    -   **备用等待 (兜底)**: 在 `_wait_loading_gone` 超时后，可以添加一个备用等待，等待 `el-table` 重新出现或其行数发生改变。例如:
        ```python
        # 在click_query后，等待表格行数不再为0
        WebDriverWait(self.driver, 5).until(lambda d: self.get_table_row_count() > 0)
        ```
    -   **不建议使用 `time.sleep()`**，当前封装已符合最佳实践。

## 5. ROI 分析

-   **版本**: 1.0
-   **预估开发时间**:
    -   PageObject代码已存在，需优化 `_js_click_search_or_reset` 方法 (0.5小时)。
    -   编写2个P0测试用例 (含建议新增的验证点) (1.5小时)。
    -   **总计**: **2 小时**
-   **预估维护成本**: 页面复杂度低，定位器较稳定。主要成本是当表格字段或查询条件变化时。预估 **0.5 小时 / 月**。
-   **手工执行时间**:
    -   执行1个P0用例链 (显示 + 查询 + 结果验证) 约 2 分钟。
    -   每月按 20 个工作日，每天触发1次回归计，总手工时间 = 2分钟/次 * 20次/月 = **40 分钟 / 月**。

-   **ROI 计算**:
    -   **3个月周期 (前期)**: ROI = (40分钟/月 * 3月) - (2小时 * 60分钟) - (0.5小时/月 * 60分钟 * 3月) = 120 - 120 - 90 = **-90 分钟** (净亏损)
    -   **6个月周期 (中期)**: ROI = (40分钟/月 * 6月) - 120 - (0.5 * 60 * 6) = 240 - 120 - 180 = **-60 分钟** (净亏损)
    -   **12个月周期 (长期)**: ROI = (40 * 12) - 120 - (0.5 * 60 * 12) = 480 - 120 - 360 = **0 分钟** (收支平衡)
    -   **12个月后**: 自动化开始展现其净收益。

**结论**: 本页面的自动化**ROI 周期较长**（约12个月收支平衡）。但由于其是P0核心功能，且为每日回归测试的必测项，**强烈建议自动化**。它可以确保基础功能在每次迭代后不被破坏，其稳定性价值远高于短期的时间成本。

## 6. 风险与建议

-   **定位器风险**:
    -   当前 `set_start_date` 和 `set_end_date` 使用的 `placeholder` 是B级，如果产品将中文文案改为英文，会导致测试失败。
    -   **建议** (来自TECH_ANALYSIS): 推动开发为 `el-date-picker` 添加稳定的 `data-testid` 属性，将此定位器提升至A级。
-   **未覆盖的核心交互**: 当前PageObject和测试脚本未包含 `el-select` (选择取样位置) 的实现和用例，这是页面的核心交互之一。
    -   **建议**: 尽快补充 `select_location1(text)` 和 `select_location2(text)` 方法，并为其设计测试用例。在实现前，应在策略中标注 `el-select` 的定位风险。