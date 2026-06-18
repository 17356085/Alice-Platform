好的，遵照您的指示。基于您提供的 `PAGE_CONTEXT.md` 和 `TECH_ANALYSIS.md`，我将制定“人员管理-资质管理”页面的自动化策略。

---

## AUTO_STRATEGY.md

### 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
|---------|------|--------|----------|------|
| TC-001 | 页面正常加载 | P0 | ✅ | 基础冒烟，确保路由、面包屑、搜索区、操作栏、表格、分页组件正常渲染。 |
| TC-002 | 搜索-按名称精确搜索 | P0 | ✅ | 核心搜索功能，定位器稳定（`#search-name`）。 |
| TC-003 | 搜索-按类型下拉筛选 | P0 | ✅ | 核心筛选功能，`el-select` 下拉框选取。 |
| TC-004 | 搜索-按状态下拉筛选 | P0 | ✅ | 核心筛选功能。 |
| TC-005 | 搜索-按日期范围筛选 | P0 | ✅ | `el-date-picker` 日期范围选择。 |
| TC-006 | 搜索-重置所有筛选条件 | P0 | ✅ | 验证“重置”按钮功能。 |
| TC-007 | 新增资质-成功创建 | P0 | ✅ | CRUD 核心流程，验证弹窗、必填项、表单提交及成功反馈。 |
| TC-008 | 编辑资质-成功修改 | P0 | ✅ | CRUD 核心流程，验证数据回填、修改及提交。 |
| TC-009 | 查看资质详情 | P1 | ✅ | 验证只读弹窗数据渲染。 |
| TC-010 | 删除资质-确认后删除 | P0 | ✅ | 核心操作，验证删除确认框（`el-message-box`）及删除成功反馈。 |
| TC-011 | 新增资质-取消操作 | P1 | ✅ | 验证弹窗关闭逻辑（点击取消/X/遮罩）。 |
| TC-012 | 新增资质-必填项校验 | P1 | ✅ | 验证表单校验（如名称、类型、发证机关为空时点击保存）。 |
| TC-013 | 分页-切换每页显示条数 | P1 | ✅ | 验证 `el-pagination` 的 `size-change` 事件。 |
| TC-014 | 分页-点击下一页 | P1 | ✅ | 验证 `current-change` 事件。 |
| TC-015 | 权限控制-无新增权限时按钮隐藏 | P1 | ✅ | 验证 `btn-add` 元素不存在。 |
| TC-016 | 权限控制-无编辑/删除权限时操作列不显示 | P1 | ✅ | 验证行内操作按钮 `btn-edit`, `btn-delete` 不存在。 |
| TC-017 | 加载状态-表格显示 Loading 动画 | P1 | ❌ | 等待 `v-loading` 消失是自动化前置条件，不单独作为用例。 |
| TC-018 | 空数据-表格显示“暂无数据” | P1 | ✅ | 验证 `el-empty` 组件在无数据时显示。 |
| TC-019 | 附件上传-上传成功 | P2 | ❌ | 上传操作依赖系统弹窗（OS文件选择器），自动化成本高且不稳定。 | 
| TC-020 | 附件上传-文件格式/大小校验 | P2 | ❌ | 校验逻辑可能在前端`before-upload`或后端执行，前端校验需要mock file对象，维护成本高。 |
| TC-021 | 日期校验-有效期至不能早于获得日期 | P2 | ❌ | 该校验规则通常由后端处理，或作为复杂前端逻辑。自动化风险高，ROI低。 |
| TC-022 | 性能-页面元素加载耗时不超过5s | P3 | ❌ | 不适合UI自动化，应使用专门的性能测试工具。 |

**风险标注：**
- TC-007, 008 (Dialog表单): 弹窗中`el-upload`的定位和交互需关注，若`el-upload`列表项无稳定id，则定位不稳定，风险中。
- TC-015, 016 (权限): 权限模拟需通过修改登录用户权限或API mock实现，有一定环境准备成本。

### 2. PageObject 拆分方案

```
suggested_page_objects:
  - class_name: QualificationPage
    file: pages/personnel/qualification_page.py
    responsibilities:
      - 搜索区域操作 (search_name, select_type, select_status, pick_date_range, click_search, click_reset)
      - 操作栏操作 (click_add)
      - 表格操作 (get_table_rows, get_cell_value, click_row_action_button)
      - 分页操作 (select_page_size, click_next_page)
      - 状态判断 (is_empty, is_loading)
  - class_name: QualificationDialog
    file: pages/personnel/qualification_dialog.py
    responsibilities:
      - 弹窗打开/关闭状态判断
      - 表单填充 (fill_name, select_type, fill_issuer, pick_date, fill_remark)
      - 附件上传 (upload_file) # 注意：此操作不稳定，作为可选方法
      - 表单提交/取消 (click_save, click_cancel, click_close)
      - 表单校验 (get_form_error_messages)
      - 详情查看 (get_dialog_detail_values)
```

### 3. 公共组件复用分析

