# 技术分析: 备品领用申请 (Spare Requisition)

## 1. 分析概述

- **目标页面**: 备品领用申请 (Spare Requisition)
- **技术栈**: Vue 3 + Element Plus
- **PO 类**: `SpareRequisitionPage` (继承 `BasePage`)
- **测试框架**: Selenium 4.15.2 + pytest 7.4.4
- **数据来源**: 基于 PO 代码 (`page/warehouse_page/SpareRequisitionPage.py`) 和测试脚本 (`script/warehouse/test_spare_requisition.py`) 分析

## 2. Element Plus 组件识别

| 组件名称 | 用途说明 | 布局区域 |
|----------|----------|----------|
| `el-input` | 申请人搜索输入框、弹窗内表单输入 | 搜索区, 弹窗 |
| `el-date-picker` | 日期选择搜索 | 搜索区 |
| `el-select` | 流程状态下拉筛选 | 搜索区 (在 wh-filter-toolbar 内) |
| `el-button` | 查询/重置/新增/查看/编辑/提交/删除 | 搜索区, 工具栏, 表格行内 |
| `el-table` | 展示备品领用申请列表 | 表格区 |
| `el-table-column` | 定义表格列 | 表格区 |
| `el-tag` | 流程状态标签 | 表格区（通过 `get_first_row_status` 读取 `.el-tag`） |
| `el-pagination` | 分页组件 | 表格底部 |
| `el-dialog` | 新增弹窗、编辑弹窗、查看详情弹窗 | 弹窗层 |
| `el-form` | 弹窗内表单容器 | 弹窗内 |
| `el-message-box` | 删除确认弹窗 | 弹窗层 |
| `el-message` | 操作成功/错误 Toast 提示 | 页面级 |

## 3. 假设 DOM 结构

```html
<!-- 页面主容器 -->
<div id="app">
  <nav>...</nav>
  <div class="main-content">
    <div class="breadcrumb">库管管理 / 备品备件管理 / 领用申请</div>

    <!-- 搜索区 —— 自定义 wh-filter-toolbar 组件 -->
    <div class="wh-filter-toolbar">
      <div class="filter-item">
        <el-input placeholder="请输入申请人" />
      </div>
      <div class="filter-item">
        <el-date-picker placeholder="选择日期" />
      </div>
      <div class="filter-item">
        <div class="el-select__wrapper">
          <!-- 流程状态下拉 -->
          <el-select placeholder="流程状态">
            <el-option label="全部" value="" />
            <el-option label="待提交" value="pending" />
            <el-option label="审批中" value="approving" />
            <el-option label="已通过" value="approved" />
            <el-option label="已驳回" value="rejected" />
          </el-select>
        </div>
      </div>
      <div class="filter-item">
        <el-button>查询</el-button>
        <el-button>重置</el-button>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <el-button>新增</el-button>
    </div>

    <!-- 表格 -->
    <el-table>
      <el-table-column prop="applicant" label="申请人" />
      <el-table-column prop="date" label="申请日期" />
      <!-- 流程状态列: el-tag 渲染 -->
      <el-table-column label="流程状态">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button v-if="canView" type="primary" link>查看</el-button>
          <el-button v-if="canEdit" type="primary" link>编辑</el-button>
          <el-button v-if="canSubmit" type="success">提交</el-button>
          <el-button v-if="canDelete" type="danger" link>删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination :total="total" />

    <!-- 新增/编辑弹窗 -->
    <el-dialog title="新增备品领用申请" v-model="dialogVisible">
      <el-form>
        <el-form-item label="申请人">
          <el-input placeholder="申请人" />
        </el-form-item>
        <!-- 其他字段 -->
      </el-form>
      <template #footer>
        <el-button @click="cancel">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</div>
```

## 4. Locator 设计分析

### A 级定位器（稳定，基于 placeholder/文本）

| Locator | 策略 | 稳定性 | PO 常量 | 备注 |
|---------|------|--------|---------|------|
| `//input[@placeholder="请输入申请人"]` | placeholder | 高 | `FILTER_APPLICANT` | 稳定 |
| `//input[@placeholder="选择日期"]` | placeholder | 高 | `FILTER_DATE` | 稳定 |
| `//button[contains(.,"查询")]` | 按钮文本 | 高 | `BTN_QUERY` | 多查询按钮场景需注意作用域 |
| `//button[contains(.,"重置")]` | 按钮文本 | 高 | `BTN_RESET` | 同上 |
| `//button[contains(.,"新增")]` | 按钮文本 | 高 | `BTN_ADD` | 同上 |
| `//button[contains(.,"查看")]` | 按钮文本 | 高 | `BTN_VIEW` | 同上 |
| `//button[contains(.,"编辑")]` | 按钮文本 | 高 | `BTN_EDIT` | 同上 |
| `//button[contains(.,"提交")]` | 按钮文本 | 高 | `BTN_SUBMIT` | 同上（绿色按钮，`type="success"` 中置信度）|
| `//button[contains(.,"删除")]` | 按钮文本 | 高 | `BTN_DELETE` | 同上（红色按钮，`type="danger"` 中置信度）|

### B 级定位器（通用但有一定风险）

| Locator | 策略 | 稳定性 | 来源 | 备注 |
|---------|------|--------|------|------|
| `.el-table__body-wrapper tbody tr.el-table__row` | CSS class | 高 | `BasePage.TABLE_ROWS` | Element Plus 标准 |
| `.el-dialog:not([style*="display: none"])` | CSS + 可见性 | 中 | `BasePage.DIALOG` | 多弹窗叠加需注意 |
| `.el-pagination__total` | CSS class | 高 | `BasePage.TOTAL_COUNT` | 分页总数 |
| `.el-tag` | CSS class | 高 | 无独立常量（`get_first_row_status` 内使用） | 状态标签 |

