好的，已收到您的请求。模块: `personnel`，页面: `exam-record`。

基于您提供的 **PAGE_CONTEXT.md**（页面上下文）、**TECH_ANALYSIS.md**（技术分析）以及项目基座上下文，我将输出自动化策略文档。

---

# AUTO_STRATEGY.md — 考试记录页面

## 1. 自动化覆盖矩阵
**参考**: `PAGE_CONTEXT.md` 中的页面分析框架 & `TECH_ANALYSIS.md` 中的定位器稳定性评估

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
| :--- | :--- | :--- | :--- | :--- |
| TC-P0-001 | 搜索：按人员姓名搜索 | P0 | ✅ | 核心搜索功能，定位器稳定。 |
| TC-P0-002 | 搜索：按考试日期范围搜索 | P0 | ✅ | 核心搜索功能，定位器稳定。 |
| TC-P0-003 | 搜索：按考试类型搜索 | P0 | ✅ | 核心搜索功能，定位器稳定。 |
| TC-P0-004 | 搜索：按状态搜索 | P0 | ✅ | 核心搜索功能，定位器稳定。 |
| TC-P0-005 | 搜索：重置搜索条件 | P0 | ✅ | 核心交互，定位器稳定。 |
| TC-P0-006 | 表格：分页功能 (切换页数/页码) | P0 | ✅ | 核心交互，`el-pagination` 定位器稳定。 |
| TC-P0-007 | 交互：点击 “查看” 按钮，查看考试记录详情 | P0 | ✅ | 核心功能，弹窗定位器 (`dialog_detail`) 稳定。 |
| TC-P0-008 | 弹窗：查看详情弹窗点击 “确定” 关闭 | P0 | ✅ | 弹窗关闭逻辑，稳定。 |
| TC-P0-009 | 异常：搜索无结果 | P2 | ❌ | 属于异常/边界用例，自动化收益低，执行频率不高。 |
| TC-P0-010 | 异常：输入超长字符搜索 | P3 | ❌ | 非常规操作，维护成本高。 |
| TC-P1-001 | 导出：点击导出按钮 | P1 | ❌ | **不建议自动化** (一次性操作，通常涉及文件下载路径选择，人工确认更合理)。 |

**风险标注**:
- `dialog_detail` 弹窗：技术分析指出 `el-dialog__wrapper` 可能动态生成，已采用 `title` 属性作为稳定定位器。**风险: 低**

## 2. PageObject 拆分方案
遵循“一个页面一个 Page 类，复杂弹窗独立”原则。

```
├── pages/
│   ├── exam_record/
│   │   ├── exam_record_page.py          # 主页面 Page Object
│   │   └── exam_detail_dialog.py        # 考试记录详情弹窗 Page Object
│   └── ...
```

### 2.1 `ExamRecordPage` 职责
*   **搜索区 (SearchArea)**
    *   `click_search_btn()`
    *   `click_reset_btn()`
    *   `input_person_name(name: str)`
    *   `select_exam_type(type: str)`
    *   `select_status(status: str)`
    *   `pick_exam_date_range(start: str, end: str)`
*   **表格区 (TableArea)**
    *   `get_table_data()` -> 返回表格数据列表
    *   `click_action_button(row_index, button_name)` (如果只有一个操作按钮，直接 `view_detail(row_index)`)
*   **分页区 (Pagination)**
    *   `switch_page(page_number)`
    *   `set_page_size(size)`

### 2.2 `ExamDetailDialog` 职责
*   **弹窗交互**
    *   `get_detail_info()` -> 返回详情字段字典
    *   `click_confirm()`
    *   `click_cancel()`  (如果有关闭按钮)

## 3. 公共组件复用分析
*   **可复用 `BasePage` 现有方法**:
    *   `wait_table_loaded` -> 用于表格数据加载后的等待。
    *   `wait_dialog_visible` -> 用于 `dialog_detail` 弹窗出现后的等待。
    *   `wait_loading_disappear` -> 用于搜索/页面切换时的加载等待。
    *   `click_button_by_text` -> 用于点击分页按钮、弹窗的“确定”按钮（如果 `BasePage` 已封装此通用方法）。
*   **无需扩展 `ElementPlusHelper`**:
    *   当前页面交互 ( `el-input`, `el-select`, `el-table`, `el-dialog` ) 均属于常规交互，`ElementPlusHelper` 已有 `select_option` 等方法覆盖。
    *   ✅ **无需扩展**

## 4. 等待策略建议
*   **页面特有的异步行为**:
    *   `el-loading` 覆盖在 `el-table` 上。
    *   `el-dialog` 出现/消失的动画。
*   **建议的等待封装**:
    *   **通用**: 在 `ExamRecordPage` 的 `search()` 方法中添加 `self.wait_loading_disappear()`。
    *   **弹窗**: 在 `ExamDetailDialog` 的构造函数或 `wait_ready()` 方法中添加 `self.wait_dialog_visible()`。

## 5. ROI 分析
*   **预估开发时间**: **12 小时** (1.5 人天)
    *   PageObject 编写: 6 小时
    *   测试用例编写与调试: 6 小时
*   **预估维护成本**: **2 小时/月** (UI 变更不频繁，主要是 XPath 定位微调)
*   **手工执行时间**: **8 分钟/次** (覆盖 P0 用例)
*   **执行频率**: 每天一次 (包含在回归集中)
*   **ROI 计算 (按 1 年)**:
    *   **自动化收益**: `手工执行时间 × 执行频率 × 月数 = 8 分钟 × 22 天/月 × 12 月 = 2112 分钟 ≈ 35 小时`
    *   **自动化成本**: `开发时间 + 维护成本 × 月数 = 12 小时 + 2 小时/月 × 12 月 = 36 小时`
    *   **ROI**: **(35 - 36) / 36 ≈ -2.8%** (1 年回本不明显，但考虑到回归频率后期上升，或 P1 用例加入后，2 年内有显著回报。对于高频 P0 用例，自动化是必要的。)
    *   **评估**: **建议自动化**