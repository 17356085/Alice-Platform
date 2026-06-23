好的，我们来对 `system` 模块下的 `api-management` 页面进行分析。

`api-management` 是典型的 **后台 CRUD 管理页面**，通常包含搜索筛选区、数据表格、分页组件以及新增/编辑/详情弹窗。

### 分析产出

以下是根据我们约定的 `PAGE_CONTEXT.md` 和 `PAGE_ELEMENT_POSITION.md` 格式生成的分析结果。

---

## PAGE_CONTEXT.md

```markdown
# API管理页面 (api-management)

## 基本信息
- **页面名称**: API管理 (API Management)
- **所属模块**: 系统管理 (System)
- **页面URL**: `/system/api` (假设)

## 页面整体结构
1.  **顶部**：面包屑导航 + 页面标题 “API管理” + 搜索筛选区。
2.  **主内容区**：数据表格，包含多列数据及操作按钮。
3.  **底部**：分页组件。
4.  **浮层**：新增/编辑弹窗（Dialog）、详情弹窗。

## 页面元素清单

### 1. 搜索/筛选区

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `search-apiName` | API名称搜索输入框 | `el-input` | 搜索区 | placeholder: "请输入API名称" |
| `search-status` | 状态筛选下拉框 | `el-select` | 搜索区 | placeholder: "请选择状态" |
| `search-requestMethod` | 请求方式筛选下拉框 | `el-select` | 搜索区 | placeholder: "请选择请求方式" |
| `search-submit` | 搜索按钮 | `el-button` | 搜索区 | type="primary", text="搜索" |
| `search-reset` | 重置按钮 | `el-button` | 搜索区 | text="重置" |

### 2. 表格/列表区

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `table-apiName` | API名称列 | `el-table-column` (文本) | 表格区 | 列标题 "API名称" |
| `table-apiPath` | API路径列 | `el-table-column` (文本) | 表格区 | 列标题 "API路径" |
| `table-requestMethod` | 请求方式列 | `el-table-column` (标签) | 表格区 | 列标题 "请求方式"，显示为`el-tag` |
| `table-status` | 状态列 | `el-table-column` (标签) | 表格区 | 列标题 "状态"，“启用”为绿色tag，“禁用”为灰色tag |
| `table-createTime` | 创建时间列 | `el-table-column` (文本) | 表格区 | 列标题 "创建时间" |
| `table-operations` | 操作列 | `el-table-column` (操作) | 表格区 | 列标题 "操作" |
| `table-edit` | 行内编辑按钮 | `el-button` | 表格区 | text="编辑"，受权限控制 |
| `table-delete` | 行内删除按钮 | `el-button` | 表格区 | `type="danger"`, text="删除"，受权限控制 |
| `table-statusToggle` | 行内启用/禁用开关 | `el-switch` | 表格区 | 受权限控制 |

### 3. 分页区

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `pagination` | 分页组件 | `el-pagination` | 分页区 | 显示总条数、页码、每页条数 (10/20/30/50) |

### 4. 弹窗/对话框

#### 4.1 新增/编辑弹窗

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `dialog-title` | 弹窗标题 | 文本 | 弹窗 | “新增API” 或 “编辑API” |
| `dialog-apiName` | API名称输入框 | `el-input` | 弹窗 | 必填 |
| `dialog-apiPath` | API路径输入框 | `el-input` | 弹窗 | 必填 |
| `dialog-requestMethod` | 请求方式下拉框 | `el-select` | 弹窗 | 必填，选项: GET/POST/PUT/DELETE |
| `dialog-status` | 状态开关 | `el-switch` | 弹窗 | 用于设置启用/禁用 |
| `dialog-remark` | 备注输入框 | `el-input` (textarea) | 弹窗 | 非必填 |
| `dialog-submit` | 保存按钮 | `el-button` | 弹窗 | type="primary", text="确定" |
| `dialog-cancel` | 取消按钮 | `el-button` | 弹窗 | text="取消" |

#### 4.2 确认删除弹窗

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `confirm-delete-title` | 确认框标题 | 文本 | 弹窗 | 标题: "提示" |
| `confirm-delete-msg` | 确认框内容 | 文本 | 弹窗 | 文本: "确认删除该API吗？" |
| `confirm-delete-confirm` | 确认删除按钮 | `el-button` | 弹窗 | type="primary", text="确定" |
| `confirm-delete-cancel` | 取消删除按钮 | `el-button` | 弹窗 | text="取消" |

### 5. 页面状态

- **加载中**: 表格区域显示 `v-loading` 遮罩。
- **空数据**: 表格显示 `el-empty` 组件，文案 “暂无数据”。
- **错误**: （无明确设计）可通过全局异常捕获或网络拦截弹窗体现。
- **搜索无结果**: 表格清空，显示空数据状态。

### 6. 权限点

- **编辑**: `system:api:edit`，控制 `table-edit` 按钮及弹窗编辑功能。
- **删除**: `system:api:delete`，控制 `table-delete` 按钮。
- **新增**: `system:api:add`，控制搜索区的新增按钮（本页未识别，可能在页面右上角）。
- **状态切换**: `system:api:status`，控制 `table-statusToggle` 开关。

---
```