| 操作 | 可复用的 BasePage 方法 | 扩展建议 |
|------|------------------------|----------|
| 输入框 `el-input` | `BasePage.input_text(locator, text)` | 可以直接复用，locator 由子类传入。 |
| 下拉框 `el-select` | `BasePage.select_dropdown_option(locator, option_text)` | 可直接复用，需要确保 `ElementPlusHelper` 中的下拉框点击与选项选择逻辑正确。 |
| 日期选择器 `el-date-picker` | `BasePage.pick_date_range(locator, start_date, end_date)` | 可直接复用，需要确保 `ElementPlusHelper` 正确处理日期面板的Teleport定位。 |
| 表格 `el-table` | `BasePage.get_cell_text(table_locator, row_index, col_index)` | 可直接复用。建议在 `QualificationPage` 中封装基于列名称的获取方法，更语义化。 |
| 分页 `el-pagination` | `BasePage` 无分页操作。 | 建议在 `ElementPlusHelper` 中新增 `select_pagination_size` 和 `click_pagination_page` 方法。 |
| 弹窗 `el-dialog` | `BasePage.is_dialog_present(locator)` | 可直接复用。`ElementPlusHelper` 应包含 `wait_for_dialog_visible` / `invisible` 方法。 |
| 按钮 `el-button` | `BasePage.click(locator)` | 可直接复用。 |
| 上传 `el-upload` | `BasePage` 无上传操作。`ElementPlusHelper` 不处理。 | `QualificationDialog` 需要使用 Selenium `send_keys` 操作 `input[type='file']`，这是一个高风险操作，需单独封装并加日志。 |
| 确认框 `el-message-box` | `BasePage.confirm_in_dialog(text=None)` | 可直接复用，用于确认删除等操作。 |

### 4. 等待策略建议

该页面的异步行为主要集中在数据加载和弹窗过渡。建议为该页面定制一个等待管理器或使用基类的统一等待。

| 场景 | 触发条件 | 预期变化 | 等待策略 | 实现建议 |
|------|---------|---------|----------|----------|
| **表格数据加载** | 搜索、重置、翻页、新增/编辑/删除后 | `v-loading` 指令控制的遮罩层消失 & 表格行数据更新 | 等待 `v-loading` 遮罩消失（`visibility_of_element_located` 到 `invisibility_of_element_located`）。 | `BasePage.wait_for_table_loaded(table_locator)` |
| **弹窗打开** | 点击“新增”、“编辑”、“查看”按钮 | `el-dialog__wrapper` 或 `.el-overlay.dialog-wrapper` 出现，且 `v-show` 或 `v-if` 生效 | 等待弹窗容器可见，并短暂等待其动画完成（建议使用显式等待 `.el-dialog__body` 子元素可见）。 | `BasePage.wait_for_dialog_visible(dialog_locator)` |
| **弹窗关闭** | 点击保存/取消/关闭按钮 | 弹窗容器消失 | 等待弹窗容器隐藏 (`invisibility_of_element_located`)。 | `BasePage.wait_for_dialog_invisible(dialog_locator)` |
| **确认框 (MessageBox)** | 点击“删除”按钮 | `.el-message-box__wrapper` 出现 | 等待确认框出现。点击确认后，等待确认框消失。 | `BasePage.wait_for_confirm_dialog_visible()` |
| **Toast 消息提示** | 成功/失败/警告的任何操作反馈 | `el-message` 组件出现 | 短暂等待 Toast 出现即可断言文本，或使用 `EC.presence_of_element_located`。 | `BasePage.wait_and_get_toast_message()` |
| **下拉选项加载** | 点击 `el-select` 输入框 | `<body>` 下的 `el-select-dropdown` 出现 | 等待 `.el-select-dropdown__item` 列表可见。 | `ElementPlusHelper.WaitForSelectDropdownOptions(locator)` |
| **文件上传** | 点击上传按钮并选择文件 | 表格或列表中出现上传项 | 等待 `el-upload-list__item` 出现。由于上传时间不可控，建议设置较长的超时时间（如 15s）。 | `QualificationDialog.wait_for_upload_complete(upload_locator)` |

### 5. ROI 分析

| 项目 | 评估 | 计算 |
|------|------|------|
| **预估开发时间** | 16 小时 | 包含 PageObject 类编写、元素定位器确认、测试脚本编写、1 轮调试、自检与 PR。 |
| **预估维护成本** | 3 小时/月 | UI 小改动的定位器更新、交互逻辑变更时的维护。 |
| **手工执行时间** | 15 分钟/次 | 执行 TC-001 ~ TC-018 全套冒烟回归。 |
| **执行频率** | 20 次/月 | 每日构建回归 (1次/工作日) + 缺陷验证 / 版本发布。 |
| **ROI 计算 (12个月)** | `(15*20*12) - (16*60 + 3*60*12)` | 公式: `(手工执行总分钟数) - (开发总分钟数 + 维护总分钟数)` |
| | | `= 3600 - (960 + 2160) = 480 分钟 = 8 小时 (ROI 为正值)` |
| **结论** | **建议自动化** | 自动化在12个月内即可节省约8小时的测试执行时间，且随着时间推移，ROI将持续提升。考虑到P0和P1用例的覆盖率，自动化对质量的保障作用远大于纯时间计算。 |

---

**相关文件：**
- [测试用例 (TEST_CASES.md)] (../test/TEST_CASES.md)
- [技术分析 (TECH_ANALYSIS.md)](TECH_ANALYSIS.md)
- [自动化架构概览](../AUTOMATION_ARCHITECTURE.md)