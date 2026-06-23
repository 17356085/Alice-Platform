# PAGE_ELEMENT_POSITION — system-user / user-list

> 基于 PAGE_CONTEXT V2.0 (Selenium 实测 DOM) | 2026-06-11
> A级=稳定属性 / B级=CSS Selector / C级=XPath保底

## 搜索/筛选区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 搜索输入框 | XPATH | `//input[@placeholder='搜索用户名/姓名/手机号']` | A | placeholder 稳定 |
| 角色筛选 | XPATH | `//div[contains(@class,'el-form-item')][.//label[contains(.,'角色')]]//div[contains(@class,'el-select')]` | B | label="角色" 定位 |
| 状态下拉 | XPATH | `//div[contains(@class,'el-form-item')][.//label[contains(.,'状态')]]//div[contains(@class,'el-select')]` | B | ⚠️ 实测为 el-select 非 radio-group |
| 查询按钮 | XPATH | `//button[.//span[text()='查询']]` | A | |
| 重置按钮 | XPATH | `//button[.//span[text()='重置']]` | A | |

## 工具栏

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 新增按钮 | CSS+XPATH | `.el-button--primary` 中第一个 | B | 备用: `//button[.//span[text()='新增']]` |
| 导出按钮 | CSS | `.el-button--success` | B | |
| 批量删除 | CSS | `.el-button--danger` | B | 未勾选时 disabled |

## 数据表格

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 表格容器 | CSS | `.el-table` | A | |
| 表格行 | CSS | `.el-table__body-wrapper .el-table__row` | B | |
| 复选框 | CSS | `.el-checkbox` (行内) | B | |
| 用户名列(Col1) | CSS | `td:nth-child(2) .cell` | B | 1-based索引 |
| 角色列 | CSS | `td:nth-child(5) .el-tag` | B | el-tag标签组 |
| 状态列 | CSS | `td:nth-child(7) .el-tag` | B | |
| 查看按钮 | XPATH | `.//button[.//span[text()='查看']]` | A | per-row |
| 编辑按钮 | XPATH | `.//button[.//span[text()='编辑']]` | A | per-row |
| 分配角色 | XPATH | `.//button[.//span[text()='分配角色']]` | A | per-row |
| 更多下拉 | CSS | `td .el-dropdown button` | B | per-row |
| 更多-重置密码 | XPATH | `//li[contains(@class,'el-dropdown-menu__item') and contains(.,'重置密码')]` | B | |
| 更多-删除 | XPATH | `//li[contains(@class,'el-dropdown-menu__item') and contains(.,'删除')]` | B | |

## 分页

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 分页总数 | CSS | `.el-pagination__total` | A | |
| 上一页 | CSS | `.el-pagination .btn-prev` | A | |
| 下一页 | CSS | `.el-pagination .btn-next` | A | |

## 弹窗 — 新增/编辑用户

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 弹窗容器 | CSS | `.el-dialog` | A | 可见的那个 |
| 弹窗标题 | CSS | `.el-dialog__title` | A | 新增="添加用户" |
| 用户名 | XPATH | `//input[@placeholder='请输入用户名']` | A | |
| 姓名 | XPATH | `//input[@placeholder='请输入姓名']` | A | |
| 密码 | XPATH | `//input[@placeholder='请输入密码']` | A | |
| 确认密码 | XPATH | `//input[@placeholder='请确认密码']` | A | |
| 部门 | XPATH | `//div[contains(@class,'el-form-item')][.//label[contains(.,'部门')]]//div[contains(@class,'el-select')]` | B | tree-select |
| 用户类型 | XPATH | `//div[contains(@class,'el-form-item')][.//label[contains(.,'用户类型')]]//div[contains(@class,'el-select')]` | B | ⚠️ 不是"岗位" |
| 手机号 | XPATH | `//input[@placeholder='请输入手机号']` | A | |
| 邮箱 | XPATH | `//input[@placeholder='请输入邮箱']` | A | |
| 角色(多选) | XPATH | `//div[contains(@class,'el-form-item')][.//label[contains(.,'角色')]]//div[contains(@class,'el-select')]` | B | multi-select |
| 备注 | XPATH | `//textarea[@placeholder='请输入备注']` | A | |
| 确定按钮 | CSS | `.el-dialog__footer .el-button--primary` | A | |
| 取消按钮 | CSS | `.el-dialog__footer button:not(.el-button--primary)` | B | |

## Toast

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| Toast消息 | CSS | `.el-message__content` | A | 取 `last()` 获取最新 |

## 与 PO 差异注意点

| 差异 | PO预期 | 实测 | 定位影响 |
|------|--------|------|----------|
| 状态控件 | el-radio-group | el-select | select_status()需用select定位 |
| 列标题Col5 | "部门" | "组织名称" | 索引定位不受影响 |
| 表单字段"岗位" | "岗位" | "用户类型" | 更新label文本 |
| 行按钮数 | 3个 | 4个(+查看) | 新增查看按钮定位 |

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
