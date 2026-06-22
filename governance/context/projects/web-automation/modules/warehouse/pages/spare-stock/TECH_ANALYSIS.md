# 技术分析报告：Warehouse - Spare Stock 页面

## 1. Element Plus 组件识别

| 组件 | 用途 | 区域 |
|------|------|------|
| `el-input` | 物品名称搜索输入框 | 搜索区 |
| `el-button` | 查询、重置按钮 | 搜索区 |
| `el-table` | 库存数据列表展示 | 主数据区 |
| `el-table-column` | 表格列（物品名称、规格、库存量、库位等） | 主数据区 |
| `el-pagination` | 表格数据分页 | 主数据区底部 |

## 2. DOM 结构分析（基于 PO 定位器推断）

```html
<!-- 页面主容器 -->
<div class="app-container">
  <!-- 搜索区 -->
  <div class="filter-container">
    <el-form>
      <el-form-item label="物品名称">
        <el-input placeholder="请输入物品名称" v-model="queryParams.itemName" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleQuery">查询</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>
  </div>

  <!-- 表格区域 -->
  <div class="table-container">
    <el-table :data="stockList" v-loading="loading">
      <el-table-column prop="itemName" label="物品名称" min-width="150" />
      <el-table-column prop="itemCode" label="物品编码" width="150" />
      <el-table-column prop="spec" label="规格型号" width="150" />
      <el-table-column prop="unit" label="单位" width="80" />
      <el-table-column prop="currentStock" label="当前库存" width="100" />
      <el-table-column prop="location" label="库位" width="120" />
    </el-table>
    <el-pagination
      v-show="total > 0"
      :total="total"
      :page-sizes="[10, 20, 50, 100]"
      :page-size="queryParams.pageSize"
      :current-page="queryParams.pageNum"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />
  </div>
</div>
```

### 动态属性说明
- **Vue 哈希 Class**: `_v-xxxxx`，动态生成，不可用于定位。
- **v-if 控制**: 分页器（`v-show`）、空数据提示、加载遮罩。
- **循环渲染**: 表格行 (el-table__row)、分页器选项。

## 3. 定位器设计表

### A 级（稳定，优先使用）

| 元素 | 定位策略 | 定位值 | 稳定性 | 备注 |
|------|---------|--------|--------|------|
| 物品名称搜索框 | XPath (placeholder) | `//input[@placeholder="请输入物品名称"]` | A | placeholder 通常稳定 |
| 查询按钮 | XPath (text contains) | `//button[contains(.,"查询")]` | A | 文本内容稳定 |
| 重置按钮 | XPath (text contains) | `//button[contains(.,"重置")]` | A | 文本内容稳定 |
| 分页总条数 | CSS | `.el-pagination .el-pagination__total` | A | 分页组件固定结构 |

### B 级（通用，可用）

| 元素 | 定位策略 | 定位值 | 稳定性 | 备注 |
|------|---------|--------|--------|------|
| 表格容器 | CSS | `.el-table` | B | 标准组件 |
| 表格行 | CSS | `.el-table__body-wrapper .el-table__row` | B | 动态行 |
| 翻页输入框 | CSS | `.el-pagination .el-pagination__jump .el-input__inner` | B | 跳页交互 |
| 每页显示条数 | CSS | `.el-pagination__sizes .el-input__inner` | B | 分页大小 |

### C 级（动态内容，谨慎使用）

| 元素 | 定位策略 | 定位值 | 稳定性 | 备注 |
|------|---------|--------|--------|------|
| 表格中指定物品行 | XPath | `//div[@class='el-table__body-wrapper']//tr[contains(td,'物品名称')]` | C | 列索引依赖实际 DOM 顺序 |
| 加载遮罩 | CSS | `.el-loading-mask` | C | 仅数据加载时存在 |

## 4. Vue 异步等待策略

| 场景 | 等待条件 | WebDriverWait 示例 |
|------|---------|-------------------|
| 页面加载 & 表格就绪 | 表格出现 | `wait.until(EC.presence_of_element_located(TABLE_CONTAINER))` |
| 执行搜索后 | 旧表格 loading 消失 | `wait.until(EC.invisibility_of_element_located(LOADING_MASK))` |
| 重置后 | 表格数据刷新 | `wait.until(EC.invisibility_of_element_located(LOADING_MASK))` |
| 分页切换 | 分页总条数更新 | `wait.until(EC.text_to_be_present_in_element(PAGINATION_TOTAL, expected_text))` |

## 5. 自动化风险点

- **动态数据**: 表格行、分页控件根据 API 返回的动态数据渲染，需等待接口完成。
- **空数据状态**: 无库存数据时，表格显示空状态提示，`TABLE_ROWS` 定位器可能返回空列表（测试需处理 `rows >= 0` 的宽松断言）。
- **`v-loading` 遮罩**: 搜索或分页切换时，表格可能出现 loading 遮罩，需等待消失后再获取数据。
- **只读页面无弹窗**: 无需处理 dialog/confirm 类异步交互，降低自动化复杂度。

## 6. 结论

该页面为只读查询页面，基于标准 Element Plus 组件库构建，DOM 结构简洁。搜索区仅有一个物品名称输入框，配合查询和重置按钮。建议优先使用 **A 级定位器（基于 placeholder / text）**，并利用 **BasePage** 的等待方法处理异步加载。由于无 CRUD 操作和弹窗交互，自动化实现成本较低。
