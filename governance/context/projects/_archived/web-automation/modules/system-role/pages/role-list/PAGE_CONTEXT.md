好的，收到。我们来为 **模块: system-role，页面: role-list** 进行页面分析。

由于没有提供页面截图或 HTML 源码，我将基于当前时间背景下（2026年），一个典型的中后台管理系统（特别是基于 Vue 3 + Element Plus 技术栈）中，“角色列表”页面的常见标准设计进行推断分析。

分析输出将包含 `PAGE_CONTEXT.md`、`PAGE_ELEMENT_POSITION.md` 以及合并后的 `PAGE_INTERFACE.yaml`。

---

### 文件1: PAGE_CONTEXT.md

```markdown
# 页面上下文: 角色列表 (role-list)

## 基本信息
- **页面名称**: 角色列表
- **所属模块**: 系统角色 (system-role)
- **页面 URL**: `/system/role` (假设)
- **技术栈**: Vue 3, Element Plus

## 1. 页面整体结构
- **布局**: 典型的中后台布局。顶部为页面标题与面包屑导航，主内容区由“搜索/筛选区”和“表格/列表区”组成。
- **权限提示**: 页面上的“新增”、“编辑”、“删除”、“分配用户”等操作按钮，通常由后端返回的权限点控制显隐。

## 2. 搜索/筛选区
位于表格上方，包含：
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `search-role-name` | 角色名称输入框 | `el-input` | 搜索区 | 用于模糊搜索角色名称 |
| `search-status` | 状态选择器 | `el-select` | 搜索区 | 用于筛选角色状态 (启用/禁用) |
| `search-btn` | 搜索按钮 | `el-button` (primary) | 搜索区 | 触发搜索操作 |
| `reset-btn` | 重置按钮 | `el-button` (default) | 搜索区 | 重置所有搜索条件并重新加载数据 |
| `create-btn` | 新增按钮 | `el-button` (primary) | 搜索区 | 打开“新增角色”弹窗 |

<details>
<summary><b>3. 表格/列表区</b> (点击展开)</summary>

表格展示角色数据，支持分页和排序（如按创建时间排序）。

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `table` | 角色信息表格 | `el-table` | 表格区 | |
| `col-index` | 序号列 | `el-table-column` (type="index") | 表格区 | 静态列 |
| `col-role-name` | 角色名称列 | `el-table-column` (prop="roleName") | 表格区 | 文本 |
| `col-role-code` | 角色编码列 | `el-table-column` (prop="roleCode") | 表格区 | 文本，唯一标识 |
| `col-status` | 状态列 | `el-table-column` (prop="status") | 表格区 | 显示为 `el-tag` (启用/禁用) |
| `col-create-time` | 创建时间列 | `el-table-column` (prop="createTime") | 表格区 | 文本，可排序 |
| `col-description` | 备注列 | `el-table-column` (prop="description") | 表格区 | 文本，可能被省略 (show-overflow-tooltip) |
| `col-operations` | 操作列 | `el-table-column` (fixed="right") | 表格区 | 包含多个操作按钮，宽度固定 |
| `op-edit` | 编辑按钮 | `el-button` (text, icon) | 表格区操作列 | 打开“编辑角色”弹窗 |
| `op-delete` | 删除按钮 | `el-button` (text, icon, danger) | 表格区操作列 | 删除操作，通常有二次确认弹窗 |
| `op-permission` | 分配权限按钮 | `el-button` (text, icon) | 表格区操作列 | 打开“分配权限”弹窗或跳转权限配置页 |
| `op-assign-user` | 分配用户按钮 | `el-button` (text, icon) | 表格区操作列 | 打开“选择用户”弹窗 |
</details>

## 4. 分页区
位于表格底部，使用 Element Plus 的 `el-pagination` 组件。

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `pagination` | 分页组件 | `el-pagination` | 分页区 | |
| `page-size-select` | 每页条数选择器 | `el-pagination` 内部 | 分页区 | 默认 `[10, 20, 50, 100]` |
| `current-page` | 当前页码 | `el-pagination` 内部 | 分页区 | |
| `total` | 总记录数 | `el-pagination` 内部 | 分页区 | 显示文字“共 X 条” |
| `page-prev` | 上一页按钮 | `el-pagination` 内部 | 分页区 | |
| `page-next` | 下一页按钮 | `el-pagination` 内部 | 分页区 | |
| `page-jump` | 跳转输入框 | `el-pagination` 内部 | 分页区 | |

## 5. 弹窗/对话框

### 5.1 新增/编辑角色弹窗 (`dialog-role-form`)
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `dialog-role-form` | 角色表单弹窗 | `el-dialog` | 弹窗 | 标题：“新增角色” / “编辑角色” |
| `field-role-name` | 角色名称输入框 | `el-input` | 弹窗表单 | 必填项，长度限制 |
| `field-role-code` | 角色编码输入框 | `el-input` | 弹窗表单 | **新增时必填**，编辑时可能禁用 |
| `field-status` | 状态开关 | `el-switch` | 弹窗表单 | 默认启用 |
| `field-description` | 备注输入框 | `el-input` (textarea) | 弹窗表单 | 选填 |
| `dialog-save` | 保存按钮 | `el-button` (primary) | 弹窗底部 | |
| `dialog-cancel` | 取消按钮 | `el-button` | 弹窗底部 | 关闭弹窗 |

### 5.2 删除确认弹窗 (`dialog-delete-confirm`)
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `dialog-delete-confirm` | 删除确认弹窗 | `el-dialog` / `ElMessageBox.confirm` | 弹窗 | 标题：“提示”，内容：“确认删除角色 [角色名称] 吗？” |
| `confirm-btn` | 确认按钮 | `el-button` (danger) | 弹窗底部 | |
| `cancel-btn` | 取消按钮 | `el-button` | 弹窗底部 | |

### 5.3 分配用户弹窗 (`dialog-assign-user`)
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `dialog-assign-user` | 分配用户弹窗 | `el-dialog` | 弹窗 | 标题：“选择用户” |
| `user-table` | 用户列表表格 | `el-table` | 弹窗内 | 多选，支持搜索 |
| `selected-users` | 已选用户标签 | `el-tag` | 弹窗顶部 | 显示已选用户数量或名称 |
| `dialog-assign-save` | 确定按钮 | `el-button` (primary) | 弹窗底部 | |
| `dialog-assign-cancel` | 取消按钮 | `el-button` | 弹窗底部 | |

## 6. 页面状态
| 状态 | 表现 |
|---|---|
| 加载中 | 表格区显示 `v-loading` 骨架屏或旋转图标 |
| 空数据 | 表格区显示 `el-empty` 组件，提示“暂无数据” |
| 搜索无结果 | 表格区显示 `el-empty` 组件，提示“没有找到匹配的记录” |
| 网络/请求错误 | 全局 `ElMessage.error` 提示“获取角色列表失败” |
| 操作成功 | 全局 `ElMessage.success` 提示“操作成功” |
| 操作失败 | 全局 `ElMessage.error` 提示错误信息 |

## 7. 权限点
| 元素ID | 关联权限点 (假设) | 说明 |
|---|---|---|
| `create-btn` | `system:role:add` | 新增角色 |
| `op-edit` | `system:role:edit` | 编辑角色 |
| `op-delete` | `system:role:delete` | 删除角色 |
| `op-permission` | `system:role:permission` | 分配权限 |
| `op-assign-user` | `system:role:assign` | 分配用户 |
```

