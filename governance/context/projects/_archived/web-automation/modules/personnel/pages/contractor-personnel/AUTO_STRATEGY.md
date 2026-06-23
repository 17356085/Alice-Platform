好的，收到您的指令。现在我将作为自动化策略设计专家，基于您提供的测试用例、技术分析、Page Object代码、测试脚本及页面上下文，制定一份详细的自动化策略文档。

---

## AUTO_STRATEGY — contractor-personnel

**模块**: personnel
**页面**: contractor-personnel
**生成日期**: 2026-06-18
**依据来源**：
- PAGE_CONTEXT.md
- TEST_CASES.md (从 `test_contractor_personnel.py` 推断)
- TECH_ANALYSIS.md
- ContractorPersonnelPage.py (现有代码)
- test_contractor_personnel.py (现有脚本)

---

### 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由与风险评估 |
| :--- | :--- | :--- | :--- | :--- |
| TC-001 (CP-001) | 页面打开时正常显示承包商人员列表 | **P0** | ✅ **必须** | 核心冒烟用例。现有 `is_page_loaded`、`get_total_count_text` 方法可用。<br>⚠️ **风险**：`SEARCH_NAME_INPUT` 定位器过于宽泛（多条件 or），存在误定位风险。 |
| TC-002 (CP-002) | 分页功能正常 | **P1** | ✅ **建议** | 验证分页基础交互。已有 `click_next_page`、`click_prev_page` 方法。<br>⚠️ **风险**：需有足够测试数据（>1页）才能执行；依赖于上游测试数据创建。 |
| TC-003 (CP-003) | 按人员姓名搜索 | **P0** | ✅ **必须** | 核心业务功能。现有 `input_search_name`、`click_search` 方法可用。 |
| TC-004 (CP-004) | 按所属单位搜索 | **P1** | ✅ **建议** | 核心业务功能，但依赖前置数据（承包商单位）。<br>**风险评估**：选择器 `SEARCH_WORK_TYPE_SELECT` 依赖文本“工种”，与页面描述“所属单位”不一致，**定位器风险高**。 |
| TC-005 (CP-005) | 按入场状态搜索 | **P1** | ✅ **建议** | 核心业务功能。<br>⚠️ **风险**：`SEARCH_STATUS_SELECT` 选择器文本包含“入场状态”，相对稳定。 |
| TC-006 (CP-006) | 列表显示正确、搜索列表更新 | **P0** | ✅ **必须** | 可并入搜索用例验证。 |
| TC-007 (CP-007) | 新增-编辑-查看-删除（闭环） | **P0** | ✅ **见下方** | **P0级流程**，但涉及复杂弹窗交互和依赖操作，建议**半自动化**或**脚本拆分**：<br>1. **(建议自动化)**`新增 -> 表格验证` 由 `test_AddCreate` 执行。<br>2. **(建议自动化)**`编辑 -> 表格验证`由`test_Edit` 执行，`删除` 由 `test_Delete` 执行。<br>3. **(不建议自动化)** 查看编辑后的详情、验证编辑的一致性（人工核实更可靠）。<br>⚠️ **风险**：新增/编辑弹窗内的 `el-select` 组件定位需特别关注。 |
| TC-008 | 出口台账中相应记录更新 | **P2** | ❌ **不建议** | 跨页面/跨模块验证，涉及数据源变更，自动化成本极高，但价值有限。 |
| TC-009 | 导出功能（如果有） | **P2-P3** | ❌ **不建议** | 导出操作后通常需人工检查文件内容，自动化难以有效验证。 |
| TC-010 (CP-009) | 停用承包商人员 | **P1** | ✅ **建议** | 行内操作，流程清晰。依赖于 `el-message-box` 确认弹窗。<br>**风险评估**：需先有 `CREATED_PERSONNEL_NAME`。 |
| TC-011 (CP-010) | 删除承包商人员 | **P0** | ✅ **必须** | 数据清理的必经流程，必须在闭环测试中涵盖。 |

---

### 2. PageObject 拆分方案

当前 `ContractorPersonnelPage.py` 结构基本合理，但存在改进空间。

