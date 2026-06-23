好的，遵照您的指示，我将基于提供的 `MyExamPage.py`、`test_my_exam.py` 和 `PAGE_CONTEXT.md`（以及其附带的元素定位信息），制定详细的自动化测试策略。

---

# AUTO_STRATEGY: 我的考试 (my-exam)

> **模块**: personnel  
> **页面**: 我的考试 (my-exam)  
> **策略版本**: 1.0  
> **分析日期**: 2026-06-18  
> **分析依据**: `MyExamPage.py`, `test_my_exam.py`, `PAGE_CONTEXT.md`, `BasePage` 能力清单

## 1. 自动化覆盖矩阵

| 用例编号 (示例) | 标题 (示例) | 优先级 | 是否自动化 | 理由与风险 |
| :--- | :--- | :--- | :--- | :--- |
| TC-MYEXAM-001 | **正常加载**：页面正常加载，表格显示考试列表 | **P0** | ✅ | **基础冒烟**。核心路径。`MyExamPage.navigate()` 和 `wait_element_visible` 已覆盖。 |
| TC-MYEXAM-002 | **搜索**：按考试名称搜索，表格数据正确刷新 | **P0** | ✅ | **核心功能**。`MyExamPage.search()` 已覆盖。**风险提示**：搜索后若表格为空，需处理 `TABLE_EMPTY` 状态。 |
| TC-MYEXAM-003 | **重置**：搜索后点击重置，表格恢复默认数据 | **P0** | ✅ | **核心功能**。`MyExamPage.reset_search()` 已覆盖。 |
| TC-MYEXAM-004 | **状态筛选**：按“未开始/进行中/已完成”筛选 | **P0** | ✅ | **核心功能**。`MyExamPage.select_status()` 已覆盖。**风险提示**：`el-select` 下拉选项的动态加载和可能存在的多个 `el-select` (若页面上有第二个筛选器)。 |
| TC-MYEXAM-005 | **分页操作**：切换页码，表格数据正确更新 | **P0** | ✅ | **核心功能**。需要调用 `BasePage.click_page()` 或直接点击分页按钮。 |
| TC-MYEXAM-006 | **“开始考试”操作**：对“未开始”的考试点击“开始考试” | **P0** | ✅ | **核心业务操作**。`MyExamPage.click_row_action()` 和 `MyExamPage.confirm_start_exam()` (需在 PO 中添加) 已规划。 |
| TC-MYEXAM-007 | **“开始考试”确认弹窗**：点击“确定”后进入考试页面 (或触发后续行为) | **P0** | ✅ | **核心流程**。需要验证弹窗交互。`DIALOG_CONFIRM_START` 定位器已定义。**风险提示**：点击“确定”后，页面可能跳转或触发 `window.location` 变化，需要处理 `wait_for_new_window` 或 URL 变化。 |
| TC-MYEXAM-008 | **无数据状态**：搜索一个不存在的考试名称，页面显示“暂无数据” | **P1** | ✅ | **异常路径**。可以验证空状态 UI。`MyExamPage.is_table_empty()` 已覆盖。 |
| TC-MYEXAM-009 | **模态弹窗交互** (查看详情) | **P1** | ✅ | **辅助功能**。验证“查看详情”弹窗的打开、关闭和内容显示。`DIALOG_DETAIL` 系列定位器已定义。 |
| TC-MYEXAM-010 | **权限测试**：无权限时，“开始考试”按钮不显示 | **P2** | ❌ | **依赖特定权限配置**。不适合作为普通自动化用例，因为它依赖特定的、不易动态创建的用户权限上下文。更适合`半自动化`或集成测试。 |
| TC-MYEXAM-011 | **性能测试**：页面上万条数据时的加载时间 | **P3** | ❌ | **非功能测试**。不适合现在的前端自动化框架。 |
| TC-MYEXAM-012 | **一次性操作**：在页面上线前执行一次数据初始化 | **P0 (临时)** | ❌ | **一次性任务**。不应写入自动化脚本，避免引入不必要的维护。 |

---

## 2. PageObject 拆分方案

**建议维持单一 `MyExamPage` 类，无需拆分。**

- **理由**：
    1. 页面结构清晰，搜索区、表格、分页、弹窗都在一个页面上，且交互逻辑紧密。
    2. `DIALOG_DETAIL` 和 `DIALOG_CONFIRM_START` 弹窗的交互相对简单（只有打开、关闭、确定、取消），可以看作是 `MyExamPage` 的操作方法的一部分。
    3. 拆分出独立的 `Dialog` 类（如 `ExamDetailDialog`, `ConfirmStartDialog`）会增加项目复杂性和维护成本，而收益不大。

**职责说明**:
- **`MyExamPage`**: 封装整个“我的考试”页面的所有操作，包括：
    - 搜索/筛选/重置
    - 表格数据读取与校验
    - 分页导航
    - 行操作（点击“开始考试”/“查看成绩”）
    - 弹窗交互（确认开始、查看详情）

---