---

### 文件2: PAGE_ELEMENT_POSITION.md

```markdown
# 元素定位: 角色列表 (role-list)

## 定位器设计原则
- **A级**: 优先使用 `data-testid`、稳定的 `id`、唯一的 `placeholder`、`aria-label`。
- **B级**: CSS Selector，使用稳定 class 组合。
- **C级**: XPath，作为保底方案。
- **Element Plus注意**: 下拉框选项、日期选择器等通过 Teleport 渲染到 `<body>` 下，定位器需加上 `body > .el-popper` 前缀。

## 定位器清单

### 搜索区
| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|---|---|---|---|---|
| `search-role-name` | CSS Selector | `#search-role-name .el-input__inner` | A | `placeholder` 属性: `input[placeholder="角色名称"]` (A级) |
| `search-status` | CSS Selector | `#search-status .el-select__wrapper` | B | XPath: `//div[contains(@id, 'search-status')]//input` (C级) |
| `search-btn` | CSS Selector | `button.btn-search` | B | XPath: `//button[span[text()='搜 索']]` (C级) |
| `reset-btn` | CSS Selector | `button.btn-reset` | B | XPath: `//button[span[text()='重 置']]` (C级) |
| `create-btn` | CSS Selector | `button.btn-create` | B | `data-testid="create-role-btn"` (A级-若存在) |

### 表格区
| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|---|---|---|---|---|
| `table` | CSS Selector | `.el-table` | B | |
| `col-role-name` | CSS Selector | `.el-table__body-wrapper tbody tr td:nth-child(2) .cell` | B | XPath: `//table//tr[{{row_index}}]/td[2]` (C级) |
| `op-edit` (首行) | XPath | `(//tr[contains(@class, 'el-table__row')])[1]//button[span[text()='编辑']]` | C | CSS: `.el-table__body-wrapper tr:first-child .el-button--text:has(.el-icon-edit)` (B级-若图标稳定) |
| `op-delete` (首行) | XPath | `(//tr[contains(@class, 'el-table__row')])[1]//button[span[text()='删除']]` | C | 同上，图标匹配 `.el-icon-delete` |
| `op-permission` (首行) | XPath | `(//tr[contains(@class, 'el-table__row')])[1]//button[span[text()='分配权限']]` | C | |
| `op-assign-user` (首行) | XPath | `(//tr[contains(@class, 'el-table__row')])[1]//button[span[text()='分配用户']]` | C | |

### 分页区
| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|---|---|---|---|---|
| `pagination` | CSS Selector | `.el-pagination` | B | |
| `page-size-select` | CSS Selector | `.el-pagination__sizes .el-select__wrapper` | B | |
| `page-next` | CSS Selector | `.el-pagination .btn-next` | B | XPath: `//div[contains(@class, 'el-pagination')]//button[@class='btn-next']` |

