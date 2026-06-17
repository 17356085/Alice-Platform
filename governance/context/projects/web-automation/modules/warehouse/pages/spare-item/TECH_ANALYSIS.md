好的，收到您的指示。作为自动化测试专家，我将遵循 Vue 3 + Element Plus 技术栈，基于通用的备件管理页面模式，为您产出 `TECH_ANALYSIS.md` 和 `PAGE_ELEMENT_POSITION.md`。

由于未提供具体的 HTML 源码和截图，我将基于 `warehouse` 模块下 `spare-item`（备件管理）页面的常见功能模式进行分析和设计。您可以将此作为模板，待获取真实页面信息后进行微调。

---

### `TECH_ANALYSIS.md`

# 技术分析报告：Warehouse - Spare Item 页面

## 1. Element Plus 组件识别

| 组件 | 用途 | 区域 |
|------|------|------|
| `el-input` | 备件编码/名称搜索、弹窗内输入框 | 搜索区、弹窗 |
| `el-select` | 备件分类/供应商/仓库筛选、状态选择、弹窗内下拉选项 | 搜索区、弹窗 |
| `el-date-picker` | 入库/出库日期范围筛选（可选） | 搜索区 |
| `el-table` | 备件列表展示 | 主数据区 |
| `el-table-column` | 表格列（编码、名称、规格、库存量、单价、状态等） | 主数据区 |
| `el-pagination` | 表格数据分页 | 主数据区底部 |
| `el-button` | 搜索、重置、新增、编辑、删除、导入、导出 | 搜索区、操作栏、弹窗 |
| `el-dialog` | 新增/编辑备件信息弹窗 | 弹窗区域 |
| `el-tag` | 显示备件状态（正常/停用/低库存） | 表格内 |
| `el-switch` | 启用/停用备件状态 | 表格内或弹窗 |
| `el-upload` | 导入备件数据文件 | 操作栏 |
| `el-tree` | 备件分类树（可选） | 侧边栏 |

## 2. DOM 结构分析（假设）

```html
<!-- 页面主容器 -->
<div class="app-container">
  <!-- 搜索区 -->
  <div class="filter-container">
    <el-form>
      <el-form-item label="备件编码">
        <el-input placeholder="请输入备件编码" v-model="queryParams.code" />
      </el-form-item>
      <el-form-item label="备件名称">
        <el-input placeholder="请输入备件名称" v-model="queryParams.name" />
      </el-form-item>
      <el-form-item label="备件分类">
        <el-select v-model="queryParams.categoryId" placeholder="请选择分类" clearable>
          <el-option v-for="item in categoryList" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleQuery">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>
  </div>

  <!-- 操作栏 -->
  <div class="action-container">
    <el-button type="primary" @click="handleAdd">新增</el-button>
    <el-button type="success" @click="handleImport">导入</el-button>
    <el-button v-if="multipleSelection.length > 0" type="danger" @click="handleBatchDelete">批量删除</el-button>
  </div>

  <!-- 表格区域 -->
  <div class="table-container">
    <el-table :data="spareItemList" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" />
      <el-table-column prop="code" label="备件编码" width="150" />
      <el-table-column prop="name" label="备件名称" width="200" />
      <el-table-column prop="categoryName" label="分类" width="120" />
      <el-table-column prop="stockQuantity" label="库存量" width="100" />
      <el-table-column prop="unit" label="单位" width="80" />
      <el-table-column prop="unitPrice" label="单价" width="120">
        <template #default="scope">
          ￥{{ scope.row.unitPrice }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="scope">
          <el-tag v-if="scope.row.status === 0" type="success">正常</el-tag>
          <el-tag v-else-if="scope.row.status === 1" type="danger">停用</el-tag>
          <el-tag v-else-if="scope.row.stockQuantity <= scope.row.minStock" type="warning">低库存</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="scope">
          <el-button type="text" size="small" @click="handleEdit(scope.row)">编辑</el-button>
          <el-button type="text" size="small" @click="handleDelete(scope.row)" style="color: red;">删除</el-button>
        </template>
      </el-table-column>
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

  <!-- 新增/编辑弹窗 -->
  <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="600px">
    <el-form ref="form" :model="form" label-width="120px">
      <el-form-item label="备件编码" prop="code">
        <el-input v-model="form.code" placeholder="请输入编码" />
      </el-form-item>
      <el-form-item label="备件名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入名称" />
      </el-form-item>
      <el-form-item label="备件分类" prop="categoryId">
        <el-select v-model="form.categoryId" placeholder="请选择分类">
          <el-option v-for="item in categoryList" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="库存数量" prop="stockQuantity">
        <el-input-number v-model="form.stockQuantity" :min="0" />
      </el-form-item>
      <el-form-item label="单位" prop="unit">
        <el-input v-model="form.unit" placeholder="请输入单位" />
      </el-form-item>
      <el-form-item label="单价" prop="unitPrice">
        <el-input-number v-model="form.unitPrice" :min="0" :precision="2" />
      </el-form-item>
      <el-form-item label="状态">
        <el-switch v-model="form.status" active-value="0" inactive-value="1" active-text="正常" inactive-text="停用" />
      </el-form-item>
    </el-form>
    <span slot="footer" class="dialog-footer">
      <el-button @click="dialogVisible = false">取 消</el-button>
      <el-button type="primary" @click="submitForm">确 定</el-button>
    </span>
  </el-dialog>
</div>
```

