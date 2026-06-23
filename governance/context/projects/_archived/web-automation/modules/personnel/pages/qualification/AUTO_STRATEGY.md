好的，收到指令。我将基于您提供的 `PAGE_CONTEXT.md` 和项目上下文中的 `TECH_ANALYSIS.md`，并结合 `templates/auto-strategy.template.md` 模板，制定一份详细的自动化测试策略。

---

## AUTO_STRATEGY.md

### 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
|---------|------|--------|----------|------|
| TC-DISPLAY-001 | 页面正常加载 | P0 | ✅ | 基础冒烟，定位器稳定（CSS: `.el-table`，`.el-pagination`） |
| TC-SEARCH-001 | 按资质名称搜索 | P0 | ✅ | 搜索是核心功能，定位器稳定（`input[placeholder*='请输入资质名称']`） |
| TC-SEARCH-002 | 按资质类型下拉搜索 | P0 | ✅ | 核心功能，定位器采用XPath（文字）策略，属于B级，但预期稳定 |
| TC-SEARCH-003 | 按日期范围搜索 | P0 | ✅ | 核心功能，定位器稳定（`input[placeholder="开始日期"]`） |
| TC-SEARCH-004 | 搜索后分页状态正确 | P0 | ✅ | 验证搜索与分页联动，属于基础功能 |
| TC-RESET-001 | 重置按钮功能 | P0 | ✅ | 重置是搜索配套操作，定位器稳定 |
| TC-CRUD-001 | 新增一条资质记录 | P0 | ✅ | CRUD 核心流程，定位器稳定 |
| TC-CRUD-002 | 编辑一条资质记录 | P0 | ✅ | CRUD 核心流程，定位器稳定（行内操作依赖行索引，标记为 B 级风险） |
| TC-CRUD-003 | 删除一条资质记录 | P0 | ✅ | CRUD 核心流程，定位器稳定（行内操作依赖行索引，标记为 B 级风险） |
| TC-CRUD-004 | 新增重复名称资质 | P1 | ❌ | **不建议自动化**：验证后端唯一性约束，预期明确，但需要清理数据和等待接口回调，开发和维护成本高于收益。 |
| TC-PAGINATION-001 | 切换每页显示条数 | P1 | ✅ | 定位器稳定（`.el-pagination`），自动化收益高，验证 UI 行为。 |
| TC-PAGINATION-002 | 表格出现空数据状态 | P1 | ✅ | 验证边界场景（搜索无结果），定位器稳定（`.el-empty`）。 |
| TC-PERM-001 | 无新增权限时，按钮隐藏 | P2 | ❌ | **不建议自动化**：依赖权限配置，需要准备特定权限账号，维护成本较高。 |
| TC-PERM-002 | 无编辑权限时，按钮禁用 | P2 | ❌ | 同上，不建议自动化。 |
| TC-EXPORT-001 | 导出资质列表 | P2 | ✅ | 核心功能，流程固定。需注意下载文件处理（可在 BasePage 中封装）。 |
| TC-LOADING-001 | 页面加载时显示 loading 动画 | P1 | ✅ | 基础体验验证，通过 `v-loading` 属性判定，稳定性高。 |

#### 风险标注
- **TC-SEARCH-002**: 定位器稳定性为 B 级（依赖XPath+文字），如果页面重构或文案变更可能导致失败，需在页面更新时重点维护。
- **TC-CRUD-002/TC-CRUD-003**: 行内操作依赖行索引（`.el-table__row[n]`），如果表格排序、新增/删除后行顺序变化，可能导致操作错位。**建议**: 使用 `element-plus-test-utils` 或自定义 fixture 来确保操作前获取到的行索引是正确的。

### 2. PageObject 拆分方案

```
- `QualificationPage`：
    - 职责：封装资质管理主页面（搜索区、操作栏、表格、分页）的所有操作。
        - 搜索操作（`search_by_name`, `search_by_type`, `search_by_date_range`, `reset_search`）
        - 表格操作（`get_table_row_count`, `get_cell_text`, `click_edit_button_by_index`, `click_delete_button_by_index`）
        - 分页操作（`switch_page`, `change_page_size`）
        - 导出操作（`click_export`）
    - 定位器：页面级别的稳定元素（搜索框、按钮、表格容器、分页组件）。

- `QualificationDialog`：
    - 职责：封装新增/编辑资质的弹窗（`el-dialog`）内的所有操作。
        - 表单填写（`set_name`, `set_type`, `set_issuer`, `set_obtain_date`, `set_expiry_date`, `set_remark`, `upload_file`）
        - 提交/取消（`click_save`, `click_cancel`）
        - 状态检查（`is_dialog_visible`, `is_name_input_required` 等）
    - 定位器：弹窗内的表单元素（`.el-dialog__body .el-form-item`），避免与页面其他元素混淆。

- `QualificationEditDialog` (可选)：
    - 继承 `QualificationDialog`。
    - 职责：如果需要区分新增和编辑弹窗的行为（例如编辑时某些字段置灰或加载已有数据），可以独立，否则复用 `QualificationDialog`。
```

