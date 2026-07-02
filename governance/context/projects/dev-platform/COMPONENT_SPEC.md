# COMPONENT_SPEC.md — AITest Platform 组件规格

> 基于 `COMPONENT_TREE.md` 生成 | UI 组件库: **Element Plus (Vue 3)**  
> 覆盖状态: `loading` · `empty` · `error` · `disabled` · `hover` · `focus`

---

## 1. AppLayout

| 属性 | 内容 |
|------|------|
| **职责** | 全局应用壳布局：侧栏 + 顶栏 + 主内容区。响应式折叠、权限菜单过滤。 |
| **根元素** | `<el-container>` 嵌套 `<el-aside>` + `<el-container>` |

### Props

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `collapse` | `boolean` | `false` | 侧栏是否折叠 |
| `menuList` | `MenuItem[]` | `[]` | 权限过滤后的菜单树 |

### Events

| 名称 | 载荷 | 说明 |
|------|------|------|
| `toggle-collapse` | `boolean` | 点击折叠按钮 |
| `menu-select` | `{ path, title }` | 菜单项选中 |

### 状态矩阵

| 状态 | 触发条件 | 视觉行为 |
|------|----------|----------|
| **loading** | 菜单数据异步加载中 | 侧栏菜单区域显示 `LoadingSkeleton`（3-8 条骨架行） |
| **empty** | `menuList` 为空（无权限/无菜单） | 侧栏居中显示 `EmptyState`，文案"暂无可用菜单" |
| **error** | 菜单请求失败 | 侧栏显示 `ErrorState` + 重试按钮，主区域不受影响 |
| **disabled** | — | 折叠按钮在移动端不可用时不渲染 |
| **hover** | 鼠标移入折叠按钮 | 按钮颜色加深（`--el-color-primary-light-3`） |
| **focus** | 键盘 Tab 到折叠按钮 | 显示 `outline: 2px solid var(--el-color-primary)` |

### 插槽

| 插槽名 | 位置 | 默认内容 |
|--------|------|----------|
| `header-left` | 顶栏左侧 | `Breadcrumb` |
| `header-center` | 顶栏中间 | `GlobalSearch` |
| `header-right` | 顶栏右侧 | `UserDropdown` |
| `sidebar-top` | 侧栏顶部 | Logo 区域 |
| `sidebar-bottom` | 侧栏底部 | 折叠按钮 |
| `default` | 主内容区 | `<router-view>` |

### 视觉变体

- **默认**: 侧栏展开 220px，Logo + 菜单全显
- **折叠**: 侧栏 64px，仅图标，`el-menu` 的 `collapse` 属性驱动
- **移动端**: 侧栏 overlay 模式，点击遮罩关闭

---

## 2. GlobalSearch

| 属性 | 内容 |
|------|------|
| **职责** | 全局搜索入口：输入关键词 → 异步联想 → 分类结果下拉 → 跳转 |
| **根元素** | `<div class="global-search">` 内嵌 `<el-autocomplete>` |

### Props

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `placeholder` | `string` | `"搜索菜单、单据…"` | 输入框占位 |
| `debounce` | `number` | `300` | 防抖毫秒 |
| `maxResults` | `number` | `10` | 每类最多条数 |

### Events

| 名称 | 载荷 | 说明 |
|------|------|------|
| `select` | `{ type, id, title }` | 选中一条结果 |
| `search` | `string` | 触发搜索（防抖后） |

### 状态矩阵

| 状态 | 触发条件 | 视觉行为 |
|------|----------|----------|
| **loading** | 请求联想结果中 | 下拉面板显示 `<el-icon class="is-loading"><Loading/></el-icon>` |
| **empty** | 联想返回空 | 下拉面板显示 "暂无匹配结果" + 搜索图标 |
| **error** | 联想请求异常 | 下拉面板显示 "搜索失败，请重试" + 重试文字按钮 |
| **disabled** | `disabled` prop 为 true | 输入框灰显，禁止输入 |
| **hover** | 鼠标移入结果项 | 背景变为 `--el-fill-color-light` |
| **focus** | 输入框聚焦 | 边框变为 `--el-color-primary`，若已有输入内容则自动弹出下拉 |