**现状分析**: 当前 Page 类包含了 **页面操作 + 表格操作 + 弹窗操作**，属于中型 Page，尚未臃肿。但弹窗内的复杂交互（下拉选择、必填校验）正越来越多。

**建议的方案**：

| Page 类 | 职责 | 原因/依据 |
|:---|:---|:---|
| `ContractorPersonnelPage` | 主页面操作：<br>• 导航、页面加载验证<br>• 搜索区（输入、点击搜索/重置）<br>• 工具栏按钮（新增）<br>• 表格查询（获取行数、单元格数据）<br>• 分页操作<br>• 行内操作按钮定位（编辑、删除） | 保持核心职责清晰，当前代码可接受。 |
| `ContractorPersonnelDialog` | **新增/编辑弹窗**内的所有操作：<br>• 输入姓名、身份证、手机号等<br>• 选择所属承包商下拉 (`el-select`)<br>• 点击“确定”/“取消”按钮<br>• 验证弹窗标题、字段错误提示 | **符合“为复杂弹窗独立”规则**。弹窗包含独立表单、多步操作，单独封装可复用。 |
| `ConfirmDialog` (通用) | 通用确认弹窗 (`el-message-box`)：<br>• 点击“确定”/“取消”/“关闭”<br>• 获取弹窗文本 | 建议改为 **公共组件**，供所有需要处理确认弹窗的页面复用。若当前 BasePage 还未封装，可在 `common/` 下创建。 |

**代码示例 (`ContractorPersonnelDialog`)**:
```python
# page/personnel_page/ContractorPersonnelDialog.py
from base.base_page import BasePage
from selenium.webdriver.common.by import By

class ContractorPersonnelDialog(BasePage):
    """承包商人员新增/编辑弹窗"""
    DIALOG_TITLE = (By.XPATH, '//div[@role="dialog"]//span[contains(@class,"el-dialog__title")]')
    # 弹窗内字段
    NAME_INPUT = (By.XPATH, '//div[@role="dialog"]//label[text()="姓名"]/following-sibling::div//input')
    ID_CARD_INPUT = (By.XPATH, '//div[@role="dialog"]//label[text()="身份证"]/following-sibling::div//input')
    # ... 其他字段
    SUBMIT_BUTTON = (By.XPATH, '//div[@role="dialog"]//button[contains(@class,"el-button--primary")]')
    
    def set_name(self, name):
        ...
```

---

### 3. 公共组件复用分析

| 操作 | 是否可复用 BasePage/已有方法 | 是否需要扩展 |
|:---|:---|:---|
| 侧边栏导航 (`navigate_to`) | ✅ 已实现，良好。 | - |
| 输入框操作 (`find_visible().send_keys()`) | ✅ 基础方法。 | 建议新增 `clear_and_type(element, value)` 方法到 BasePage，防止文本覆盖问题。 |
| `el-select` 选择操作 | ❌ **尚无通用方法**。 | **需要扩展 `ElementPlusHelper`**，增加 `select_option(driver, dropdown_locator, option_text)` 方法。 |
| `el-message-box` 确认操作 | ❌ 当前代码中未封装。 | **建议扩展** `ElementPlusHelper` 或创建单独的 `CommonDialog` 组件。 |
| `wait_loading_gone` | ✅ 已实现。 | - |
| 表格行数据获取 (`get_first_row_data`) | ✅ 已实现。 | - |

---

### 4. 等待策略建议

