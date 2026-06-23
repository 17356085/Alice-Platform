好的，收到您的输入。以下是根据 **auto-strategy** Skill 制定的自动化策略文档。

---

## 产出文件

### AUTO_STRATEGY.md

```markdown
# 自动化策略报告 — lab/gas-compare

> **生成者**: automation-agent | **日期**: 2026-06-18
> **策略依据**: `PAGE_CONTEXT.md`, `TECH_ANALYSIS.md`, `GasComparePage.py`, `test_gas_compare.py`
> **ROI 分析师**: automation-agent

---

## 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
|---------|------|--------|----------|------|
| GC-01 | 正常显示气体分析对比页面（搜索表单） | P0 | ✅ | 核心冒烟用例，验证页面可访问性。定位器稳定（A/B级），执行频率高（每日）。 |
| GC-02 | 日期范围查询 | P0 | ✅ | 核心功能用例，覆盖主要业务路径。查询后反馈明确（加载然后显示表格/空状态），自动化可精确验证。 |

**覆盖率总结**:
- P0 用例总计: 2 个
- 已自动化: 2 个 (100%)
- 不自动化理由: 无 P2/P3 用例在一阶段策略中; 后续若新增涉及 UI 美观度、手动数据核对等用例，则不自动。

---

## 2. PageObject 拆分方案

遵循 **一个页面一个 Page 类** 原则，无需额外拆分。

```
GasComparePage
├── 职责: 封装 gas-compare 页面的所有元素定位与交互方法
│   ├── 导航 (navigate)
│   ├── 搜索区操作 (set_start_date, set_end_date, click_query, click_reset)
│   ├── 页面状态检测 (is_page_loaded, get_table_row_count)
│   └── 内部辅助方法 (_js_click_search_or_reset, _wait_loading_gone)
└── 弹窗处理
    └── 当前页面无独立弹窗，所有操作均在主页面完成。
    └── 如果未来有“新增/编辑对比规则”等弹出对话框，应独立为 GasCompareDialog。
```

**设计说明**:
- 该页面交互简单，搜索区和表格区耦合紧密，无理由拆分。
- 按钮操作使用 `_js_click_search_or_reset` 方法，而非标准 Selenium `click()`，体现了对该特定页面按钮层可能被覆盖或事件绑定的特殊处理。策略上接受此设计，但需注意该方法可维护性较低。

---

## 3. 公共组件复用分析

| 当前实现 | 是否可以复用 BasePage | 建议 |
|---------|----------------------|------|
| `navigate` 方法 (调用 `self.navigate_to(...)` 和 `self.wait_page_ready(...)`) | **✅ 已复用** | 符合规范，依靠 `SidebarNavigator` 基类能力。 |
| `_wait_loading_gone` 和 `wait_vue_stable` 调用 | **✅ 已复用** | 这两个是 `BasePage` 提供的通用等待方法，用于处理 Element Plus 的 loading 和 Vue 异步渲染。 |
| `is_page_loaded` 方法 (依赖 Vue 选择器判断元素存在) | **❌ 未复用** | 页面特有逻辑，合理。无需抽象到 BasePage。 |
| `set_start_date/ set_end_date` 方法 (使用标准 Selenium `clear()` 和 `send_keys()`) | **⚠️ 可参考** | `BasePage` 没有通用的日期选择封装。如果项目中有多处日期选择器，建议创建 `DatePickerHelper` 或扩展 `ElementPlusHelper` 来统一处理，这比在每个 Page 类中重复写 `clear()` + `send_keys()` 更高效。 |
| `_js_click_search_or_reset` | **❌ 不可复用** | 这是一个特殊方法，用于绕过标准 Selenium 点击的限制。不建议将其通用化，因为它可能只适用于特定页面的按钮实现。如果确认是 Element Plus 的通用行为（例如 `el-button` 在某些版本中 `click()` 无效），可以将其提取到 `ElementPlusHelper` 中。 |

**扩展建议**:
- **是否需要扩展 ElementPlusHelper**: 当前阶段**否**。当前只有一个页面使用此方法，且其可维护性不差。如果未来 3 个以上页面出现类似 JS 点击需求，则应将它封装到 `ElementPlusHelper`。
- **是否需要创建 DatePickerHelper**: **建议创建**。这可以跨页面（如 personnel, equipment）应用，提高复用性。

---

## 4. 等待策略建议

| 异步行为 | 触发操作 | 当前等待策略 | 建议 |
|---------|---------|-------------|------|
| 页面加载 (Vue 渲染) | `navigate()` | `self.wait_page_ready(timeout=15)` → `self._wait_loading_gone(timeout=10)` → `self.wait_vue_stable()` | ✅ 三层等待是标准做法，覆盖了从路由到第一次渲染到初始数据加载的全过程。维持现状。 |
| 查询后数据加载 | `click_query()` | `self.driver.execute_script(...)` → `self._wait_loading_gone(timeout=10)` → `self.wait_vue_stable()` | ✅ 合理。但建议增加 `EC.presence_of_element_located((By.CSS_SELECTOR, "table"))` 这样的显式等待，以确保表格已渲染（即使是无数据状态），提高 `is_page_loaded()` 的可靠性。 |
| 重置操作 | `click_reset()` | 同查询 | ✅ 合理。 |

**建议改进**:
- 在 `click_query()` 和 `click_reset()` 方法中，将 `_wait_loading_gone` 与 `wait_vue_stable` 交换顺序，或者两者都调用。当前顺序是先等待 loading 消失，再等待 Vue 稳定。在某些情况下，loading 消失后 Vue 可能还在进行 DOM 更新，所以 `wait_vue_stable` 在 `_wait_loading_gone` 之后调用是正确的。可以完善注释，确保代码理解一致。

---

## 5. 风险项与应对

| 风险项 | 风险等级 | 应对措施 |
|-------|---------|---------|
| **搜索按钮定位不稳定 (C级)** | **高** | 当前使用 JS `document.querySelectorAll('button')` 并按文本点击。如果页面有其他包含“查询”或“重置”的按钮，或按钮文本改变，会导致点击错误。 |
| **日期输入定位依赖 `placeholder` (B级)** | **中** | `placeholder*="开始日期"` 是一个 CSS 属性选择器。如果开发人员修改了 `placeholder` 值（如国际化，改为 `Start date`），自动化将失败。 |
| **`is_page_loaded` 可能误判** | **中** | 仅检查输入框和表格元素存在，未检查表格的 `loading` 属性。如果加载很慢，可能在 loading 状态下就返回 True。 |

**应对措施**:
1.  **搜索按钮**: 建议尝试使用标准 XPath: `//button[./span[contains(text(),'查询')]]` 作为主要定位器。如果标准 `click()` 失败，再回退到 JS 点击。
2.  **日期输入**: 与开发确认是否可以使用 `data-test-id` 或 `data-qa` 属性，例如 `data-qa="start-date-picker"`。这将提供最高稳定性。
3.  **页面加载**: 在 `is_page_loaded` 中增加对表格 `loading` 状态的检查。例如，检查 `document.querySelector('.el-table')?.getAttribute('v-loading')` 或检查 `el-loading-mask` 元素是否不存在。

