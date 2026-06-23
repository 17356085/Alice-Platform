# Technical Analysis: spare-in-order (备品入库)

## 1. Element Plus Component Identification

| 组件 | Element Plus 类型 | 使用场景 | 来源 |
|------|-------------------|----------|------|
| 搜索输入框 | `el-input` | 经办人搜索过滤 | PO定位器 `//input[@placeholder="请输入经办人"]` |
| 日期选择器 | `el-date-picker` | 日期搜索过滤 | PO定位器 `//input[@placeholder="选择日期"]` |
| 查询按钮 | `el-button` | 提交搜索 | PO定位器 `//button[contains(.,"查询")]` |
| 重置按钮 | `el-button` | 清除搜索条件 | PO定位器 `//button[contains(.,"重置")]` |
| 新增入库按钮 | `el-button` | 打开新增对话框 | PO定位器 `//button[contains(.,"新增入库")]` |
| 查看按钮 | `el-button` | 查看记录详情 | PO定位器 `//button[contains(.,"查看")]` |
| 对话框 | `el-dialog` | 新增入库表单 | 方法名 `click_add` 推断 |
| 对话框输入框 | `el-input` | 经办人录入 | PO定位器 `//input[@placeholder="经办人"]` |
| 表格 | `el-table` | 入库单列表展示 | `is_row_present`, `test_columns_count` 推断 |
| 分页 | `el-pagination` | 表格分页 | 测试 `test_pagination_visible` 推断 |

---

## 2. Hypothetical DOM Structure

```vue
<template>
  <div class="spare-in-order-page">
    <!-- Search Bar -->
    <el-form :inline="true" class="search-form">
      <el-form-item label="经办人">
        <el-input
          v-model="searchForm.handler"
          placeholder="请输入经办人"
          clearable
        />
      </el-form-item>
      <el-form-item label="日期">
        <el-date-picker
          v-model="searchForm.date"
          type="date"
          placeholder="选择日期"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleQuery">查询</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- Toolbar -->
    <div class="table-toolbar">
      <el-button type="primary" @click="openAddDialog">新增入库</el-button>
    </div>

    <!-- Table (8 columns) -->
    <el-table :data="tableData" v-loading="loading">
      <el-table-column prop="inOrderNo" label="入库单号" />
      <el-table-column prop="spareName" label="备件名称" />
      <el-table-column prop="spec" label="规格型号" />
      <el-table-column prop="quantity" label="数量" />
      <el-table-column prop="handler" label="经办人" />
      <el-table-column prop="inDate" label="入库日期" />
      <el-table-column prop="status" label="状态" />
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button type="text" @click="handleView(row)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Pagination -->
    <el-pagination
      v-show="total > 0"
      :total="total"
      v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize"
    />

    <!-- Add In Order Dialog -->
    <el-dialog title="新增入库单" v-model="dialogVisible">
      <el-form :model="form" :rules="rules" ref="formRef">
        <el-form-item label="经办人" prop="handler">
          <el-input
            v-model="form.handler"
            placeholder="经办人"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cancelAdd">取消</el-button>
        <el-button type="primary" @click="submitAdd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
```

> Note: Column fields beyond those specified are hypothetical based on typical spare-parts in-order table layouts. The actual column structure may differ. Known: 8 columns, 6 <= headers <= 12.

---

## 3. Locator Design & Stability Assessment

| 定位器 | 策略 | XPath | 稳定性层级 | 风险说明 |
|--------|------|-------|-----------|----------|
| `FILTER_HANDLER` | Placeholder XPath | `//input[@placeholder="请输入经办人"]` | A | placeholder属性稳定 |
| `FILTER_DATE` | Placeholder XPath | `//input[@placeholder="选择日期"]` | A | placeholder属性稳定 |
| `BTN_QUERY` | 文本包含 | `//button[contains(.,"查询")]` | A | 按钮文本固定 |
| `BTN_RESET` | 文本包含 | `//button[contains(.,"重置")]` | A | 按钮文本固定 |
| `BTN_ADD` | 文本包含 | `//button[contains(.,"新增入库")]` | A | 文本"新增入库"足够唯一 |
| `BTN_VIEW` | 文本包含 | `//button[contains(.,"查看")]` | B | 多个"查看"可能共存（表格每行都有） |

