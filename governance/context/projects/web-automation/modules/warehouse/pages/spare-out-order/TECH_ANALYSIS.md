# 技术分析: 备品出库 (Spare Out Order)

## 1. 分析概述

- **目标页面**: 备品出库 (Spare Out Order)
- **技术栈**: Vue 3 + Element Plus
- **PO 类**: `SpareOutOrderPage` (继承 `BasePage`)
- **测试框架**: Selenium 4.15.2 + pytest 7.4.4
- **数据来源**: 基于 PO 代码 (`page/warehouse_page/SpareOutOrderPage.py`) 和测试脚本 (`script/warehouse/test_spare_out_order.py`) 分析

## 2. Element Plus 组件识别

| 组件名称 | 用途说明 | 布局区域 |
|----------|----------|----------|
| `el-input` | 经办人搜索输入框、弹窗内表单输入 | 搜索区, 弹窗 |
| `el-date-picker` | 日期选择搜索 | 搜索区 |
| `el-button` | 查询/重置/新增/备件查询/查看/LY 单号链接 | 搜索区, 工具栏, 表格行内 |
| `el-table` | 展示备品出库列表 | 表格区 |
| `el-table-column` | 定义表格列，包括 LY 单号列 | 表格区 |
| `el-tag` | 备品状态标签（中置信度，无直接证据） | 表格区 |
| `el-pagination` | 分页组件 | 表格底部 |
| `el-dialog` | 新增弹窗、查看详情弹窗 | 弹窗层 |
| `el-form` | 弹窗内表单容器 | 弹窗内 |
| `el-message-box` | 删除确认弹窗 | 弹窗层 |

## 3. 假设 DOM 结构

```html
<!-- 页面主容器 -->
<div id="app">
  <!-- 导航栏 -->
  <nav>...</nav>

  <!-- 主内容区 -->
  <div class="main-content">
    <!-- 面包屑 -->
    <div class="breadcrumb">库管管理 / 备品备件管理 / 出库</div>

    <!-- 搜索区 -->
    <div class="search-area">
      <el-form>
        <el-form-item>
          <el-input placeholder="请输入经办人" />
        </el-form-item>
        <el-form-item>
          <el-date-picker placeholder="选择日期" />
        </el-form-item>
        <el-form-item>
          <el-button>查询</el-button>
          <el-button>重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <el-button>新增</el-button>
      <el-button>备件查询</el-button>
    </div>

    <!-- 表格 -->
    <el-table>
      <el-table-column prop="lyNumber" label="LY单号">
        <!-- 自定义渲染: el-button is-link -->
        <template #default="{ row }">
          <el-button type="primary" link>{{ row.lyNumber }}</el-button>
        </template>
      </el-table-column>
      <!-- 其他列: 经办人/日期/状态/数量/... -->
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button type="primary" link>查看</el-button>
          <!-- 删除通过 click_row_button 通用方法定位 -->
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination :total="total" />

    <!-- 新增弹窗 (Teleport 到 body) -->
    <el-dialog title="新增备品出库" v-model="dialogVisible">
      <el-form>
        <el-form-item label="经办人">
          <el-input placeholder="经办人" />
        </el-form-item>
        <!-- 其他表单字段 -->
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
| `//input[@placeholder="请输入经办人"]` | placeholder 文本 | 高 | `FILTER_HANDLER` | placeholder 文本在 Element Plus 中稳定 |
| `//input[@placeholder="选择日期"]` | placeholder 文本 | 高 | `FILTER_DATE` | 同上 |
| `//button[contains(.,"查询")]` | 按钮文本 | 高 | `BTN_QUERY` | 文本定位，但多查询按钮场景需注意作用域 |
| `//button[contains(.,"重置")]` | 按钮文本 | 高 | `BTN_RESET` | 同上 |
| `//button[contains(.,"新增")]` | 按钮文本 | 高 | `BTN_ADD` | 同上 |
| `//button[contains(.,"备件查询")]` | 按钮文本 | 高 | `BTN_SPARE_QUERY` | 同上 |
| `//button[contains(.,"查看")]` | 按钮文本 | 高 | `BTN_VIEW` | 同上 |
| `//button[contains(.,"{ly_number}")]` | 动态文本 | 中 | （动态构造） | 依赖 LY 单号文本内容，运行时动态拼装 |

### B 级定位器（通用但有一定风险）

| Locator | 策略 | 稳定性 | 来源 | 备注 |
|---------|------|--------|------|------|
| `.el-table__body-wrapper tbody tr.el-table__row` | CSS class | 高 | `BasePage.TABLE_ROWS` | Element Plus 标准 |
| `.el-dialog:not([style*="display: none"])` | CSS class + 可见性过滤 | 中 | `BasePage.DIALOG` | 多弹窗叠加时需注意 |
| `.el-pagination__total` | CSS class | 高 | `BasePage.TOTAL_COUNT` | 分页总数字段 |

### C 级定位器（动态/脆弱）

本页面无 C 级定位器。所有 locator 均基于文本或 stable class。

## 5. Vue 异步等待策略

