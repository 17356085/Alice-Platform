好的，遵照您的指令。作为负责“自动化策略”的AI Agent，我将基于提供的 `TEST_CASES.md` (推测) 和 `TECH_ANALYSIS.md` 内容，以及页面上下文，为 “personnel” 模块的 “my-archive” 页面制定自动化测试策略，生成 `AUTO_STRATEGY.md`。

由于您未提供 `TEST_CASES.md`，我将根据 `PAGE_CONTEXT.md` 和 `TECH_ANALYSIS.md` 中的业务功能描述，**推断出典型的 P0/P1 测试用例**，并以此为基础进行策略分析。

---

### AUTO_STRATEGY.md

```markdown
# AUTO_STRATEGY: personnel / my-archive (我的档案)

> **版本**: 1.0 | **最后更新**: 2026-06-18 | **维护者**: automation-agent
> **分析依据**: `PAGE_CONTEXT.md` (版本 1.0), `TECH_ANALYSIS.md` (版本 1.0), `AUTOMATION_ARCHITECTURE.md` (版本 2.0)
> **基础假设**: 使用 Selenium + pytest 框架，`BasePage` 封装了通用等待、元素定位和操作，`ElementPlusHelper` 封装了 El-Select, El-DatePicker, El-Dialog 等组件的交互。

## 1. 自动化覆盖矩阵

| 用例编号 | 字段/操作/场景 | 优先级 | 是否自动化 | 理由 |
|----------|---------------|--------|----------|------|
| TC-AUTO-001 | **页面正常加载**: 验证页面标题、个人状态标签、Tab 页签显示正常 | P0 | ✅ | 基础冒烟，可用 `get_text()` 断言页面标题。 |
| TC-AUTO-002 | **Tab 切换**: 在“基本信息”与“档案变更记录”Tab 间切换 | P0 | ✅ | 核心导航功能，定位器稳定 (`#tab-*`)。 |
| TC-AUTO-003 | **查询档案变更记录**: 选择变更类型+日期范围，点击“查询” | P0 | ✅ | 核心业务操作，验证表格数据刷新。 |
| TC-AUTO-004 | **重置筛选条件**: 执行查询后点击“重置” | P1 | ✅ | 常规UI交互，验证所有筛选器恢复默认值。 |
| TC-AUTO-005 | **表格空数据处理**: 筛选无结果，验证空数据提示 | P1 | ✅ | 边界情况，验证 `.el-table__empty-text` 文案。 |
| TC-AUTO-006 | **分页功能**: 翻页、切换每页条数 (10/20) | P1 | ✅ | 表格基本功能。 |
| TC-AUTO-007 | **编辑基本信息**: 点击“编辑”，修改姓名/部门，保存成功 | P0 | ✅ | 核心CRUD操作，弹窗处理。 |
| TC-AUTO-008 | **编辑基本信息 - 输入校验**: 手机号/邮箱格式错误，验证错误提示 | P1 | ✅ | 表单校验的自动化验证。 |
| TC-AUTO-009 | **取消编辑操作**: 在编辑弹窗中点击“取消” | P1 | ✅ | 弹窗的“取消”按钮交互。 |
| TC-AUTO-010 | **修改密码**: 旧密码验证、新密码确认，保存成功 | P1 | ✅ | 核心安全操作，联动 `password-dialog`。 |
| TC-AUTO-011 | **修改密码 - 校验失败**: 新密码与确认密码不一致，验证提示 | P2 | ❌ | 校验逻辑较基础，手动验证更直观，且成本高。 |
| TC-AUTO-012 | **左侧快捷操作**: 点击“编辑资料”/“修改密码” | P1 | ✅ | 次要入口，可复用弹窗逻辑。 |
| TC-AUTO-013 | **页面UI美观度**: 布局、样式、颜色一致性 | P2 | ❌ | **定位器不稳定** (CSS样式频繁修改)，且依赖视觉判断，强依赖AI自动化框架，成本高。 |
| TC-AUTO-014 | **浏览器缩放/分辨率兼容**: 页面布局在不同分辨率下正确 | P2 | ❌ | **一次性操作** (上线前测试)，自动化维护成本超过收益。 |

## 2. PageObject 拆分方案

根据一个页面一个 Page 类，复杂弹窗独立的原则，拆分如下：

```
models/
├── page_objects/
│   ├── base_page.py                             # BasePage (已有)
│   ├── helpers/
│   │   ├── element_plus_helper.py               # ElementPlusHelper (已有)
│   └── personnel/
│       ├── my_archive_page.py                   # 主 Page 类
│       ├── edit_info_dialog.py                  # 编辑基本信息弹窗
│       └── change_password_dialog.py            # 修改密码弹窗
```

