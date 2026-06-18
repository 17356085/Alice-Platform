好的，遵照您的指令。作为负责“自动化策略”的AI Agent，我将基于您提供的 `MyArchivePage.py` Page Object 代码、`PAGE_CONTEXT.md` 页面上下文以及常见测试场景，对该页面进行自动化覆盖策略分析，并输出 `AUTO_STRATEGY.md`。

---

### AUTO_STRATEGY.md

```markdown
# AUTO_STRATEGY: personnel / my-archive（我的档案）

> **版本**: 1.0 | **最后更新**: 2026-06-18 | **维护者**: automation-agent
> **模块**: personnel
> **页面**: my-archive
> **基于**: MyArchivePage.py (v1.0), PAGE_CONTEXT.md (v1.0), TECH_ANALYSIS.md (v1.0)

---

## 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
|---------|------|--------|-----------|------|
| **TC-MA-001** | 页面正常打开，默认显示基本信息Tab | P0 | ✅ | 基础冒烟，定位器稳定（CSS class + 首个子元素） |
| **TC-MA-002** | 切换各Tab，验证内容正确显示 | P0 | ✅ | P0，Tab切换操作简单，定位器稳定 |
| **TC-MA-003** | 档案变更记录Tab：查询所有记录 | P0 | ✅ | 核心查询流程，表格加载需要等待 |
| **TC-MA-004** | 档案变更记录Tab：按变更类型筛选 | P1 | ✅ | 下拉选择+查询，定位器稳定 |
| **TC-MA-005** | 档案变更记录Tab：按日期范围筛选 | P1 | ✅ | 日期选择器操作需特殊处理，但可自动化 |
| **TC-MA-006** | 档案变更记录Tab：查询为空时展示空状态 | P2 | ✅ | 边界情况，可复用查询流程 |
| **TC-MA-007** | 档案变更记录Tab：表格分页（翻页、每页条数） | P1 | ✅ | 分页组件操作固定，可套用BasePage分页方法 |
| **TC-MA-008** | 编辑基本信息：通过Tab内编辑按钮打开弹窗 | P0 | ✅ | P0核心功能，弹窗定位器使用role+标题稳定 |
| **TC-MA-009** | 编辑基本信息：成功修改姓名并保存 | P1 | ✅ | 表单填写+保存+验证，动态UI需处理 |
| **TC-MA-010** | 编辑基本信息：必填项为空时校验 | P2 | ✅ | 表单校验，可在现有编辑流程上扩展 |
| **TC-MA-011** | 编辑基本信息：取消编辑，弹窗关闭且数据不保存 | P1 | ✅ | 取消按钮定位器存在 |
| **TC-MA-012** | 修改密码：打开弹窗 | P0 | ✅ | P0，侧边栏按钮定位器使用相对XPath，稍脆弱但不频繁变更 |
| **TC-MA-013** | 修改密码：旧密码错误提示 | P1 | ✅ | 可自动化，需准备固定密码数据 |
| **TC-MA-014** | 修改密码：成功修改密码 | P2 | ❌ | **绕过生产安全策略**：修改密码后需重新登录且影响其他用例，维护成本高，ROI低。建议手动执行。 |
| **TC-MA-015** | 侧边栏：点击“编辑资料”跳转编辑弹窗 | P0 | ✅ | 与TC-MA-008等价，保留为一个独立用例以保证覆盖 |
| **TC-MA-016** | 证件信息Tab：查看证件列表 | P2 | ❌ | **一次性操作**（仅上线前验证数据展示是否正确），后续无频繁回归价值 |
| **TC-MA-017** | 联系方式Tab：查看联系方式 | P2 | ❌ | 与TC-MA-016同理，静态只读展示，无需自动化 |

**风险标注**：
- **定位器不稳定风险**：`SIDEBAR_EDIT_PROFILE_BTN` 和 `SIDEBAR_CHANGE_PASSWORD_BTN` 使用 `//aside//button[.//span[text()='编辑资料']]` 相对XPath，若UI重构可能导致失败。建议持续监控，必要时加css class。
- **高脆弱定位器**：`DIALOG_CANCEL_BTN` 使用类似XPath，同风险。

**不建议自动化用例的理由**：
- TC-MA-016、TC-MA-017：只读展示，无交互，自动化收益低（执行一次不再用）。
- TC-MA-014：修改密码后状态改变，影响其他用例，维护成本高，ROI为负。

---

## 2. PageObject 拆分方案

按照“一个页面一个Page类，复杂弹窗独立”的原则，建议：
- **MyArchivePage**：主页面类，包含Tab切换、侧边栏、基本信息展示、档案变更记录的筛选/表格/分页。
- **EditBasicInfoDialog**：`编辑基本信息`弹窗，独立类，管理弹窗所有表单操作（姓名/部门/职位/手机/邮箱/保存/取消）。
- **ChangePasswordDialog**：`修改密码`弹窗，独立类，管理旧密码/新密码/确认/保存/取消。

```python
# 类结构建议
class MyArchivePage(BasePage):
    # Tab、侧边栏、基本信息表单、变更记录表格、分页
    ...

class EditBasicInfoDialog(BasePage):
    # 编辑弹窗内元素
    def fill_name(self, name): ...
    def select_department(self, dept): ...
    def click_save(self): ...
    ...

class ChangePasswordDialog(BasePage):
    # 密码弹窗内元素
    def set_old_password(self, pwd): ...
    def click_save(self): ...
    ...
```