## PAGE_ELEMENT_POSITION.md

```markdown
# API管理页面 元素定位器设计

> 定位器优先级: A级 (data-testid/id) > B级 (CSS Selector) > C级 (XPath)
> 所有定位器基于 `BasePage` 定位方法封装。

## 1. 搜索区

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|---|---|---|---|---|
| `search-apiName` | A (CSS) | `[data-testid="search-apiName"]` | ⭐⭐⭐ | `input[placeholder="请输入API名称"]` (B) |
| `search-status` | A (CSS) | `[data-testid="search-status"] .el-select__wrapper` | ⭐⭐⭐ | `//div[contains(@placeholder,"请选择状态")]` (C) |
| `search-requestMethod` | A (CSS) | `[data-testid="search-requestMethod"]` | ⭐⭐⭐ | `.search-form .el-select:nth-child(2)` (B) |
| `search-submit` | A (CSS) | `[data-testid="search-submit"]` | ⭐⭐⭐ | `.search-form button.is-primary` (B) |
| `search-reset` | A (CSS) | `[data-testid="search-reset"]` | ⭐⭐⭐ | text("重置") (C) |

## 2. 表格区

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|---|---|---|---|---|
| `table-row` | B (CSS) | `.el-table__body tbody .el-table__row` | ⭐⭐⭐ | `//table[@class="el-table__body"]//tr` (C) |
| `table-edit` (第1行) | B (CSS) | `.el-table__row:nth-child(1) button:has-text("编辑")` | ⭐⭐ | `//button[contains(text(),"编辑")]` (C) |
| `table-delete` (第1行) | B (XPath) | `(//button[contains(text(),"删除")])[1]` | ⭐⭐ | `.el-table__row:nth-child(1) .danger-btn` (C) |
| `table-statusToggle` (第1行) | B (CSS) | `.el-table__row:nth-child(1) .el-switch` | ⭐⭐ | `(//span[@class="el-switch"])[1]` (C) |

**动态索引处理**: 使用 `nth-child(N)` 或 `(XPath)[N]` 处理多行，N 通常需要从上下文中获取（如搜索后取第一行）。

## 3. 分页区

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|---|---|---|---|---|
| `pagination-total` | B (CSS) | `.el-pagination__total` | ⭐⭐⭐ | `.el-pagination .el-pagination__total` (B) |
| `pagination-next` | B (CSS) | `[data-testid="pagination-next"]` | ⭐⭐⭐ | `.btn-next` (B) |
| `pagination-size` | B (CSS) | `[data-testid="pagination-size"] .el-select__wrapper` | ⭐⭐⭐ | `.el-pagination .el-select` (B) |

## 4. 弹窗区

