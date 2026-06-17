好的，遵照您的指示，作为一位Web端测试工程师和Selenium自动化测试专家，我将基于“系统管理”模块下的“菜单管理”页面，按照提供的模板和规范，为您进行完整的`page-analysis`。

由于没有提供实际的页面截图或HTML源码，我将基于“系统管理 -> 菜单管理”这类页面的通用结构和Element Plus组件库的特性，创建一个典型的、规范的示例输出。

---

### **模块上下文 (MODULE_CONTEXT.md - 摘要)**

**模块名称:** 系统管理
**模块描述:** 负责系统的核心配置，包括用户、角色、权限、菜单、字典、系统参数等后台管理功能。
**公共布局:** `Layout` (左侧菜单栏，右侧主内容区)。
**通用组件:** `el-dialog`, `el-table`, `el-form`, `el-tree`, `el-cascader`。
**导航模式:** `SidebarNavigator` 点击左侧菜单项，右侧内容区动态渲染。

---

### **Skill 输出: PAGE_CONTEXT.md**

# PAGE_CONTEXT.md — 菜单管理页面

## 1. 页面信息
- **页面名称**: 菜单管理 (Menu Management)
- **所属模块**: 系统管理 (System)
- **页面URL**: `/api/system/menu` (假设)
- **页面描述**: 用于管理系统的侧边栏菜单和按钮权限，支持树形结构展示，可进行新增、编辑、删除菜单/目录/按钮。

## 2. 页面整体结构
- **布局**: 左侧是**菜单目录树** (`el-tree`)，右侧是**菜单详情/列表区域** (`el-table` 或 详情面板)，顶部有操作按钮。
- **交互逻辑**: 点击左侧树节点，右侧切换显示该节点下的子菜单列表或菜单详情。

## 3. 页面元素清单

### 3.1 左侧：目录树区域

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| `menu-tree` | 菜单目录树，展示所有顶级菜单和子菜单的层级结构 | `el-tree` | 左侧区域 | 默认展开第一级，节点点击事件 |
| `tree-search-input` | 目录树搜索框（如有），用于快速检索菜单 | `el-input` | 左侧区域顶部 | 可选，可过滤树节点 |
| `tree-node-{id}` | 树节点，id为菜单ID，包含菜单名称和图标 | `el-tree-node` | 左侧区域 | 动态生成，用于定位具体节点 |
| `expand-all-btn` | 展开/折叠全部树节点按钮 | `el-button` | 左侧区域顶部 | 可选功能 |

### 3.2 右侧：操作区 & 列表/详情区

#### 3.2.1 顶部操作栏

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| `add-menu-btn` | 新增菜单按钮 | `el-button` | 右侧顶部 | 权限点：`system:menu:add` |
| `refresh-btn` | 刷新按钮 | `el-button` | 右侧顶部 |  |
| `edit-btn` | 编辑当前选中节点按钮 | `el-button` | 右侧顶部 | 需先选中左侧树节点 |

#### 3.2.2 菜单列表/详情表格 (当选中一个父节点时展示其子列表)

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| `menu-table` | 子菜单列表表格 | `el-table` | 右侧主区域 |  |
| `col-menu-name` | 列：菜单名称 | `el-table-column` | 表格列 | 文本类型 |
| `col-icon` | 列：图标 | `el-table-column` | 表格列 | 图标标签 |
| `col-sort` | 列：排序 | `el-table-column` | 表格列 | 数字类型 |
| `col-perms` | 列：权限标识 | `el-table-column` | 表格列 | 文本类型，如 `system:user:list` |
| `col-component` | 列：组件路径 | `el-table-column` | 表格列 | 文本类型 |
| `col-status` | 列：状态 | `el-table-column` | 表格列 | `el-tag` 标签 | 显示启用/禁用 |
| `col-created-at` | 列：创建时间 | `el-table-column` | 表格列 | 日期类型 |
| `col-operations` | 列：操作 | `el-table-column` | 表格列 | 包含按钮组 |
| `op-edit-btn-{id}` | 行内编辑按钮 | `el-button` (text/link) | 操作列 | 权限点：`system:menu:edit` |
| `op-delete-btn-{id}` | 行内删除按钮 | `el-button` (text/link) | 操作列 | 权限点：`system:menu:delete` |
| `op-add-child-btn-{id}` | 行内添加子菜单按钮 | `el-button` (text/link) | 操作列 | 可选 |