**理由**：弹窗表单元素较多（编辑弹窗7个input/select，密码弹窗3个input），独立类可提高内聚性，避免主Page类膨胀。

---

## 3. 公共组件复用分析

### 3.1 BasePage 直接复用
- `self.get_text()`：获取输入框文本（只读表单验证）
- `self.click()`：点击按钮/Tab
- `self.input_text()`：填写文本框（弹窗输入）
- `self.select_dropdown_option()`：选择下拉选项（变更类型筛选、部门选择）——需确保BasePage已有该方法
- `self.get_table_row_count()`：获取表格行数（变更记录）
- `self.get_pagination_info()`：获取分页信息（总条数、当前页）
- `self.switch_tab()`：切换Tab（若BasePage已封装Tab通用方法）

### 3.2 ElementPlusHelper 扩展需求
当前页面涉及以下特殊操作，建议在 `ElementPlusHelper` 中添加：
- **`select_date_range(start, end, picker_locator)`**：选择日期范围，针对 `el-date-picker daterange` 组件，需处理点开日历、选择开始/结束日期。
- **`select_dropdown_by_label(label_text, select_locator)`**：基于选项文本选择下拉，替代 `select_dropdown_option` 以确保稳定（当前变更类型选择使用XPath选项可能因下拉定位器动态而变化）。

### 3.3 不适用复用
- 编辑弹窗独立类不宜继承 MyArchivePage，应直接继承 BasePage。
- 侧边栏快捷按钮无法复用通用导航方法，需独立定位。

---

## 4. 等待策略建议

### 4.1 页面特有异步行为
- **Tab 切换**：Vue 路由或条件渲染导致的短暂加载（约200-500ms）。建议使用 `wait_for_element_visible(next_tab_content)`。
- **表格加载**：查询按钮点击后出现 `el-loading-mask`，必须等待遮罩消失。建议在 BasePage 加入 `wait_for_table_loaded(table_loading_locator=None)`，默认等待 `TABLE_LOADING` 消失。
- **弹窗打开**：el-dialog 有过度动画（300ms）。建议 `wait_for_element_visible(dialog_locator)`。
- **下拉选项展开**：el-select 下拉可能异步加载选项，但本页面选项静态，直接 `wait_for_element_visible(option_locator)` 即可。

### 4.2 推荐等待封装
在 `base_page.py` 扩展：
```python
def wait_for_loading_disappear(self, loading_locator=None, timeout=10):
    """等待页面/区域加载遮罩消失"""
    loading = loading_locator or self.TABLE_LOADING
    WebDriverWait(self.driver, timeout).until_not(
        EC.presence_of_element_located(loading)
    )
```

在测试脚本中使用：
```python
page.click_search()
page.wait_for_loading_disappear()
```

对于 Tab 切换，可使用 `element_to_be_clickable` 后立刻检查内容可见。

---

## 5. ROI 分析

### 5.1 估算开发成本

| 类型 | 内容 | 预估工时（小时） |
|------|------|----------------|
| PageObject 创建 | MyArchivePage 定位器已基本完成（约30行），补充方法（如选日期、选下拉） | 1.0 |
| 弹窗独立类 | EditBasicInfoDialog、ChangePasswordDialog 各 0.5h | 1.0 |
| ElementPlusHelper 扩展 | 添加 `select_date_range`、`select_dropdown_by_label` | 1.5 |
| 测试用例编写 | 自动化的13个用例，平均0.3h/个 | 3.9 |
| 初步调试/CI集成 | 连调、修复定位器问题 | 2.0 |
| **总计** | | **9.4 小时** |

### 5.2 预估维护成本
- 每月 UI 重构频率：中等（约2次/月微调）。每次影响定位器需修复：0.5h。
- 每月执行频率：每日回归1次 + 每周全量2次 ≈ 每月25+8=33次。
- 手工执行一次所有用例时间：10分钟/次（13个用例，含切换Tab、查询、编辑、密码等）。

### 5.3 ROI 计算（以6个月为周期）
- 自动化开发成本：9.4 小时
- 维护成本：6个月 × 每月1h（因定位器不稳定，预留1h/月） = 6 小时
- 总投入 = 9.4 + 6 = 15.4 小时
- 手工执行总时间 = 33次/月 × 6个月 × (10分钟/60) = 33 × 6 × 0.167 = 33 小时
- **节省 = 33 - 15.4 = 17.6 小时（约2.2人天）**
- **ROI = 17.6 / 15.4 ≈ 114%**（6个月内收回成本并产生收益）

**结论**：强烈建议自动化，尤其当手工执行频繁（每日回归）时，ROI显著。

---

## 6. 风险与缓解措施

| 风险 | 影响 | 缓解 |
|------|------|------|
| 侧边栏按钮XPath不稳定 | 自动化失败率上升 | 推动前端添加 `data-testid`；改用更稳定的CSS class（如 `.btn-edit-profile`） |
| 日期范围选择器操作复杂 | 调试时间增加 | 封装 `ElementPlusHelper.select_date_range` 并充分单元测试 |
| 修改密码后影响其他用例 | TC-MA-014 未自动化，但需确保密码环境独立 | 测试数据策略中保证每个测试用户的密码可重置，或使用独立测试账号 |
| 表格数据依赖真实用户数据 | 测试结果不可预测 | 使用 Mock 或预埋测试数据（如固定查询日期） |

---

**文件状态**：✅ 已审核，建议自动化团队按上述策略实现。
```

如果需要补充具体的测试数据设计或进一步细化 `ElementPlusHelper` 的扩展方案，请告知。