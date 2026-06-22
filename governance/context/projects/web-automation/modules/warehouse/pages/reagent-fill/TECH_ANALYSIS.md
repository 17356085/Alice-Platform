# Technical Analysis: reagent-fill (三剂消耗-装填管理)

## 1. Element Plus Component Identification

| 组件 | Element Plus 类型 | 使用场景 | 来源 |
|------|-------------------|----------|------|
| 搜索输入框 | `el-input` | 三剂名称搜索过滤 | PO定位器 `//input[@placeholder="请输入三剂名称"]` |
| 查询按钮 | `el-button` | 提交搜索 | PO定位器 `//button[contains(.,"查询")]` |
| 重置按钮 | `el-button` | 清除搜索条件 | PO定位器 `//button[contains(.,"重置")]` |
| 新增按钮 | `el-button` | 打开新增对话框 | PO定位器 `//button[contains(.,"新增")]` |
| 对话框 | `el-dialog` | 新增装填记录表单 | 方法名 `click_add` 推断 |
| 对话框输入框 | `el-input` | 三剂名称录入 | PO定位器 `//input[@placeholder="三剂名称"]` |
| 表格 | `el-table` | 数据列表展示 | 方法 `is_row_present`, `delete_item_by_name` 推断 |
| 分页 | `el-pagination` | 表格分页 | 测试 `test_pagination_visible` 推断 |

---

## 2. Hypothetical DOM Structure

```vue
<template>
  <div class="reagent-fill-page">
    <!-- Search Bar -->
    <el-form :inline="true" class="search-form">
      <el-form-item label="三剂名称">
        <el-input
          v-model="searchForm.itemName"
          placeholder="请输入三剂名称"
          clearable
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleQuery">查询</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- Toolbar -->
    <div class="table-toolbar">
      <el-button type="primary" @click="openAddDialog">新增</el-button>
    </div>

    <!-- Table -->
    <el-table :data="tableData" v-loading="loading">
      <el-table-column prop="itemName" label="三剂名称" />
      <el-table-column prop="spec" label="规格型号" />
      <el-table-column prop="quantity" label="装填数量" />
      <el-table-column prop="fillDate" label="装填日期" />
      <el-table-column prop="operator" label="操作人" />
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button type="text" @click="handleDelete(row)">删除</el-button>
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

    <!-- Add Dialog -->
    <el-dialog title="新增装填记录" v-model="dialogVisible">
      <el-form :model="form" :rules="rules" ref="formRef">
        <el-form-item label="三剂名称" prop="itemName">
          <el-input
            v-model="form.itemName"
            placeholder="三剂名称"
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

> Note: Column fields beyond 三剂名称 are hypothetical based on typical reagent-fill table layouts. The actual DOM may differ. Other columns (规格型号, 装填数量, 装填日期, 操作人) are not confirmed by PO code.

---

## 3. Locator Design & Stability Assessment

| 定位器 | 策略 | XPath | 稳定性层级 | 风险说明 |
|--------|------|-------|-----------|----------|
| `FILTER_ITEM_NAME` | Placeholder XPath | `//input[@placeholder="请输入三剂名称"]` | A | placeholder属性稳定，低变动机率 |
| `BTN_QUERY` | 文本包含 | `//button[contains(.,"查询")]` | A | 按钮文本固定 |
| `BTN_RESET` | 文本包含 | `//button[contains(.,"重置")]` | A | 按钮文本固定 |
| `BTN_ADD` | 文本包含 | `//button[contains(.,"新增")]` | B | 多个"新增"按钮可能同时存在，需确保唯一性 |

**稳定性层级定义:**
- **A级 (稳定)**: 基于placeholder、固定文本，几乎不变的定位器
- **B级 (较稳定)**: 文本包含匹配，需注意页面内唯一性
- **C级 (不稳定)**: 依赖层级结构或索引，易因重构失效（此页面无C级）

---

## 4. Vue Async Wait Strategies

| 场景 | 等待策略 | 依据 |
|------|----------|------|
| 页面导航加载 | 等待 `el-table` 数据加载结束，使用 `loading` 状态判断 | 通用el-table加载模式 |
| 搜索查询 | 点击查询后等待 `loading` 消失或表格数据刷新 | 查询触发数据刷新 |
| 重置搜索 | 点击重置后等待输入框清空、表格返回初始数据 | 重置清空搜索条件 |
| 新增对话框打开 | 等待 `el-dialog` 的 `visible` 属性变化，检测对话框DOM出现 | el-dialog动画 |
| 表单填写 | `_fill_dialog_by_placeholder` 使用JS直接设置值和事件，无需额外等待 | JS方案绕过输入动画 |
| 表单提交 | 点击确定按钮后等待表格数据刷新，`loading` 消失 | 数据提交返回刷新 |
| 删除操作 | 点击删除后等待表格 `loading` 消失 | 异步删除操作 |
| 取消操作 | 点击取消后等待对话框关闭动画 | el-dialog关闭过渡 |

**推荐使用:** `WebDriverWait` + `expected_conditions` 结合 `staleness_of` / `invisibility_of_element_located`

---

## 5. Automation Risk Points

### 5.1 `_fill_dialog_by_placeholder` Anti-Fragile Pattern

The PO uses a custom JS helper `_fill_dialog_by_placeholder(placeholder_contains, value)` for dialog input:

```
流程: find visible dialog input by placeholder → JS set value → dispatch events
无降级: no fallback if placeholder match fails
```

**优势:**
- 绕过 `el-input` 组件复杂的事件触发链
- 不受 `v-model` 双向绑定实现变更影响
- 直接操作DOM，速度快

**风险:**
- 无降级策略：若placeholder不匹配，直接失败
- 依赖对话框可见性：需确保对话框已渲染完成
- 不会触发某些Vue watcher：可能绕过部分验证逻辑（但 `test_add_empty_required` 验证了错误提示）

### 5.2 Teleport/Portal 渲染

- `el-dialog` 默认使用 Teleport 渲染到 `body` 下
- `_fill_dialog_by_placeholder` 搜索全局可见输入框，因此不受 Teleport 影响
- 无需额外处理

### 5.3 动态数据影响

- 测试数据使用 `AUTO_装填_{timestamp}` 确保唯一性
- `search_by_item_name` 配合精确匹配定位目标行
- 删除操作使用 `delete_item_by_name` 而非按索引删除

### 5.4 v-if / v-show 条件渲染

- 分页组件 `v-show="total > 0"` 在无数据时隐藏
- 空表格状态的 `el-empty` 组件可能替换 `el-table`
- `is_row_present` 需处理无数据行的边界情况

### 5.5 el-input-number / el-switch

- 未在当前页面PO中发现 `el-input-number` 或 `el-switch` 使用
- 无相关风险

### 5.6 对话框动画时序

- `el-dialog` 有打开/关闭过渡动画（~300ms）
- 在点击新增后需等待对话框完全可见再填写
- 在点击取消后需等待对话框完全关闭再断言
