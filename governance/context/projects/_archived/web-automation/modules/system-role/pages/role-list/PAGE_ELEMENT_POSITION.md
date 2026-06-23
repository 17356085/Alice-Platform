# PAGE_ELEMENT_POSITION — system-role / role-list

> 基于 PAGE_CONTEXT V1.0 (Selenium 实测 DOM) | 2026-06-11

## 搜索/筛选区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 角色名称 | XPATH | `//input[@placeholder='请输入角色名称']` | A | |
| 角色编码 | XPATH | `//input[@placeholder='请输入角色编码']` | A | |
| 状态下拉 | XPATH | `//div[contains(@class,'el-form-item')][.//label[contains(.,'状态')]]//div[contains(@class,'el-select')]` | B | |
| 搜索按钮 | XPATH | `//button[.//span[text()='搜索']]` | A | |
| 重置按钮 | XPATH | `//button[.//span[text()='重置']]` | A | |

## 工具栏

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 新增 | XPATH | `//button[.//span[text()='新增']]` | A | |
| 修改 | XPATH | `//button[.//span[text()='修改']]` | B | 未勾选行时 disabled |
| 删除 | XPATH | `//button[.//span[text()='删除']]` | B | 未勾选行时 disabled |
| 清空缓存 | XPATH | `//button[.//span[text()='清空缓存']]` | A | |

## 数据表格 (8列+复选框)

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 表格容器 | CSS | `.el-table` | A | |
| 表格行 | CSS | `.el-table__body-wrapper .el-table__row` | B | |
| 复选框 | CSS | `.el-checkbox` | B | |
| 角色名称列 | CSS | `td:nth-child(2) .cell` | B | |
| 角色编码列 | CSS | `td:nth-child(3) .cell` | B | |
| 修改按钮(行内) | XPATH | `.//button[.//span[text()='修改']]` | A | |
| 删除按钮(行内) | XPATH | `.//button[.//span[text()='删除']]` | A | |
| 权限按钮(行内) | XPATH | `.//button[.//span[text()='权限']]` | A | |
| 分配用户(行内) | XPATH | `.//button[.//span[text()='分配用户']]` | A | |

## 弹窗A — 新增/编辑角色

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 弹窗 | CSS | `.el-dialog` | A | |
| 角色名称 | XPATH | `//input[@placeholder='请输入角色名称']` | A | |
| 角色编码 | XPATH | `//input[@placeholder='请输入角色编码']` | A | |
| 显示顺序 | XPATH | `//input[@placeholder*='显示顺序']` | B | |
| 状态-启用 | XPATH | `//label[contains(@class,'el-radio')][.//span[contains(.,'启用')]]` | B | |
| 状态-停用 | XPATH | `//label[contains(@class,'el-radio')][.//span[contains(.,'停用')]]` | B | |
| 备注 | XPATH | `//textarea[@placeholder='请输入备注']` | A | |
| 确定 | CSS | `.el-dialog__footer .el-button--primary` | A | |

## 弹窗B — 权限分配 (核心)

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 权限弹窗 | XPATH | `//div[contains(@class,'el-dialog')][.//span[contains(.,'PC操作权限')]]` | A | 通过Tab文字唯一标识 |
| PC操作权限Tab | CSS | `#tab-operations` | A | 稳定 ID |
| 小程序权限Tab | CSS | `#tab-miniappOperations` | A | 稳定 ID |
| 数据权限Tab | CSS | `#tab-dataScope` | A | 稳定 ID |
| 权限分类(groups) | XPATH | `//div[contains(@class,'perm-group')]` | A | 自定义组件 |
| 分类展开箭头 | CSS | `.perm-group__arrow` | B | |
| 分类名称 | CSS | `.perm-group__name` | B | |
| 指定分类 | XPATH | `//div[contains(@class,'perm-group')][.//span[contains(@class,'perm-group__name') and contains(.,'{分类名}')]]` | A | 参数化 |
| 单个权限(active tab) | XPATH | `//div[contains(@class,'el-tab-pane') and contains(@class,'is-active')]//span[contains(@class,'el-checkbox__label') and contains(.,'{权限名}')]` | A | 参数化 |
| 确定按钮 | CSS | `.el-dialog__footer .el-button--primary` | A | |

## 弹窗C — 分配用户

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 弹窗 | XPATH | `//div[contains(@class,'el-dialog')][.//span[contains(.,'分配用户 -')]]` | A | |
| 左侧搜索框 | CSS | `.user-selector-simple .simple-left input[placeholder*='搜索']` | A | |
| 左侧部门筛选 | CSS | `.user-selector-simple .simple-left .dept-select` | B | |
| 勾选用户 | XPATH | `//tr[.//div[contains(.,'{username}')]]//label[contains(@class,'el-checkbox')]` | A | 参数化 |
| 右侧面板 | CSS | `.user-selector-simple .simple-right` | A | |
| 清空按钮 | XPATH | `//button[.//span[contains(.,'清空')]]` | A | |

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
