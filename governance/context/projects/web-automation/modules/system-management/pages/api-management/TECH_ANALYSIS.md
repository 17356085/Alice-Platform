```yaml
source: ai
source_agent: tech-analysis-agent
created: 2026-06-18
module: system-management
page: api-management
technology: vue3-element-plus
```

# TECH_ANALYSIS.md — API 管理页面 (system-management/api-management)

## 1. Element Plus 组件识别

| 组件类型 | 用途 | 依据 |
|----------|------|------|
| `el-input` | API名称搜索输入框 | placeholder “请输入API名称” |
| `el-select` | 状态筛选、请求方式筛选 | class 含 `el-select` |
| `el-date-picker` | （未明确，但可预留日期筛选场景） | — |
| `el-button` | 搜索、重置、新增、编辑、删除、分页切换等 | 按钮文本 “搜索” / “重置” / “新增” |
| `el-table` | API 数据列表展示 | class `el-table` |
| `el-dialog` | 新增 / 编辑 / 详情弹窗 | 按钮文本关联 `el-dialog` |
| `el-pagination` | 分页控件 | class `el-pagination` |

## 2. DOM 结构分析（推测基于 Element Plus 标准结构）

```
<div class="api-management-page">                    <!-- 页面根容器 -->
  <div class="search-form">                          <!-- 筛选区 -->
    <el-form>
      <el-form-item label="API名称">
        <el-input placeholder="请输入API名称"></el-input>
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="status">
          <el-option label="全部" value=""/>
          <el-option label="启用" value="1"/>
          <el-option label="禁用" value="0"/>
        </el-select>
      </el-form-item>
      <el-form-item label="请求方式">
        <el-select>
          <el-option label="全部" value=""/>
          <el-option label="GET" value="GET"/>
          <el-option label="POST" value="POST"/>
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="search">搜索</el-button>
        <el-button @click="reset">重置</el-button>
      </el-form-item>
    </el-form>
  </div>
  <div class="table-container">                       <!-- 表格区 -->
    <el-table :data="apiList" v-loading="loading">
      <el-table-column prop="apiName" label="API名称"/>
      <el-table-column prop="status" label="状态"/>
      <el-table-column prop="requestMethod" label="请求方式"/>
      <el-table-column label="操作">
        <el-button type="text" @click="edit">编辑</el-button>
        <el-button type="text" @click="delete">删除</el-button>
      </el-table-column>
    </el-table>
    <el-pagination v-if="total > 0" :total="total" layout="total, prev, pager, next, jumper"/>
  </div>
  <!-- 弹窗（teleport 到 body） -->
  <el-dialog v-model="dialogVisible" title="编辑API" top="10vh">
    <el-form>
      <el-form-item label="API名称">
        <el-input v-model="form.apiName"/>
      </el-form-item>
      <!-- 更多字段 -->
    </el-form>
    <span slot="footer">
      <el-button @click="dialogVisible=false">取消</el-button>
      <el-button type="primary" @click="confirm">确定</el-button>
    </span>
  </el-dialog>
</div>
```

### 稳定属性 / 动态属性说明

- **稳定属性**：`placeholder`、按钮文本（`el-button` 内的 `span`）、`v-model` 关联的数据（不暴露给测试）。
- **动态属性**：
  - Element Plus 生成的哈希类名（如 `el-select--suffix` `el-table__body-wrapper` 等标准类名相对稳定，但 Vue 动态 class 如 `is-loading` `is-disabled` 会动态切换）。
  - `v-if` 控制的元素：弹窗内容（只有 `dialogVisible=true` 时渲染）、分页（总记录 >0 时显示）。
  - `el-select` 下拉选项通过 Teleport 渲染到 `<body>` 下，定位时需注意层级。

## 3. 定位器设计表（A级优先，C级保底）

依据 `PAGE_ELEMENT_POSITION.md` 与 Element Plus 标准结构整理。

| 元素描述 | 推荐定位策略 | 定位值 | 稳定性 | 备用方案 | 备注 |
|----------|------------|-------|--------|---------|------|
| API名称搜索输入框 | CSS placeholder | `input[placeholder*='API名称']` | **A** | XPath: `//input[@placeholder='请输入API名称']` | placeholder 恒定 |
| 状态选择器（输入框） | CSS | `.search-form .el-select:nth-child(2) .el-input__inner` | **B** | XPath: `//label[text()='状态']/following-sibling::div//input` | 依赖结构顺序 |
| 请求方式选择器（输入框） | CSS | `.search-form .el-select:nth-child(3) .el-input__inner` | **B** | XPath: `//label[text()='请求方式']/following-sibling::div//input` | 同上 |
| 搜索按钮 | CSS with text | `button:has(span:text("搜索"))` | **B** | XPath: `//button[.//span[text()='搜索']]` | 文本稳定；“:has”需浏览器支持，Selenium 4.x 可用 |
| 重置按钮 | CSS with text | `button:has(span:text("重置"))` | **B** | XPath: `//button[.//span[text()='重置']]` | 同上 |
| 表格体 | CSS | `.el-table` | **A** | — | Element Plus 固定类 |
| 表格数据行 | CSS | `tr.el-table__row` | **B** | XPath: `//tr[contains(@class,'el-table__row')]` | 每行动态生成 |
| 编辑按钮（第一行） | CSS | `tr.el-table__row:nth-child(1) button:has(span:text("编辑"))` | **C** | XPath: `(//tr[contains(@class,'el-table__row')])[1]//button[span[text()='编辑']]` | 行索引敏感，若分页可能行变化 |
| 新增按钮 | CSS with text | `button:has(span:text("新增"))` | **A** | XPath: `//button[.//span[text()='新增']]` | 页面级别按钮，唯一 |
| 弹窗（el-dialog） | CSS | `.el-dialog` | **A** | — | 若有多弹窗需额外限定（`:has(div[class*='title'])`） |
| 弹窗确定按钮 | XPath | `//div[contains(@class,'el-dialog')]//button[.//span[text()='确定']]` | **A** | CSS: `.el-dialog .el-button--primary` | 限定弹窗范围内，避免误点 |
| 弹窗取消按钮 | XPath | `//div[contains(@class,'el-dialog')]//button[.//span[text()='取消']]` | **A** | CSS: `.el-dialog .el-button--default` | 同上 |
| 分页器 | CSS | `.el-pagination` | **A** | — | 可通过 `el-pagination__total` 进一步定位 |
| 表格 loading 蒙层 | CSS | `div.el-loading-mask` | **B** | — | `v-loading` 触发时出现，`invisibility_of_element_located` |

