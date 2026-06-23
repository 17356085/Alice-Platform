# PAGE_CONTEXT — 用户表单页（新增/编辑/查看/分配角色 弹窗）

> **数据来源**: Selenium + Chrome 实际访问 `https://aiwechatminidemo.cimc-digital.com/#/system/user`，JS 提取 4 种弹窗的完整 DOM
> **采集日期**: 2026-06-10 | **测试用户**: szj (史战军)
> **关联文档**: [user-list/PAGE_CONTEXT.md](../user-list/PAGE_CONTEXT.md) | [MODULE_CONTEXT.md](../../MODULE_CONTEXT.md) | [ROLE_CONTEXT.md](../../../system-role/ROLE_CONTEXT.md)

---

## 1. 页面概述

用户管理模块采用**单页面 + 多弹窗**架构，所有增删改查操作均通过 Dialog 在列表页上完成。本文件记录 4 种弹窗的完整结构。

```
用户列表页 (/system/user)
    │
    ├── [新增] 按钮 ──→ 弹窗 A: 添加用户 (Dialog, 600px)
    │
    ├── 行内 [查看] ──→ 弹窗 B: 用户详情 (Dialog, 800px, el-descriptions)
    ├── 行内 [编辑] ──→ 弹窗 C: 修改用户 (Dialog, 600px)
    ├── 行内 [分配角色] → 弹窗 D: 分配角色 (Dialog, 500px, checkbox-group)
    └── 行内 [更多▾] ──→ 启用/重置密码 | 删除
```

### 1.1 弹窗总览

| 弹窗 | 标题 | 宽度 | 触发按钮 | 布局组件 | 底部按钮 |
|------|:---:|:---:|------|------|------|
| **A — 新增** | `添加用户` | 600px | 工具栏「新增」 | `el-form` (双列 `el-row`) | 确定 / 取消 |
| **B — 查看** | `用户详情` | 800px | 行内「查看」 | `el-descriptions` (只读表格) | 关 闭 |
| **C — 编辑** | `修改用户` | 600px | 行内「编辑」 | `el-form` (双列 `el-row`) | 确定 / 取消 |
| **D — 分配角色** | `分配角色` | 500px | 行内「分配角色」 | `el-form` + `el-checkbox-group` | 确定 / 取消 |
| **E — 更多菜单** | — | — | 行内「更多▾」 | `el-dropdown-menu` | — |

---

## 2. 弹窗 A — 添加用户（新增）

### 2.1 弹窗属性

| 属性 | 值 |
|------|------|
| 标题 | `添加用户` |
| 宽度 | `600px` |
| 表单布局 | `el-row` 双列（每列 `el-col-12`） |
| 标签宽度 | `100px`，右对齐 |

### 2.2 表单字段（11 个）

| 序号 | 字段标签 | 控件类型 | 必填 | placeholder | 默认值 | 位置 |
|:---:|------|:---:|:---:|------|------|:---:|
| 1 | **用户名** | `<input>` | ✅ | `请输入用户名` | — | Row1-左 |
| 2 | **姓名** | `<input>` | ✅ | `请输入姓名` | — | Row1-右 |
| 3 | **密码** | `<input type="password">` | ✅ | `请输入密码` | — | Row2-左 |
| 4 | **确认密码** | `<input type="password">` | ✅ | `请确认密码` | — | Row2-右 |
| 5 | **部门** | `<el-select>` | ✅ | `请选择部门（可多选）` | — | Row3-左 |
| 6 | **用户类型** | `<el-select>` | ✅ | — | — | Row3-右 |
| 7 | **状态** | `<input>` | | — | `1` | Row4-左 |
| 8 | **手机号** | `<input>` | | `请输入手机号` | — | Row4-右 |
| 9 | **邮箱** | `<input>` | | `请输入邮箱` | — | Row5-左 |
| 10 | **角色** | `<el-select>` | | — | — | Row5-右 |
| 11 | **备注** | `<textarea>` | | `请输入备注` | — | 全宽 |

### 2.3 底部按钮

| 按钮 | 类型 | 操作 |
|------|:---:|------|
| **确定** | `el-button--primary` | 前端校验 → `POST /api/system/user` → Toast → 关闭弹窗 → 刷新列表 |
| **取消** | `el-button` (default) | 关闭弹窗，不保存 |

---

## 3. 弹窗 B — 用户详情（查看）

### 3.1 弹窗属性

| 属性 | 值 |
|------|------|
| 标题 | `用户详情` |
| 宽度 | `800px` |
| 布局 | `el-descriptions` 只读表格（带边框 `is-bordered`） |

### 3.2 展示字段（el-descriptions 表格，2列布局）

