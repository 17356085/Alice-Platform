以下是根据提供的代码和上下文生成的 **TECH_ANALYSIS.md**，结合 Element Plus 组件特性和测试脚本中使用的定位器、等待逻辑，输出完整的工程技术分析。

---

# TECH_ANALYSIS.md

## 1. Element Plus 组件识别

| 组件类型         | 出现位置         | 用途说明                           | 代码定位器示例                                                   |
|------------------|------------------|------------------------------------|------------------------------------------------------------------|
| `el-select`      | 筛选区（状态）   | 下拉筛选状态                       | `XPath: (//div[contains(@class,"wh-filter-toolbar")]//div[contains(@class,"el-select__wrapper")])[1]` |
| `el-input`       | 筛选区（经办人） | 文本搜索经办人                     | `XPath: //input[@placeholder="请输入经办人"]`                    |
| `el-date-picker` | 筛选区（日期）   | 日期筛选                           | `XPath: //input[@placeholder="选择日期"]`                        |
| `el-button`      | 工具栏/弹窗/行内 | 触发操作（查询、重置、新增、查看、编辑、提交） | `XPath: //button[contains(.,"查询")]`                            |
| `el-table`       | 主区域           | 展示危废入库记录                   | 通用定位器：`BasePage.TABLE_ROWS`（A级）                         |
| `el-pagination`  | 主区域底部       | 分页                               | 通用定位器：`BasePage.TOTAL_COUNT`（A级）                        |
| `el-dialog`      | 弹窗A新增入库    | 模态表单                           | 通用定位器：`BasePage.DIALOG`（A级）                             |
| `el-dialog`      | 弹窗B选择危废品  | 嵌套模态（选择危废品）             | 无独立定位器，通过 JS 检测可见 `el-dialog` 数量判断              |
| `el-overlay`     | 弹窗遮罩层       | 嵌套弹窗遮罩（备用判断）           | 测试脚本通过 JS 统计 `el-overlay`                                |
| `el-tag`（推测）  | 表中状态列       | 状态标签（如“待审批”）             | 未在代码中直接使用，但常见于 Element Plus 表格                   |
| `el-switch`（推测） | 编辑弹窗       | 开关控件（如启用/禁用）            | 未出现                                                           |

> 所有按钮均为 `el-button`，未使用 `el-button-group`。

---

## 2. DOM 结构分析

### 关键节点层级（基于 Element Plus 标准结构 + 自定义容器）

```
body
├── #app
│   ├── .wh-filter-toolbar        // 筛选区（自定义类）
│   │   ├── .el-select__wrapper   // 状态筛选
│   │   ├── .el-input             // 经办人输入
│   │   ├── .el-date-editor       // 日期选择
│   │   └── .el-button            // 查询 / 重置
│   ├── .wh-table-wrapper         // 表格+工具栏容器（推测）
│   │   ├── .el-button            // 新增入库
│   │   ├── .el-table             // 表格主体
│   │   │   ├── .el-table__header-wrapper th
│   │   │   └── .el-table__body-wrapper .el-table__row
│   │   └── .el-pagination        // 分页
│   └── (弹窗A) .el-dialog         // 新增入库弹窗（通过 Teleport 挂载到 body 下？）
├── (弹窗B) .el-dialog             // 选择危废品弹窗（嵌套）
└── .el-overlay                    // 遮罩层（每个弹窗对应一个）
```

### 稳定属性

| 属性类型 | 具体值 | 定位器评价 |
|---------|--------|-----------|
| placeholder | `"请输入经办人"`、`"选择日期"` | **B级**（可能更改，但当前稳定） |
| class 前缀 | `el-select__wrapper`、`el-table`、`el-dialog` | **A级**（Element Plus 固定前缀） |
| class 具体 | `wh-filter-toolbar` | **B级**（自定义类，可能变动） |
| 文本内容 | `"查询"`、`"新增入库"` | **C级**（多语言或重构可能更改） |

### 动态属性 / Vue 控制

