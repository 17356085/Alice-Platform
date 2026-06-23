好的，页面分析基于提供的 **PAGE_CONTEXT** 和 **Element Plus 框架特征** 生成。由于未提供具体 HTML 源码，以下分析综合了上下文描述的 DOM 结构和 Element Plus 组件行为。

---

## TECH_ANALYSIS.md

> 模块：`workflow` | 页面：`approval-history` (我已审批)

### 1. Element Plus 组件识别

| 组件 | 用途 | 数量 |
|------|------|------|
| `el-form` | 搜索表单容器 | 1 |
| `el-form-item` | 表单字段包裹 | 3 |
| `el-select` | 审批状态下拉选择、工厂代码下拉选择 | 2 |
| `el-date-range-picker` | 报表日期范围选择 | 1 |
| `el-button` | 搜索、重置、查看详情按钮 | ≥3 |
| `el-table` | 审批记录列表展示 | 1 |
| `el-table-column` | 表格列（报表日期、工厂代码、申请人等） | 7 |
| `el-tag` | 审批状态标签（已通过/已驳回） | 每行数据一个 |
| `el-dialog` | 详情查看弹窗 | 1 |
| `el-input` (内部) | 工厂代码输入（el-select 的 filterable 输入） | 1 |

### 2. DOM 结构分析

**搜索区层级：**
```
body
└── #app
    └── .main-container
        └── .el-form (搜索表单)
            ├── .el-form-item (审批状态)
            │   └── .el-select
            │       └── .el-input__wrapper → input[readonly]
            ├── .el-form-item (报表日期)
            │   └── .el-date-range-picker
            ├── .el-form-item (工厂代码)
            │   └── .el-select
            │       └── .el-input__wrapper → input.el-input__inner[placeholder="请选择"]
            ├── button.el-button (搜索)
            └── button.el-button (重置)
```

**表格区：**
```
.el-table
├── .el-table__header-wrapper (表头)
│   └── thead → th (各列标题)
└── .el-table__body-wrapper (数据体)
    └── table → tbody → tr.el-table__row (数据行)
        └── td → .cell (列内容，含 el-tag 或 按钮)
```

**弹窗（详情）：**
```
body > .el-overlay.dialog-wrapper
└── .el-dialog
    ├── .el-dialog__header
    │   └── .el-dialog__title (标题)
    └── .el-dialog__body
        └── 详情信息（只读表单）
    └── .el-dialog__footer
        └── button.el-button (关闭)
```

**动态属性：**
- `el-select` 下拉选项通过 Teleport 渲染到 `body` 下，class 为 `el-select-dropdown__popper`（动态哈希）
- `el-table` 的 `el-table__row` 是动态生成的，行号不固定
- `el-tag` 的 type（success/danger）根据状态动态变化
- 弹窗 `el-dialog` 的 `wrapper` 层级可能随页面结构变化

### 3. 定位器设计表（A/B/C 三级）

| 元素 | 推荐定位策略 | 定位值 | 稳定性 | 备注 |
|------|-------------|--------|--------|------|
| 搜索表单 | CSS (class) | `.el-form` | A | 页面唯一搜索表单 |
| 审批状态下拉框 | XPATH (相邻标签) | `//label[text()='审批状态']/following-sibling::div//input` | A | label 稳定 |
| 报表日期输入 | XPATH | `//label[text()='报表日期']/following-sibling::div//input` | A | 或通过 BasePage 通用方法 |
| 工厂代码输入 | JS 遍历 label | 见下方备注 | B | 需 JS 找到“工厂” label 后的 input |
| 搜索按钮 | XPATH (文字) | `//button[.//span/text()='搜索']` | A | 文字稳定 |
| 重置按钮 | XPATH | `//button[.//span/text()='重置']` | A | |
| 表格容器 | CSS | `.el-table` | A | |
| 表格行 | CSS | `.el-table__body-wrapper .el-table__row` | B | 动态行 |
| 第一行“查看详情”按钮 | XPATH | `(//tr[contains(@class,'el-table__row')][1]//button[contains(text(),'查看')])` | B | 优先使用 `button[text()='详情']` |
| 详情弹窗 | CSS | `.el-dialog` | A | |
| 弹窗关闭按钮 | XPATH | `//div[contains(@class,'el-dialog')]//button[.//span/text()='关闭']` | A | |
| 审批状态标签 | XPATH | `//span[contains(@class,'el-tag')][text()='已通过' or text()='已驳回']` | B | 用于断言 |
| 加载遮罩 | CSS | `.el-loading-mask` | A | 搜索/刷新时出现 |

