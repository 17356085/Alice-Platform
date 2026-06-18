好的，遵照您的指令。作为负责“自动化策略”的AI Agent，我将基于您提供的“personnel/my-archive”页面的 `PAGE_CONTEXT.md`，结合假设的 `TECH_ANALYSIS.md` 和项目基座上下文中的 `BasePage` 能力，制定一份详细的自动化测试策略。

---

## AUTO_STRATEGY.md

> **版本**: 1.0 | **最后更新**: 2026-06-18 | **维护者**: automation-agent
> **页面**: personnel / my-archive (我的档案)
> **依赖**: `testcases-personnel-my-archive.md`, `TECH_ANALYSIS.md`, `BasePage` 能力清单

---

## 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
|----------|------|--------|------------|------|
| TC-LOGIN-001 | 页面正常加载 | P0 | ✅ | 基础冒烟，定位器稳定 |
| TC-BASIC-001 | 切换Tab至基本信息 | P0 | ✅ | 核心页面导航校验 |
| TC-BASIC-002 | 查看基本信息表单内容 | P0 | ✅ | 关键数据展示，`el-input`定位稳定 |
| TC-BASIC-003 | 点击“编辑基本信息”按钮 | P1 | ✅ | 触发弹窗的关键操作 |
| TC-BASIC-004 | 编辑基本信息并保存 | P1 | ✅ | 重要业务流程，需用边界值校验（可选） |
| TC-BASIC-005 | 编辑基本信息并取消 | P1 | ⚠️ | 可自动化，但定位器`el-message`不稳定，风险较高 |
| TC-PWD-001 | 打开“修改密码”弹窗 | P2 | ❌ | 一次性操作（仅限用户主动执行），ROI低 |
| TC-ARCHIVE-001 | 切换Tab至档案变更记录 | P0 | ✅ | 核心Tab切换，校验表格是否加载 |
| TC-ARCHIVE-002 | 按变更类型筛选记录 | P1 | ✅ | 功能性筛选，`el-select`操作稳定 |
| TC-ARCHIVE-003 | 按日期范围筛选记录 | P2 | ⚠️ | 定位器`el-date-picker`稳定，但日期选择逻辑复杂，维护成本高 |
| TC-ARCHIVE-004 | 查询后表格数据更新 | P1 | ✅ | 验证筛选功能的有效性 |
| TC-ARCHIVE-005 | 分页功能验证 | P2 | ✅ | 优先校验分页组件是否正常出现，不覆盖多页导航 |
| TC-SMOKE-001 | 个人标签状态（在职/试用期） | P2 | ❌ | 需要特定测试数据，维护成本高，手工检查更高效 |

**风险标注**:
- `TC-BASIC-005`: `el-message` 为瞬态元素，定位时机难以精确把控，建议使用更稳定的断言方式。
- `TC-ARCHIVE-003`: `el-date-picker` 的日期选择和确认操作在无 `id` 或 `class` 标记时容易定位到错误的DOM节点，需使用精确的XPath策略。

## 2. PageObject 拆分方案

### 2.1 `MyArchivePage` (主页面类)

```python
class MyArchivePage(BasePage):
    def __init__(self, driver: WebDriver):
        super().__init__(driver)
        self.page_locator = (By.CSS_SELECTOR, ".my-archive-page")

    # Tab 切换
    def switch_to_basic_info_tab(self):
        """切换至基本信息Tab"""
        self.click(self.basic_info_tab)
        return self

    def switch_to_archive_tab(self):
        """切换至档案变更记录Tab"""
        self.click(self.archive_tab)
        return self

    # 基本信息 Tab
    def get_employee_name(self) -> str:
        """获取基本信息中的员工姓名"""
        return self.get_input_value(self.field_employee_name)

    def click_edit_basic_info(self):
        """点击编辑按钮"""
        self.click(self.edit_basic_info_btn)
        return EditInfoDialog(self.driver)

    # 档案变更记录 Tab
    def select_change_type(self, type_value: str):
        """在变更类型下拉框中选择选项"""
        self.select_by_value(self.change_type_select, type_value)
        return self

    def click_search(self):
        """点击查询按钮"""
        self.click(self.search_btn)
        return self

    # ... 其他方法
```

### 2.2 `EditInfoDialog` (弹窗类)

```python
class EditInfoDialog(BasePage):
    def __init__(self, driver: WebDriver):
        super().__init__(driver)
        self.dialog_locator = (By.XPATH, "//div[contains(@class, 'el-dialog')][.//span[contains(text(), '编辑基本信息')]]")

    # 表单输入
    def fill_name(self, name: str):
        self.fill_input(self.dialog_name_input, name)
        return self

    def select_department(self, dept: str):
        self.select_by_label(self.dialog_department_select, dept)
        return self

    # 操作
    def click_save(self):
        self.click(self.dialog_save_btn)
        return self
```