- **动态 class**：`.el-select__wrapper` 在激活/展开时添加 `is-focus`、`is-dropdown` 等 class；`.el-dialog` 通过 `v-if` 或 `v-show` 控制显示。
- **Teleport 渲染**：`el-select` 选项列表、`el-date-picker` 面板默认挂载到 `<body>` 下，不在筛选区容器内，但筛选区本身仍为普通 DOM。
- **弹窗嵌套**：弹窗B（选择危废品）可能渲染在弹窗A之上，甚至使用独立的 `el-overlay`，测试脚本通过 JS 判断可见弹窗数量。

---

## 3. 定位器设计表（A/B/C 三级）

| 元素 | 推荐定位策略 | 定位值（示例） | 稳定性 | 备注 |
|------|-------------|---------------|--------|------|
| **筛选状态** | CSS | `div.wh-filter-toolbar .el-select__wrapper` | B | 自定义类 `wh-filter-toolbar` 可能变动 |
| **经办人输入** | CSS | `input[placeholder='请输入经办人']` | B | placeholder 文本稳定时可用；推荐与 XPath 搭配优先级 |
| **日期选择器** | XPath | `//input[@placeholder='选择日期']` | C | placeholder 文本；无唯一标识 |
| **查询按钮** | XPath | `//button[contains(.,'查询')]` | C | 文本匹配；若多个查询则需更精确 |
| **重置按钮** | XPath | `//button[contains(.,'重置')]` | C | 同上 |
| **新增入库按钮** | XPath | `//button[contains(.,'新增入库')]` | C | 同上；可加 `.wh-toolbar` 范围提升稳定性 |
| **表格行（通用）** | CSS（BasePage） | `table.el-table__body-wrapper tbody tr.el-table__row` | A | 继承自 BasePage，通用稳定 |
| **分页总记录数** | CSS（BasePage） | `[class*="el-pagination"] .el-pagination__total` | A | 同上 |
| **查看按钮（首行）** | XPath | `(//button[contains(.,'查看')])[last()]` | B | 假设操作列在最后；用 `last()` 避免第一行干扰 |
| **编辑按钮（首行）** | XPath | `(//button[contains(.,'编辑')])[last()]` | B | 同上 |
| **弹窗A（新增入库）** | CSS（BasePage） | `.el-dialog:not([style*='display: none'])` | A | 当前弹窗可见且未隐藏 |
| **弹窗A-入库时间** | CSS + XPath | `./el-dialog[not(contains(@style,'display:none'))]//input[@placeholder='选择日期']` | C | 当前实现；建议改进为基于弹窗标题或角色属性 |
| **弹窗A-经办人** | CSS + XPath | 同上类似，placeholder='请输入经办人' | C | 同上 |
| **弹窗A-选择危废品按钮** | XPath | `//button[contains(.,'选择危废品')]` | C | 文本匹配；若弹窗内有其他同类按钮需指定弹窗范围 |
| **弹窗A-提交申请按钮** | XPath | `//button[contains(.,'提交申请')]` | C | 同上 |
| **弹窗B（选择危废品）** | JS + CSS | 通过 `document.querySelectorAll('.el-dialog:not([style*=none])')` >1 判断 | A | 动态检测，不依赖具体定位器 |
| **toast 提示** | CSS（BasePage） | `.el-message` 或 `.el-notification` | A | 通用定位器，`wait_for_toast_text()` 封装 |

> 当前代码中大量使用 XPath 文本匹配（C级），建议逐步替换为更稳定的：
> - 为关键按钮添加 `data-testid` 属性（最佳）
> - 或使用 class 组合 + 层级限制（如 `.el-table__body-wrapper button:has(span:contains('查看'))` 但 Selenium 不支持 `:contains` 原生，可用 XPath 替代）

---

## 4. Vue 异步等待策略

