好的，收到。这是基于 `exam-record` 页面的 **PAGE_CONTEXT.md** 和 **TECH_ANALYSIS.md**（预测版），为您制定的自动化测试策略。

---

# AUTO_STRATEGY.md

**页面**: `exam-record`（考试记录）  
**模块**: `personnel`  
**生成日期**: 2026-06-18  
**基于**: PAGE_CONTEXT.md (预测版) + TECH_ANALYSIS.md (预测版)  
**依赖**: `BasePage`, `ElementPlusHelper`, `pytest`

---

## 1. 自动化覆盖矩阵

| 用例编号 (假设) | 标题 | 优先级 | 是否自动化 | 理由与风险 |
| :--- | :--- | :--- | :--- | :--- |
| TC-PERSONNEL-EXAM-RECORD-001 | 页面正常加载 (元素可见) | P0 | ✅ | 基础冒烟，覆盖关键元素即可。 |
| TC-PERSONNEL-EXAM-RECORD-002 | 按“人员姓名”搜索 | P0 | ✅ | 核心功能，`el-input` 定位器稳定 (A级)。 |
| TC-PERSONNEL-EXAM-RECORD-003 | 按“考试类型”搜索 | P0 | ✅ | 核心功能，`el-select` 下拉选择。 |
| TC-PERSONNEL-EXAM-RECORD-004 | 按“状态”搜索 | P0 | ✅ | 核心功能，`el-select` 下拉选择。 |
| TC-PERSONNEL-EXAM-RECORD-005 | 组合搜索 (姓名+类型+状态) | P0 | ✅ | 核心功能验证。 |
| TC-PERSONNEL-EXAM-RECORD-006 | 搜索后重置 | P0 | ✅ | 基础交互，`el-button` 文本定位 (A级)。 |
| TC-PERSONNEL-EXAM-RECORD-007 | 表格数据正确加载与分页 | P0 | ✅ | 验证表格行数和分页组件存在。 |
| TC-PERSONNEL-EXAM-RECORD-008 | 查看考试记录详情 | P1 | ✅ | 核心交互, 触发 `el-dialog` 弹窗。 |
| TC-PERSONNEL-EXAM-RECORD-009 | 查看详情弹窗元素可见 | P1 | ✅ | 验证弹窗内表单字段可见。 |
| TC-PERSONNEL-EXAM-RECORD-010 | 查看详情弹窗关闭 | P1 | ✅ | 基础交互。 |
| TC-PERSONNEL-EXAM-RECORD-011 | 导出功能 (触发下载) | P0 | ✅ | 核心操作。**风险**：需处理浏览器下载弹窗，建议使用 `Chrome Options` 预配置下载路径。 |
| TC-PERSONNEL-EXAM-RECORD-012 | 空数据搜索 | P1 | ❌ | 建议作为手动测试或单独数据准备脚本，自动化维护成本高。 |
| TC-PERSONNEL-EXAM-RECORD-013 | 长时间搜索 (性能) | P2 | ❌ | 性能测试不属于UI自动化范畴。 |
| TC-PERSONNEL-EXAM-RECORD-014 | 导出权限控制 | P0 | ✅ | 权限测试，可以通过检查元素是否存在或`is_enabled()` 验证。**风险**：权限依赖登录用户角色，需要配合fixture设置。 |
| TC-PERSONNEL-EXAM-RECORD-015 | 考试日期范围搜索 | P1 | ✅ | `el-date-picker` 交互较复杂，但属于核心功能。 |

---

## 2. PageObject 拆分方案

```
pages/
├── exam_record_page.py          # 主页面：搜索、表格、分页、导出操作
└── exam_record_detail_dialog.py # 独立 Dialog 类：查看/编辑详情弹窗
```

- **`ExamRecordPage`**:
    - **职责**: 封装 `exam-record` 页面所有元素定位器和业务操作方法（搜索、重置、导出、获取表格行数、翻页）。
    - **依赖**: `BasePage`.