### 插槽

| 插槽名 | 位置 | 默认内容 |
|--------|------|----------|
| `prefix` | 输入框前缀 | 搜索图标 |
| `result-item` | 下拉结果单项 | 高亮关键词 + 类型标签 + 路径面包屑 |
| `result-group` | 下拉分组头 | 分类名（如"设备""人员"） |

---

## 3. SidebarMenu

| 属性 | 内容 |
|------|------|
| **职责** | 左侧导航菜单渲染，支持多级嵌套、权限过滤、当前激活高亮。 |
| **根元素** | `<el-menu>` (mode="vertical") |

### Props

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `menuList` | `MenuItem[]` | `[]` | 菜单树数据 |
| `collapse` | `boolean` | `false` | 折叠模式 |
| `defaultActive` | `string` | `""` | 当前激活路由 path |

### Events

| 名称 | 载荷 | 说明 |
|------|------|------|
| `select` | `{ index, indexPath }` | 菜单项点击（el-menu 原生） |

### 状态矩阵

| 状态 | 触发条件 | 视觉行为 |
|------|----------|----------|
| **loading** | `menuList` 为 `null`/`undefined` | 显示 6 条 `LoadingSkeleton` 菜单骨架 |
| **empty** | `menuList` 为 `[]` | 显示 "暂无菜单" 空状态 |
| **error** | —（由父级 AppLayout 统一处理） | — |
| **disabled** | `menuItem.disabled === true` | 菜单项灰色不可点击，`cursor: not-allowed` |
| **hover** | 鼠标移入菜单项 | 背景变为 `--el-menu-hover-bg-color` |
| **focus** | 键盘导航到菜单项 | 显示 `outline` 焦点环 |

### 插槽

| 插槽名 | 位置 | 默认内容 |
|--------|------|----------|
| `logo` | 菜单顶部 | Logo 图片 + 系统名称 |
| `menu-item-icon` | 单个菜单项图标前 | `<el-icon>` 图标组件 |
| `menu-item-title` | 单个菜单项文字 | 菜单标题文字 |

### 视觉变体

- **展开**: 图标 + 文字，缩进指示层级
- **折叠**: 仅图标 + `el-tooltip` 显示完整标题
- **多级**: `el-sub-menu` 嵌套，箭头展开/收起

---

## 4. Breadcrumb

| 属性 | 内容 |
|------|------|
| **职责** | 页面路径面包屑导航，自动匹配路由 `meta.breadcrumb`。 |
| **根元素** | `<el-breadcrumb>` |

### Props

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `items` | `BreadcrumbItem[]` | 自动从路由取 | `[{ path, title }]` |
| `separator` | `string` | `"/"` | 分隔符 |

### Events

| 名称 | 载荷 | 说明 |
|------|------|------|
| `click` | `{ path, title }` | 点击某一级（最后一级不可点击） |

### 状态矩阵

| 状态 | 触发条件 | 视觉行为 |
|------|----------|----------|
| **loading** | — | 不适用（数据同步获取自路由） |
| **empty** | 路由无 `meta.breadcrumb` | 仅显示当前页面标题 |
| **error** | — | 不适用 |
| **disabled** | 最后一级（当前页） | 不可点击，颜色为 `--el-text-color-regular` |
| **hover** | 鼠标移入可点击项 | 文字颜色变为 `--el-color-primary`，显示下划线 |
| **focus** | 键盘聚焦可点击项 | 显示 `outline` 焦点环 |

### 插槽

| 插槽名 | 位置 | 默认内容 |
|--------|------|----------|
| `default` | 替换默认渲染 | — |
| `item` | 单项渲染 | 文字 + link |

---

## 5. UserDropdown

| 属性 | 内容 |
|------|------|
| **职责** | 用户信息展示 + 下拉菜单（个人中心、修改密码、退出登录）。 |
| **根元素** | `<el-dropdown>` trigger="click" |

### Props

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `userInfo` | `UserInfo` | `{}` | `{ avatar, name, role }` |

### Events

