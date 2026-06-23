## TECH_ANALYSIS.md — 模块 dcs，页面 all-data

> ⚠️ **声明**：当前无真实 HTML 源码与截图。以下分析基于 **Vue 3 + Element Plus 典型数据列表页**的通用模式，所有定位器与等待策略需接入实际页面后 **重新验证**。

---

### 1. 推测的 Element Plus 组件清单

| 组件 | 功能角色 |
|------|---------|
| `el-input` | 搜索条件输入框（名称/编码/ID 等） |
| `el-select` | 状态/分类下拉筛选 |
| `el-date-picker` | 时间范围选择 |
| `el-button` | 搜索/重置/新增/操作按钮 |
| `el-table` | 数据列表展示主体 |
| `el-table-column` | 表头与单元格渲染 |
| `el-pagination` | 分页组件（居右显示） |
| `el-dialog` | 新增/编辑/详情弹窗 |
| `el-tag` | 状态标签 |
| `el-switch` | 状态启用/禁用切换 |

---

### 2. 假定的 DOM 结构（层级示例）

```
<div id="app">
  <div class="search-area">           <!-- 搜索条件区域 -->
    <el-input placeholder="名称" />   
    <el-select placeholder="状态" />  
    <el-button type="primary">搜索</el-button>
  </div>
  <div class="table-container">       <!-- 表格容器 -->
    <el-table>
      <el-table-column label="名称">
        ...el-table-column>
      <el-table>
    </el-table>
    <el-pagination>...</el-pagination>
  </div>
  <el-dialog>...</el-dialog>          <!-- 弹窗（若存在） -->
</div>
```

---

### 3. 定位器设计表（A/B/C 三级，需实际验证）

| 元素 | 推荐策略 | 定位值（示例） | 稳定性 | 备注 |
|------|---------|---------------|--------|------|
| 名称搜索输入框 | CSS | `#app input[placeholder*='名称']` | A | placeholder 需确认 |
| 状态选择下拉框 | CSS | `#app .search-area .el-select .el-input__inner` | B | 若下拉框触发后渲染在 body 层 |
| 搜索按钮 | XPATH | `//button[.//span[text()='搜索']]` | A | 文字稳定 |
| 表格主体 | CSS | `.el-table__body` | A | |
| 任意行单元格 | CSS | `.el-table__body tbody tr td` | B | 动态数量 |
| 分页器 | CSS | `.el-pagination` | A | |
| 新增按钮 | XPATH | `//button[.//span[text()='新增']]` | A | |
| 确认弹窗 | CSS | `.el-dialog` | A | |
| 弹窗确定按钮 | XPATH | `//div[contains(@class,'el-dialog')]//button[.//span[text()='确定']]` | A | EP-001: 确保弹窗可见 |

> **待定项**：具体表头列、状态标签、操作按钮等需依赖实际列定义。

---

### 4. 异步等待策略（基于 Element Plus 通用行为）

| 场景 | 等待条件 | 示例代码（BasePage 已封装） |
|------|---------|--------------------------|
| 页面数据加载完成 | 表格行出现 | `wait_table_loaded()` |
| 搜索后刷新 | loading 消失 | `wait_loading_disappear()` |
| 弹窗打开 | 弹窗可见 | `wait_dialog_visible()` |
| 弹窗关闭 | 弹窗不可见 | `wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.el-dialog'))))` |
| 分页跳转 | 页面重新加载 | 结合 `wait_table_loaded()` |
| 下拉选项渲染 | 选项列表可见（body 层） | `wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'body > .el-popper .el-select-dropdown__item')))` |

---

### 5. 自动化风险点（潜在）

- **动态 class**：Vue 生成的 `el-input--suffix` 等结构稳定，但 el-select 下拉面板的 `el-popper` 可能带动态 ID。
- **权限控制**：某些按钮（新增、编辑）可能不显示，需定位前先判断元素存在性。
- **异步渲染**：el-table 在数据加载前可能显示“暂无数据”占位，需区分。
- **Teleport 导致元素不在常规父容器内**：下拉选项、日期选择面板、弹窗需通过 body 层级定位（遵循 EP-001）。
- **慢响应场景**：REST API 响应慢导致 loading 消失后表格仍未填充，建议加自定义等待：`wait.until(lambda d: len(d.find_elements(...)) > 0)`

---

### 6. 后续操作建议

1. 获取实际页面 HTML（F12  Elements 面板）并截图，补充到本分析中。
2. 根据真实 DOM 调整定位器表，特别是搜索区域的实际 placeholder 或 label。
3. 运行一次冒泡 Selenium 脚本验证每个定位器的可点击/可操作状态。
4. 若发现下拉面板挂载位置不同，优先使用 `body > .el-popper` 定位器。
5. 考虑录制一段操作轨迹，辅助确认异步渲染时序。

---

## PAGE_ELEMENT_POSITION.md

（此文件可与 TECH_ANALYSIS.md 合并。以下为单独表格版本，定位器同上表。）

| 功能点 | 定位器 | 备注 |
|--------|--------|------|
| 名称输入框 | `(By.CSS_SELECTOR, "input[placeholder*='名称']")` | placeholder 可能为“名称/编号”，需适配 |
| 状态选择 | `(By.CSS_SELECTOR, ".search-area .el-select")` | 先 click 再选选项 |
| 搜索按钮 | `(By.XPATH, "//button[.//span[text()='搜索']]")` | 文字需与实际一致 |
| 表格行 | `(By.CSS_SELECTOR, ".el-table__body-wrapper .el-table__row")` | 动态数量 |
| 分页 | `(By.CSS_SELECTOR, ".el-pagination")` | |
| 新增按钮 | `(By.XPATH, "//button[.//span[text()='新增']]")` | 需确认按钮文本 |
| 弹窗 | `(By.CSS_SELECTOR, ".el-dialog")` | 弹窗可见时才能操作 |
| 弹窗确认 | `(By.XPATH, "//div[contains(@class,'el-dialog')]//button[.//span[text()='确定']]")` | |

---

> **下一步**：请提供页面 HTML 源码或截图，以便进行精确的组件识别与定位器设计。