| 场景 | 异步行为 | 建议的等待策略 |
|:---|:---|:---|
| **页面首次加载** | 侧边栏菜单展开动画 + 表格数据异步加载。 | 1. `wait_page_ready()` (等待DOM稳定)<br>2. `_wait_loading_gone()` (等待loading消失)<br>3. `wait_vue_stable()` (Vue 渲染稳定) |
| **点击“搜索”后** | 表格重新渲染，后端请求。 | `_wait_loading_gone()` 是最佳实践。若加载太快无法捕获，可依赖 `wait_vue_stable()` |
| **打开“新增”弹窗后** | `el-dialog` 动画（渐变/缩放）。 | 增加等待：`wait.until(EC.visibility_of_element_located(DIALOG))` |
| **点击弹窗“确定”后** | 提交请求 -> 关闭弹窗 -> 显示 `el-message` -> 表格刷新。 | 1. `wait.until(EC.invisibility_of_element_located(DIALOG))`<br>2. `_wait_loading_gone()` |
| **点击“删除”/“停用”行内按钮** | 弹出 `el-message-box`。 | `wait.until(EC.visibility_of_element_located(CONFIRM_DIALOG))` |
| **选择下拉框选项** | 下拉菜单 (`el-select-dropdown`) 出现动画。 | 不要使用固定 sleep。使用 `wait.until(EC.visibility_of_element_located(dropdown_option_locator))` |

**建议**: 上述等待逻辑应封装到 `ContractorPersonnelPage` 或 `ContractorPersonnelDialog` 对应的 `*_and_wait` 方法中。

---

### 5. ROI 分析

**假设条件**:
- 手工执行一轮所有 P0+P1 测试用例（单次）：**15 分钟**。
- 自动化脚本平均执行频率：**1 次/日** (日常回归或CI触发)。
- 月度维护成本（定位器变更、新功能适配）：**4 小时/月**。
- 自动化开发（含调试、封装）：**12 小时**。

**计算**:

| 项目 | 时长 | 备注 |
|:---|:---|:---|
| **自动化开发成本** | 12 小时 | 一次性投入 |
| **月度维护成本** | 4 小时 | 持续投入 |
| **单次手工执行** | 15 分钟 | - |
| **执行频率** | 22 次/月 | 假设工作日执行 |

**月度收益**:
- 手工执行总时间: 15分钟/次 x 22次/月 = 330分钟/月 = **5.5 小时/月**
- 自动化执行时间（约 2分钟/次）：22次 x 2分钟 = 44分钟/月 ≈ 0.73 小时/月
- 自动化净节省时间: 5.5 - 0.73 = **4.77 小时/月**

**投入回报**:
- **纯手动成本**: 5.5 小时/月
- **自动化总成本** (开发 + 维护): 12小时 + 4小时*月数
- **3个月后 ROI**: 自动化净节省(4.77 x 3) - 总成本(12 + 4x3) = 14.31 - 24 = **-9.69 小时 (负)**
- **6个月后 ROI**: 4.77 x 6 - (12 + 4x6) = 28.62 - 36 = **-7.38 小时 (负)**
- **12个月后 ROI**: 4.77 x 12 - (12 + 4x12) = 57.24 - 60 = **-2.76 小时 (仍为负)**

**结论**: 由于维护成本较高（4小/月 > 净节省4.77小/月），该项目 **长期ROI为负**。这是一个典型的维护密集型项目。

**优化建议以提高ROI**:
1. **降低维护成本**: 减少硬编码XPath，使用更稳定的CSS选择器；定位器抽象化，减少日后改一个动一片的风险。
2. **增加自动化频率或价值**: 如果执行频率提升为 **每日3次** (如 CI/DIT 多次触发)，ROI 将明显改善。
3. **缩小范围**: 只自动化 **P0** 用例（当前3个），将开发成本降低至6小时，维护成本降至2小时/月。重新计算12个月ROI：
    - 手工执行P0: 5分钟/次 x 22次 = 110分钟/月 ≈ 1.8 小时
    - 自动净节省: 1.8 - 0.73(假设) = 1.07 小时/月
    - 12个月ROI: 1.07 x 12 - (6 + 2x12) = 12.84 - 30 = **-17.16 小时** 依然为负。
    - *根本原因*: 页面极不稳定，维护成本过高。

**最终建议**:
- **从成本角度，不建议大规模自动化**。应将重点放在 **提升页面稳定性**（与开发团队约定减少DOM无意义修改），或 **采用更稳定的技术（如接口测试替代页面操作验证核心流程）** 上。
- 当前可以考虑 **半自动化**: 将P0搜索和新增用自动化跑，P1行内操作和弹窗复杂交互仍保留人工执行，以降低维护压力。