| 名称 | 载荷 | 说明 |
|------|------|------|
| `command` | `string` | 下拉菜单命令：`"profile"` `"password"` `"logout"` |

### 状态矩阵

| 状态 | 触发条件 | 视觉行为 |
|------|----------|----------|
| **loading** | 用户信息异步加载 | 头像区域显示 `LoadingSkeleton` 圆形骨架（直径 36px） |
| **empty** | `userInfo` 为 `{}` | 显示默认头像 + "未登录" |
| **error** | 用户信息加载失败 | 显示默认头像 + "加载失败"，下拉菜单仅保留"退出" |
| **disabled** | — | — |
| **hover** | 鼠标移入 | 头像外圈显示 `--el-color-primary` 边框，光标变 pointer |
| **focus** | 键盘聚焦触发元素 | 显示 `outline` 焦点环 |

### 插槽

| 插槽名 | 位置 | 默认内容 |
|--------|------|----------|
| `trigger` | 下拉触发器 | 头像 + 用户名 + 箭头图标 |
| `dropdown` | 下拉面板 | `el-dropdown-menu` 三个菜单项 |

---

## 6. FilterPanel

| 属性 | 内容 |
|------|------|
| **职责** | 列表页顶部的查询/筛选表单区域，支持多条件组合、重置、导出。 |
| **根元素** | `<el-form>` inline + `<el-card>` 包裹 |

### Props

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `fields` | `FilterField[]` | `[]` | 筛选字段配置 |
| `modelValue` | `Record<string,any>` | `{}` | 表单值 v-model |
| `collapsed` | `boolean` | `true` | 是否折叠超出两行的字段 |

### Events

| 名称 | 载荷 | 说明 |
|------|------|------|
| `search` | `Record<string,any>` | 点击搜索 |
| `reset` | — | 点击重置 |
| `export` | `Record<string,any>` | 点击导出（携带当前筛选条件） |

### 状态矩阵

| 状态 | 触发条件 | 视觉行为 |
|------|----------|----------|
| **loading** | 选项数据（下拉/级联）异步加载 | 对应字段显示 `<el-skeleton :rows="1" animated />` 骨架 |
| **empty** | 下拉/级联选项为空 | 下拉面板显示 "暂无数据" |
| **error** | 选项数据请求失败 | 下拉面板显示 "加载失败" + 重试按钮 |
| **disabled** | 特定字段配置 `disabled: true` | 该字段灰显不可交互；全部 disabled 时操作按钮也 disabled |
| **hover** | 鼠标移入操作按钮 | 按钮颜色按 Element Plus 默认 hover 态 |
| **focus** | 聚焦到输入型字段 | 边框颜色变为 `--el-color-primary`，显示 focus 阴影 |

### 插槽

| 插槽名 | 位置 | 默认内容 |
|--------|------|----------|
| `field-{name}` | 替换字段 `{name}` 的渲染 | 默认 `el-input` / `el-select` / `el-date-picker` |
| `actions` | 操作按钮区域 | 查询 + 重置 + 导出按钮组 |
| `extra` | 按钮组之后扩展区 | 展开/收起按钮 |

### 视觉变体

- **展开**: 显示所有字段（最多 3 行）
- **折叠**: 仅显示首行（自动计算），尾部显示 "展开" 链接
- **内联**: 与 DataTable 顶部工具栏合并（`compact` prop）

---

## 7. DataTable

| 属性 | 内容 |
|------|------|
| **职责** | 通用数据表格：列配置渲染 + 排序 + 勾选 + 操作列 + 分页。 |
| **根元素** | `<div class="data-table">` 内嵌 `<el-table>` + `<el-pagination>` |

### Props

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `columns` | `Column[]` | `[]` | 列配置 |
| `data` | `any[]` | `[]` | 表格数据 |
| `loading` | `boolean` | `false` | 表格 loading |
| `total` | `number` | `0` | 总条数 |
| `page` | `number` | `1` | 当前页码 |
| `pageSize` | `number` | `20` | 每页条数 |
| `selection` | `boolean` | `false` | 是否开启勾选列 |

### Events