## 3. 公共组件复用分析

- **可复用 `BasePage` 方法**:
  - `self.wait_element_visible(locator)`: 用于所有页面和弹窗的元素可见性等待。
  - `self.click(locator)`: 用于所有按钮、Tab、复选框等可点击元素。
  - `self.fill_input(locator, text)`: 用于所有输入框 (`el-input`, `el-input__inner`)。
  - `self.get_input_value(locator)`: 用于获取只读输入框的值。
  - `self.select_by_value(locator, value)` / `self.select_by_label(locator, label)`: 用于所有 `el-select` 下拉框选择。

- **需要扩展 `ElementPlusHelper` 的方法**:
  - `handle_date_picker(locator, start_date, end_date)`: `el-date-picker` (daterange) 的自动化操作可抽象为公共方法，封装点击输入框、选择日期、确认等步骤。
  - `wait_for_table_load(locator)`: `el-table` 加载数据可能耗时较长（异步请求），可扩展一个专用等待方法，等待表格行出现或加载动画消失。

## 4. 等待策略建议

| 操作 | 建议等待策略 | 备注 |
|------|---------------|------|
| 页面加载 | `wait_element_visible(MyArchivePage.page_locator)` | 前置条件：登录完成后 |
| Tab切换 | `wait_until_attribute_is(active_tab_locator, "aria-selected", "true")` | 确保新Tab内容已渲染 |
| 弹窗出现 | `wait_element_visible(dialog_locator)` | 依赖 `ElementPlusHelper.wait_dialog_visible()` |
| 表单内容渲染 | `wait_for_value(field_locator)` | 等待只读 `el-input` 中填充值不为空 |
| 表格数据加载 | `wait_for_table_cell_exists(change_table_locator)` | 等待 `el-table` 下至少出现一个单元格 |
| 保存操作 | `wait_for_success_message()` + 等待弹窗消失 | 保存后通常会有成功提示和弹窗关闭动画 |
| 日期选择器 | `element_to_be_clickable(date_picker_locator)` + `time.sleep(0.5)` | Element Plus 日期选择器有复杂动画，强制等待不可完全避免但需控制时长 |

**建议封装**:
```python
# 在 ElementPlusHelper 或 MyArchivePage 中
def wait_for_table_data_loaded(self, timeout=10):
    # 1. 等待加载动画消失（如果有）
    # 2. 等待表格出现行
    self.wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr.el-table__row"))
    )
```

## 5. ROI 分析

- **预估开发时间**:
  - 页面主类和弹窗类编写: 3 小时
  - 核心用例 (P0): 2 小时
  - 扩展用例 (P1, P2): 3 小时
  - 调试与定位器校准: 2 小时
  - **总计**: **10 小时**

- **预估维护成本**:
  - 平均每月因UI改动导致的定位器失效: 0.5 小时
  - 平均每月因业务逻辑变更导致的用例失败: 1 小时
  - **预估维护成本**: **1.5 小时/月**

- **手工执行时间**:
  - 执行全部 P0-P2 测试用例所需时间: 约 20 分钟
  - **手工执行时间**: **20 分钟/次**

- **ROI 计算**:
  > 假设每周执行一轮回归测试（每月约4次）。

  - **1 年后 ROI**:
    - 手工执行总时间 = 20分钟/次 × 48次 = 960分钟 ≈ 16小时
    - 自动化开发 + 1年维护成本 = 10小时 + (1.5小时/月 × 12月) = 28小时
    - **ROI = 16 - 28 = -12小时** (第一年投入较大)

  - **2 年后 ROI**:
    - 手工执行总时间 = 20分钟/次 × 96次 = 1920分钟 ≈ 32小时
    - 自动化开发 + 2年维护成本 = 10小时 + (1.5小时/月 × 24月) = 46小时
    - **ROI = 32 - 46 = -14小时** (第二年后仍为负值，主要因为维护成本超出预期)

  - **调整建议**: 通过简化定位器和增加异常处理，可将年维护成本控制在10小时以内，则2年后ROI为正。

**结论**: 对于“我的档案”页面，自动化测试在**长期**（2-3年后），尤其是在维护成本得到良好控制的情况下，能显著节省手工执行时间。建议**优先自动化P0和P1级核心用例**，对P2级低价值用例保持谨慎。