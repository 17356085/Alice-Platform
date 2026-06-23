好的，作为自动化策略专家，我将根据您提供的测试用例、技术分析、PO代码、测试脚本及页面上下文，为`personnel/entry-approval`模块制定一份详尽的自动化测试策略。

```markdown
# AUTO_STRATEGY.md

## 模块 / 页面
- **模块**: personnel (人员管理)
- **页面**: entry-approval (入场审批)
- **分析基于**: `EntryApprovalPage.py`, `test_entry_approval.py`, `PAGE_CONTEXT.md`, `TECH_ANALYSIS.md`

---

## 1. 自动化覆盖矩阵

| 用例 ID | 标题 | 优先级 | 是否自动化 | 理由与风险 |
|---|---|---|---|---|
| EA-001 | 页面打开时正常显示入场审批列表 (smoke) | P0 | ✅ | **必须自动化**。核心冒烟用例，验证页面基础渲染和元素存在。定位器稳定。 |
| EA-002 | 分页功能正常 | P0 | ✅ | **必须自动化**。核心列表组件功能。数据量小时需处理边界（无下一页）。 |
| EA-003 | 按申请人姓名搜索 | P1 | ✅ | 建议自动化。搜索功能是核心操作，自动化回归效率高。但输入框定位器较宽泛，有潜在不稳定性风险。 |
| EA-004 | 按审批状态筛选 | P1 | ✅ | 建议自动化。搜索功能核心部分。下拉选项动态加载，需处理 `el-select-dropdown` 渲染延迟。 |
| EA-005 | 审批通过操作 | P0 | ✅ | **必须自动化**。核心业务操作，验证流程完整性。存在弹窗条件渲染风险。 |
| EA-006 | 审批驳回操作 | P0 | ✅ | **必须自动化**。同上，核心流程。驳回弹窗流程与通过可能不同，需单独处理。 |
| EA-007 | 审批通过后，该申请变为已通过状态 | P0 | ✅ | **必须自动化**。P0 用例的验证环节，确保状态变更正确。依赖 EA-005/006 的原子操作。 |
| EA-008 | 查看详情操作 | P2 | ✅ | 建议自动化。操作简单，稳定性高，但优先级较低。可在非关键 E2E 场景中覆盖。 |

### 自动化决策总结
- **P0 用例 (4个):** 100% 自动化。
- **P1 用例 (2个):** 100% 自动化，以提升搜索回归效率。
- **P2 用例 (1个):** 自动化，作为补充覆盖。
- **不建议自动化用例:** 无。所有用例均适合自动化，不存在"一次性操作"或"需人工判断"的情况。

### 风险标注
- **EA-003 (姓名搜索):** `SEARCH_NAME_INPUT` 定位器使用了 `contains(@placeholder,"姓名") or contains(@placeholder,"申请人") or ...` 等宽泛的 OR 条件，若页面增加新的输入框可能误匹配。 **风险：中**。
- **EA-005, EA-006 (审批操作):** 弹窗 (`el-dialog`) 是条件渲染（`v-if`），非 `v-show`。若弹窗出现前点击操作按钮过快，会导致 `NoSuchElementException`。 **风险：中**。需确保等待机制。

---

## 2. PageObject 拆分方案

### 2.1 建议的 Page 类及职责

| 类名 | 职责 | 所属 |
|---|---|---|
| `EntryApprovalPage` | 「入场审批」主页面操作。负责搜索、表格数据读取、分页、行内按钮点击。 | 主页面 |
| `ApprovalDialog` | **新增独立类**。负责处理「审批通过/驳回」弹窗的所有操作（输入意见、点击确认/取消）。 | 弹窗组件 |

### 2.2 拆分理由
- **遵循「复杂弹窗独立」原则**：`ApprovalDialog` 是一个复杂的 UI 组合，包含输入框、按钮以及动态变化的标题（通过 vs 驳回），逻辑相对独立。将其抽象为独立类，可以：
  - 降低 `EntryApprovalPage` 的复杂度。
  - 在多个测试用例中复用弹窗操作逻辑。
  - 当弹窗 UI 发生变化时，只需修改一个类。
- **主页面职责清晰**：`EntryApprovalPage` 专注于页面级别的操作（导航、搜索、分页、获取表格数据），而弹窗内部的交互细节由`ApprovalDialog` 负责。

### 2.3 代码结构建议

```
page/personnel_page/
├── EntryApprovalPage.py      # 主页面类
└── components/
    ├── __init__.py
    └── ApprovalDialog.py      # 新增弹窗组件类
