好的，作为测试架构师，我将基于您提供的 `PAGE_CONTEXT.md`，并结合 `warehouse/hazard-out-order` 页面的标准测试设计和技术分析模式，为您生成一份完整的自动化测试策略文档 (`AUTO_STRATEGY.md`)。

---

### 产出物：AUTO_STRATEGY.md

**文件路径:** `docs/modules/warehouse/hazard-out-order/AUTO_STRATEGY.md`

```markdown
# 自动化测试策略: 危险品出库单 (Hazard Outbound Order)

## 1. 自动化覆盖矩阵

以下分析基于 `PAGE_CONTEXT.md` 和通用的测试用例设计原则。假设测试用例已按 P0-P2 优先级分级。

| 用例编号 (示例) | 标题 | 优先级 | 是否自动化 | 理由 |
| :--- | :--- | :--- | :--- | :--- |
| `TC-HO-001` | 页面加载与元素完整（搜索区、表格、分页） | P0 | ✅ | **基础冒烟**，所有自动化回归的起点。 |
| `TC-HO-010` | 按“出库单号”模糊搜索 | P0 | ✅ | **核心功能**，高频操作，业务价值高。 |
| `TC-HO-012` | 按“单据状态”筛选 | P0 | ✅ | **核心功能**，高频操作，且是后续状态流转测试的入口。 |
| `TC-HO-015` | 按“危险品类型”筛选 | P0 | ✅ | **核心功能**，危险品业务的核心筛选维度。 |
| `TC-HO-020` | 搜索条件组合搜索 | P1 | ✅ | **稳定性回归**，验证搜索逻辑的健壮性。 |
| `TC-HO-025` | 搜索后“重置” | P1 | ✅ | **功能回归**，确保重置行为符合预期。 |
| `TC-HO-030` | 表格分页功能（翻页、跳转、每页条数） | P0 | ✅ | **基础UI功能**，数据量大时的核心操作。 |
| `TC-HO-035` | 表格列排序（如按创建时间） | P1 | ✅ | **功能回归**，验证数据排序的正确性。 |
| `TC-HO-040` | 新增危险品出库单（填写所有必填项） | P0 | ✅ | **核心业务流程**，创建数据的入口，频率高。 |
| `TC-HO-045` | 新增危险品出库单（必填项为空提示） | P1 | ✅ | **表单校验**稳定，可自动化验证UI错误提示。 |
| `TC-HO-050` | 编辑“待审批”状态的出库单 | P1 | ✅ | **条件性操作**，自动化可依赖“新增”用例准备数据。 |
| `TC-HO-055` | 删除“待审批”状态的出库单 | P1 | ✅ | **条件性操作**，自动化可集成在“新增后清理”流程中。 |
| `TC-HO-060` | 审批“待审批”状态的出库单 | P0 | ✅ | **核心业务流程**，状态流转的关键节点。 |
| `TC-HO-065` | 驳回“待审批”状态的出库单 | P1 | ✅ | **状态流转的分支流程**，验证系统逻辑。 |
| `TC-HO-070` | 出库确认“已审批”状态的出库单 | P0 | ✅ | **核心业务流程**，仓库实际操作的核心。 |
| `TC-HO-075` | 查看单条单据的详情 | P1 | ✅ | **功能回归**，自动化验证详情页数据与列表一致。 |
| `TC-HO-080` | 打印“已审批”状态的出库单 | P2 | ❌ | **工具性操作**，打印结果需要人工校验，自动化ROI低。 |
| `TC-HO-085` | 多次快速点击“搜索”按钮 | P2 | ❌ | **性能/稳定性**，前端防抖逻辑更适合专项测试。 |
| `TC-HO-090` | 新增时，选择“仓库”后下拉框正常回显 | P0 | ✅ | **基础UI交互**，验证联动功能的稳定性。 |
| `TC-HO-095` | 配置代码表（一次性上线前操作） | P2 | ❌ | **一次性活动**，不适用于持续回归的自动化场景。 |

**风险标注:**
- 涉及 **`el-select`下拉选项** 的用例 (如 TC-HO-012, TC-HO-090)，由于选项值依赖后端数据，若数据不稳定或频繁变更，定位器（如 `XPath` 文本）将存在稳定性风险。
- 涉及 **状态流转** 的用例 (如 TC-HO-060, TC-HO-070)，必须依赖前置用例（如新增并提交审批），导致用例之间产生**数据依赖**，是自动化设计中的高复杂度风险点。
- 操作按钮（如编辑、审批）的**可见性**与行数据状态强相关，若状态更新存在延迟，Selenium 定位可能失败，属于**时序风险**。

## 2. PageObject 拆分方案

为了遵循“一个页面一个 Page 类，复杂弹窗独立”的原则，拆分方案如下：

```
pages/
├── hazard_out_order_page.py        # 主页面对象
│   ├── 属性: A区搜索元素, B区表格容器, C区分页元素
│   ├── 方法: search_by_no(), search_by_status(), click_add(), get_table_rows(), click_pagination() 等
│   └── 方法: get_danger_tag_text(), get_status_tag_text() # 解析表格数据
│
├── hazard_out_order_dialog.py      # 新增/编辑弹窗 Page Object (el-drawer)
│   ├── 属性: 表单内的 warehouse_select, sender_input, remarks_textarea
│   ├── 方法: fill_form(warehouse, sender, ...), click_submit(), click_cancel()
│   └── 方法: get_form_error_message()
│
├── approve_dialog.py               # 审批/驳回弹窗 Page Object (el-dialog)
│   ├── 属性: approve_btn, reject_btn, remark_textarea
│   └── 方法: approve(), reject(remark)
│
└── (可选) confirm_out_dialog.py    # 出库确认弹窗 Page Object
    └── 方法: confirm_outbound()
