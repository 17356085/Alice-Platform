好的，我将基于模块 `personnel` 和页面 `my-exam` 的页面上下文，并结合测试用例和技术分析的假设，输出自动化测试策略文档。

---

## 产出物: AUTO_STRATEGY.md

```markdown
# 自动化测试策略: 我的考试 (my-exam)

> **策略版本**: 1.0 | **制定日期**: 2026-06-18 | **技术栈**: Selenium + pytest + Element Plus
> **前置依赖**: [PAGE_CONTEXT](./PAGE_CONTEXT.md) | [TECH_ANALYSIS](./TECH_ANALYSIS.md)

## 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
| :--- | :--- | :--- | :--- | :--- |
| TC-001 | 页面正常加载 - 标题/搜索区/表格/分页区全部渲染 | P0 | ✅ | 基础冒烟，定位器稳定 (CSS选择器基于class) |
| TC-002 | 默认请求 - 发送分页加载请求，展示数据 | P0 | ✅ | 核心数据流，可断言表格行数和分页信息 |
| TC-003 | 搜索 - 按考试名称模糊搜索 | P0 | ✅ | 核心业务操作，`el-input` 定位稳定 |
| TC-004 | 筛选 - 按考试状态筛选 | P0 | ✅ | 核心业务操作，`el-select` 属标准EP模式 |
| TC-005 | 搜索+筛选 - 组合条件查询 | P1 | ✅ | P1，自动化成本低，可复用TC-003/TC-004步骤 |
| TC-006 | 重置搜索条件 | P1 | ✅ | 基础易覆盖，可放在P0用例后链式调用 |
| TC-007 | 表格数据正确性 - 列名/数据格式符合预期 | P1 | ✅ | 通过获取多个cell文本断言，自动化可行 |
| TC-008 | 状态列标签颜色 - 不同状态的tag颜色不同 | P2 | ❌ | 需要人工视觉判断颜色；若提供 `el-tag` type属性可自动化，标记为**需确认** |
| TC-009 | 链接型按钮显示/隐藏 - 根据考试状态显示不同操作 | P0 | ✅ | 核心交互，通过元素存在性/可见性判断 |
| TC-010 | 分页切换 - 切到第2页 | P1 | ✅ | EP分页组件 `el-pagination` 有稳定定位 (CSS class) |
| TC-011 | 分页每页条数切换 | P1 | ✅ | 同上 |
| TC-012 | 空数据状态 - 搜索无结果时显示empty提示 | P1 | ✅ | `el-empty` class 可定位，重要边界场景 |
| TC-013 | 加载中状态 - 请求时显示loading | P1 | ✅ | `v-loading` 本质为CSS class `.el-loading-mask`，可断言存在/消失 |
| TC-014 | 考试详情弹窗 - 点击“查看”打开弹窗 | P0 | ✅ | 核心交互；确定弹窗定位器稳定 (CSS ID: `dialog_exam_detail`） |
| TC-015 | 考试详情弹窗 - 弹窗内关数据正确性 | P1 | ✅ | 可在弹窗打开后获取元素文本断言 |
| TC-016 | 考试详情弹窗 - 关闭弹窗（点X/点取消/点遮罩层） | P1 | ✅ | 标准EP dialog交互，可自动化 |
| TC-017 | 确认开始考试弹窗 - 点击“开始考试”弹出确认框 | P0 | ✅ | 核心交互 |
| TC-018 | 确认开始考试弹窗 - 点击“确定”后跳转至答题页面 | P0 | ❌ | 跨页面跳转，属于跨模块流转；应在 **flow test** 中覆盖，但若**该页有数据回调可断言**，可保留；**定位器不稳定（跳转URL动态）** |
| TC-019 | 确认开始考试弹窗 - 点击“取消”不跳转 | P1 | ✅ | 弹窗关闭即可断言 |
| TC-020 | 多页数据翻页后操作 | P1 | ✅ | 翻页后“开始考试”按钮交互；需确保每页数据有“未开始”状态 |
| TC-021 | 未登录/权限不足时页面表现 redirect | P2 | ❌ | 应在权限/登录测试中覆盖 |
| TC-022 | 表格操作列按钮权限管控 | P1 | ✅ | 有权限时显示“开始考试”，无权限时隐藏；可断言元素存在性 |
| TC-023 | 网络异常错误状态 | P2 | ❌ | UI自动化难以模拟网络异常（减少依赖mock或API层） |
| TC-024 | 批量操作？（假设无批量操作） | - | - | 该页面可能无批量操作 |

**标记风险**:
- TC-008: 如果状态列 `el-tag` 通过动态绑定 `:type` 实现颜色，可以自动化；若通过 `:style` 动态颜色，则CSS定位器不稳定，建议通过后端API断言type枚举。
- TC-018: 跨页面跳转，跳转后URL动态且非本页面，自动化维护成本高，定位器失效风险大，不建议自动化；建议在App层面做端到端验收，或mock该动作。

## 2. PageObject 拆分方案

### 2.1 建议的 Page 类

| 模块 | 页面 | Page 类名 | 类文件 | 主要职责 | 备注 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `personnel` | `my-exam` | `MyExamPage` | `my_exam_page.py` | 搜索区、表格区、分页区所有元素操作 | 主要页面类 |
| `personnel` | `my-exam` | `ExamDetailDialog` | `exam_detail_dialog.py` | 考试详情弹窗内元素操作 | 独立弹窗类 |
| `personnel` | `my-exam` | `StartExamConfirmDialog` | `start_exam_confirm_dialog.py` | 确认开始考试弹窗内元素操作 | 独立弹窗类 |

### 2.2 Page 类职责边界

**MyExamPage.class**:
- 定位: 搜索input、select、搜索/重置按钮、表格、分页
- 方法:
  - `search_exam(name: str = None)` — 输入名称点击搜索
  - `filter_by_status(status: str)` — 选择状态筛选
  - `reset_search()` — 点击重置
  - `get_exam_table_rows()` — 获取表格所有行元素列表
  - `get_row_data_by_index(index: int)` — 获取指定行各列文本
  - `get_pagination_info()` — 获取当前页/总条数
  - `switch_page(page_number: int)` — 翻页
  - `change_page_size(size: int)` — 切换每页条数
  - `click_action_start(index: int)` — 点击指定行的“开始考试”
  - `click_action_view(index: int)` — 点击指定行的“查看”
  - `is_empty_state()` — 判断空数据状态
  - `wait_for_loading_finish()` — 等待加载完成（通用等待）

**ExamDetailDialog.class**:
- 定位: 弹窗标题、考试名称文本、考试说明文本、关闭按钮
- 方法:
  - `get_title()`、`get_exam_name()`、`get_exam_description()`
  - `close()`、`click_close_btn()`、`click_overlay_to_close()`
  - `is_displayed()` / `wait_until_display()`

**StartExamConfirmDialog.class**:
- 定位: 弹窗标题、确认/取消按钮
- 方法:
  - `click_confirm()` — 点击确定
  - `click_cancel()` — 点击取消
  - `is_displayed()`、`wait_until_display()`、`wait_until_hidden()`

## 3. 公共组件复用分析

### 3.1 可复用 BasePage 已有方法

| 操作 | BasePage 方法 | 使用方式 |
| :--- | :--- | :--- |
| 输入文本 | `type_text(locator, text)` | `self.type_text(self.exam_name_input, name)` |
| 点击元素 | `click_element(locator)` | `self.click_element(self.search_btn)` |
| 获取元素文本 | `get_element_text(locator)` | `self.get_element_text(self.col_exam_name)` |
| 元素可见性 | `is_element_visible(locator)` | `self.is_element_visible(self.row_cell_action_start)` |
| 等待元素消失 | `wait_element_invisible(locator)` | 用于等待loading消失 |

### 3.2 需要扩展 ElementPlusHelper

| 操作 | 需扩展方法 | 原因 |
| :--- | :--- | :--- |
| `el-select` 选择下拉选项 | `select_by_label(select_locator, label, timeout=5)` | Element Plus `el-select` 下拉面板渲染在 `body` 下，标准鼠标操作不可靠，需要特殊封装 |
| `el-table` 获取某行某列文本 | `get_table_cell_text(table_locator, row_index, column_index)` | 提高代码可读性，避免频繁定位 th/td |
| `el-pagination` 切换分页 | `click_pagination_item(page_label)` | 点击 `ul.el-pager` 下指定页码按钮 |
| `el-dialog` 等待打开/关闭 | `wait_for_dialog_visible(dialog_locator)` / `wait_for_dialog_hidden(dialog_locator)` | 弹窗有动画（0.3s），单纯 `visibility_of_element_located` 可能不够 |

### 3.3 定位器复用（建议定义在类属性中）

参照 `PAGE_ELEMENT_POSITION.md` 中定义的定位器常量，直接作为类属性。建议统一存放为元组格式：`LOCATOR = (By.CSS_SELECTOR, ".el-input .el-input__inner")`。

## 4. 等待策略建议

### 4.1 页面特有异步行为

| 场景 | 异步行为 | 建议封装等待类型 |
| :--- | :--- | :--- |
| 页面初次加载 | 异步请求获取考试列表数据，完成后渲染表格 | `wait_for_element_visible(table_exam_list)` |
| 搜索/筛选 | 前端 `debounce` 300ms + 异步请求 + 表格重新渲染 | `wait_for_text_present_in_element(table_exam_list, expected_text)` 或 `wait_for_loading_finish()` |
| 分页切换/改变每页条数 | 发起新请求，表格重新渲染 | `wait_for_staleness_of(old_row)` 或 `wait_for_text_present_in_element(pagination, expected_page_number)` |
| 弹窗打开 | `el-dialog` 动画 0.3秒 | `wait_for_element_visible(dialog_locator)` |
| 弹窗关闭 | `el-dialog` 动画 0.3秒 | `wait_for_element_invisible(dialog_locator)` |

### 4.2 全局默认等待

- 建议设置 `WebDriverWait` 的 `timeout=10`（通用），弹窗等待 `timeout=5`。
- 对于 `el-select` 下拉选项（渲染在 `body`），需使用 `WebDriverWait(driver, 5).until(EC.visibility_of_element_located(dropdown_option_locator))`。

## 5. ROI（投资回报率）分析

### 5.1 计算参数

| 参数项 | 估值 | 说明 |
| :--- | :--- | :--- |
| 手工单次执行时间 | `Z = 8` 分钟 | 包括搜索、筛选、翻页、弹窗检查等核心测试点 |
| 回归频率 | `F = 2` 次/周（8次/月） | 假设每次发版前和每周五执行 |
| 预估开发时间 | `X = 12` 小时 | 包括页面类编写、弹窗类编写、定位器调试、公共方法扩展 |
| 预估维护成本 | `Y = 2` 小时/月 | 定位器微调、兼容性修改（版本迭代引起） |
| 自动化用例数 | `N = 18` 个 | 根据覆盖矩阵统计 ✅ 数量 |
| 执行周期 | `Months = 6` 个月 | 分析时间跨度 |

### 5.2 ROI 计算

- **手工成本（6个月）** = `Z × F × 4 × 6` = `8 分钟 × 8次/月 × 6月` = `384 分钟 = 6.4 小时`
- **自动化成本（6个月）** = `X + Y × 6` = `12 + 2 × 6` = `24 小时`
- **净收益** = 手工成本 - 自动化成本 = `6.4 - 24 = -17.6 小时`（短期内为负收益）
- **投资回收期**：手工成本累计超过自动化成本所需月数 = `24 / (6.4/6) ≈ 22.5` 个月

### 5.3 ROI 结论

| 指标 | 数值 | 评估 |
| :--- | :--- | :--- |
| 净收益（6个月） | -17.6 小时 | 短期投入大于节省 |
| 回收期 | ~22.5 个月 | 长期回归收益较可观 |
| 按年计算 | - | **第一年**：自动化成本=12+2×12=36h，手工成本=6.4×2（年）=12.8h，仍为负收益；**第二年**：手工成本=12.8h/年，维护成本=6.4h/年（两年后定位稳定，维护成本减半）+12h（可能需适配大版本）= 26.8h，仍省不了；需达到执行频率更高（每日）或增加自动化用例（更多页面复用同一组件）才能正向 |

**建议**：
- **该页面建议优先自动化 P0 和 P1 核心场景（TC-001~TC-007, TC-009~TC-017, TC-019, TC-020）**，放弃P2及跨页面场景。
- 如项目有高频回归（每日1次），则 ROI 转正周期可缩短至 ~4个月，强烈建议自动化。
- 如仅为每周回归1次，建议**半自动化**：P0手动，P1选择性手动。

## 6. 定位器稳定性风险评估

| 元素ID | 稳定性评级 | 风险描述 | 缓解措施 |
| :--- | :--- | :--- | :--- |
| `exam_name_input` | 🟢 稳定 | `el-input` 使用 `placeholder` 定位 | 建议加上标签文字辅助：`input.el-input__inner[placeholder="考试名称"]` |
| `exam_status_select` | 🟡 中风险 | `el-select` 下拉框渲染在 `body` 下，且 `readonly` input 可能有多个 | 使用 `label` + `class` 组合定位：`input.el-select__input` + 父级 `el-select` 关联 |
| `search_btn`/`reset_btn` | 🟢 稳定 | `button.el-button` + 文本定位 | 组合 `.el-button--primary` 和文本 |
| `table_exam_list` | 🟢 稳定 | `el-table` class 唯一 | 多表时需加容器范围 |
| `pagination` | 🟢 稳定 | `el-pagination` class 唯一 | 多分页时加容器范围 |
| `dialog_exam_detail` | 🔴 高风险 | `el-dialog` 元素存在性与动画导致定位不稳定 | 使用自定义 `data-dialog-id` 属性最佳；否则通过 `visible-arrow` 和 `aria-label` 定位 |
| `row_cell_action_start` | 🟡 中风险 | 动态按钮（根据不同状态显示/隐藏） | 使用索引+列号组合：`.el-table__body-wrapper tbody tr:nth-child(n) td:last-child button:first-child` |

## 7. 实施优先级

| 优先级 | 用例组 | 建议开发顺序 | 备注 |
| :--- | :--- | :--- | :--- |
| **P0** | TC-001~TC-004, TC-009, TC-014, TC-017 | 第1周完成 | 核心冒烟+搜索筛选+弹窗主流程 |
| **P1** | TC-005~TC-007, TC-010~TC-013, TC-015~TC-016, TC-019~TC-020 | 第2周完成 | 边界、分页、弹窗细节、权限 |
| **P2** | TC-008, TC-018, TC-021~TC-023 | 第3周评估 | 强边界（状态颜色需视觉确认）仅考虑API层；跨页面流程放flow测试 |

---

**版本记录**
| 版本 | 日期 | 变更内容 | 维护者 |
| :--- | :--- | :--- | :--- |
| 1.0 | 2026-06-18 | 初始版本，基于PAGE_CONTEXT和TECH_ANALYSIS制定 | automation-agent |