### 动态属性说明
- **Vue 哈希 Class**: `_v-xxxxx`，动态生成，不可用于定位。
- **v-if 控制**: 弹窗 (el-dialog)、空数据提示、批量删除按钮。
- **循环渲染**: 表格行 (el-table__row)、分页器、弹窗内选项。

## 3. 定位器设计表

### A 级（稳定，优先使用）

| 元素 | 定位策略 | 定位值 | 稳定性 | 备注 |
|------|---------|--------|--------|------|
| 备件编码搜索框 | CSS (placeholder) | `input[placeholder='请输入备件编码']` | A | |
| 备件名称搜索框 | CSS (placeholder) | `input[placeholder='请输入备件名称']` | A | |
| 搜索按钮 | XPATH | `//button[.//span[text()='搜索']]` | A | |
| 重置按钮 | XPATH | `//button[.//span[text()='重置']]` | A | 或者 `//button[.//span[text()='重置']]` |
| 新增按钮 | XPATH | `//button[.//span[text()='新增']]` | A | |
| 批量删除按钮 | XPATH | `//button[.//span[text()='批量删除']]` | B | `v-if` 控制，可能不存在 |
| 弹窗标题 | CSS | `.el-dialog__title` | A | |
| 弹窗确定按钮 | XPATH | `//div[contains(@class,'el-dialog')]//button[.//span[text()='确 定']]` | A | 注意 `确定` 中间有空格 |
| 表格容器 | CSS | `.el-table` | A | |
| 分页总条数 | CSS | `.el-pagination .el-pagination__total` | A | |

### B 级（通用，可用）

| 元素 | 定位策略 | 定位值 | 稳定性 | 备注 |
|------|---------|--------|--------|------|
| 表格行 | CSS | `.el-table__body-wrapper .el-table__row` | B | 动态行 |
| 表格第一行编辑按钮 | XPATH | `(//div[@class='el-table__body-wrapper']//button[.//span[text()='编辑']])[1]` | B | |
| 表格第一行删除按钮 | XPATH | `(//div[@class='el-table__body-wrapper']//button[.//span[text()='删除']])[1]` | B | |
| 弹窗内的 `el-select` | CSS | `.el-dialog .el-select` | B | 可指定表单内 |
| 翻页到第几页 | CSS | `.el-pagination .el-pagination__jump .el-input__inner` | B | |
| 每页显示条数 | CSS | `.el-pagination__sizes .el-input__inner` | B | |

### C 级（动态内容，谨慎使用）

| 元素 | 定位策略 | 定位值 | 稳定性 | 备注 |
|------|---------|--------|--------|------|
| 表格中的指定备件行 | XPATH | `//div[@class='el-table__body-wrapper']//tr[contains(td[2],'备件名称')]` | C | `td[2]` 索引依赖列顺序 |
| 弹窗内的指定 `el-option` | XPATH | `//body/div[last()]//span[text()='分类名称']` | C | Teleport 渲染到 body |

## 4. Vue 异步等待策略

| 场景 | 等待条件 | WebDriverWait 示例 |
|------|---------|-------------------|
| 页面加载 & 表格就绪 | 表格出现 | `wait.until(EC.presence_of_element_located(TABLE_CONTAINER))` |
| 执行搜索后 | 旧表格 loading 消失 | `wait.until(EC.invisibility_of_element_located(LOADING_CLASS))` |
| 新增/编辑弹窗打开 | 弹窗可见 | `wait.until(EC.visibility_of_element_located(DIALOG_WINDOW))` |
| 弹窗关闭 | 弹窗不可见 | `wait.until(EC.invisibility_of_element_located(DIALOG_WINDOW))` |
| 分页/表格刷新 | 分页总条数更新 | `wait.until(EC.text_to_be_present_in_element(PAGINATION_TOTAL, expected_text))` |
| 选择下拉选项 | 下拉选项可见 | `wait.until(EC.visibility_of_all_elements_located(DROPDOWN_OPTIONS))` |

## 5. 自动化风险点

- **Teleport 渲染**: `el-select` 下拉面板和 `el-date-picker` 的日历控件渲染在 `<body>` 下，使用 `body > .el-popper` 定位。
- **动态数据**: 表格行、分页控件根据 API 返回的动态数据渲染，需等待接口完成。
- **`v-if` 条件渲染**: 批量删除按钮、空状态提示等元素可能不存在，需先判断是否可见。
- **`el-input-number`**: 自带增减按钮，直接定位内部 `input` 并使用 `clear()` + `send_keys()` 可能丢失千分位格式，建议通过 `execute_script` 设置值。
- **`el-switch`**: 需点击切换，避免直接点击 `input[type=checkbox]`，应点击外部的 `.el-switch` 元素。

