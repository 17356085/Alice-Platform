好的，收到您的请求。作为自动化测试专家，我将基于您提供的 `PAGE_CONTEXT.md` 和 `TECH_ANALYSIS.md` 信息，为 `personnel/visitor` 页面制定自动化覆盖策略。

---

# 自动化策略报告: 访客管理 (personnel/visitor)

## 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
|---------|------|--------|----------|------|
| TC-VISITOR-001 | 页面正常加载 | P0 | ✅ | 基础冒烟，覆盖表格、搜索区、分页，定位器稳定 |
| TC-VISITOR-002 | 搜索-按姓名/单位搜索 | P1 | ✅ | P1回归用例，定位器稳定，覆盖核心搜索功能 |
| TC-VISITOR-003 | 搜索-按手机号搜索 | P1 | ✅ | P1回归用例，定位器稳定 |
| TC-VISITOR-004 | 搜索-按状态筛选 | P1 | ✅ | P1回归用例，涉及 `el-select` 操作，可通过 `ElementPlusHelper` 复用 |
| TC-VISITOR-005 | 搜索-按来访日期范围搜索 | P1 | ✅ | P1回归用例，涉及 `el-date-picker` 操作，可通过 `ElementPlusHelper` 复用 |
| TC-VISITOR-006 | 搜索-重置 | P1 | ✅ | P1回归用例，验证重置功能，可与搜索用例组合为一个测试方法 |
| TC-VISITOR-007 | 新增访客 | P0 | ✅ | 核心业务流程，P0必测 |
| TC-VISITOR-008 | 编辑访客 | P0 | ✅ | 核心业务流程，P0必测 |
| TC-VISITOR-009 | 删除访客 | P0 | ✅ | 核心业务流程，P0必测，需处理确认弹窗 |
| TC-VISITOR-010 | 导出访客列表 | P2 | ❌ | 自动化价值低，仅验证下载行为，稳定性和文件处理复杂 |
| TC-VISITOR-011 | 批量导入访客 | P2 | ❌ | 一次性批量操作，且涉及文件上传，维护成本高 |
| TC-VISITOR-DATA-001 | 数据清理验证 | P0 | ✅ | 作为TC-VISITOR-007/008/009的teardown步骤，确保不留脏数据 |

## 2. PageObject 拆分方案

```
Page 类及职责：
- VisitorPage: 访客管理列表页，负责搜索、表格数据读取、分页操作。
- VisitorAddEditDialog: 新增/编辑访客弹窗，负责表单填写、提交、取消。
- VisitorViewDialog: 查看访客详情弹窗，负责读取详情数据。
- ConfirmDeleteDialog: 通用确认删除弹窗，负责点击“确认”或“取消”。
- VisitorImportDialog: 批量导入弹窗，负责文件上传和导入操作（如需自动化）。
```

## 3. 公共组件复用分析

| 操作 | 复用组件/方法 | 说明 |
|------|-------------|------|
| 点击搜索/重置/新增/编辑等按钮 | `BasePage.safe_click(locator)` | 直接复用，定位器由 `VisitorPage` 提供 |
| 输入文本（姓名、手机号） | `BasePage.safe_input(locator, value)` | 直接复用 |
| 选择 `el-select` 选项（状态） | `ElementPlusHelper.select_el_option(locator, option_text)` | 复用公共方法，处理Element Plus下拉框 |
| 选择日期范围 | `ElementPlusHelper.pick_date_range(locator, start_date, end_date)` | 复用公共方法，处理Element Plus日期选择器 |
| 等待表格加载完成 | `BasePage.wait_for_element_visible(locator)` + `ElementPlusHelper.wait_for_table_loaded()` | 先等待表格可见，再等待表格加载动画完成 |
| 获取表格行数据 | `ElementPlusHelper.get_table_all_rows(locator, timeout)` | 复用公共方法，获取整个表格数据 |
| 获取表格行操作按钮 | `ElementPlusHelper.get_action_button_in_row(table_locator, row_index, button_text)` | 复用公共方法，根据行索引和按钮文字定位操作列按钮 |
| 操作弹窗 | `ElementPlusHelper.wait_for_dialog_visible()` / `wait_for_dialog_close()` | 复用公共方法，等待弹窗出现或关闭 |
| 处理确认弹窗 | `ElementPlusHelper.confirm_dialog(locator)` | 复用公共方法，点击“确认”或“取消” |
| 等待并获取 Toast 消息 | `ElementPlusHelper.get_toast_message(timeout)` | 复用公共方法，获取操作成功或失败的提示信息 |

## 4. 等待策略建议

| 场景 | 等待方式 | 说明 |
|------|---------|------|
| 页面初次加载 | `BasePage.wait_for_element_visible(locator_table)` 等待表格可见 | 确保核心内容渲染完成 |
| 执行搜索后 | `ElementPlusHelper.wait_for_table_loaded()` 等待表格加载动画消失 | 表格会显示加载遮罩，需等待其消失 |
| 新增/编辑/删除操作后 | `ElementPlusHelper.wait_for_dialog_close()` + `ElementPlusHelper.get_toast_message()` | 等待弹窗关闭并获取提示信息 |
| 点击表格中的操作按钮 | 无需额外等待，`safe_click` 自带隐式等待 | 按钮在表格渲染后立即可见 |

## 5. ROI 分析

- **预估开发时间**: 8 小时（`VisitorPage` 2h，`VisitorAddEditDialog` 2h，`VisitorViewDialog` 1h，`ConfirmDeleteDialog` 0.5h，测试脚本 2.5h）
- **预估维护成本**: 0.5 小时/月（页面布局和元素非常稳定，主要维护成本来自测试数据生成策略变化）
- **手工执行时间**: 15 分钟/次（覆盖 P0 + P1 核心用例）
- **每月手工执行频率**: 10 次（按项目迭代节奏估算）

**ROI 计算**:
> 月度收益 = (手工执行时间/次 × 执行频率) - (开发成本 / 回收周期) - (维护成本 / 月)
> = (15 分钟/次 × 10 次) - (8 小时 × 60 分钟/小时 / 6 个月) - (0.5 小时 × 60 分钟)
> = 150 分钟 - 80 分钟 - 30 分钟
> = **40 分钟/月**

**结论**: 自动化收益为正，约6个月可收回开发成本。考虑到 P0 用例的稳定性和 P1 用例的高回归价值，**强烈建议自动化**。

---

## 6. 风险项

- **批量导入 (TC-VISITOR-011)**：涉及文件上传和异步处理，自动化稳定性较差，且为一次性操作，不建议自动化。
- **导出 (TC-VISITOR-010)**：浏览器下载行为不易模拟和断言，自动化价值低，不建议自动化。
- **表格操作列按钮**: 例如 `row_action_force_logout` 仅在特定状态下展示，自动化用例需考虑状态前置条件。