- **`ExamRecordDetailDialog`**:
    - **职责**: 封装“查看详情”弹窗的元素定位和交互（获取表单值、关闭弹窗）。
    - **依赖**: `BasePage`.
    - **理由**: 弹窗是一个独立的、可复用的UI组件（可能在其他页面也有类似“详情”弹窗），独立成类便于维护和复用。

---

## 3. 公共组件复用分析

| 操作 | 复用/扩展方案 |
| :--- | :--- |
| **搜索** | 复用 `BasePage` 的 `search_and_click(self, input_locator, button_locator, text)` 方法。 |
| **重置** | 复用 `BasePage` 的 `click_element(self, locator)` 方法。 |
| **选择下拉框** | 需要扩展 `ElementPlusHelper` 或 `BasePage`，封装 `select_el_option(self, trigger_locator, option_text)` 方法。 |
| **日期选择** | 需要扩展 `BasePage`，封装 `select_el_date_picker_range(self, start_locator, end_locator, start_date, end_date)` 方法。 |
| **表格行操作** | 复用 `BasePage` 的 `click_table_action_button(self, row_index, action_text)` 方法（如果存在）。否则，基于 `el-table` 的结构（`el-table__body-wrapper tbody tr`）进行扩展。 |
| **弹窗操作** | `ExamRecordDetailDialog` 将复用 `BasePage` 的 `wait_for_element_visible`, `get_text`, `click_element` 等方法。 |
| **分页** | 复用 `ElementPlusHelper` 提供的分页交互方法。 |

---

## 4. 等待策略建议

| 元素/交互 | 等待策略 | 备注 |
| :--- | :--- | :--- |
| **搜索后表格刷新** | `element_to_be_invisible(By.CSS_SELECTOR, "el-table__empty-text")` 并等待特定行出现。 | **核心等待**，防止读取到旧的或空的表格数据。 |
| **弹窗出现** | `visibility_of_element_located` (Dialog 主容器)。 | 标准显式等待。 |
| **下拉选择框展开** | `visibility_of_element_located` (popper容器中的 `el-option`)。 | `el-select` 的选项渲染在 `body` 下，需要等待 popper 出现。 |
| **日期选择器浮层** | `visibility_of_element_located` (`el-picker-panel` 容器)。 | 同上，浮层可能渲染在 `body` 下。 |
| **导出下载** | 文件下载无DOM变化，无法通过Selenium直接等待。建议使用pytest插件（如 `pytest-watchdog`）或固定等待时间（如5秒）后检查下载目录。 | 非完美方案，但可接受。 |

**建议**: 在 `BasePage` 或 `ExamRecordPage` 中创建一个专用的 `wait_for_search_result()` 方法，封装表格数据加载的等待逻辑。

---

## 5. ROI 分析

| 项目 | 估算值 | 说明 |
| :--- | :--- | :--- |
| **自动化开发时间 (X)** | **10 小时** | 包含编写PageObject、封装通用方法、编写测试脚本（P0+P1）、调试。 |
| **单次手工执行时间 (Z)** | **15 分钟** | 覆盖全部P0和P1用例。 |
| **预估手动执行频率** | **30 次/周** (回归测试 + CI) | 取中间值，随着迭代频率增加。 |
| **月度维护成本 (Y)** | **2 小时/月** | 主要维护元素定位器和数据断言，UI变动导致。 |
| **月度自动化运行成本** | **忽略不计** | (CI运行时间，约30分钟) |
| **月度节约时间 (ROI)** | **20 小时/月** | 计算过程：`(15分钟/次 * 30次/周 * 4周) - (2小时维护) - (0.5小时运行) ≈ 20 小时` |

**结论**: 高ROI，强烈建议自动化。即使每月维护成本上升至 **4 小时/月**，自动化依然能节约大量手工回归时间。

---

> **下一步**: 根据此策略，`automation-agent` 将进入 **Skill: code-generation** 阶段，生成具体的 `ExamRecordPage`、`ExamRecordDetailDialog` 和对应的测试脚本。