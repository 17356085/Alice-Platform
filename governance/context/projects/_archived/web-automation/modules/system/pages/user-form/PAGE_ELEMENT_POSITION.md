# PAGE_ELEMENT_POSITION — system-user / user-form

> 从 PAGE_CONTEXT V2.0 (Selenium 实测) + UserManagePage.py 提取 | 2026-06-11

## 弹窗A — 新增用户 (600px)

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 弹窗 | CSS | `.el-dialog` [标题="添加用户"] | A |
| 用户名 | XPATH | `//input[@placeholder='请输入用户名']` | A |
| 姓名 | XPATH | `//input[@placeholder='请输入姓名']` | A |
| 密码 | XPATH | `//input[@placeholder='请输入密码']` | A |
| 确认密码 | XPATH | `//input[@placeholder='请确认密码']` | A |
| 部门(tree) | XPATH | `//div[contains(@class,'el-form-item')][.//label[contains(.,'部门')]]//div[contains(@class,'el-select')]` | B |
| 用户类型 | XPATH | `//div[contains(@class,'el-form-item')][.//label[contains(.,'用户类型')]]//div[contains(@class,'el-select')]` | B |
| 手机号 | XPATH | `//input[@placeholder='请输入手机号']` | A |
| 邮箱 | XPATH | `//input[@placeholder='请输入邮箱']` | A |
| 角色(多选) | XPATH | `//div[contains(@class,'el-form-item')][.//label[contains(.,'角色')]]//div[contains(@class,'el-select')]` | B |
| 备注 | XPATH | `//textarea[@placeholder='请输入备注']` | A |
| 确定 | CSS | `.el-dialog__footer .el-button--primary` | A |

## 弹窗B — 查看详情 (800px)

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 弹窗 | CSS | `.el-dialog` [标题="用户详情"] | A |
| el-descriptions | CSS | `.el-descriptions` | A |
| 关闭 | CSS | `.el-dialog__footer .el-button` | B |

## 弹窗C — 编辑用户

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 弹窗 | CSS | `.el-dialog` [标题="修改用户"] | A |
| 表单字段 | — | 同新增(密码字段留空=不修改) | A |

## 弹窗D — 分配角色

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 弹窗 | CSS | `.el-dialog` [含"分配角色"标题] | A |
| 角色checkbox组 | CSS | `.el-checkbox-group` | A |
| 单个角色 | XPATH | `//label[contains(@class,'el-checkbox')][.//span[contains(.,'{角色名}')]]` | A |
| 确定 | CSS | `.el-dialog__footer .el-button--primary` | A |

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