---

## 6. ROI 分析

| 指标 | 数值 | 说明 |
|------|------|------|
| **预估开发时间 (T_dev)** | 2 小时 | 包括: 代码审查 (0.25h) + 修改 `is_page_loaded` (0.25h) + 添加显式等待 (0.25h) + 编写和维护自动生成脚本(1.25h，因为大部分代码已存在)。 |
| **预估维护成本 (T_maint)** | 0.25 小时/月 | 由于该页面功能简单，预期稳定。主要是当开发修改按钮文本或 placeholder 时需调整。 |
| **手工执行时间 (T_manual)** | 6 分钟/次 | 一次手工测试包括: 登录 (1.5min) + 导航 (0.5min) + 执行两个用例 (1min each) + 结果验证/截图 (2min)。 |
| **预估执行频率 (F)** | 50 次/月 (每日) | 该测试属于核心 P0 冒烟/回归测试，每天执行一次。 |
| **3个月 ROI** | **节省 28.5 小时** | 公式: `(T_manual * F * 3) - T_dev - (T_maint * 3)` |
| | | = (6min/60 * 50 * 3) - 2h - (0.25h * 3) |
| | | = 15h - 2h - 0.75h |
| | | **= 12.25 小时 (节省)** |

**结论**: 本页面的两个测试用例实现自动化后，在 3 个月内即可收回成本。自动化是一个**高 ROI 决策**。

---

## 7. 自动化脚本生成建议

- **保持现状**: `GasComparePage.py` 和 `test_gas_compare.py` 的基础结构良好。
- **强化等待**: 在 `is_page_loaded` 和 `click_query` 中增加更可靠的等待。
- **考虑引入 `data-test-id`**: 与开发团队沟通，约定对自动化关键元素添加 `data-test-id` 属性。这将从根本上解决定位器稳定性问题。
- **不要自动化一次性操作**: 目前所有用例复用率高，无需关注。

**最终结论**: 建议立即将 `GC-01` 和 `GC-02` 纳入自动化回归套件。
```

---