| 名称 | 载荷 | 说明 |
|------|------|------|
| `page-change` | `{ page, pageSize }` | 分页变化 |
| `sort-change` | `{ prop, order }` | 排序变化 |
| `selection-change` | `any[]` | 勾选变化 |
| `row-click` | `row, column, event` | 行点击 |

### 状态矩阵

| 状态 | 触发条件 | 视觉行为 |
|------|----------|----------|
| **loading** | `loading` prop 为 `true` | 表格区域覆盖半透明遮罩 + `el-icon Loading` 旋转图标 + "加载中…" |
| **empty** | `data` 为空数组 | 表格显示 `EmptyState` 组件，文案"暂无数据" |
| **error** | 接口报错（由父级传入） | 表格显示 `ErrorState` 组件，文案"数据加载失败"，含重试按钮 |
| **disabled** | 操作列按钮条件禁用 | 按钮灰色，`pointer-events: none` |
| **hover** | 鼠标移入行 | 行背景变为 `--el-table-row-hover-bg-color` |
| **focus** | 键盘聚焦表格 | 表格外框显示 `outline` |

### 插槽

| 插槽名 | 位置 | 默认内容 |
|--------|------|----------|
| `toolbar` | 表格上方工具栏 | 批量操作按钮 + 记录计数 |
| `column-{prop}` | 替换列 `{prop}` 的单元格渲染 | 纯文本 |
| `column-header-{prop}` | 替换列头 | 列标题 + sort icon |
| `actions` | 操作列 | 编辑/详情/删除按钮组 |
| `empty` | 空数据占位 | `EmptyState` |
| `pagination` | 分页区 | `el-pagination` |

### 视觉变体

- **带勾选**: `selection=true` 时首列显示 checkbox
- **树形**: `row-key` + `tree-props` 开启树形展开
- **合并**: 工具栏与 FilterPanel 合并模式

---

## 8. FormDialog

| 属性 | 内容 |
|------|------|
| **职责** | 新增/编辑实体的表单弹窗，含校验、提交 loading、关闭确认。 |
| **根元素** | `<el-dialog>` 内嵌 `<el-form>` |

### Props

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `visible` | `boolean` | `false` | 弹窗显隐 |
| `title` | `string` | `"新增"` | 弹窗标题 |
| `fields` | `FormField[]` | `[]` | 表单字段配置 |
| `modelValue` | `Record<string,any>` | `{}` | 表单数据 |
| `rules` | `FormRules` | `{}` | 校验规则 |
| `submitLoading` | `boolean` | `false` | 提交 loading |
| `mode` | `"create" \| "edit"` | `"create"` | 模式 |

### Events

| 名称 | 载荷 | 说明 |
|------|------|------|
| `submit` | `Record<string,any>` | 校验通过后提交 |
| `cancel` | — | 点击取消 / 关闭 |
| `update:visible` | `boolean` | v-model:visible |

### 状态矩阵

| 状态 | 触发条件 | 视觉行为 |
|------|----------|----------|
| **loading** | 编辑模式回填数据异步加载 | 表单区域显示 `LoadingSkeleton`（4-8 行表单骨架） |
| **empty** | 下拉/级联等选项为空 | 对应字段下拉面板显示 "暂无数据" |
| **error** | 回填数据请求失败 | 弹窗内容显示 `ErrorState`，含取消 + 重试按钮 |
| **disabled** | `mode="edit"` 且字段 `readonly: true` | 该字段灰显不可编辑 |
| **hover** | 鼠标移入提交按钮 | 按钮按 Element Plus primary hover 态变深 |
| **focus** | 弹窗打开后自动聚焦首个输入字段 | 字段边框 `--el-color-primary` |

### 插槽

| 插槽名 | 位置 | 默认内容 |
|--------|------|----------|
| `field-{name}` | 替换字段 `{name}` 渲染 | 默认 `el-input` / `el-select` / `el-date-picker` / `el-input-number` |
| `footer` | 弹窗底部按钮区 | 取消 + 确定按钮 |
| `extra-actions` | footer 中间 | — |

### 视觉变体