| 序号 | 字段 | 渲染方式 | 实测示例 (szj) |
|:---:|------|------|------|
| 1 | **用户名** | 加粗文本 `<span style="font-weight:600">` | `szj` |
| 2 | **姓名** | 普通文本 | `史战军` |
| 3 | **手机号** | 普通文本 | `18369096382` |
| 4 | **邮箱** | 普通文本，空值显示 `-` | `-` |
| 5 | **组织名称** | 普通文本，空值显示 `-` | `-` |
| 6 | **角色** | `<el-tag type="info" size="small">` 标签组 | 7 个标签（普通员工、日报表填报员…） |
| 7 | **状态** | `<el-tag type="success" size="small">` | `启用`（绿色） |
| 8 | **最后登录** | 日期时间文本 | `2026-06-05 14:55:09` |
| 9 | **备注** | 普通文本，空值显示 `-`，跨 3 列 | `-` |

### 3.3 底部按钮

| 按钮 | 类型 | 说明 |
|------|:---:|------|
| **关 闭** | `el-button` (default) | 唯一按钮 — 纯查看模式，无编辑入口 |

---

## 4. 弹窗 C — 修改用户（编辑）

### 4.1 弹窗属性

| 属性 | 值 |
|------|------|
| 标题 | `修改用户` |
| 宽度 | `600px` |
| 表单布局 | `el-row` 双列（同新增弹窗） |

### 4.2 表单字段（13 个 — 比新增多 5 个，缺 3 个）

| 序号 | 字段标签 | 控件类型 | 状态 | 实测值 (szj) | 相比新增 |
|:---:|------|:---:|:---:|------|:---:|
| 1 | **用户名** | `<input>` | ✅ 可编辑 | `szj` | 相同 |
| 2 | **姓名** | `<input>` | ✅ 可编辑 | `史战军` | 相同 |
| 3 | **部门** | `<el-select>` | 🔒 **DISABLED** | — | ⚠️ 编辑时不可修改 |
| 4 | **用户类型** | `<el-select>` | 🔒 **DISABLED** | — | ⚠️ 编辑时不可修改 |
| 5 | **状态** | `<input>` | ✅ 可编辑 | `1` | 相同（默认启用） |
| 6 | **性别** | `<el-select>` | 🔒 **DISABLED** | — | 🆕 新增时无此字段 |
| 7 | **身份证号** | `<input>` | ✅ 可编辑 | — | 🆕 新增时无此字段 |
| 8 | **入职日期** | `<input>` (date) | ✅ 可编辑 | — | 🆕 新增时无此字段 |
| 9 | **岗位** | `<el-select>` | 🔒 **DISABLED** | — | 🆕 新增时无此字段 |
| 10 | **手机号** | `<input>` | ✅ 可编辑 | `18369096382` | 相同 |
| 11 | **邮箱** | `<input>` | ✅ 可编辑 | — | 相同 |
| 12 | **角色** | `<el-select multiple>` | 🔒 **DISABLED** | 7 个角色 | 🆕 新增时无此字段；multi模式 |
| 13 | **备注** | `<textarea>` | ✅ 可编辑 | — | 相同 |

### 4.3 新增 vs 编辑字段对比

| 新增有、编辑无 | 编辑有、新增无 | 编辑中 DISABLED |
|------|------|------|
| **密码** | **性别** | **部门** |
| **确认密码** | **身份证号** | **用户类型** |
| | **入职日期** | **岗位** |
| | **岗位** | **角色** |
| | **角色** | **性别** |

> ⚠️ **关键发现**: 编辑模式下，部门、用户类型、岗位、角色、性别均为 **disabled** 状态，不可修改！用户如需变更这些属性，需要去对应的管理页面（角色管理、组织管理）操作。这与预期不同——PO 代码 (`input_edit_name`) 仅能修改姓名。

### 4.4 底部按钮

| 按钮 | 类型 | 操作 |
|------|:---:|------|
| **确定** | `el-button--primary` | 提交 → `PUT /api/system/user` |
| **取消** | `el-button` (default) | 关闭弹窗 |

---

## 5. 弹窗 D — 分配角色

### 5.1 弹窗属性

| 属性 | 值 |
|------|------|
| 标题 | `分配角色` |
| 宽度 | `500px` |
| 布局 | `el-form` + `el-checkbox-group` |

### 5.2 字段

| 字段标签 | 控件类型 | 说明 |
|------|:---:|------|
| **用户名** | `<input disabled>` | 只读展示当前用户名 |
| **角色** | `<el-checkbox-group>` | 17 个角色 checkbox，已分配的默认勾选 |

### 5.3 角色列表（17 个角色，实测）

| 角色名称 | 超管 | 管理员 | 人员培训管理员 | 人员培训员工 | 普通员工 | 日报表填报员 | 日报表审核员 | 化验室取样填报员 | 化验室取样审核员 | 备品备件仓库管理员 | 仓库领用员 | 三剂消耗管理员 | 管理员(小程序) | 领导层(小程序) | 部门主管(小程序) | 承包商(小程序) | 普通员工(小程序) |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| szj | ☐ | ☐ | ☑ | ☐ | ☑ | ☑ | ☑ | ☑ | ☑ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☑ |

### 5.4 底部按钮

| 按钮 | 类型 | 操作 |
|------|:---:|------|
| **确定** | `el-button--primary` | 提交角色分配 → `PUT /api/system/user/role` |
| **取消** | `el-button` (default) | 关闭弹窗 |

### 5.5 🟢 与角色管理模块的关联