## 3. 公共组件复用分析

### 与 `BasePage` 的复用
- **已复用**:
    - `self.navigate_to()`
    - `self.wait_vue_stable()`
    - `self.wait_element_visible()`, `self.wait_element_clickable()`, `self.wait_element_invisible()`
    - `self.find_elements()`
    - `self.logger`
    - `self.is_element_visible()`

- **建议复用**:
    - **分页操作**: 将分页导航（点击下一页、上一页、指定页码）提升到 `BasePage` 或 `ElementPlusHelper` 中，避免每个 Table Page 都重复实现。
        - 示例方法: `click_page(page_number)`, `click_next_page()`, `click_prev_page()`
        - `MyExamPage` 可以直接调用 `self.click_page(2)`
    - **`el-select` 选择**: 大部分 `el-select` 的交互模式是固定的：点击触发器 → 等待下拉菜单出现 → 点击菜单项。可考虑在 `ElementPlusHelper` 中提供一个通用的 `handle_select` 方法，接收 `(trigger_locator, option_text)` 或 `(trigger_locator, option_locator)` 参数。

### 与 `ElementPlusHelper` 的交互
- **`click_row_action`**: 该方法目前直接使用 `self.wait_element_clickable`。如果 `ElementPlusHelper` 有 `click_button_by_locator` 等封装，可以复用。
- **`select_status`**: 该方法目前是手动实现 `el-select` 的交互。如果 `ElementPlusHelper` 中已有 `handle_select` 方法，应替换简化。

---

## 4. 等待策略建议

| 操作 | 异步行为 | 建议等待策略 | 备注 |
| :--- | :--- | :--- | :--- |
| **搜索/筛选/重置** | `el-table` 的 `v-loading` 指令触发 loading 遮罩 | **等待 `TABLE_LOADING` 消失**: `self.wait_element_invisible(self.TABLE_LOADING)` | **风险提示**: 如果页面上有多个 loading 遮罩 (如表头和表体各自有)，此定位器可能不准确。建议使用 `//div[contains(@class, 'el-table')]//div[contains(@class, 'el-loading-mask')]` 来确保是表格内的 loading。 |
| **分页切换** | 同上，`v-loading` 触发 | **复用搜索/筛选的等待策略** | - |
| **弹窗打开** (确认开始/查看详情) | `el-dialog` 的 `v-if` 或 `v-show` 控制 | **等待弹窗可见**:
    - 确认弹窗: `self.wait_element_visible(self.DIALOG_CONFIRM_START)`
    - 详情弹窗: `self.wait_element_visible(self.DIALOG_DETAIL)` | **建议**: 在打开弹窗后，额外等待一个弹窗内的稳定元素（如弹窗标题或按钮）以确保渲染完成。 |
| **弹窗关闭** | 点击关闭按钮后，`el-dialog` 隐藏 | **等待弹窗消失**: `self.wait_element_invisible(self.DIALOG_DETAIL)` | - |
| **页面跳转** (开始考试后) | `window.location.href` 变化或新窗口打开 | **等待 URL 变化** 或 **等待新窗口出现**。 | `BasePage` 应封装 `wait_for_url_contains(url_part)` 或 `wait_for_new_window()` 方法。 |

---

## 5. ROI 分析 (共 10 个自动化用例)

| 指标 | 数值 | 说明 |
| :--- | :--- | :--- |
| **预估开发时间** | **4 小时** | 包含编写/优化 PO、用例、调试、定位器微调。 |
| **手工执行时间** (单次完整回归) | **5 分钟** | 包含手动执行 10 个用例 + 环境准备。 |
| **自动化执行时间** (单次完整回归) | **2 分钟** | 包含驱动启动、页面加载、断言。 |
| **手工回归执行频率** | **每月 40 次** (工作日每天2次) | 较高频，适合自动化。 |
| **预估维护成本** | **0.5 小时/月** | 主要涉及 UI 或 Element Plus 版本升级后的定位器调整。 |
| **ROI** | **`(5 - 2) * 40 - (4*60 / 60) - (0.5) = 120 - 4 - 0.5 = 115.5 分钟/月` (即节省约 **2 小时/月**)** | **3-4 个月收回初始投资**。 |

**结论**: **强烈建议自动化**。该页面核心功能稳定，测试用例高频且可重复，自动化能显著提升回归效率。

---

## 检查清单

- [x] **覆盖矩阵**: 每个 P0 用例标注 ✅ 自动化
- [x] **覆盖矩阵**: 每个非自动化用例有明确的“不建议自动化理由”
- [x] **PageObject 拆分方案**: 一个页面一个 Page 类，解释了不拆分的理由
- [x] **公共组件复用分析**: 标注了哪些可合并到 BasePage/ElementPlusHelper (分页、el-select)
- [x] **等待策略**: 标注了页面特有的异步行为 (v-loading、弹窗渲染、页面跳转)
- [x] **ROI 计算完整**: 开发时间 + 维护成本 + 手工执行时间，得出结论