## 4. 异步等待策略

| 场景 | 等待条件 | Selenium 代码示例（等待 10s） |
|------|---------|-------------------------------|
| **页面加载** (表格数据可见) | `presence_of_element_located(TABLE_ROWS)` | `WebDriverWait(driver, 10).until(EC.presence_of_element_located(TABLE_LOCATOR))` |
| **搜索/筛选完成** (loading 消失) | `invisibility_of_element_located(LOADING_MASK)` | `WebDriverWait(driver, 10).until(EC.invisibility_of_element_located(LOADING_MASK))` |
| **弹窗打开** | `visibility_of_element_located(DIALOG)` | `WebDriverWait(driver, 10).until(EC.visibility_of_element_located(DIALOG))` |
| **弹窗关闭** (确定/取消后) | `invisibility_of_element_located(DIALOG)` | `WebDriverWait(driver, 10).until(EC.invisibility_of_element_located(DIALOG))` |
| **表格刷新** (新增/删除后) | `staleness_of` 旧行 + `presence_of_element_located` 新行 | `WebDriverWait(driver, 10).until(EC.staleness_of(old_row))` → 再等待新行 |
| **下拉选项展开** (el-select) | `visibility_of_element_located(SELECT_DROPDOWN)` + 选项可点击 | `wait.until(EC.visibility_of_element_located(SELECT_DROPDOWN))` |
| **翻页** (点击页码后) | 同上 loading 消失 + 行数据更新 | 等待 `LOADING_MASK` 消失后检查表格总行数 |

### 注意事项
- `el-select` 下拉选项通过 Teleport 渲染到 `<body>` 下，定位器需以 `body > .el-popper` 开头。
- 弹窗 `v-model` 驱动 `el-dialog` 的 `display`，可用 `visibility_of_element_located` 判断。
- 表格数据量较大时可能使用虚拟滚动，等待时需关注表格容器内是否出现占位行。

## 5. 自动化风险点

| 风险 | 说明 | 应对措施 |
|------|------|----------|
| **Teleport 渲染 (EP-001)** | `el-select`、`el-date-picker`、`el-dialog` 内容可能渲染到 `<body>` 下 | 使用 `body > .el-popper` 定位；避免 `is_displayed()` 判断 Teleport 元素 |
| **动态 class / v-if 控制** | Element Plus 的动态 class（`is-loading`）和 Vue 的 `v-if` 切换导致元素不存在 | 用稳定性高的属性（placeholder/text）定位；等待 `visibility_of_element_located` |
| **分页动态渲染** | 分页组件仅在有数据时显示 | 等待表格行出现后，再断言分页是否出现 |
| **权限控制元素缺失** | 部分按钮（如删除、新增）可能因权限不显示 | 定位时用 `find_elements` 判断数量，再决定是否可操作 |
| **下拉选项定位层级错误** | 点击 `el-select` 后，选项框出现在 `<body>` 下 | 使用 `driver.find_element(By.CSS_SELECTOR, "body > .el-popper .el-select-dropdown__item")` |
| **表格虚拟滚动** | 不可见行不在 DOM 中，无法直接定位 | 滚动到目标行（`actions.move_to_element`），或使用 `execute_script` 滚动 |
| **弹窗嵌套** | 多个弹窗同时出现时，定位器可能匹配错误 | 限定父弹窗 class（如 `.el-dialog[aria-modal='true']`）或使用 XPath 索引 |

## 6. 已有页面上下文适配说明

参考 `PAGE_ELEMENT_POSITION.md`（由 test-design-agent 生成）中的定位器表，已遵循 A/B/C 三级原则。本技术分析将直接使用其中 A 级定位器作为 PO 实现首选，B/C 级作为备用。对于未覆盖的元素（如 `el-date-picker`、`el-upload`），预留扩展点，按相同策略设计。

---

**附录：引用规范**
- Element Plus 已知坑位：`element-plus-pitfalls.md` (EP-001~EP-011)
- 自动化编码规范：`coding-standards.md` (Page Object 规范、Locator 声明规则)
- 定位器设计原则参考：`base-api-reference.md` (BasePage 通用定位器)