- **创建模式**: 表单为空，标题"新增{实体名}"
- **编辑模式**: 表单回填数据，标题"编辑{实体名}"
- **详情模式**: `readonly=true`，所有字段不可编辑，按钮仅"关闭"

---

## 9. DetailPanel

| 属性 | 内容 |
|------|------|
| **职责** | 实体详情信息展示，按分组渲染字段，含操作按钮。 |
| **根元素** | `<div class="detail-panel">` + `<el-descriptions>` |

### Props

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `data` | `Record<string,any>` | `{}` | 详情数据 |
| `schema` | `DetailField[]` | `[]` | 字段展示配置 |
| `loading` | `boolean` | `false` | 数据加载中 |

### Events

| 名称 | 载荷 | 说明 |
|------|------|------|
| `edit` | `data` | 点击编辑 |
| `back` | — | 点击返回 |

### 状态矩阵

| 状态 | 触发条件 | 视觉行为 |
|------|----------|----------|
| **loading** | `loading` prop 为 true | 显示 `LoadingSkeleton`：分组标题骨架 + 5-10 行描述项骨架 |
| **empty** | `data` 为空对象 | 显示 `EmptyState`，"暂无详情数据" |
| **error** | 数据接口异常 | 显示 `ErrorState`，"数据加载失败，请重试" + 重试按钮 |
| **disabled** | — | 编辑按钮根据权限隐藏/禁用 |
| **hover** | 鼠标移入可操作区域 | —（纯展示，通常无 hover 态） |
| **focus** | — | 编辑按钮 focus 显示 outline |

### 插槽

| 插槽名 | 位置 | 默认内容 |
|--------|------|----------|
| `header` | 详情顶部 | 实体标题 + `StatusTag` |
| `field-{name}` | 替换字段 `{name}` 渲染 | 纯文本 / 标签 / 图片 |
| `actions` | 底部/顶部操作区 | 编辑 + 返回按钮组 |
| `group-{groupName}` | 替换整个分组 | `el-descriptions` 分组 |

### 视觉变体

- **单栏**: 字段少时单列展示
- **双栏**: 字段多时使用 `el-descriptions` `column={2}` / `border`
- **带状态**: 顶部 header 插槽展示 `StatusTag` + 标题

---

## 10. StatusTag

| 属性 | 内容 |
|------|------|
| **职责** | 枚举状态值 → 颜色映射的标签展示。 |
| **根元素** | `<el-tag>` |

### Props

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `status` | `string \| number` | — | 状态值 |
| `typeMap` | `Record<string, TagType>` | 内置默认 | `{ 0:"info", 1:"success", 2:"warning", 3:"danger" }` |
| `size` | `"small" \| "default" \| "large"` | `"small"` | — |

### Events

无特殊事件（透传 `el-tag` 事件）。

### 状态矩阵

| 状态 | 触发条件 | 视觉行为 |
|------|----------|----------|
| **loading** | — | 显示宽度 48px 高度 20px 的 `<el-skeleton>` 片段 |
| **empty** | `status` 为 `null`/`undefined`/`""` | 显示灰色标签 "—" |
| **error** | `status` 不在 `typeMap` 中 | 显示 `type="info"` 标签 + 原始值（降级） |
| **disabled** | — | 不适用（纯展示） |
| **hover** | 鼠标移入 | `el-tag` 默认 hover（轻微放大阴影） |
| **focus** | — | 不适用 |

### 插槽

| 插槽名 | 位置 | 默认内容 |
|--------|------|----------|
| `default` | 标签内容 | 映射后的中文文本 |

### 视觉变体

- **dot**: 加小圆点前缀（`dot` prop）
- **plain**: 浅色背景（`effect="plain"`）

---

## 11. EmptyState

| 属性 | 内容 |
|------|------|
| **职责** | 统一空状态占位图 + 提示文案 + 可选操作按钮。 |
| **根元素** | `<div class="empty-state">` + `<el-empty>` |

### Props

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `description` | `string` | `"暂无数据"` | 提示文案 |
| `image` | `string` | 内置默认图 | 自定义图片 URL |
| `showAction` | `boolean` | `false` | 是否显示操作按钮 |