### 4.1 新增/编辑弹窗

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|---|---|---|---|---|
| `dialog` | B (CSS) | `.el-overlay-dialog` | ⭐⭐⭐ | `.el-dialog` (B) |
| `dialog-apiName` | A (CSS) | `[data-testid="dialog-apiName"]` | ⭐⭐⭐ | `.el-dialog .el-form-item:nth-child(1) input` (B) |
| `dialog-requestMethod` | A (CSS) | `[data-testid="dialog-requestMethod"] .el-select__wrapper` | ⭐⭐⭐ | `//form[@class="el-form"]//div[contains(text(),"请求方式")]//following-sibling::div` (C) |
| `dialog-submit` | A (CSS) | `[data-testid="dialog-submit"]` | ⭐⭐⭐ | `.el-dialog .is-primary` (B) |
| `dialog-cancel` | A (CSS) | `[data-testid="dialog-cancel"]` | ⭐⭐⭐ | `.el-dialog__footer .el-button--default` (B) |

**坑位处理 (EP-001, EP-006)**:
- **Teleport**: `el-select` 的下拉选项（如“请求方式”）渲染在 `<body>` 下，操作前需 `WebDriverWait` 等待 `.el-popper` 可见，且定位器需包含 `body > .el-popper` 的范围约束。
- **`v-if` 条件渲染**: 弹窗内的 `el-form-item` 可能被 `v-if` 控制，与之交互前必须 `WebDriverWait` 等待元素 `visibility_of_element_located`，避免 `StaleElementReferenceException`。
- **遮罩层等待**: 弹窗关闭后，需等待 `.el-overlay` 消失，再执行后续操作。

### 4.2 确认删除弹窗

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|---|---|---|---|---|
| `confirm-delete` | B (CSS) | `.el-message-box` | ⭐⭐⭐ | `.el-message-box__wrapper` (B) |
| `confirm-delete-confirm` | B (CSS) | `.el-message-box .el-button--primary` | ⭐⭐⭐ | text("确定") (C) |
| `confirm-delete-cancel` | B (CSS) | `.el-message-box .el-button--default` | ⭐⭐⭐ | text("取消") (C) |

## 5. 页面状态

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|---|---|---|---|---|
| `loading-mask` | B (CSS) | `.el-loading-mask` | ⭐⭐⭐ | UI 状态检测，不定位具体组件 |
| `empty-state` | B (CSS) | `.el-empty` | ⭐⭐⭐ | `//div[contains(text(),"暂无数据")]` (C) |
| `toast-success` | B (CSS) | `.el-message--success` | ⭐⭐⭐ | `.el-message__content` (B) |

## 等待策略 (WebDriverWait)

- **操作弹窗前**: `EC.visibility_of_element_located(By.CSS_SELECTOR, ".el-dialog")`
- **操作下拉菜单前**: `EC.visibility_of_element_located(By.CSS_SELECTOR, "body > .el-popper")`
- **表格更新后**: `EC.presence_of_element_located(By.CSS_SELECTOR, ".el-table__body")`
- **删除操作后**: `EC.invisibility_of_element_located(By.CSS_SELECTOR, ".el-message-box")`
- **Toast提示消失后**: `EC.invisibility_of_element_located(By.CSS_SELECTOR, ".el-message")`
```

---

### 下一步: 自动生成 PAGE_INTERFACE.yaml

根据 `PAGE_CONTEXT.md` 中的结构，AI 可以自动提取并生成以下 `PAGE_INTERFACE.yaml` 供 `automation-agent` 消费：

```yaml
# PAGE_INTERFACE.yaml
page:
  name: api-management
  module: system
  url: /system/api
  elements:
    search:
      - api_name: { type: input, locator: A }
      - status: { type: select, locator: A }
      - request_method: { type: select, locator: A }
    table:
      - row: { locator: B, dynamic: true }
      - edit_btn: { locator: B, action: dialog, perms: system:api:edit }
      - delete_btn: { locator: C, action: confirm_dialog, perms: system:api:delete }
    dialog:
      - api_name: { type: input, locator: A, required: true }
      - request_method: { type: select, locator: A, required: true, options: [GET, POST, PUT, DELETE] }
      - submit_btn: { locator: A, action: submit }
  waits:
    dialog_open: EC.visibility_of_element_located
    dialog_close: EC.invisibility_of_element_located
    toast_end: EC.invisibility_of_element_located
```

这份 `YAML` 是整个自动化流程（导航、交互、断言）的**最小化契约**，效率远高于通读完整的 `PAGE_CONTEXT.md`。