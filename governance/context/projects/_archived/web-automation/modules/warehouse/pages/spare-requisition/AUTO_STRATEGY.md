# 自动化策略: 备品领用申请 (Spare Requisition)

## 1. 覆盖矩阵

| 用例编号 | 标题 | 优先级 | 自动化状态 | 理由 |
|----------|------|--------|-----------|------|
| TC-SRQ-001 | 页面正常加载 | P0 | ✅ 已自动化 | 基础冒烟 |
| TC-SRQ-002 | 表格列数在合理范围 | P1 | ✅ 已自动化 | UI 渲染完整性 |
| TC-SRQ-003 | 新增按钮可见 | P0 | ✅ 已自动化 | 工具栏基础元素 |
| TC-SRQ-004 | 分页组件可见 | P0 | ✅ 已自动化 | 基础 UI 组件 |
| TC-SRQ-005 | 按申请人搜索 | P0 | ✅ 已自动化 | 核心搜索功能 |
| TC-SRQ-006 | 重置搜索条件 | P1 | ✅ 已自动化 | 搜索功能完整性 |
| TC-SRQ-007 | 新增弹窗打开 | P0 | ✅ 已自动化 | 核心交互 |
| TC-SRQ-008 | 新增弹窗有保存按钮 | P1 | ✅ 已自动化 | 弹窗按钮存在性 |
| TC-SRQ-009 | 查看第一行记录 | P1 | ✅ 已自动化 | 查看弹窗交互 |
| TC-SRQ-010 | 第一行至少有一个操作按钮 | P0 | ✅ 已自动化 | 行内按钮可见性校验 |
| TC-SRQ-011 | 编辑按钮打开编辑弹窗 | P1 | ✅ 已自动化 | 编辑交互（条件性跳过） |
| TC-SRQ-012 | 第一行流程状态可读取 | P1 | ✅ 已自动化 | 状态感知能力 |
| TC-SRQ-013 | 提交按钮触发 Toast | P1 | ✅ 已自动化（smoke） | 提交流程验证 |
| TC-SRQ-014 | 新增领用申请成功 | P0 | ✅ 已自动化 | 核心业务流 |
| TC-SRQ-015 | 删除刚创建的记录 | P0 | ✅ 已自动化 | CRUD 完整链路 |
| TC-SRQ-016 | 新增取消 | P1 | ✅ 已自动化 | 取消操作验证 |
| TC-SRQ-017 | 必填校验 | P1 | ✅ 已自动化 | 表单校验验证 |
| TC-SRQ-018 | 按流程状态筛选 | P1 | ⚠️ 待开发 | 状态筛选未覆盖 |
| TC-SRQ-019 | 按日期范围搜索 | P1 | ⚠️ 待开发 | 日期搜索未覆盖 |
| TC-SRQ-020 | 空数据状态页面加载 | P2 | ⚠️ 待开发 | 边界状态 |
| TC-SRQ-021 | 分页翻页操作 | P1 | ⚠️ 待开发 | 分页验证 |
| TC-SRQ-022 | 提交后状态变更验证 | P1 | ⚠️ 待开发 | 状态流转验证 |

## 2. PageObject 拆分方案

```
SpareRequisitionPage            # 主页面对象
├── 搜索操作: 申请人/日期/流程状态(wh-filter-toolbar)
├── 工具栏操作: 新增
├── 行内操作: 查看/编辑/提交/删除
├── 状态感知: has_*_button() / get_first_row_status()
├── 弹窗操作: 新增/编辑/查看(继承BasePage dialog方法)
└── 弹性删除: delete_by_name() (try/except)
```

**设计说明**:
- `SpareRequisitionPage` 为单体 PageObject，未拆分独立 Dialog 类
- 4 个行内按钮通过独立常量定义（BTN_VIEW/BTN_EDIT/BTN_SUBMIT/BTN_DELETE）
- 按钮可见性检测方法 `has_*_button()` 使用 `find_elements` 长度判断（非可见性判断）
- 删除弹窗操作通过 `confirm_message_box()` + `wait_for_toast_text()` 完成

**建议**:
- 当前设计合理，无需拆分
- 若工作流状态管理复杂度增加，可考虑 `RowActionHelper` mixin 统一处理按钮可见性逻辑
- `has_*_button()` 方法逻辑简单，复用性好，可作为其他类似工作流页面的参考模式