### 3.3 新增/编辑菜单弹窗 (`el-dialog`)

**弹窗标题**: `新增菜单`或`编辑菜单`

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| `menu-dialog` | 菜单表单对话框 | `el-dialog` | 全屏中央 |  |
| `dialog-title` | 弹窗标题 | `el-dialog__title` | 弹窗顶部 | 用于断言弹窗类型 |
| `form-menu-type` | 菜单类型 (目录/菜单/按钮) | `el-radio-group` | 弹窗表单 | 类型改变会影响下方字段 |
| `form-menu-name` | 菜单名称输入框 | `el-input` | 弹窗表单 |  |
| `form-parent-menu` | 上级菜单选择器 | `el-tree-select` / `el-cascader` | 弹窗表单 | 用于选择父节点 |
| `form-route-name` | 路由名称 | `el-input` | 弹窗表单 | 当类型为菜单时显示 |
| `form-route-path` | 路由路径 | `el-input` | 弹窗表单 | 当类型为菜单时显示 |
| `form-component` | 组件路径 | `el-input` | 弹窗表单 | 当类型为菜单时显示 |
| `form-perms` | 权限标识 | `el-input` | 弹窗表单 | 当类型为按钮时显示 |
| `form-icon` | 图标选择器 | `el-icon-picker` / `el-select` | 弹窗表单 | 当类型为目录或菜单时显示 |
| `form-sort` | 排序值 | `el-input-number` | 弹窗表单 |  |
| `form-is-cache` | 是否缓存 | `el-switch` | 弹窗表单 | 布尔值 |
| `form-is-visible` | 是否可见 | `el-switch` | 弹窗表单 | 布尔值 |
| `form-status` | 状态开关 | `el-switch` | 弹窗表单 | 启用/禁用 |
| `dialog-save-btn` | 确认保存按钮 | `el-button` (primary) | 弹窗底部 |  |
| `dialog-cancel-btn` | 取消按钮 | `el-button` | 弹窗底部 |  |
| `form-error-msg` | 表单验证错误信息 | `el-form-item__error` | 每个字段下方 | 动态出现 |

### 3.4 其他组件/状态

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| `loading-mask` | 页面加载遮罩 | `el-loading-mask` | 表格/树区域 | 数据加载时出现 |
| `empty-state` | 空数据状态 | `el-empty` | 表格区域 | 无数据时的占位符 |
| `toast-message` | 操作成功/失败提示 | `el-message` | 页面右上角 | 短暂出现 |
| `confirm-delete-dialog` | 删除确认弹窗 | `el-message-box` | 页面中央 | `msgbox` 组件，不是 `el-dialog` |

## 4. 权限敏感元素

- `add-menu-btn` (新增)
- `op-edit-btn-*` (编辑)
- `op-delete-btn-*` (删除)
- `recycle-bin-btn` (回收站，如有)

---

### **Skill 输出: PAGE_ELEMENT_POSITION.md**

# PAGE_ELEMENT_POSITION.md — 菜单管理页面定位器设计

**设计原则**:
- **A级 (推荐)**: 优先使用 `data-testid`, `id`, `name`, `placeholder`。
- **B级 (次选)**: 稳定的 `CSS Selector`。
- **C级 (兜底)**: 相对稳定的 `XPath`，使用文本或属性组合定位。
- **对于Element Plus组件**: 注意其动态渲染和Teleport特性。