### Events

| 名称 | 载荷 | 说明 |
|------|------|------|
| `action` | — | 点击操作按钮 |

### 状态矩阵

| 状态 | 触发条件 | 视觉行为 |
|------|----------|----------|
| **loading** | — | 不适用（loading 由父组件 LoadingSkeleton 负责） |
| **empty** | 始终 | — |
| **error** | — | 不适用（error 由 ErrorState 负责） |
| **disabled** | `showAction` 为 false | 不渲染操作按钮 |
| **hover** | 鼠标移入操作按钮 | 按钮 hover 态 |
| **focus** | 聚焦按钮 | outline 焦点环 |

### 插槽

| 插槽名 | 位置 | 默认内容 |
|--------|------|----------|
| `image` | 图片区域 | `<el-empty>` 默认插画 |
| `description` | 描述文字 | 文本 |
| `actions` | 操作区 | `el-button`（如"新增""导入"） |

---

## 12. ErrorState

| 属性 | 内容 |
|------|------|
| **职责** | 统一错误展示：错误图标 + 信息 + 重试/返回操作。 |
| **根元素** | `<div class="error-state">` + `<el-result>` icon="error" |

### Props

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `title` | `string` | `"加载失败"` | 错误标题 |
| `subTitle` | `string` | `"请检查网络后重试"` | 错误详情 |
| `showRetry` | `boolean` | `true` | 显示重试按钮 |
| `showBack` | `boolean` | `false` | 显示返回按钮 |

### Events

| 名称 | 载荷 | 说明 |
|------|------|------|
| `retry` | — | 点击重试 |
| `back` | — | 点击返回 |

### 状态矩阵

| 状态 | 触发条件 | 视觉行为 |
|------|----------|----------|
| **loading** | — | 不适用 |
| **empty** | — | 不适用 |
| **error** | 始终 | — |
| **disabled** | `showRetry`/`showBack` 为 false | 对应按钮不渲染 |
| **hover** | 鼠标移入按钮 | 按钮 hover 态 |
| **focus** | 聚焦按钮 | outline 焦点环 |

### 插槽

| 插槽名 | 位置 | 默认内容 |
|--------|------|----------|
| `icon` | 图标区 | `el-result` error 图标 |
| `extra` | 按钮区之后 | — |

### 视觉变体

- **整页**: 占满视口，垂直居中
- **内嵌**: 紧凑模式，用于表格/面板内
- **网络错误**: 特定图标 + "网络连接失败"
- **权限错误**: 403 图标 + "暂无访问权限"

---

## 13. LoadingSkeleton

| 属性 | 内容 |
|------|------|
| **职责** | 骨架屏占位，模拟内容区域布局。 |
| **根元素** | `<el-skeleton>` animated |

### Props

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `variant` | `"table" \| "form" \| "card" \| "detail" \| "text"` | `"text"` | 骨架变体 |
| `rows` | `number` | `3` | 行数（table/text 变体） |
| `loading` | `boolean` | `true` | 是否显示骨架 |

### Events

无。

### 状态矩阵

| 状态 | 触发条件 | 视觉行为 |
|------|----------|----------|
| **loading** | `loading=true` | `el-skeleton` 条纹动画 |
| **empty** | — | `loading=false` 且无 children 时透出默认插槽 |
| **error** | — | 不适用 |
| **disabled** | — | 不适用 |
| **hover** | — | 无交互 |
| **focus** | — | 无交互 |

### 插槽

| 插槽名 | 位置 | 默认内容 |
|--------|------|----------|
| `default` | 骨架屏内部（loading 结束后显示） | — |
| `template` | 自定义骨架模板 | `el-skeleton-item` 组合 |

### 视觉变体

| 变体 | 骨架布局 |
|------|----------|
| **table** | 表头行 + N 行 4 列矩形 |
| **form** | N 行 label(80px) + input(200px) |
| **card** | 图片区(150px) + 标题 + 2 行文本 |
| **detail** | 分组标题 + N 个 label-value 对 |
| **text** | N 行宽度随机文本块 |

---

## 14. ConfirmDialog