**稳定性层级定义:**
- **A级 (稳定)**: 基于placeholder、固定长文本，几乎不变
- **B级 (较稳定)**: 文本包含匹配，需注意唯一性（如每行一个"查看"）
- **C级 (不稳定)**: 依赖层级索引，易重构失效（此页面无C级）

---

## 4. Vue Async Wait Strategies

| 场景 | 等待策略 | 依据 |
|------|----------|------|
| 页面导航加载 | 等待 `el-table` 数据加载结束 | 通用el-table加载模式 |
| 搜索查询 | 点击查询后等待 `loading` 消失或表格数据刷新 | 查询触发异步刷新 |
| 重置搜索 | 点击重置后等待输入框清空、表格返回初始数据 | 重置清空条件 |
| 日期选择器操作 | 等待日期面板动画完成后再取值 | el-date-picker 弹出/关闭动画 |
| 新增对话框打开 | 等待 `el-dialog` visible，检测对话框DOM | el-dialog 过渡动画 |
| 对话框填写 | `_fill_dialog_by_placeholder` 使用JS直接设置值 | 绕过输入动画和事件链 |
| 表单提交 | 提交后等待表格数据刷新 | 异步提交返回 |
| 删除操作 | 触发删除后等待表格重新渲染 | 异步删除 |
| 取消操作 | 等待对话框关闭动画结束 | el-dialog 关闭过渡（~300ms） |
| 查看操作 | 等待详情弹窗/抽屉打开 | `click_view_first` 触发查看 |

**推荐使用:** `WebDriverWait` + `expected_conditions`，结合表格 `loading` 状态判断

---

## 5. Automation Risk Points

### 5.1 `_fill_dialog_by_placeholder` Anti-Fragile Pattern

The PO uses a custom JS helper `_fill_dialog_by_placeholder(placeholder_contains, value)` for dialog input:

```
流程: find visible dialog input by placeholder → JS set value → dispatch events
降级: 若placeholder不匹配 → 回退到第一个可见 dialog input
```

**与 reagent-fill 的关键区别:**
- **spare-in-order 有降级策略**: 当 placeholder 匹配失败时，自动回退到第一个可见输入框
- **reagent-fill 无降级**: placeholder 匹配失败直接失败

**优势:**
- 绕过 `el-input` 复杂事件触发链
- 降级策略增加容错性
- 不受 `v-model` 实现变更影响

**风险:**
- 降级策略可能填错字段（如果dialog有多个输入框但placeholder不唯一）
- 依赖对话框可见性

### 5.2 Teleport/Portal 渲染

- `el-dialog` 默认使用 Teleport 渲染到 `body` 下
- `_fill_dialog_by_placeholder` 搜索全局可见输入框，不受 Teleport 影响
- `el-date-picker` 的面板同样使用 Teleport，日期选择定位器在 panel 中

### 5.3 动态数据影响

- 测试数据使用 `AUTO_IN_{timestamp}` 确保唯一性
- `search_by_handler` 配合精确匹配定位目标行
- `CREATED_HANDLER` 类变量跨测试共享创建的数据标识
- `delete_by_handler` 按经办人删除而非按索引

### 5.4 v-if / v-show 条件渲染

- 分页组件 `v-show="total > 0"` 在无数据时隐藏
- 审批状态字段可能使用条件渲染不同标签样式
- 空表格状态需处理

### 5.5 el-input-number / el-switch

- 未在当前页面PO中发现 `el-input-number` 或 `el-switch` 使用
- 无相关风险

### 5.6 多按钮冲突

- `BTN_VIEW` (`//button[contains(.,"查看")]`) 可能在表格每行出现
- `click_view_first` 需要准确命中第一行的"查看"按钮
- 建议使用 `(//button[contains(.,"查看")])[1]` 加索引定位

### 5.7 审批链影响

- 新增入库单提交后可能需审批才能生效
- 自动化测试需确认测试环境是否跳过审批，或审批自动化如何处理
- `test_columns_count` 中的状态列可能展示审批状态