## 元素定位器表

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 (B/C级) | 等待策略 (WebDriverWait) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `add-menu-btn` | A级 - data-testid | `data-testid="system-menu-add-btn"` | ⭐⭐⭐⭐⭐ | B: `button:has(svg-icon[icon="plus"])` <br> C: `//button/span[text()="新增"]` | `visibility_of_element_located`<br>等待按钮可见 |
| `menu-tree` | B级 - CSS Selector | `.menu-list .el-tree` | ⭐⭐⭐ | A: 如果增加id `#menuTree` <br> C: `//div[contains(@class, 'menu-list')]//div[contains(@class, 'el-tree')]` | `presence_of_element_located`<br>等待树渲染 |
| `tree-node-{id}` | B级 - CSS Selector | `.el-tree-node[data-id="{id}"]` | ⭐⭐⭐⭐ | C: `//div[contains(@class, 'el-tree-node')]//span[text()="{treeNodeName}"]` | `element_to_be_clickable`<br>等待节点可点击 |
| `menu-dialog` | B级 - CSS Selector | `.el-dialog[aria-label="新增菜单"], .el-dialog[aria-label="编辑菜单"]` | ⭐⭐⭐⭐ | C: `//div[contains(@class, 'el-dialog') and contains(.//span, '菜单')]` | `visibility_of_element_located`<br>等待弹窗可见 |
| `form-menu-name` | A级 - placeholder | `input[placeholder="请输入菜单名称"]` | ⭐⭐⭐⭐⭐ | B: `.el-dialog .el-form .el-input__inner[placeholder="请输入菜单名称"]` | `element_to_be_clickable`<br>等待输入框可交互 |
| `form-menu-type` | B级 - CSS Selector | `.el-dialog .el-radio-group` | ⭐⭐⭐ | C: `//div[contains(@class, 'el-dialog')]//div[contains(@class, 'el-radio-group')]` | `visibility_of_element_located`<br>等待单选框组可见 |
| `dialog-save-btn` | A级 - data-testid | `button[data-testid="menu-dialog-save-btn"]` | ⭐⭐⭐⭐⭐ | B: `.el-dialog .el-button--primary:not(.el-button--default)` <br> C: `//div[contains(@class, 'el-dialog')]//button/span[text()="确 定"]` | `element_to_be_clickable`<br>等待按钮可点击 |
| `op-delete-btn-{id}` | B级 - CSS Selector | `#menu-table .el-table__row[data-id="{id}"] .el-button--danger` | ⭐⭐⭐⭐ | C: `//tr[contains(@data-id, '{id}')]//button/span[contains(text(), '删除')]` | `visibility_of_element_located`<br>等待按钮在行内可见 |
| `confirm-delete-dialog` | B级 - CSS Selector | `.el-message-box__wrapper` | ⭐⭐⭐⭐ | C: `//div[contains(@class, 'el-message-box__wrapper')]` | `visibility_of_element_located`<br>等待确认框出现 |
| `toast-message` | B级 - CSS Selector | `.el-message__content` | ⭐⭐⭐⭐⭐ | C: `//p[contains(@class, 'el-message__content')]` | `presence_of_element_located`<br>等待Toast消息渲染 |

## 关键等待策略
- **弹窗打开**: 等待 `.el-dialog` 的 `visibility_of_element_located`。
- **表格加载**: 等待表格行 `.el-table__row` 出现，或等待 `.el-loading-mask` 消失 (`invisibility_of_element_located`)。
- **网络请求**: 对于表单提交，在点击保存按钮后，应等待 `.el-loading-mask` 在对话框内消失，以确保提交完成。
- **Vue 异步渲染**: 对动态属性（如 `data-id`），应使用 `wait_for_attribute` 或轮询等待。

---

### **附件: PAGE_INTERFACE.yaml (自动生成示例)**

> 该文件由后处理步骤自动生成，本例提供内容供参考。

```yaml
page:
  module: system
  name: menu-management
  url: /api/system/menu
  description: 系统菜单管理，树形结构，CRUD操作。

elements:
  - id: add-menu-btn
    type: button
    locator:
      primary:
        by: data-testid
        value: system-menu-add-btn
    action: click
    wait: element_to_be_clickable

  - id: form-menu-name
    type: input
    locator:
      primary:
        by: placeholder
        value: 请输入菜单名称
    action: fill
    wait: element_to_be_clickable
    constraints:
      required: true
      max_length: 50

  - id: dialog-save-btn
    type: button
    locator:
      primary:
        by: data-testid
        value: menu-dialog-save-btn
    action: click
    wait: element_to_be_clickable
    side_effect:
      - toast_success: 操作成功
      - dialog_close

  # ... 更多元素定义

navigations:
  - path: 系统管理 > 菜单管理
    via: sidebar
    url: /api/system/menu
```

**总结**: 本次`page-analysis`已根据规范和最佳实践完成。产出物清晰地定义了页面结构、所有关键元素以及它们的定位器设计，可用于后续的`testcase-design`和自动化代码生成。