## 6. 结论

该页面基于标准的 Element Plus 组件库构建，DOM 结构清晰。建议优先使用 **A 级定位器（基于 placeholder / text）**，并利用 **BasePage** 的等待方法处理异步加载。Teleport 和动态内容是主要风险点，需在 Helper 层（如 `ElementPlusHelper`）进行统一封装。

---

### `PAGE_ELEMENT_POSITION.md`
## 页面元素定位手册：Spare Item

### 搜索区域

| 元素 | 标识/描述 | 控件类型 | CSS 选择器 | XPath | 区域 |
|------|-----------|----------|------------|-------|------|
| 备件编码 | 搜索输入框 | `el-input` | `input[placeholder='请输入备件编码']` | `//input[@placeholder='请输入备件编码']` | search |
| 备件名称 | 搜索输入框 | `el-input` | `input[placeholder='请输入备件名称']` | `//input[@placeholder='请输入备件名称']` | search |
| 备件分类 | 搜索下拉框 | `el-select` | `.filter-container .el-select input` | `(//div[@class='filter-container']//input[@placeholder='请选择分类'])[1]` | search |
| 搜索按钮 | 触发搜索 | `el-button` | `//button[.//span[text()='搜索']]` | `//button[.//span[text()='搜索']]` | search |
| 重置按钮 | 重置搜索条件 | `el-button` | `//button[.//span[text()='重置']]` | `//button[.//span[text()='重置']]` | search |

### 操作栏

| 元素 | 标识/描述 | 控件类型 | CSS 选择器 | XPath | 区域 |
|------|-----------|----------|------------|-------|------|
| 新增按钮 | 打开新增弹窗 | `el-button` | `//button[.//span[text()='新增']]` | `//button[.//span[text()='新增']]` | action |
| 批量删除 | 批量删除备件 | `el-button` | `//button[.//span[text()='批量删除']]` | `//button[.//span[text()='批量删除']]` | action |
| 导入按钮 | 导入备件数据 | `el-button` | `//button[.//span[text()='导入']]` | `//button[.//span[text()='导入']]` | action |

### 表格区域 (主数据)

| 元素 | 标识/描述 | 控件类型 | CSS 选择器 | XPath | 区域 |
|------|-----------|----------|------------|-------|------|
| 表格容器 | 承载数据表格 | `el-table` | `.el-table` | `//div[contains(@class,'el-table')]` | table |
| 表格行 | 数据行 | `el-table__row` | `.el-table__body-wrapper .el-table__row` | `//tr[@class='el-table__row']` | table |
| 编辑按钮 (行内) | 编辑备件信息 | `el-button` | `//button[.//span[text()='编辑']]` | `(//button[.//span[text()='编辑']])[1]` | table |
| 删除按钮 (行内) | 删除备件 | `el-button` | `//button[.//span[text()='删除']]` | `(//button[.//span[text()='删除']])[1]` | table |
| 分页器 | 表格分页 | `el-pagination` | `.el-pagination` | `//div[contains(@class,'el-pagination')]` | table |

### 弹窗区域

| 元素 | 标识/描述 | 控件类型 | CSS 选择器 | XPath | 区域 |
|------|-----------|----------|------------|-------|------|
| 弹窗窗口 | 新增/编辑表单 | `el-dialog` | `.el-dialog` | `//div[contains(@class,'el-dialog')]` | dialog |
| 弹窗标题 | 弹窗标题文字 | `el-dialog__title` | `.el-dialog__title` | `//span[@class='el-dialog__title']` | dialog |
| 弹窗表单 | 内部表单 | `el-form` | `.el-dialog .el-form` | `//div[contains(@class,'el-dialog')]//form` | dialog |
| 编码输入框 (弹窗) | 备件编码 | `el-input` | `.el-dialog input[placeholder='请输入编码']` | `//div[contains(@class,'el-dialog')]//input[@placeholder='请输入编码']` | dialog |
| 名称输入框 (弹窗) | 备件名称 | `el-input` | `.el-dialog input[placeholder='请输入名称']` | `//div[contains(@class,'el-dialog')]//input[@placeholder='请输入名称']` | dialog |
| 确定按钮 (弹窗) | 提交表单 | `el-button` | `.el-dialog .el-button--primary` | `//div[contains(@class,'el-dialog')]//button[.//span[text()='确 定']]` | dialog |
| 取消按钮 (弹窗) | 关闭弹窗 | `el-button` | `.el-dialog .el-button--default` | `//div[contains(@class,'el-dialog')]//button[.//span[text()='取 消']]` | dialog |

> **注意**: 所有 `el-select` 的下拉选项通过 Teleport 渲染到 `<body>` 下，定位时应使用 `body > .el-popper .el-select-dropdown__item` 或基于 `text()` 的 XPath。 上述定位器均基于假设的通用模板，建议获取真实页面 HTML 后进行验证和微调。