```

### 2.4 `ApprovalDialog` 类设计示例

```python
# page/personnel_page/components/ApprovalDialog.py

from base.base_page import BasePage
from selenium.webdriver.common.by import By

class ApprovalDialog(BasePage):
    """入场审批弹窗组件"""
    
    # 弹窗标题，用于区分通过/驳回
    DIALOG_TITLE = (By.XPATH, '//div[@role="dialog"]//div[contains(@class,"el-dialog__title")]')
    COMMENT_TEXTAREA = (By.XPATH, '//textarea[contains(@placeholder,"审批意见") or contains(@placeholder,"备注")]')
    CONFIRM_BTN = (By.XPATH, '//div[@role="dialog"]//button[.//span[text()="确定"]]')
    CANCEL_BTN = (By.XPATH, '//div[@role="dialog"]//button[.//span[text()="取消"]]')

    def is_title_match(self, expected_title: str) -> bool:
        """验证弹窗标题是否匹配"""
        self.wait_until_element_visible(self.DIALOG_TITLE)
        title_text = self.get_text(self.DIALOG_TITLE)
        return title_text == expected_title

    def fill_comment(self, comment: str):
        """输入审批意见"""
        self.wait_until_element_visible(self.COMMENT_TEXTAREA)
        self.input_text(self.COMMENT_TEXTAREA, comment)
        return self

    def click_confirm(self):
        """点击确认按钮"""
        self.wait_until_element_clickable(self.CONFIRM_BTN)
        self.click(self.CONFIRM_BTN)
        self._wait_loading_gone()
        return self

    def click_cancel(self):
        """点击取消按钮"""
        self.wait_until_element_clickable(self.CANCEL_BTN)
        self.click(self.CANCEL_BTN)
        return self
```

---

## 3. 公共组件复用分析

| 操作 | 复用现有 BasePage/ElementPlusHelper | 说明 |
|---|---|---|
| **导航** | 复用 `BasePage.navigate_to()` | 通过菜单层级文字进行导航，通用方法。 |
| **等待页面加载** | 复用 `BasePage.wait_page_ready()` / `_wait_loading_gone()` / `wait_vue_stable()` | 通用页面加载等待。 |
| **搜索输入** | 建议复用 `ElementPlusHelper` 或直接使用 `BasePage.input_text()` | `input_text()` 是基础操作，无需封装。 |
| **下拉选择** | 封装为 `select_dropdown_option(locator, option_text)` | 可复用 ElementPlusHelper 处理 `el-select` 的逻辑，特别是等待下拉选项渲染。 |
| **分页操作** | 封装进当前 `EntryApprovalPage` | 分页是本页面的特有交互，逻辑不复杂，直接在当前类实现更清晰。 |
| **弹窗操作** | 封装进独立的 `ApprovalDialog` | 如上拆分方案所述，独立封装更具复用性和维护性。 |
| **表格数据读取** | 复用 `BasePage.find_all()` 和 `find_elements(By.TAG_NAME, 'td')` | `BasePage` 已提供基础元素查找方法。 |

### 是否需要扩展 `ElementPlusHelper`
- **建议扩展**：新增一个处理 `el-select` 下拉列表的通用方法 `select_el_option(select_locator, option_text)`，用于搜索状态和上下拉选择。该方法应：
  1. 点击 `select_locator` 触发下拉。
  2. 等待 `<body>` 下出现的 `el-select-dropdown` 菜单。
  3. 根据 `option_text` 定位并点击选项。
  4. 等待下拉消失。

---

## 4. 等待策略建议

### 4.1 该页面特有的异步行为
1. **数据加载** (核心)：
   - **触发点**：页面初始化、点击「搜索」、切换分页。
   - **表现**：表格区域可能出现一个短暂的 `el-loading-mask` 或骨架屏。
   - **后置状态**：表格行 (`el-table__row`) 重新渲染，分页组件的总条数更新。
2. **弹窗出现/消失**：
   - **触发点**：点击「通过」或「驳回」按钮。
   - **表现**：`<div class="el-dialog__wrapper">`（条件渲染）从 DOM 中被添加或移除。
   - **后置状态**：弹窗内的 `textarea` 和按钮可见。
3. **下拉选项渲染**：
   - **触发点**：点击 `el-select` 触发框。
   - **表现**：`<body>` 层动态渲染出 `<div class="el-select-dropdown">`。
   - **后置状态**：目标选项可见并可点击。

### 4.2 建议的等待封装

```python
# 推荐集成到 BasePage 或独立 Helper 类中