### 3. 公共组件复用分析

| 操作 | 复用 BasePage 方法 | 是否需扩展 |
|------|-------------------|-----------|
| 点击搜索/重置/新增按钮 | `BasePage.click(locator)` | 否 |
| 输入文本（搜索框/表单输入） | `BasePage.fill_element(locator, text)` | 否 |
| 点击下拉选择（单选） | `ElementPlusHelper.multi_select(locator, [option_text])` | 否 |
| 选择日期范围 | `ElementPlusHelper.pick_date_range(...)` | 否 |
| 等待表格加载完毕 | `BasePage.wait_element_visible(locator)` + `wait_for_loading_to_disappear()` | 否，`wait_for_loading_to_disappear` 已在 BasePage 中实现 |
| 分页操作 | `BasePage.click(locator)` | 否，但可以封装为 `PaginationMixin` 方便多个页面复用 |
| 行内编辑/删除 | 需在 `QualificationPage` 中自定义 | **是**，需封装 `click_edit_button_by_index` 方法，内部逻辑：`get_table_rows()[index].find_element(...)` |
| 上传文件 | `BasePage.find_element(locator).send_keys(file_path)` | 否 |
| 等待弹窗可见/不可见 | `BasePage.wait_element_visible(locator)` / `wait_element_disappear(locator)` | 否 |

**需要扩展 BasePage / ElementPlusHelper 的潜在场景**:
- **行内操作**：当前 BasePage 没有基于行索引定位的方法，建议在 `QualificationPage` 中自行封装，或考虑在 `BasePage` 中添加一个通用的 `get_table_rows` / `click_action_in_row` 方法，提高复用性。
- **分页操作**：当前 `BasePage` 可能没有专门的分页方法。如果多个页面都需要分页控制，建议封装一个 `PaginationMixin` 或 `PaginationComponent`。

### 4. 等待策略建议

- **页面特有的异步行为**：
    1. **搜索/重置**：点击按钮后，表格会重新加载数据，会有短暂的 loading 动画。
        - **策略**：使用 `BasePage.wait_for_loading_to_disappear()`。
    2. **新增/编辑/删除**：操作后同样会触发数据刷新，并可能出现成功/失败提示（Toast）。
        - **策略**：先等待 Toast 出现（`wait_element_visible(By.CSS_SELECTOR, ".el-message")`），再等待它消失，最后等待表格加载完毕。
    3. **日期选择器**：点击日期选择后，月/年面板有展开/关闭动画。
        - **策略**：使用 `ElementPlusHelper` 中已有的 `_wait_for_picker_panel` 方法。
    4. **导出**：点击导出按钮后，浏览器启动下载，可能需要几秒钟。
        - **策略**：`time.sleep(2)` （不推荐）或等待下载目录中出现临时文件（更可靠，需 BasePage 扩展）。

- **建议的等待封装**：
    1. **`wait_for_table_refresh()`**：组合 `wait_for_loading_to_disappear()` 和 `wait_element_visible(By.CSS_SELECTOR, ".el-table__body-wrapper .el-table__row:first-child")`，确保新数据加载完成。
    2. **`wait_for_toast_and_dismiss(By.TOAST_TYPE, timeout=5)`**：等待特定类型的 Toast（成功/错误）出现，并确认其内容。之后等待 Toast 消失（便于执行后续步骤）。

### 5. ROI 分析

| 项目 | 估算值 | 备注 |
|------|--------|------|
| **预估开发时间** | **8 小时** | 包括：PageObject 设计（2h）、测试脚本编写（4h）、数据准备与清理（1h）、第一次调试与自检（1h）。假设无特殊环境问题。 |
| **预估维护成本** | **2 小时/月** | 主要成本是页面 UI 变化时的定位器更新和业务流程调整。初始几个月可能稍高，稳定后递减。 |
| **手工执行时间** | **15 分钟/次** | 假设手工执行一套覆盖 P0/P1 核心功能的回归。 |
| **自动化执行频率** | **2 次/天** | 假设 CI 流水线每天触发两次（代码合并 + 定时任务）。 |
| **ROI 计算** | **正向** | 每月手工回归成本：15 分钟 * 60 次（2次/天 * 30天） = 900 分钟 = 15 小时。<br>每月自动化成本（维护）：2 小时（不包括执行时间，执行由 CI 自动完成）。<br>**自动化成本回收期**: 8 小时（开发）/ (15 小时 - 2 小时) ≈ 0.6 个月。<br>**长期收益**: 每月节省约 13 小时的回归测试时间。 |

**结论**：该页面的自动化投入回报率非常高，建议立即投入开发。核心风险点在于行内操作的稳定性，建议在测试脚本中增加适当的等待和索引校验逻辑，并通过持续集成中的定期执行来监控其稳定性。