### C 级定位器（动态/脆弱）

| Locator | 策略 | 稳定性 | PO 常量 | 风险说明 |
|---------|------|--------|---------|----------|
| `(//div[contains(@class,"wh-filter-toolbar")]//div[contains(@class,"el-select__wrapper")])[1]` | XPath 索引 + 自定义 class | 低 | `FILTER_STATUS` | **高脆弱性**：依赖自定义 `wh-filter-toolbar` 容器和 `[1]` 索引；若 wh-filter-toolbar 内增加新的触发元素或调整结构，该定位器失效；`el-select__wrapper` 是 Element Plus 内部实现类可能随版本变化 |

## 5. Vue 异步等待策略

| 场景 | 等待方法 | 说明 |
|------|----------|------|
| 页面导航 | `navigate()` -> `_wait_page_ready()` -> `wait_vue_stable()` + `_wait_loading_gone()` | 页面加载完成 |
| 搜索 | `search_by_applicant()` -> input_text -> click BTN_QUERY -> `wait_vue_stable()` | 搜索等待 |
| 重置 | `reset_search()` -> click BTN_RESET -> `wait_vue_stable()` | 重置等待 |
| 新增弹窗打开 | `click_add()` -> click BTN_ADD -> `wait_dialog_open()` | 等待 el-dialog 可见 |
| 编辑弹窗打开 | `click_edit_first()` -> click BTN_EDIT -> (测试中调用 `wait_dialog_open()`) | 编辑弹窗 |
| 查看弹窗打开 | `click_view_first()` -> click BTN_VIEW -> `wait_dialog_open()` | 查看弹窗 |
| 提交审批 | `click_submit_first()` -> click BTN_SUBMIT -> `wait_for_toast_text()` | 提交后 Toast 提示 |
| 删除确认 | `click_delete_first()` -> click BTN_DELETE -> `confirm_message_box()` -> `wait_for_toast_text()` | 删除确认 + Toast |
| 弹窗保存 | `click_dialog_save()` -> `wait_vue_stable()` | BasePage 实现 |
| 弹窗取消 | `click_dialog_cancel()` -> `wait_vue_stable()` | BasePage 实现 |
| 弹性删除 | `delete_by_name()` -> 搜索 + 点击删除 + 确认，含 try/except | 已审批记录静默跳过 |

## 6. 自动化风险点

| 风险点 | 说明 | 影响 | 应对措施 |
|--------|------|------|----------|
| **wh-filter-toolbar 定位器脆弱** | `FILTER_STATUS` 使用自定义容器和索引 `[1]` 定位 | 搜索区结构变更时定位失效 | 需维护人员关注；测试中未使用该字段降低风险 |
| **JS fill 无 fallback** | `_fill_dialog_by_placeholder` 未匹配仅警告不报错 | 表单填写静默失败 | 同 spare-out-order |
| **动态按钮可见性** | 编辑/提交/删除按钮按工作流状态 v-if 条件渲染 | Selenium 定位到隐藏按钮或找不到按钮 | 使用 `has_*_button()` 预检，测试中有跳过逻辑 |
| **多弹窗叠加** | 新增弹窗打开后若存在其他弹窗，JS fill 可能填入错误弹窗 | 数据填充错误 | JS 已过滤隐藏弹窗，但多可见弹窗仍有风险 |
| **get_first_row_status 依赖行存在** | `get_first_row_status` 直接访问 `.el-table__body-wrapper` 的 `find_element(*TABLE_ROWS)` | 空表时抛出 NoSuchElementException | 测试中有前置行数检查 |
| **提交按钮类型** | 提交按钮可能是 `type="success"`（绿色）按钮，与其他按钮样式不同 | 不影响定位（基于文本） | 无定位风险 |
| **已审批记录删除异常** | `delete_by_name` 的 try/except 捕获所有异常，可能隐藏真正的 bug | 测试静默通过 | except 中记录了 warning 日志 |
| **日期/状态筛选未测试** | `FILTER_DATE` 和 `FILTER_STATUS` 定义了筛选 locator，但测试中未覆盖 | 日期/状态搜索无自动化覆盖 | 需补充测试用例 |
| **编辑弹窗无表单校验** | `test_edit_dialog_opens` 仅验证弹窗打开，未验证数据回显或编辑后保存 | 编辑功能可操作性未验证 | 中风险，建议补充 |
| **Teleport 渲染** | 弹窗和 Toast 渲染到 `<body>` 外，定位依赖 BasePage 实现 | 无额外风险 | BasePage 已处理 |

## 7. `_fill_dialog_by_placeholder` JS 模式分析

与 spare-out-order 使用相同的**无 fallback 变体**。详细分析参见 spare-out-order 的 TECH_ANALYSIS.md 对应章节。

```python
def _fill_dialog_by_placeholder(self, placeholder_contains, value):
    script = """..."""  # 与 SpareOutOrderPage 完全相同
    result = self.driver.execute_script(script, placeholder_contains, value)
    if not result:
        logger.warning("未找到 placeholder 包含 '%s' 的弹窗输入框", placeholder_contains)
    self.wait_vue_stable()
```

特征:
- 纯 JS 操作，无 Selenium 事件
- 无 fallback，未匹配仅警告
- 与 spare-out-order 的实现完全一致