| 场景 | 等待方法 | 说明 |
|------|----------|------|
| 页面导航 | `navigate()` -> `_wait_page_ready()` -> `wait_vue_stable()` + `_wait_loading_gone()` | 页面加载完成 |
| 搜索 | `search_by_handler()` -> `input_text` -> click BTN_QUERY -> `wait_vue_stable()` | 等待搜索完成 |
| 重置 | `reset_search()` -> click BTN_RESET -> `wait_vue_stable()` | 等待重置完成 |
| 新增弹窗打开 | `click_add()` -> click BTN_ADD -> `wait_dialog_open()` | 等待 el-dialog 可见 |
| 查看弹窗打开 | `click_view_first()` -> click BTN_VIEW -> `wait_dialog_open()` | 同上 |
| 弹窗关闭（保存） | `click_dialog_save()` -> `wait_vue_stable()` | BasePage 实现 |
| 弹窗关闭（取消） | `click_dialog_cancel()` -> `wait_vue_stable()` | BasePage 实现 |
| 删除确认 | `delete_by_handler()` -> click 删除 -> `confirm_message_box()` | 等待 MessageBox 确认 |
| 备件查询导航 | `click_spare_query()` -> click BTN_SPARE_QUERY -> `wait_vue_stable()` | 页面间导航 |
| LY 链接点击 | `click_ly_link()` -> click button -> （无显式等待） | 注意：无等待，依赖 Selenium 默认隐式等待 |

## 6. 自动化风险点

| 风险点 | 说明 | 影响 | 应对措施 |
|--------|------|------|----------|
| **多弹窗叠加** | 新增弹窗和可能的前置弹窗同时存在时，`_fill_dialog_by_placeholder` 遍历所有 `.el-dialog` 可能误填入错误的弹窗 | 表单数据填充到错误弹窗 | JS 脚本中已过滤 `offsetParent === null`（即隐藏弹窗），但多个可见弹窗时仍可能出错 |
| **Teleport 渲染** | `el-dialog` 默认 Teleport 到 `<body>` 下，使用 `wait_dialog_open()` 时需确认定位到正确的 dialog | 弹窗无法正确定位 | BasePage 的 DIALOG 和 DIALOG_SAVE 已处理 display:none 过滤 |
| **JS fill 无 fallback** | `_fill_dialog_by_placeholder` 未匹配 placeholder 仅打印警告，不抛出异常，测试可能静默通过但实际未填写 | 表单提交时必填校验失败或空数据 | 测试中 `fill_out_order_handler` 后无校验，依赖后续步骤验证；建议增加填写后校验 |
| **LY 单号链接定位** | 使用 `//button[contains(.,"{ly_number}")]` 全局定位，若 LY 单号不唯一可能点击错误，若数据不包含 LY 链接则跳过测试 | 测试跳过或点击错误行 | `test_ly_link_clickable` 已有跳过逻辑；建议增加精确行内定位 |
| **备件查询页面导航** | `click_spare_query` 导航到其他页面后测试无返回逻辑，后续测试可能因页面状态不一致失败 | 测试链断裂 | 当前测试中 `test_spare_query_clickable` 是独立最后一个交互测试 |
| **删除确认框** | 删除操作依赖 `confirm_message_box()`，若确认框渲染延迟或样式异常可能导致点击失败 | 删除失败 | BasePage 已实现等待逻辑 |
| **空数据状态** | 新增时若表格无数据行，`get_total_count()` 可能返回 0，`test_add_out_order_success` 的 `after >= before + 1` 断言覆盖 | 空表新增测试通过 | 正常 |
| **日期筛选未测试** | `FILTER_DATE` 定义了日期筛选 locator，但测试中未覆盖日期搜索 | 日期搜索功能无自动化覆盖 | 需补充测试用例 |
| **备件查询无返回** | 点击备件查询后页面跳转，无返回导航逻辑 | 单次执行后页面状态改变 | 建议使用 fixture 的 setup 确保每次测试独立 |

## 7. `_fill_dialog_by_placeholder` JS 模式分析

该模式在 spare-out-order 和 spare-requisition 中使用的是**无 fallback 变体**:

```javascript
// 相同实现，共用特征
var dlgs = document.querySelectorAll('.el-dialog');
for (var i = 0; i < dlgs.length; i++) {
    if (dlgs[i].offsetParent === null) continue;  // 过滤隐藏弹窗
    var inputs = dlgs[i].querySelectorAll('input:not([type="hidden"])');
    for (var j = 0; j < inputs.length; j++) {
        var ph = inputs[j].getAttribute('placeholder') || '';
        if (ph.indexOf(placeholder) >= 0) {
            inputs[j].focus();
            inputs[j].value = '';
            inputs[j].value = value;
            inputs[j].dispatchEvent(new Event('input', {bubbles: true}));
            inputs[j].dispatchEvent(new Event('change', {bubbles: true}));
            return ph;
        }
    }
}
return '';
```

**特征**:
- 无 Selenium 层面的鼠标/键盘事件，直接通过 JS 操作 DOM
- `dispatchEvent` 触发 Vue 的 `v-model` 响应（依赖 `input`/`change` 事件）
- 无 fallback：未找到匹配 input 时仅返回空字符串，不抛出异常
- PO 层调用 `logger.warning` 但未中断流程

**与有 fallback 变体的区别**: 其他页面（如部分 system 模块）的 `_fill_dialog_by_placeholder` 在 JS 失败后使用 Selenium `input_text` 作为 fallback。本页面仅使用纯 JS 方式，无 fallback。
