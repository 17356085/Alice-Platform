好的，收到你的策略制定请求。现在我将基于你提供的 **Page Object 代码 (WaterReportPage.py)**、**测试脚本 (test_water_report.py)**、**页面上下文 (PAGE_CONTEXT.md)** 和 **技术分析 (TECH_ANALYSIS.md)**，为`lab/water-report`页面制定自动化策略。

---

### AUTO_STRATEGY — lab / water-report (v1.0)

> **制定时间**: 2026-06-18 | **依据**: WaterReportPage.py + test_water_report.py + PAGE_CONTEXT.md + TECH_ANALYSIS.md | **状态**: 可执行

#### 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
|---------|------|--------|----------|------|
| TD-LW-001 | 页面正常加载 | P0 | ✅ | 基础冒烟，验证自定义表格渲染 |
| TD-LW-002 | 切换取样位置 | P0 | ✅ | 画面核心交互，验证数据刷新 |
| TD-LW-003 | 新增报告单弹窗打开 | P0 | ✅ | 核心业务入口，验证弹窗内容完整 |
| TD-LW-004 | 弹窗输入并提交 | P0 | ✅ | 核心业务流程（生成报告单） |
| TD-LW-010 | 未输入日期查询 | P1 | ❌ | 边界值，手动验证更高效 |
| TD-LW-020 | 日期范围搜索 | P0 | ✅ | 验证搜索功能与表格数据更新 |
| TD-LW-021 | 重置搜索条件 | P0 | ✅ | 验证重置逻辑 |
| TD-LW-030 | 导出报告单 | P2 | ❌ | 一次性操作（或低频），手动验证更简单 |

**风险标注**:
- **TD-LW-003 & 004**: `_js_click_search_or_reset` 和 `find_field_in_dialog` 使用JS注入，若UI重构（如按钮文本换行、label样式修改）则定位中断。**高维护风险**。
- **TD-LW-002**: `switch_location` 的定位器未公开（`switch_location`内部假设为页签），需确认实现后评估稳定性。**中等风险**。

---

#### 2. PageObject 拆分方案

**现有结构**:
```
WaterReportPage
├── 搜索区 (set_start_date / set_end_date / click_query / click_reset)
├── 新增弹窗 (click_add / dialog_input_* / dialog_confirm / dialog_cancel)
└── 表格 (get_row_count / get_rows)
```

**建议调整**:

考虑到当前页面功能相对单一（搜索 + 新增弹窗），**建议保持单一Page类**，无需拆分。但在`WaterReportPage`内部，可以按功能区域定义方法前缀，以便区分维护。

- **保留**: `WaterReportPage`
  - **搜索区操作**: 保持现有`set_start_date`, `set_end_date`, `click_query`, `click_reset`。
  - **弹窗操作**: 保持现有`dialog_`前缀的方法。
  - **表格操作**: 保持现有`get_row_count`, `get_rows`。

**不推荐独立为`WaterReportDialog`的理由**:
- 弹窗逻辑简单（输入+提交），独立类会增加模块间`page.dialog`的调用复杂度。
- 弹窗生命周期与主页面绑定紧密（弹窗打开后页面操作暂时阻塞）。

**未来扩展时再考虑拆分**:
如果新增弹窗变得复杂（如多Tab、动态表单、文件上传），再考虑独立成`WaterReportDialog`类。

---

#### 3. 公共组件复用分析

| 操作 | 是否可复用BasePage | 说明 |
|------|-------------------|------|
| `navigate` | ✅ 复用 | `self.navigate_to("化验室取样", "水质分析报告单")` 已复用`SidebarNavigator` |
| `_wait_loading_gone` | ✅ 复用 | 所有页面通用，已封装在`BasePage` |
| `wait_vue_stable` | ✅ 复用 | 所有页面通用，已封装在`BasePage` |
| 定位`el-date-picker` | ⚠️ 需扩展 | 目前搜索区用`input[placeholder*="..."]`，不通用，建议在`BasePage`或`ElementPlusHelper`增加`def date_picker(self, placeholder)` |
| 查找弹窗内表单字段 | ⚠️ 需封装 | `_find_field_in_dialog`可抽取到`BasePage`作为公共辅助方法，如`def find_page_dialog_field(self, label_keyword)` |
| 点击按钮（通过文字） | ⚠️ 需扩展 | 多个地方用到JS脚本查找按钮，建议在`ElementPlusHelper`中封装统一方法，如`click_button_by_text(text)` |
| 表格行数获取 | ❌ 不通用 | 自定义表格的DOM结构不统一，每个页面需要自己的定位器 |

---

#### 4. 等待策略建议

| 异步行为 | 建议等待 | 优先级 |
|---------|---------|--------|
| **表格数据加载** | 点击查询/重置/切换位置后，需等待`_wait_loading_gone` + `wait_vue_stable` | 高 |
| **弹窗动画** | `click_add`后，显式等`el-dialog`出现（已实现） | 高 |
| **弹窗关闭动画** | `dialog_confirm`或`dialog_cancel`后，等待弹窗消失 | 高 |
| **日期选择器展开** | `set_start_date`/`set_end_date` 内部无需额外等待，但后续查询需要 | 中 |

**等待封装建议**:
- 在`WaterReportPage`中保持现有的`_wait_loading_gone`和`wait_vue_stable`组合使用。
- 对于弹窗消失，建议增加方法:
```python
def _wait_dialog_gone(self, timeout=5):
    WebDriverWait(self.driver, timeout).until(
        EC.invisibility_of_element_located(self.DIALOG))
    self.wait_vue_stable()
```

---

#### 5. ROI 分析

| 项目 | 数值 | 计算说明 |
|------|------|---------|
| **预估开发时间** | 8 小时 | 包括3个P0用例脚本编写、调试、定位器确认、1轮review |
| **预估维护成本** | 1 小时/月 | 基于PAGE_CONTEXT常规维护周期：UI迭代（约2次/月），每次约0.5小时调整 |
| **手工执行时间** | 15 分钟/次 | 5个P0用例，手动操作+验证约3分钟/用例 |
| **执行频率** | 10 次/月 | 日常回归+新功能验证 |
| **月度手工成本** | 2.5 小时 | 15分钟/次 × 10次/月 |
| **月度自动化成本** | 0.5 小时 | 维护1小时 + 执行成本忽略（CI自动触发） |
| **月节省** | 2 小时 | 2.5 - 0.5 |
| **投资回收期** | 4 个月 | 8小时开发 / 2小时/月 |

**ROI结论**:
- **正向**: 由于页面结构相对稳定（搜索+弹窗），且P0用例数量适中，自动化后2个月即可回收开发成本。
- **风险警示**: 如果下季度该页面面临重构（如从自定义表格换为`el-table`），则维护成本激增，ROI转负。开发时应预留足够的抽象（如将自定义表格的操作封装在独立的`_table_helper`方法中）。

---

### 后续行动项

| 序号 | 行动 | 负责人 | 截止 |
|------|------|--------|------|
| 1 | 确认`switch_location`定位器的具体实现（基于PAGE_CONTEXT假设的页签） | 自动化开发 | 代码构建前 |
| 2 | 实现`ElementPlusHelper.click_button_by_text`通用方法，替换现有JS脚本 | 自动化开发 | Sprint 1 |
| 3 | 实现`ElementPlusHelper.date_picker`方法，替换现有日期选择器定位 | 自动化开发 | Sprint 1 |
| 4 | 根据前端截图/HTML，确认自定义表格的DOM结构，实现稳定`get_rows()` | 自动化开发 | Sprint 1 |