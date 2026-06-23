# 技术分析报告：Warehouse - Spare Stocktake 页面

## 1. Element Plus 组件识别

| 组件 | 用途 | 区域 |
|------|------|------|
| `el-input` | 盘点人搜索输入框 | 搜索区 |
| `el-date-picker` | 日期范围筛选 | 搜索区 |
| `el-button` | 查询、重置按钮 | 搜索区 |
| `el-table` | 盘点记录列表展示 | 主数据区 |
| `el-table-column` | 表格列（盘点单号、盘点人、盘点日期、状态等） | 主数据区 |
| `el-pagination` | 表格数据分页 | 主数据区底部 |

## 2. DOM 结构分析（基于 PO 定位器推断）

```html
<!-- 页面主容器 -->
<div class="app-container">
  <!-- 搜索区 -->
  <div class="filter-container">
    <el-form :model="queryParams" inline>
      <el-form-item label="盘点人">
        <el-input placeholder="请输入盘点人" v-model="queryParams.handler" clearable />
      </el-form-item>
      <el-form-item label="日期">
        <el-date-picker
          placeholder="选择日期"
          v-model="queryParams.date"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleQuery">查询</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>
  </div>

  <!-- 表格区域 -->
  <div class="table-container">
    <el-table :data="stocktakeList" v-loading="loading">
      <el-table-column prop="stocktakeNo" label="盘点单号" width="180" />
      <el-table-column prop="handler" label="盘点人" width="120" />
      <el-table-column prop="stocktakeDate" label="盘点日期" width="120" />
      <el-table-column prop="itemCount" label="盘点项数" width="100" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="statusType(scope.row.status)">{{ scope.row.statusLabel }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createTime" label="创建时间" width="180" />
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
- **v-if/v-show 控制**: 分页器（根据 `total > 0` 显示）、加载遮罩、空数据提示。
- **循环渲染**: 表格行 (el-table__row)、分页器选项。
- **el-date-picker Teleport**: 日期选择器下拉面板渲染到 `<body>` 下，需使用 `body > .el-popper` 定位。

## 3. 定位器设计表

### A 级（稳定，优先使用）

| 元素 | 定位策略 | 定位值 | 稳定性 | 备注 |
|------|---------|--------|--------|------|
| 盘点人搜索框 | XPath (placeholder) | `//input[@placeholder="请输入盘点人"]` | A | placeholder 通常稳定 |
| 日期选择器 | XPath (placeholder) | `//input[@placeholder="选择日期"]` | A | placeholder 通常稳定 |
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
| 日期范围-开始日期 | XPath | `(//input[@placeholder="选择日期"]/preceding-sibling::input[@placeholder="开始日期"])[1]` | B | 依赖于具体 DOM 结构 |

### C 级（动态内容，谨慎使用）

| 元素 | 定位策略 | 定位值 | 稳定性 | 备注 |
|------|---------|--------|--------|------|
| 表格中指定盘点行 | XPath | `//div[@class='el-table__body-wrapper']//tr[contains(td,'盘点人名称')]` | C | 列索引依赖实际 DOM 顺序 |
| 加载遮罩 | CSS | `.el-loading-mask` | C | 仅数据加载时存在 |
| 日期选择器日历面板 | CSS | `body > .el-picker-panel` | C | Teleport 渲染到 body |

## 4. Vue 异步等待策略

| 场景 | 等待条件 | WebDriverWait 示例 |
|------|---------|-------------------|
| 页面加载 & 表格就绪 | 表格出现 | `wait.until(EC.presence_of_element_located(TABLE_CONTAINER))` |
| 执行搜索后 | 旧表格 loading 消失 | `wait.until(EC.invisibility_of_element_located(LOADING_MASK))` |
| 重置后 | 表格数据刷新 | `wait.until(EC.invisibility_of_element_located(LOADING_MASK))` |
| 分页切换 | 分页总条数更新 | `wait.until(EC.text_to_be_present_in_element(PAGINATION_TOTAL, expected_text))` |
| 日期选择器打开 | 日历面板可见 | `wait.until(EC.visibility_of_element_located(DATE_PICKER_PANEL))` |

## 5. 自动化风险点

- **`el-date-picker` Teleport 渲染**: 日期选择器的日历控件渲染在 `<body>` 下，定位需使用 `body > .el-popper` 或对应 CSS 类名。`el-date-picker` 可能存在范围选择模式，需要处理开始/结束日期的选择。
- **动态数据**: 表格行、分页控件根据 API 返回的动态数据渲染，需等待接口完成。
- **空数据状态**: 无盘点记录时，表格显示空状态提示，`TABLE_ROWS` 定位器可能返回空列表（测试需处理 `rows >= 0` 的宽松断言）。
- **`v-loading` 遮罩**: 搜索或分页切换时，表格可能出现 loading 遮罩，需等待消失后再获取数据。
- **日期格式**: 选择日期时需要确保日期格式与后端期望一致（如 `YYYY-MM-DD`）。

## 6. 结论

该页面为只读查询页面，基于标准 Element Plus 组件库构建。搜索区包含盘点人文本输入和日期选择器，配合查询和重置按钮。`el-date-picker` 的 Teleport 渲染和日期选择交互是主要自动化风险点。建议优先使用 **A 级定位器（基于 placeholder / text）**，对于日期选择器需在 Helper 层进行统一封装处理。