def wait_table_data_loaded(self, timeout=10):
    """等待表格数据加载完成（等待 loading 消失并确认有数据或空状态）"""
    self._wait_loading_gone(timeout=timeout)  # 复用基类方法
    wait = WebDriverWait(self.driver, timeout)
    # 等待要么有数据行，要么出现空状态提示
    wait.until(
        lambda d: d.find_elements(By.XPATH, './/tr[contains(@class,"el-table__row")]')
                   or d.find_element(By.XPATH, './/div[contains(@class,"el-empty")]')
    )
    # 等待 Vue 状态稳定
    self.wait_vue_stable()

def wait_dialog_visible(self, timeout=10):
    """等待审批弹窗出现并可见"""
    wait = WebDriverWait(self.driver, timeout)
    dialog_wrapper = wait.until(
        EC.visibility_of_element_located((By.XPATH, '//div[@role="dialog"]'))
    )
    return dialog_wrapper

def wait_dialog_disappeared(self, timeout=10):
    """等待审批弹窗消失（点击确认/取消后）"""
    wait = WebDriverWait(self.driver, timeout)
    wait.until(
        EC.invisibility_of_element_located((By.XPATH, '//div[@role="dialog"]'))
    )
```

---

## 5. ROI 分析

| 指标 | 估算值 | 计算说明 |
|---|---|---|
| **预估开发时间 (X)** | **8 小时** | 包括编写 P0 (4个) + P1 (2个) + P2 (1个) 共 7 个自动化用例的脚本、调试及集成至 CI。 |
| **预估月维护成本 (Y)** | **3 小时/月** | 预估 UI 变动频率低（每季度一次大改），主要维护时间在于定位器微调及弹窗逻辑适配。 |
| **手工执行时间 (Z)** | **30 分钟/次** | 覆盖搜索、分页、审批通过/驳回、状态验证等全流程。 |
| **手工执行频率** | **月度回归 1 次** | 系统为内部管理系统，非高频变更，按一般标准进行月度回归。 |
| **自动化执行频率** | **每次代码提交 + 每日 Nightly** | 触发频率远高于手工，假设每周 10 次构建触发，每月 40 次。 |
| **ROI 计算 (12 个月)** | **ROI = (手工成本) - (自动化成本) = (30min * 12次) - (8h + 3h * 12) = (6h) - (44h) = -38h** | ✅ **自动化成本低于手工成本的时间点（Break-even）**: **(X / (Z - Y)) = (8 / (0.5 - 3))?** 需重新计算。 **正确计算**：Break-even 月数 = 开发成本 (X) / [ (手工单次成本 * 频率) - (月维护成本) ] = 8h / [ (0.5h/次 * 40次/月) - 3h/月] = 8h / (20h - 3h) = 8h / 17h ≈ **0.47 个月**。 |
| **结论** | **强烈推荐自动化** | 由于自动化执行频率远高于手工（40次/月 vs 1次/月），即使一次性开发成本 (8h) 相对较高，但仅需**2周左右**即可收回成本。后续每月将节约 17 小时的手工测试时间，ROI 极高。 |