```
角色管理 (#/system/role)              用户管理 (#/system/user)
  │                                      │
  ├── 创建角色 (roleCode, 角色名)         │
  ├── 权限分配 → 菜单+按钮权限点          │
  │     └── PC操作权限 (500个checkbox)    │
  │     └── 小程序操作权限                │
  │     └── 数据权限 (单选)               │
  │                                      │
  │                              弹窗D: 分配角色
  │                              └── 勾选角色 → 用户获得角色
  │                                   └── 角色携带的权限 → 用户间接获得
  │
  └── 分配用户 → 反方向关联
```

> **核心理解**: 角色管理定义"哪些角色拥有哪些权限"，用户管理的「分配角色」是**将角色赋予用户**——用户通过角色间接获得菜单/按钮/数据权限。

---

## 6. 弹窗 E — 「更多」下拉菜单

| 菜单项 | 操作 |
|------|------|
| **启用/重置密码** | MessageBox 确认 → `PUT /api/system/user/password/reset/{id}` → Toast 展示新密码明文 |
| **删除** | MessageBox 确认 → `DELETE /api/system/user/{id}` → Toast → 刷新列表 |

---

## 7. 页面状态

| 状态 | 新增弹窗 | 编辑弹窗 | 查看弹窗 | 分配角色弹窗 |
|------|:---:|:---:|:---:|:---:|
| 字段为空（新增） | 全部空白 | — | — | — |
| 预填数据（编辑） | — | 用户名/姓名/手机号等已填充 | — | — |
| 只读模式 | — | — | el-descriptions 表格 | 用户名 disabled |
| 校验失败 | 红色 `.el-form-item__error` | 同左 | — | — |
| 提交中 | 确定按钮 loading | 同左 | — | 同左 |
| 提交成功 | green Toast + 关闭 | 同左 | — | green Toast + 关闭 |
| 提交失败 | red Toast: "数据已存在" | 同左 | — | 同左 |

---

## 8. 自动化定位速查

### 8.1 弹窗定位

| 弹窗 | 推荐定位方式 |
|------|------|
| 新增 | `//div[contains(@class,'el-dialog')][.//span[contains(.,'添加用户')]]` |
| 编辑 | `//div[contains(@class,'el-dialog')][.//span[contains(.,'修改用户')]]` |
| 查看 | `//div[contains(@class,'el-dialog')][.//span[contains(.,'用户详情')]]` |
| 分配角色 | `//div[contains(@class,'el-dialog')][.//span[contains(.,'分配角色')]]` |

### 8.2 字段定位（弹窗内）

```python
# 通过 label 定位输入框
def get_dialog_input(dialog, label_text):
    item = dialog.find_element(By.XPATH, 
        f'.//div[contains(@class,"el-form-item")][.//label[contains(.,"{label_text}")]]')
    return item.find_element(By.XPATH, './/input')

# 通过 label 定位下拉框
def get_dialog_select(dialog, label_text):
    item = dialog.find_element(By.XPATH,
        f'.//div[contains(@class,"el-form-item")][.//label[contains(.,"{label_text}")]]')
    return item.find_element(By.XPATH, './/div[contains(@class,"el-select")]')
```

### 8.3 查看弹窗 — el-descriptions 定位

```python
# 查看弹窗使用 el-descriptions 表格而非表单
# 定位: td.el-descriptions__label (字段名) + td.el-descriptions__content (字段值)
labels = driver.find_elements(By.CSS_SELECTOR, '.el-descriptions__label')
contents = driver.find_elements(By.CSS_SELECTOR, '.el-descriptions__content')
```

---

## 9. 与 Page Object 代码的差异

| 编号 | 差异点 | PO 预期 (UserManagePage.py) | 实测结果 |
|:---:|------|------|------|
| **D-01** | 编辑弹窗标题 | 未明确定义 | `修改用户` |
| **D-02** | 编辑弹窗字段数 | ~7 个 | **13 个** |
| **D-03** | 编辑时用户名字段 | 可能不可修改 | **可编辑！** |
| **D-04** | 编辑弹窗有密码字段 | PO 有 `input_password_in_dialog` | **实测无密码/确认密码字段** |
| **D-05** | 查看弹窗组件 | 未覆盖 | `el-descriptions`（不是 form） |
| **D-06** | 分配角色弹窗组件 | `el-checkbox` 组 | ✅ 正确 — 17 个 checkbox |
| **D-07** | 弹窗字段 "岗位" | 有 `select_dialog_option_by_text("岗位")` | 编辑弹窗中岗位字段 🔒**disabled** |
| **D-08** | 新增弹窗字段 "部门" placeholder | PO 未明确 | `请选择部门（可多选）` |

---

## 附录 A：变更记录

| 日期 | 版本 | 变更内容 |
|------|:---:|------|
| 2026-06-09 | V0.1 | 原始创建（内容已丢失） |
| 2026-06-10 | **V2.0** | Selenium 实测：4 种弹窗完整 DOM — 新增(11字段)/编辑(13字段6个disabled)/查看(el-descriptions)/分配角色(17个checkbox) |