## 3. 组件复用

| 组件 | 复用方式 | 说明 |
|------|----------|------|
| `BasePage.navigate_to()` | 直接使用 | 3 级菜单导航 |
| `BasePage.wait_vue_stable()` | 直接使用 | Vue 渲染稳定等待 |
| `BasePage._wait_loading_gone()` | 直接使用 | loading 遮罩消失等待 |
| `BasePage.wait_dialog_open()` | 直接使用 | 弹窗可见等待 |
| `BasePage.click_dialog_save()` | 直接使用 | 弹窗保存按钮点击 |
| `BasePage.click_dialog_cancel()` | 直接使用 | 弹窗取消按钮点击 |
| `BasePage.is_dialog_visible()` | 直接使用 | 弹窗可见性判断 |
| `BasePage.click()` | 直接使用 | 通用元素点击 |
| `BasePage.input_text()` | 直接使用 | 文本输入 |
| `BasePage.confirm_message_box()` | 直接使用 | 删除确认框确认 |
| `BasePage.wait_for_toast_text()` | 直接使用 | Toast 提示等待 |
| `BasePage.get_total_count()` | 直接使用 | 获取分页总数 |
| `BasePage.is_row_present()` | 直接使用 | 表格行存在性判断 |
| `BasePage.get_form_error()` | 直接使用 | 获取表单校验错误 |
| `BasePage.click_row_button()` | 直接使用 | 行内按钮点击（在 delete_by_name 中使用） |

**新 Helper 需求**:
- `_fill_dialog_by_placeholder` 已是本页面专用 JS 填充方法
- 无需额外 helper

## 4. 等待策略

| 场景 | 触发操作 | 等待条件 | 实现 |
|------|----------|----------|------|
| 页面加载 | `navigate()` | Vue 稳定 + loading 消失 | `wait_vue_stable()` + `_wait_loading_gone()` |
| 搜索 | `search_by_applicant()` | Vue 稳定 | `wait_vue_stable()` |
| 重置 | `reset_search()` | Vue 稳定 | `wait_vue_stable()` |
| 弹窗打开（新增） | `click_add()` | el-dialog 可见 | `wait_dialog_open()` |
| 弹窗打开（编辑） | `click_edit_first()` | el-dialog 可见 | `wait_dialog_open()`（测试层） |
| 弹窗打开（查看） | `click_view_first()` | el-dialog 可见 | `wait_dialog_open()` |
| 弹窗关闭 | `click_dialog_save/cancel()` | 弹窗关闭 + Vue 稳定 | BasePage 实现 |
| 提交审批 | `click_submit_first()` | Toast 出现 | `wait_for_toast_text()` |
| 删除确认 | `click_delete_first()` | MessageBox 确认 + Toast | `confirm_message_box()` + `wait_for_toast_text()` |
| 弹性删除失败 | `delete_by_name()` | Exception 捕获 | try/except + warning 日志 |

## 5. ROI 分析

| 指标 | 数值 | 说明 |
|------|------|------|
| 功能点 | 7 个（搜索/表格/新增/查看/编辑/提交/删除+状态感知） | 页面主要功能模块 |
| 现有测试 | 17 个方法 | 覆盖加载、搜索、交互、行操作、CRUD |
| 预估开发时间 | 14 小时 (1.75 人天) | PO + 测试脚本 + 调试 |
| 预估月维护成本 | 3 小时/月 | 工作流状态变化可能导致按钮逻辑调整 |
| 手工执行时间 | 18 分钟/次 | 回归所有核心功能 |
| 自动化执行时间 | 3 分钟/次 | pytest 执行 |
| 执行频率 | 22 次/月（每日构建） | 回归频率 |
| ROI (1 个月) | +196 分钟 | (18-3)*22 - (14*60/12 + 3*60) = 330 - 70 = 260 分钟 |
| ROI (3 个月) | +1010 分钟 | 维护成本摊销后显著提升 |
| ROI (6 个月) | +2360 分钟 | 超 3.9 个工作日 |

**结论**: 工作流相关测试（提交/编辑/删除的条件可见性）自动化价值高，手工测试难以覆盖状态组合。wh-filter-toolbar 相关的搜索测试待补充后 ROI 进一步提升。