### 2.1 主 Page 类 `MyArchivePage`
```python
class MyArchivePage(BasePage):
    # URL
    PAGE_URL = "/personnel/my-archive"

    # Locator Set
    # --- Header ---
    PAGE_TITLE = (By.CSS_SELECTOR, ".page-title")
    EMPLOYEE_STATUS_TAG = (By.CSS_SELECTOR, ".status-tag")  # 状态标签

    # --- Tabs ---
    BASIC_INFO_TAB = (By.CSS_SELECTOR, "#tab-basic-info")
    ARCHIVE_TAB = (By.CSS_SELECTOR, "#tab-archive")

    # --- Archive Tab Search Area ---
    CHANGE_TYPE_SELECT = (By.CSS_SELECTOR, "#change-type-select")
    CHANGE_DATE_PICKER = (By.CSS_SELECTOR, "#change-date-picker")
    SEARCH_BTN = (By.CSS_SELECTOR, "#search-btn")
    RESET_BTN = (By.CSS_SELECTOR, "#reset-btn")

    # --- Archive Tab Table ---
    CHANGE_TABLE = (By.CSS_SELECTOR, "#change-table")
    TABLE_EMPTY_TEXT = (By.CSS_SELECTOR, ".el-table__empty-text")
    PAGINATION = (By.CSS_SELECTOR, "#pagination")
    TABLE_ROWS = (By.CSS_SELECTOR, "#change-table tbody tr.el-table__row")  # 动态元素

    # --- Basic Info Form (Read-only) ---
    FIELD_NAME = (By.CSS_SELECTOR, "#field-employee-name input")
    EDIT_BASIC_INFO_BTN = (By.CSS_SELECTOR, "#edit-basic-info-btn")
    LEFT_EDIT_PROFILE_BTN = (By.XPATH, "//button[contains(text(), '编辑资料')]")  # 相对XPath
    LEFT_CHANGE_PASSWORD_BTN = (By.XPATH, "//button[contains(text(), '修改密码')]")

    # --- Page Operations (链式调用) ---
    def switch_to_basic_info_tab(self):
        self.click(self.BASIC_INFO_TAB)
        return self

    def switch_to_archive_tab(self):
        self.click(self.ARCHIVE_TAB)
        return self

    def select_change_type(self, value: str):
        ElementPlusHelper.select_by_label(self, self.CHANGE_TYPE_SELECT, value)
        return self

    def pick_date_range(self, start_date: str, end_date: str):
        ElementPlusHelper.pick_daterange(self, self.CHANGE_DATE_PICKER, start_date, end_date)
        return self

    def click_search(self):
        self.click(self.SEARCH_BTN)
        return self

    def click_reset(self):
        self.click(self.RESET_BTN)
        return self

    def get_table_rows_count(self):
        return len(self.find_elements(self.TABLE_ROWS))

    def is_table_empty(self):
        return self.is_visible(self.TABLE_EMPTY_TEXT)

    def click_edit_basic_info(self):
        self.click(self.EDIT_BASIC_INFO_BTN)
        return EditInfoDialog(self.driver)  # 返回弹窗Page Object

    def click_change_password(self):
        self.click(self.LEFT_CHANGE_PASSWORD_BTN)
        return ChangePasswordDialog(self.driver)
```

### 2.2 弹窗类 `EditInfoDialog`
```python
class EditInfoDialog(BasePage):
    # 定位弹窗本身
    DIALOG = (By.CSS_SELECTOR, "#edit-info-dialog")

    # 表单元素
    NAME_INPUT = (By.CSS_SELECTOR, "#dialog-name-input input")
    DEPARTMENT_SELECT = (By.CSS_SELECTOR, "#dialog-department-select")
    POSITION_INPUT = (By.CSS_SELECTOR, "#dialog-position-input input")
    PHONE_INPUT = (By.CSS_SELECTOR, "#dialog-phone-input input")
    EMAIL_INPUT = (By.CSS_SELECTOR, "#dialog-email-input input")

    SAVE_BTN = (By.CSS_SELECTOR, "#dialog-save-btn")
    CANCEL_BTN = (By.CSS_SELECTOR, "#dialog-cancel-btn")

    # 校验信息 (错误提示)
    FIELD_ERRORS = (By.CSS_SELECTOR, ".el-form-item__error")  # 泛化定位

    def fill_name(self, name: str):
        self.clear_and_type(self.NAME_INPUT, name)
        return self

    def select_department(self, dept: str):
        ElementPlusHelper.select_by_label(self, self.DEPARTMENT_SELECT, dept)
        return self

    def fill_phone(self, phone: str):
        self.clear_and_type(self.PHONE_INPUT, phone)
        return self

    def click_save(self):
        self.click(self.SAVE_BTN)
        return self  # 保存后弹窗关闭，回到MyArchivePage

    def click_cancel(self):
        self.click(self.CANCEL_BTN)
        return self

    def get_error_messages(self):
        return [el.text for el in self.find_elements(self.FIELD_ERRORS)]
```