> ⚠️ 工厂代码特殊处理（参考 PAGE_CONTEXT）：  
> 使用 JS 遍历 `.el-form-item__label` 找到文本为「工厂」的 label，再获取其同级 `el-select` 内的 `input.el-input__inner`。  
> 封装方法：`input_factory(value)`

### 4. Vue 异步等待策略

| 场景 | 等待条件 | WebDriverWait 示例 |
|------|---------|-------------------|
| 页面加载 | 表格存在 | `wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".el-table")))` |
| 搜索/重置触发 | loading 消失 | `wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-loading-mask")))` |
| el-select 选项展开（Teleport） | 下拉面板可见 | `wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "body > .el-select-dropdown")))# 或 el-popper` |
| el-date-range-picker 面板打开 | 面板可见 | `wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".el-date-range-picker__panel")))` |
| 详情弹窗打开 | 弹窗可见 | `wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".el-dialog")))` |
| 详情弹窗关闭 | 弹窗不可见 | `wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-dialog")))` |
| 表格数据刷新（行变化） | 自实现等待 | 循环检查新旧行数或数据内容 |
| Toast 消息（若有） | Toast 出现/消失 | `EC.presence_of_element_located((By.CSS_SELECTOR, ".el-message"))` |

### 5. 自动化风险点

| 风险 | 说明 | 应对 |
|------|------|------|
| **Teleport 渲染** | el-select 选项、el-date-picker 面板、el-dialog 挂载在 body 下 | 定位器使用 `body > .el-popper`；避免 `is_displayed()` 判断 |
| **搜索按钮拦截** | 搜索/重置使用 JS 点击绕过前端的表单拦截 | 已封装 `_js_click_search_or_reset` 方法 |
| **工厂代码字段特殊** | 没有 label 的 for 属性，需 JS 遍历文字 | 保持 `input_factory()` 方法独立 |
| **空状态文案变体** | 空表格可能显示不同文案，影响断言 | 检查 `el-empty` 组件或 `no-data` 文案 |
| **El-table 行序号不稳定** | 分页、排序后行顺序变化 | 使用列内容（如申请人）定位，不依赖绝对行号 |
| **筛选后表单值残留** | 重置可能不完全清除 el-date-range-picker | 重置后额外清空该字段 |
| **权限影响元素可见性** | 可能部分用户无“查看详情”按钮 | 先断言按钮存在再点击 |

---

## PAGE_ELEMENT_POSITION.md

（可与 TECH_ANALYSIS.md 合并，此处独立展示关键定位器位置索引）

| 元素 | 定位器 | 备注 |
|------|--------|------|
| 审批状态下拉框 | `By.XPATH, "//label[text()='审批状态']/following-sibling::div//input"` | A级 |
| 报表日期输入 | `By.XPATH, "//label[text()='报表日期']/following-sibling::div//input"` | A级 |
| 工厂代码输入 | 参见 `input_factory()` JS 方法 | B级 |
| 搜索按钮 | `By.XPATH, "//button[.//span/text()='搜索']"` | A级 |
| 重置按钮 | `By.XPATH, "//button[.//span/text()='重置']"` | A级 |
| 表格容器 | `By.CSS_SELECTOR, ".el-table"` | A级 |
| 表格行 | `By.CSS_SELECTOR, ".el-table__body-wrapper .el-table__row"` | B级 |
| 第一行“详情”按钮 | `By.XPATH, "(//tr[contains(@class,'el-table__row')][1]//button[contains(text(),'详情')])"` | B级 |
| 详情弹窗 | `By.CSS_SELECTOR, ".el-dialog"` | A级 |
| 弹窗关闭 | `By.XPATH, "//div[contains(@class,'el-dialog')]//button[.//span/text()='关闭']"` | A级 |
| 加载遮罩 | `By.CSS_SELECTOR, ".el-loading-mask"` | A级 |
| 审批状态标签（已通过） | `By.XPATH, "//span[contains(@class,'el-tag')][text()='已通过']"` | B级 |

---

以上分析基于 PAGE_CONTEXT 的页面描述和 Element Plus 通用结构。实际 HTML 可能略有差异，建议在真实页面上执行一次 **diagnose** 脚本（如 `diagnose_page_approval.py`）来验证定位器有效性。