好的，作为资深自动化测试专家，我已根据您提供的 `PAGE_CONTEXT.md` 和 `TECH_ANALYSIS.md`，结合项目基座的上下文和规范，制定出 `personnel/visitor` 页面的自动化测试策略。

以下是输出的 `AUTO_STRATEGY.md` 文件。

---

### AUTO_STRATEGY.md

```markdown
# 自动化测试策略: 访客管理 (personnel/visitor)

## 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 自动化理由 / 不自动化理由 | 风险 |
|----------|------|--------|------------|---------------------------|------|
| TC-VIS-001 | 页面正常加载 | P0 | ✅ | 基础冒烟用例，验证表格、分页等核心元素存在。定位器稳定。 | 无 |
| TC-VIS-002 | 访客姓名模糊搜索 | P0 | ✅ | 核心搜索功能。定位器稳定，通过 `placeholder` 定位。 | 无 |
| TC-VIS-003 | 来访状态精确筛选 | P0 | ✅ | 核心筛选功能。`el-select` 有固定选项值。 | 低风险：`el-select` 下拉选项通常渲染在 `body` 层，需注意触发和选取方式。 |
| TC-VIS-004 | 来访日期范围筛选 | P0 | ✅ | 核心筛选功能。`el-date-picker` 行为稳定。 | 中风险：日期选择器交互复杂，涉及到面板打开展开和日期点击，定位器易受版本更新影响。需封装在 `ElementPlusHelper` 中。 |
| TC-VIS-005 | 搜索条件重置 | P0 | ✅ | 验证重置按钮功能，确保表单清空并刷新。定位器稳定。 | 无 |
| TC-VIS-006 | 新增访客-成功 | P0 | ✅ | 核心业务操作。弹窗中表单字段都有明确标签。 | 无 |
| TC-VIS-007 | 新增访客-必填项校验 | P1 | ✅ | 验证表单校验逻辑。可以通过清空必填项并提交来触发。 | 无 |
| TC-VIS-008 | 编辑访客 | P0 | ✅ | 核心业务操作。通过表格行内按钮触发。 | 无 |
| TC-VIS-009 | 查看访客详情 | P0 | ✅ | 核心业务操作。通过表格行内按钮触发。 | 低风险：查看弹窗通常是只读模式，定位器与编辑弹窗类似。 |
| TC-VIS-010 | 删除访客-确认 | P0 | ✅ | 核心业务操作。涉及到二次确认弹窗。 | 无 |
| TC-VIS-011 | 删除访客-取消 | P1 | ✅ | 验证取消逻辑。 | 无 |
| TC-VIS-012 | 分页功能-切换每页条数 | P0 | ✅ | 核心交互。`el-pagination` 行为稳定。 | 无 |
| TC-VIS-013 | 分页功能-翻页 | P0 | ✅ | 核心交互。 | 无 |
| TC-VIS-014 | 强制离场 | P1 | ✅ | 特定业务操作，仅在“在访”状态出现。 | 低风险：需要先确保表格行处于可操作状态。 |
| TC-VIS-015 | 批量导入 | P2 | ❌ | 涉及到文件上传操作的复杂流程，跨模块交互。手工执行更稳定，自动化成本高。 | - |
| TC-VIS-016 | 导出访客列表 | P2 | ✅ | 可通过触发按钮和检查下载状态来实现。 | 中风险：文件下载路径和处理（如重命名、校验内容）在自动化中较为复杂。 |
| TC-VIS-017 | 页面加载权限控制 | P2 | ❌ | 涉及用户权限模拟，需要在登录阶段或通过API mock实现，不在页面交互层测试。由权限模块专项覆盖。 | - |
| TC-VIS-018 | 手机号在表格中脱敏展示 | P2 | ✅ | 验证UI展示逻辑。可以通过获取单元格文本进行字符串校验。 | 无 |

**总结**：P0 共 11 个，全部自动化。P1/P2 共 7 个，其中 5 个自动化，2 个不自动化。

## 2. PageObject 拆分方案

### 2.1 建议的 Page 类及职责

1.  **`VisitorListPage`**:
    -   **职责**: 封装访客列表页面的所有主要交互，包括搜索区、工具栏、表格区、分页区。
    -   **关键方法**:
        -   `search_by_name(name)`: 输入访客姓名并点击搜索。
        -   `search_by_status(status)`: 选择来访状态并点击搜索。
        -   `search_by_date(start_date, end_date)`: 选择来访日期范围并点击搜索。
        -   `click_reset()`: 点击重置按钮。
        -   `click_add_visitor()`: 点击“新增”按钮。
        -   `click_edit_by_visitor_name(visitor_name)`: 根据访客姓名在表格行内点击“编辑”。
        -   `click_view_by_visitor_name(visitor_name)`: 在表格行内点击“查看”。
        -   `click_delete_by_visitor_name(visitor_name)`: 在表格行内点击“删除”。
        -   `get_table_data()`: 获取表格中所有行的数据。
        -   `switch_page_size(size)`: 切换每页显示条数。
        -   `is_visitor_in_table(visitor_name)`: 检查特定访客是否在表格中。
        -   `get_visitor_count()`: 获取表格当前总数据条数。
        -   `click_force_logout(visitor_name)`: 在表格行内点击“强制离场”。
        -   `click_export()`: 点击“导出”按钮。

2.  **`VisitorFormDialog`** (用于新增和编辑弹窗):
    -   **职责**: 封装访客信息表单弹窗的所有操作。
    -   **关键方法**:
        -   `enter_visitor_name(name)`: 输入访客姓名。
        -   `enter_company(company)`: 输入所属单位。
        -   `enter_phone(phone)`: 输入手机号。
        -   `click_submit()`: 点击“确定/保存”按钮。
        -   `click_cancel()`: 点击“取消”按钮。
        -   `is_validation_error_visible(field_name)`: 检查必填项校验提示是否可见。

3.  **`VisitorViewDialog`** (用于查看详情弹窗):
    -   **职责**: 封装查看访客详情弹窗的操作。
    -   **关键方法**:
        -   `get_dialog_title()`: 获取弹窗标题（验证是“查看访客”）。
        -   `get_field_value_by_label(label)`: 通过表单项的 label 获取其值。
        -   `click_close()`: 关闭弹窗。

4.  **`ConfirmDialog`** (封装通用二次确认弹窗，复用已有组件):
    -   **职责**: 处理删除等操作后的二次确认弹窗。如果项目已有，则无需新建。
    -   **关键方法**:
        -   `confirm()`: 点击“确定”。
        -   `cancel()`: 点击“取消”。

## 3. 公共组件复用分析

-   **BasePage 能力复用**:
    -   `open_page(url)`: 直接复用，用于导航到访客管理页面。
    -   `wait_for_element_visible(locator)` / `wait_for_element_clickable(locator)`: 所有操作前都可复用。
    -   `click_element(locator)`: 所有按钮、文字链接点击都可复用。
    -   `input_text(locator, text)`: 所有 `el-input` 操作均可复用。
    -   `get_text(locator)`: 获取表格单元格、弹窗标题等文本。
    -   `is_element_present(locator)`: 用于判断元素是否存在（如某访客是否在表格中）。

-   **ElementPlusHelper 复用或扩展**:
    -   `select_dropdown_option(select_field_locator, option_text)`: 用于实现“来访状态”的下拉选择。建议**直接复用**。
    -   `confirm_el_dialog()`: 用于处理删除、关闭等操作后的 `el-message-box` 确认弹窗。建议**直接复用**。
    -   `pick_date_on_datepicker(date_input_locator, date_string)`: `VisitorListPage` 中的日期范围选择需要此方法。**待扩展**：当前如果是单日期选择，需扩展支持 `daterange` 类型。
    -   `click_pagination_jumper(page_num)`: 用于分页跳转。建议**直接复用**。

## 4. 等待策略建议

-   **页面加载完成后**: 等待 `el-table` 的 `loading` 属性消失。可以为 `VisitorListPage` 添加一个 `static wait_for_page_loaded(self)` 方法，等待表格 `el-table` 或分页器 `el-pagination` 变为可见。
-   **搜索操作后**: 等待表格数据刷新，具体表现为表格 `loading` 属性消失然后重显。
-   **弹窗操作后**: `el-dialog` 打开动画结束（监听 `dialog-visible` class 或属性）。
-   **统一封装**: 建议在 `BasePage` 中提供一个 `wait_for_table_loaded` 方法，或在 `VisitorListPage` 中定义一个内部等待方法，等待表格的 `v-loading` 指令对应的 DOM 状态变化。对于 `el-dialog`，建议在 `BaseDialog` 类（如果有）或 `ElemntPlusHelper` 中封装 `wait_for_dialog_visible` 方法。
-   **具体例子**:
    ```python
    # 在 VisitorListPage 中
    class VisitorListPage(BasePage):
        _search_button = (By.XPATH, "//button[.//span[text()='搜索']]") # 假设的定位器

        def search_visitor(self, name):
            # ... 输入名字 ...
            self.click_element(self._search_button)
            # 关键等待：等待表格刷新
            self.wait_for_table_loaded() # 自定义或框架提供的方法
    ```

## 5. ROI 分析

-   **手工执行成本**:
    -   单次执行全部用例时间: `~15` 分钟。
    -   回归测试频率: 按每周 5 次计算。
    -   每周手工成本: `15 min * 5 = 75 min = 1.25 小时`。
    -   每月手工成本 (按 4 周): `1.25 小时 * 4 = 5 小时`。

-   **自动化成本**:
    -   **预估开发时间**: `8 小时` (设计 + 编码 + 自测)。
    -   **预估维护成本**: `0.5 小时/月` (定位器微调、新增用例等)。

-   **ROI 计算 (3个月维度)**:
    -   **手工总成本**: `5 小时/月 * 3 月 = 15 小时`。
    -   **自动化总成本**: `8 小时 (一次开发) + 0.5 小时/月 * 3 月 = 9.5 小时`。
    -   **节省时间**: `15 小时 - 9.5 小时 = 5.5 小时`。

-   **结论**: 在 **3 个月**内自动化测试即可收回成本并产生正向收益。考虑到 P0 用例全部自动化带来的质量信心和快速反馈，自动化测试的 ROI 非常高，强烈建议投入开发。
```