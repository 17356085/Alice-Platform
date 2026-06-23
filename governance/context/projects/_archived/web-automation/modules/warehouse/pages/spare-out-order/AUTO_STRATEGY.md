# 自动化策略: 备品出库 (Spare Out Order)

## 1. 覆盖矩阵

| 用例编号 | 标题 | 优先级 | 自动化状态 | 理由 |
|----------|------|--------|-----------|------|
| TC-SOO-001 | 页面正常加载 | P0 | ✅ 已自动化 | 基础冒烟，所有回归的起点 |
| TC-SOO-002 | 表格列数在合理范围 | P1 | ✅ 已自动化 | 验证 UI 渲染完整性 |
| TC-SOO-003 | 分页组件可见 | P0 | ✅ 已自动化 | 基础 UI 组件 |
| TC-SOO-004 | 新增按钮可见 | P0 | ✅ 已自动化 | 工具栏基础元素 |
| TC-SOO-005 | 备件查询按钮可见 | P1 | ✅ 已自动化 | 特殊导航按钮 |
| TC-SOO-006 | 按经办人搜索 | P0 | ✅ 已自动化 | 核心搜索功能 |
| TC-SOO-007 | 重置搜索条件 | P1 | ✅ 已自动化 | 搜索功能完整性 |
| TC-SOO-008 | 新增弹窗打开 | P0 | ✅ 已自动化 | 核心交互 |
| TC-SOO-009 | 新增弹窗有表单输入项 | P1 | ✅ 已自动化 | 弹窗表单完整性 |
| TC-SOO-010 | LY 单号链接可点击 | P1 | ✅ 已自动化（smoke） | 特殊交互，数据依赖 |
| TC-SOO-011 | 备件查询按钮导航 | P1 | ✅ 已自动化（smoke） | 跨页面导航 |
| TC-SOO-012 | 查看第一行记录 | P1 | ✅ 已自动化 | 查看弹窗交互 |
| TC-SOO-013 | 新增出库成功 | P0 | ✅ 已自动化 | 核心业务流 |
| TC-SOO-014 | 删除刚创建的记录 | P0 | ✅ 已自动化 | CRUD 完整链路 |
| TC-SOO-015 | 新增出库取消 | P1 | ✅ 已自动化 | 取消操作验证 |
| TC-SOO-016 | 必填校验 | P1 | ✅ 已自动化 | 表单校验验证 |
| TC-SOO-017 | 按日期搜索 | P1 | ⚠️ 待开发 | 日期搜索未覆盖 |
| TC-SOO-018 | 空数据状态页面加载 | P2 | ⚠️ 待开发 | 边界状态验证 |
| TC-SOO-019 | 分页翻页操作 | P1 | ⚠️ 待开发 | 分页功能完整验证 |
| TC-SOO-020 | 重置后搜索条件清空验证 | P1 | ⚠️ 待开发 | 重置功能完整验证 |

## 2. PageObject 拆分方案

```
SpareOutOrderPage              # 主页面对象
├── 搜索操作: 经办人/日期
├── 工具栏操作: 新增/备件查询
├── 行内操作: 查看/删除(通过click_row_button)
├── 特殊操作: LY单号链接点击
└── 弹窗操作: 新增/查看(继承BasePage dialog方法)
```

**设计说明**:
- `SpareOutOrderPage` 为单体 PageObject，未拆分独立 Dialog 类
- 新增弹窗操作通过 `_fill_dialog_by_placeholder` + `click_dialog_save/cancel` 完成
- LY 单号链接操作通过动态 XPath 构造
- 删除操作通过 `BasePage.click_row_button` 通用方法按文本定位，无独立 locator

**建议**:
- 当前设计合理，无需拆分
- 若新增弹窗复杂度增加（如多字段、el-select、el-tree），可考虑抽取 `SpareOutOrderDialog`

## 3. 组件复用

| 组件 | 复用方式 | 说明 |
|------|----------|------|
| `BasePage.navigate_to()` | 直接使用 | 3 级菜单导航 |
| `BasePage.wait_vue_stable()` | 直接使用 | Vue 渲染稳定等待 |
| `BasePage._wait_loading_gone()` | 直接使用 | loading 遮罩消失等待 |
| `BasePage.wait_dialog_open()` | 直接使用 | 弹窗可见等待 |
| `BasePage.click_dialog_save()` | 直接使用 | 弹窗内保存按钮点击 |
| `BasePage.click_dialog_cancel()` | 直接使用 | 弹窗内取消按钮点击 |
| `BasePage.is_dialog_visible()` | 直接使用 | 弹窗可见性判断 |
| `BasePage.click()` | 直接使用 | 通用元素点击 |
| `BasePage.input_text()` | 直接使用 | 文本输入 |
| `BasePage.confirm_message_box()` | 直接使用 | 删除确认框确认 |
| `BasePage.get_total_count()` | 直接使用 | 获取分页总数 |
| `BasePage.is_row_present()` | 直接使用 | 表格行存在性判断 |
| `BasePage.get_form_error()` | 直接使用 | 获取表单校验错误 |
| `BasePage.click_row_button()` | 直接使用 | 行内按钮点击 |

**新 Helper 需求**:
- `_fill_dialog_by_placeholder` 已是本页面专用 JS 填充方法
- 无需额外 helper

## 4. 等待策略

| 场景 | 触发操作 | 等待条件 | 实现 |
|------|----------|----------|------|
| 页面加载 | `navigate()` | Vue 稳定 + loading 消失 | `wait_vue_stable()` + `_wait_loading_gone()` |
| 搜索 | `search_by_handler()` | Vue 稳定 | `wait_vue_stable()` |
| 重置 | `reset_search()` | Vue 稳定 | `wait_vue_stable()` |
| 弹窗打开（新增） | `click_add()` | el-dialog 可见 | `wait_dialog_open()` |
| 弹窗打开（查看） | `click_view_first()` | el-dialog 可见 | `wait_dialog_open()` |
| 弹窗关闭 | `click_dialog_save/cancel()` | 弹窗关闭 + Vue 稳定 | BasePage 实现 |
| 删除确认 | `confirm_message_box()` | MessageBox 可见并确认 | BasePage 实现 |
| LY 链接点击 | `click_ly_link()` | (无显式等待) | 依赖隐式等待，风险点 |
| 备件查询导航 | `click_spare_query()` | Vue 稳定 | `wait_vue_stable()` |

## 5. ROI 分析

| 指标 | 数值 | 说明 |
|------|------|------|
| 功能点 | 6 个（搜索/表格/新增/LY链接/查询导航/CRUD） | 页面主要功能模块 |
| 现有测试 | 16 个方法 | 覆盖页面加载、搜索、交互、CRUD |
| 预估开发时间 | 12 小时 (1.5 人天) | PO + 测试脚本 + 调试 |
| 预估月维护成本 | 2 小时/月 | 页面结构相对稳定 |
| 手工执行时间 | 15 分钟/次 | 回归所有核心功能 |
| 自动化执行时间 | 2 分钟/次 | pytest 执行 |
| 执行频率 | 22 次/月（每日构建） | 回归频率 |
| ROI (1 个月) | +266 分钟 | (15-2)*22 - (12*60/12 + 2*60) = 286 - 60 = 226 分钟 |
| ROI (3 个月) | +978 分钟 | 维护成本摊销后显著提升 |
| ROI (6 个月) | +2456 分钟 | 超 4 个工作日 |

**结论**: 自动化投入在 1 个月内即可回本，P0 核心功能（新增/搜索/CRUD）自动化价值极高。