| 属性 | 内容 |
|------|------|
| **职责** | 危险操作二次确认弹窗，支持自定义标题/内容/按钮文案/图标。 |
| **根元素** | `<el-dialog>` + `<el-icon><WarningFilled/></el-icon>` |

### Props

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `visible` | `boolean` | `false` | 显隐 |
| `title` | `string` | `"确认操作"` | 标题 |
| `content` | `string` | `"确定要执行此操作吗？"` | 内容 |
| `confirmText` | `string` | `"确定"` | 确认按钮 |
| `cancelText` | `string` | `"取消"` | 取消按钮 |
| `type` | `"warning" \| "danger"` | `"warning"` | 风格 |
| `confirmLoading` | `boolean` | `false` | 确认按钮 loading |

### Events

| 名称 | 载荷 | 说明 |
|------|------|------|
| `confirm` | — | 点击确定 |
| `cancel` | — | 点击取消/关闭 |
| `update:visible` | `boolean` | — |

### 状态矩阵

| 状态 | 触发条件 | 视觉行为 |
|------|----------|----------|
| **loading** | `confirmLoading=true` | 确定按钮显示 loading 动画，禁用点击 |
| **empty** | — | 不适用 |
| **error** | — | 不适用（错误由调用方处理） |
| **disabled** | `confirmLoading=true` | 确定+取消按钮均 disabled |
| **hover** | 鼠标移入确定按钮 | `type="danger"` 时使用 `--el-color-danger-light-3` |
| **focus** | 弹窗打开时自动聚焦取消按钮 | outline 焦点环 |

### 插槽

| 插槽名 | 位置 | 默认内容 |
|--------|------|----------|
| `icon` | 内容顶部 | `WarningFilled` 黄色 / `CircleCloseFilled` 红色 |
| `content` | 文字区 | 提示文案 |
| `footer` | 底部按钮 | 取消 + 确定 |

### 视觉变体

- **warning**: 黄色警告图标，`confirmText` 使用 warning 按钮
- **danger**: 红色危险图标，`confirmText` 使用 danger 按钮

---

## 15. ImportDialog

| 属性 | 内容 |
|------|------|
| **职责** | 数据导入向导：下载模板 → 上传文件 → 预览校验 → 确认导入。 |
| **根元素** | `<el-dialog>` 内含步骤条 `<el-steps>` + 各步骤内容 |

### Props

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `visible` | `boolean` | `false` | — |
| `templateUrl` | `string` | — | 模板下载地址 |
| `accept` | `string` | `".xlsx,.xls"` | 允许文件类型 |

### Events

| 名称 | 载荷 | 说明 |
|------|------|------|
| `import` | `{ file, options }` | 确认导入 |
| `update:visible` | `boolean` | — |

### 状态矩阵

| 状态 | 触发条件 | 视觉行为 |
|------|----------|----------|
| **loading** | 文件上传解析中 / 导入提交中 | 对应步骤显示 loading 动画 + 进度百分比 |
| **empty** | 文件解析后无有效数据 | 预览步骤显示 `EmptyState`，"未解析到有效数据" |
| **error** | 文件格式错误/解析失败 | 当前步骤显示 `ErrorState`，具体错误信息 + 重新上传按钮 |
| **disabled** | 未完成当前步骤 | "下一步"按钮 disabled |
| **hover** | 鼠标移入拖拽区域 | 上传区域边框变为 `--el-color-primary` 虚线 |
| **focus** | 聚焦上传按钮 | outline 焦点环 |

### 插槽

| 插槽名 | 位置 | 默认内容 |
|--------|------|----------|
| `step-download` | 步骤1 | 模板下载链接 + 说明 |
| `step-upload` | 步骤2 | `el-upload` 拖拽区域 |
| `step-preview` | 步骤3 | 预览表格（正确/错误行高亮） |
| `step-result` | 步骤4 | 导入结果统计（成功N条/失败N条） |
| `footer` | 底部 | 上一步 + 下一步/确认导入 |

### 视觉变体

- **3步**: 跳过预览（小数据量）
- **4步**: 含预览校验（默认）
- **