```

**设计说明:**
- `HazardOutOrderPage` 负责列表页的筛选、数据获取、导航。
- `HazardOutOrderDialog` **独立**于主页面，因为它是一个独立的UI容器（`el-drawer`），内部包含完整的表单逻辑。
- `ApproveDialog` / `ConfirmOutDialog` 虽然简单，但为了代码清晰和隔离状态流转逻辑，建议独立为类。如果它们高度相似，可考虑合并。

## 3. 公共组件复用分析

- **BasePage 复用:**
    - `BasePage.wait_for_element_visible()`: 用于等待弹窗 (`el-drawer` / `el-dialog`) 完全打开。
    - `BasePage.click_button()`: 复用，用于点击搜索、重置等简单按钮。
    - `BasePage.enter_text()`: 复用，用于填充 `el-input`。
    - `BasePage.select_dropdown()`: **需要检查 BasePage 是否有**。如果没有，则设计一个通用选择器来处理 `el-select`。
    - `BasePage.handle_date_range_picker()`: 复用，用于填充 `el-date-picker`。

- **ElementPlusHelper 扩展建议:**
    - **`select_option_by_label(self, dropdown_element, label_text)`**: 封装针对 `el-select` 的常用操作：1) 点击触发下拉；2) 等待下拉条目 `el-select-dropdown` 出现；3) 查找并点击包含 `label_text` 的 `li` 元素。这是高频操作，封装后能提高稳定性。
    - **`get_table_cell_text(self, row_element, column_index)`**: 封装从表格行 (`el-table__row`) 中获取特定列文本的操作，提高代码可读性。

## 4. 等待策略建议

该页面存在明显的**异步行为**，需要精细化的等待策略，避免使用隐式等待或固定 `time.sleep()` 调用。

| 场景 | 异步行为 | 推荐等待策略 | 示例代码 (Selenium) |
| :--- | :--- | :--- | :--- |
| 点击“搜索”或“重置”后 | 表格数据重新加载，请求后端数据。 | 等待表格**数据行**（`.el-table__body-wrapper .el-table__row`）或特定表格内容的**状态变化** (如等待旧的加载状态消失)。 | `WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".el-table__body-wrapper .el-table__row")))` |
| 点击下拉框后 | `el-select-dropdown` 动态渲染到 `<body>` 底部。 | 等待下拉菜单的 **`display` 属性不为 `none`**。 | `WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "ul.el-select-dropdown__list"))))` |
| 点击“新增”或“编辑”后 | `el-drawer` 从右侧滑入，内部表单异步加载。 | 等待抽屉容器 (`el-drawer`) 的 **`visibility`** 以及在表单内出现第一个输入框。 | `WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".el-drawer")))` <br> `wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#form-warehouse")))` |
| 操作成功后的 Toast 提示 | Element Plus 的 `ElMessage` 短暂的弹出和消失。 | 不依赖 Toast 提示，而是等待**页面状态**的变化（如表单关闭、表格更新）。 | 等待表单关闭: `WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-drawer")))` |

**建议:** 在 `BasePage` 或 `ElementPlusHelper` 中封装一个通用方法 `wait_for_element_stable(element)`, 结合 `EC.visibility_of` 和 `EC.presence_of`，减少每次业务操作时的等待代码冗余。

## 5. ROI 分析

| 指标 | 数值 | 说明 |
| :--- | :--- | :--- |
| **功能点** | 5个主要模块 (搜索、表格、分页、新增/编辑、状态流转) | 筛选、表格数据、分页、弹窗、审批/驳回/出库确认 |
| **预估开发时间** | 24小时 (3人天) | 包括 PageObject 封装、测试脚本编写、数据准备和调试。 |
| **预估维护成本** | 4小时/月 (平均) | 包括页面UI改动、新增筛选条件、操作按钮变化。危险品页面作为业务核心，预期变更频率中等。 |
| **手工执行时间** | 20分钟/次 | 假设手动回归一次所有核心功能（搜索、增/删/改/查、状态流）需要20分钟。 |
| **自动化执行时间** | 3分钟/次 | 自动化脚本执行一遍所有核心流程的时间。 |
| **执行频率** | 每日构建 (Daily Build)，每周全量回归 | 约22次/月。 |
| **ROI (1个月)** | **+216 分钟** | 节约时间 = 手工执行时间 - 自动化执行时间 = 17分钟/次 <br> 总节约时间 = 17分钟 * 22次 = 374分钟 <br> 总成本 = 开发时间 (折算成月) + 维护时间 = (1440分钟 / 12个月)、+ 240分钟/月 ≈ 360分钟 <br> **ROI = 374 - 360 = +14分钟 (正收益)** |
| **ROI (3个月)** | **+1150 分钟** | 维护成本摊销后，ROI 显著提升。 |
| **ROI (6个月)** | **+2780 分钟** | 超4个工作日，投入回报比极高。 |

**结论:** 虽然首月ROI微正，但在3-6个月的时间维度内，自动化投入的回报非常显著。对于P0级别的核心业务流（状态流转）和P0级别的搜索功能，自动化是值得的。

**风险对冲:**
- **数据准备自动化**: 创建“新增出库单 -> 提交 -> 审批”的API接口或 fixture，避免 UI 流程过长导致失败。
- **模块化用例**: 将每个状态流转步骤（新增、编辑、审批、出库确认）设计成原子化用例，降低依赖断裂的风险。