| 场景 | 等待条件 | WebDriverWait 示例（使用 BasePage 封装） |
|------|---------|----------------------------------------|
| **页面加载完成** | 表格行出现 + loading 消失 | `wait_vue_stable()` + `_wait_loading_gone()`（`wait.until(EC.invisibility_of_element_located(By.CSS_SELECTOR, '.el-loading-mask'))`） |
| **表格刷新（搜索/重置）** | Vue 稳定 + loading 消失 | `wait_vue_stable()`（内部调用 `wait.until(EC.staleness_of(old_row)` 或 JS 判断 Vue 渲染完成） |
| **弹窗A打开** | 弹窗可见 | `wait_dialog_open()`（`wait.until(EC.visibility_of_element_located(BasePage.DIALOG))`） |
| **弹窗嵌套（弹窗B）** | 弹窗数量 >1 | 测试脚本通过 JS 轮询：`document.querySelectorAll('.el-dialog:not([style*=none])').length > 1`，可封装为 `wait.until(lambda d: d.execute_script("...") >= 2)` |
| **弹窗关闭** | 弹窗不可见 | `wait_dialog_close()`（`wait.until(EC.invisibility_of_element_located(BasePage.DIALOG))`） |
| **Toast 提示** | toast 可见并自动消失 | `wait_for_toast_text()`（`wait.until(EC.visibility_of_element_located(By.CSS_SELECTOR, '.el-message'))`，并提取文本） |
| **提交申请后** | toast 出现 + 页面更新 | 第一步等待 toast，第二步 `wait_vue_stable()` 等待表格刷新 |

当前代码中均已实现，无需额外定义。

---

## 5. 自动化风险点

| 风险类别 | 风险描述 | 影响 | 缓解措施 |
|---------|---------|------|---------|
| **动态 placeholder** | 筛选表单 `placeholder` 文本可能因设计变更而修改 | 导致现有 XPath 定位失败 | 优先使用 `data-testid` 或 class 层级；建立文本变更多语言映射 |
| **Teleport 渲染** | `el-select` 选项、`el-date-picker` 面板可能渲染到 `<body>` 下，不在 `wh-filter-toolbar` 内 | 使用 `./div[contains(@class,"el-select")]` 无法定位选项 | 选项定位改用 `body > .el-popper .el-select-dropdown__item`；日期面板定位改用 `body > .el-picker-panel` |
| **嵌套弹窗遮挡** | 弹窗B可能覆盖弹窗A，直接操作弹窗A元素导致 `ElementClickInterceptedException` | 测试中断 | 先关闭弹窗B或确认焦点；使用 `move_to_element` 或 JS 点击 |
| **表格列数不稳定** | 列数可能在 6~12 之间变化（取决于权限/配置） | 列索引硬编码风险 | 使用列标题文本动态定位列；断言使用范围而非精确值 |
| **空数据状态** | 搜索结果为空时，表格行可能出现“暂无数据”行或行数为 0 | `TABLE_ROWS` 返回 0 行导致后续操作失败 | 判断行数 >0 再执行点击等操作；`wait_table_loaded()` 应判断非 loading 状态 |
| **权限控制** | 不同角色的按钮可见性不同（如“编辑”按钮可能隐藏） | 找不到元素导致 TimeoutError | 在 Fixture 中验证权限；使用条件等待（`find_elements` 并检查长度） |
| **Vue 动态 class** | `el-select[class*=" is-"]` 等动态 class 可能被 Selenium 缓存 | 定位器失效 | 使用稳定前缀，避免依赖动态后缀 |
| **el-table 虚拟滚动** | 若启用 `el-table` 的 `virtual-scroll`，表格行不在 DOM 中 | 点击指定行失败 | 使用 `execute_script` 滚动到行；或禁用虚拟滚动（非推荐） |

---

## 建议改进

1. **定位器升级**：将 C 级定位器（文本 XPath）尽量升级为 B 级（CSS + placeholder），或与开发协商增加 `data-testid` 属性。
2. **弹窗B操作封装**：当前无独立 Page Object 方法操作弹窗B内容，需新增方法（如 `select_waste_from_dialog`）并包含等待二次弹窗关闭的逻辑。
3. **嵌套弹窗等待封装**：将 JS 检测弹窗数量 >1 的等待逻辑抽成一个通用方法 `wait_nested_dialog_open()`，放入 `BasePage` 或 `ElementPlusHelper`。
4. **分离筛选区定位器**：为筛选区增加一个稳定的父容器定位器（如 `.search-area`），使内部定位器变为相对路径，提升可维护性。

---

*本分析基于代码版本 `warehouse/hazard-in-order`，与实际运行时的页面 HTML 可能略有差异，建议运行时核对。*