### 弹窗 (新增/编辑)
| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|---|---|---|---|---|
| `dialog-role-form` | CSS Selector | `.el-dialog:has(.el-dialog__title:contains('角色'))` | B | XPath: `//div[contains(@class, 'el-dialog') and .//span[contains(text(), '角色')]]` (C级) |
| `field-role-name` | CSS Selector | `.el-dialog:has(.el-dialog__title:contains('角色')) input[placeholder="请输入角色名称"]` | B | A级: `id="role-name"` 或 `data-testid="role-name-input"` |
| `dialog-save` | CSS Selector | `.el-dialog .el-dialog__footer .el-button--primary` | B | XPath: `//div[contains(@class, 'el-dialog')]//button[span[text()='确 定']]` (C级) |
| `dialog-cancel` | CSS Selector | `.el-dialog .el-dialog__footer .el-button:not(.el-button--primary)` | B | XPath: `//div[contains(@class, 'el-dialog')]//button[span[text()='取 消']]` (C级) |

### 弹窗 (分配用户)
| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|---|---|---|---|---|
| `dialog-assign-user` | CSS Selector | `.el-dialog:has(.el-dialog__title:contains('选择用户'))` | B | XPath: `//div[contains(@class, 'el-dialog') and .//span[contains(text(), '选择用户')]]` (C级) |
| `dialog-assign-save` | CSS Selector | `.el-dialog:has(.el-dialog__title:contains('选择用户')) .el-button--primary` | B | XPath: `//div[contains(@class, 'el-dialog')]//button[span[text()='确 定']]` (C级) |

### 通用 Toast/提示
| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|---|---|---|---|---|
| `toast-message` | CSS Selector | `.el-message .el-message__content` | A | 通用，捕获成功/失败反馈 |
| `dialog-confirm` | CSS Selector | `.el-message-box` | B | 用于确认删除等操作 |
| `confirm-save` | CSS Selector | `.el-message-box .el-button--primary` | B | 消息盒子中的确定按钮 |
| `confirm-cancel` | CSS Selector | `.el-message-box .el-button:not(.el-button--primary)` | B | 消息盒子中的取消按钮 |

## 等待策略
| 场景 | 等待条件 | 建议策略 |
|---|---|---|
| 页面初始化 | 表格第一行数据可见 | `WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".el-table__row")))` |
| 搜索时 | 搜索按钮变为可用 | `WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-search")))` |
| 弹窗出现 | 弹窗文本可见 | `WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".el-dialog")))` |
| 弹窗消失 | 弹窗完全消失 | `WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-dialog")))` |
| Toast出现 | Toast内容可见 | `WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".el-message")))` |
```

---

### 文件3: PAGE_INTERFACE.yaml (P1-2 自动生成)

```yaml
module: system-role
page: role-list
description: 系统角色管理-角色列表页面，支持角色的增删改查、权限配置和用户分配。

interfaces:
  - id: search-roles
    description: 搜索角色列表
    actions:
      - element: search-role-name
        action: input
        value: "{role_name}"
        wait: 1
      - element: search-status
        action: select
        value: "{status_value}"
        wait: 1
      - element: search-btn
        action: click
        wait: table-reload

  - id: reset-search
    description: 重置搜索条件
    actions:
      - element: reset-btn
        action: click
        wait: table-reload

  - id: navigate-to-create
    description: 打开新增角色弹窗
    actions:
      - element: create-btn
        action: click
        wait: dialog-role-form

  - id: create-role
    description: 填写并提交新增角色表单
    actions:
      - element: field-role-name
        action: input
        value: "{role_name}"
      - element: field-role-code
        action: input
        value: "{role_code}"
      - element: field-status
        action: switch
        value: "{status}" # true/false
      - element: field-description
        action: input
        value: "{description}"
      - element: dialog-save
        action: click
        wait: dialog-close

  - id: edit-role
    description: 编辑指定角色
    params:
      - name: row_index
        type: integer
        description: 从1开始的表格行索引
    actions:
      - element: op-edit
        action: click
        params:
          row_index: "{row_index}"
        wait: dialog-role-form
      - element: field-role-name
        action: clear
      - element: field-role-name
        action: input
        value: "{new_role_name}"
      - element: dialog-save
        action: click
        wait: dialog-close

  - id: delete-role
    description: 删除指定角色
    params:
      - name: row_index
        type: integer
        description: 从1开始的表格行索引
    actions:
      - element: op-delete
        action: click
        params:
          row_index: "{row_index}"
        wait: dialog-delete-confirm
      - element: confirm-btn
        action: click
        wait: toast-success

  - id: assign-permission
    description: 为指定角色分配权限
    params:
      - name: row_index
        type: integer
    actions:
      - element: op-permission
        action: click
        params:
          row_index: "{row_index}"
        wait: 1

  - id: check-table-data
    description: 获取表格指定行的数据
    params:
      - name: row_index
        type: integer
    output:
      - col-role-name
    actions:
      - action: get_text
        element: col-role-name
        params:
          row_index: "{row_index}"
```