### 2.3 弹窗类 `ChangePasswordDialog`
```python
class ChangePasswordDialog(BasePage):
    DIALOG = (By.CSS_SELECTOR, "#password-dialog")
    OLD_PASSWORD_INPUT = (By.CSS_SELECTOR, "#dialog-old-password-input input")
    NEW_PASSWORD_INPUT = (By.CSS_SELECTOR, "#dialog-new-password-input input")
    CONFIRM_PASSWORD_INPUT = (By.CSS_SELECTOR, "#dialog-confirm-password-input input")
    SAVE_BTN = (By.CSS_SELECTOR, "#dialog-save-btn")
    CANCEL_BTN = (By.CSS_SELECTOR, "#dialog-cancel-btn")

    def fill_old_password(self, pwd: str):
        self.clear_and_type(self.OLD_PASSWORD_INPUT, pwd)
        return self

    def fill_new_password(self, pwd: str):
        self.clear_and_type(self.NEW_PASSWORD_INPUT, pwd)
        return self

    def fill_confirm_password(self, pwd: str):
        self.clear_and_type(self.CONFIRM_PASSWORD_INPUT, pwd)
        return self

    # ... click_save, click_cancel 同 EditInfoDialog
```

## 3. 公共组件复用分析

- **高复用性**:
  - 表格(`el-table`): 全部复用 `BasePage` 的 `wait_for_element`, `get_text` 等方法。
  - 分页(`el-pagination`): 复用 `BasePage` 的 `click` 方法操作分页按钮/输入框。
  - 弹窗(`el-dialog`): 复用 `BasePage` 的 `wait_for_element` 和 `is_visible` 检查弹窗状态。
  - 按钮(`el-button`): 复用 `BasePage` 的 `click`。
- **需要扩展 ElementPlusHelper**:
  - **日期选择器**: `el-date-picker` 的 `daterange` 模式需要封装一个 `pick_daterange()` 方法，专门处理点选开始/结束日期的交互。
  - **可搜索下拉框**: `el-select` 的 filterable 模式可能需要 `send_keys` 搜索词再选择，需封装 `search_and_select_by_label()`。
- **低复用性 (需新建)**:
  - 表单校验错误信息获取: 如 `EditInfoDialog.get_error_messages()`，逻辑较独立，直接在对应 Page 类中实现。

## 4. 等待策略建议

- **页面加载**: 使用 `wait_for_url_contains` (`/personnel/my-archive`) + `wait_for_element_visible` (`PAGE_TITLE`)。
- **Tab 切换**: 每次切换后，等待内容区域的 `el-tab-pane` 完全渲染 (观察其 `active` 类或 `v-show` 状态)。可使用 `wait_for_element_visible` (目标Tab内容的第一个元素)。
- **查询/重置**: 点击“查询”/“重置”后，应等待 `el-table` 的加载状态（如骨架屏或loading动画）消失。建议自定义 `wait_for_table_loaded()` 方法，监听表格的 `load` 类或 `aria-busy` 属性。
- **弹窗打开/关闭**: 使用 `wait_for_element_visible` (DIALOG) 和 `wait_for_element_invisible` (DIALOG)。
- **表单校验触发**: 在 `fill_*` 或 `click_save` 操作后，使用 `wait_for_element_visible` (FIELD_ERRORS) 来获取校验错误提示，并增加一个较短的超时时间 (如3秒)，保证测试效率。

## 5. ROI 分析

- **预估开发时间**:
  - 3 个 Page 类的编写: 4 小时。
  - `ElementPlusHelper` 扩展 (`pick_daterange`, `search_and_select_by_label`): 2 小时。
  - 测试脚本编写 (针对 P0/P1 用例): 6 小时。
  - **总开发时间**: **12 小时**。
- **预估维护成本**:
  - UI 文本变更 (页面标题、错误提示等): 每月约 1 小时。
  - 元素定位器变更 (如按钮ID修改): 每季度约 2 小时。
  - **月均维护成本**: **1.5 小时/月**。
- **手工执行时间**:
  - 完整回归一次所有 P0/P1 用例: **15 分钟/次**。
  - 假设每日回归 1 次 (CI/CD 触发): **15 分钟/天**。
- **ROI 计算 (按 12 个月)**:
  - 自动化节省时间 = (15 分钟/次 * 22 天/月 * 12 月) - (开发时间 + 维护时间)
  - = (180 分钟/月 * 12 月) - (12 小时 + 1.5 小时/月 * 12 月)
  - = (3 小时/月 * 12 月) - (12 小时 + 18 小时)
  - = 36 小时 - 30 小时 = **净节省 6 小时 (12个月)**。
  - **结论**: 该页面自动化 **ROI 为正，值得投资**。考虑到 CI/CD 中每日回归可更早发现回归问题，实际价值会更高。

## 6. 风险标注

- **⚠️ 风险**: `EditInfoDialog.FIELD_ERRORS` 使用 `.el-form-item__error` 作为泛化定位器。如果页面中存在其他表单元素的错误提示，可能会获取到错误的结果。建议在无法获取唯一ID时，优先使用相对XPath，结合父级表单字段进行定位，以提高稳定性。
- **✅ 稳定**: 主要操作按钮和输入框使用了 `id` 属性 (`#search-btn`, `#dialog-name-input input`)，定位器非常稳定。
- **⚠️ 待观察**: `select_change_type` 和 `pick_date_range` 方法依赖于 `ElementPlusHelper` 的扩展实现。如果 El-Select 或 El-DatePicker 的 DOM 结构在 Element Plus 版本升级后发生变化，需要同步更新 `ElementPlusHelper`。
```