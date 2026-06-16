# PAGE_CONTEXT — workflow / approval-chain

> 浏览器诊断：2026-06-15 15:07 | 诊断脚本 `tools/diag_approval_chain.py`
> ⚠️ 测试策略：仅操作已有审批链，不新增不删除

## 页面信息

| 属性 | 值 |
| --- | --- |
| 页面名称 | 审批链配置 |
| 路由 | `#/system/workflow/approval-chain` |
| 所属模块 | 工作流管理 (workflow) |
| 页面类型 | 表格页（checkbox多选 + 8列） + 弹窗表单 |
| Page Object | `page/workflow_page/ApprovalChainPage.py` (~310行, 3轮修复) |
| 测试脚本 | `script/workflow/test_approval_chain.py` (6 cases) |
| 诊断数据 | `tools/diag_approval_chain.json` |

> ⚠️ **不新增/不删除审批链**：审批链为生产预配置数据，创建/删除由运维手工执行。

---

---

## 环境实际数据（14 条，2026-06-15 CDP 诊断）

### 全部审批链清单

| # | 名称 | 编码 | 步骤数 | 审批流程 |
|:--:|------|------|:--:|------|
| 1 | 承包商入场审批 | `contractor_entry` | 1* | 安全部门审批(AND) → **系统管理员** |
| 2 | 危废入库审批链 | `wh_hazard_in` | 2 | 主管审批(AND) → **系统管理员** / 仓管审批(AND) → **陈骞** |
| 3 | 危废出库审批链 | `wh_hazard_out` | 2 | 主管审批(AND) → **陈骞** / 仓管审批(AND) → **系统管理员** |
| 4 | 备件盘点审批链 | `wh_stocktake` | 2 | 主管审批(AND) → **系统管理员** / 仓管审批(AND) → **tjw** |
| 5 | 备件入库审批链 | `wh_in` | 1 | 仓管审批(AND) → **系统管理员** |
| 6 | 备件出库审批链 | `wh_out` | 1 | 仓管审批(AND) → **系统管理员, 陈骞** |
| 7 | 备件领用申请审批链 | `wh_requisition` | 2 | 主管审批(AND) → **系统管理员, 陈骞** / 库管确认(AND) → **tjw** |
| 8 | 请假申请审批链 | `leave` | 1 | 管理员(AND) → **系统管理员, 陈骞** |
| 9 | 其他申请审批链 | `other` | 1 | 管理员(AND) → **系统管理员, 陈骞** |
| 10 | 访客登记审批链 | `visitor` | 1 | 管理员(AND) → **184, 陈骞** |
| 11 | 入场申请审批链 | `entry` | 1 | 管理员(AND) → **系统管理员, 陈骞** |
| 12 | 领用申请审批链 | `spare` | 1 | 管理员(AND) → **系统管理员, 陈骞** |
| 13 | 设备维保审批链 | `equipment` | 1 | 管理员(AND) → **系统管理员, 陈骞** |
| 14 | 生产报表审批流 | `GLOBAL` | 1 | 管理员(AND) → **系统管理员, 陈骞** |

> ①全部启用，适用部门="全局"。②审批模式全部为 AND（会签：所有人通过才流转）。③\*承包商入场审批在早期诊断显示为2步（安全部门审批+入场确认），近期诊断仅捕获1步，需人工确认。
> 分页：第1页 10 条，第2页 4 条。

### 审批人清单

| 审批人 | 出现次数 | 角色定位 |
|------|:--:|------|
| **系统管理员** | 12 | 系统超级管理员 |
| **陈骞** | 11 | 仓库主管/管理员 |
| **tjw** | 2 | 盘点确认+领用确认 |
| **184** | 1 | (疑似用户ID非显示名，见访客登记) |

### 步骤字段结构

| 字段 | 组件 | DOM 定位 | 说明 |
|------|:---:|------|------|
| 步骤名称 | `<el-input>` | `.step-card input` | 职位/角色描述，如"主管审批" |
| 审批模式 | `<el-select>` (二选一) | `.step-card .el-select` | AND / OR |
| 审批人 | `.approver-wrapper` | `.approver-tag .el-tag__content` | el-tag 列表，通过"选择审批人"按钮添加人员 |

---

## 页面关键功能

### 搜索区（3 个筛选字段 + 搜索/重置按钮）

| 控件 | 类型 | placeholder | 定位方式 |
| --- | :---: | --- | --- |
| 审批链名称 | `<el-input>` | `请输入` | JS label遍历 "审批链名称" → input |
| 审批链编码 | `<el-input>` | `请输入` | JS label遍历 "审批链编码" → input |
| 状态 | `<el-select>` | — | 下拉选择（启用/停用） |
| 搜索按钮 | `<el-button>` | — | `_js_click_search_or_reset("搜索")` |
| 重置按钮 | `<el-button>` | — | `_js_click_search_or_reset("重置")` |

### 工具栏

| 按钮 | 类型 | 定位方式 |
| --- | :---: | --- |
| 新增 | `<el-button primary>` | JS 文本搜索 `textContent.indexOf('新增')` |

### 表格列（8 列，含 checkbox 选择列）

| # | 列标题 | 数据类型 | 说明 |
|:--:| --- | --- | --- |
| 0 | (checkbox) | el-checkbox | 多选列，无列标题 |
| 1 | 审批链名称 | 文本 | 如"承包商入场审批" |
| 2 | 编码 | 文本 | 唯一标识，如 `contractor_entry` |
| 3 | 适用部门 | 文本 | 当前全部为"全局" |
| 4 | 步骤数 | 数字 | 1 或 2 |
| 5 | 状态 | el-switch | 全部启用 |
| 6 | 备注 | 文本 | 审批流说明 |
| 7 | 操作 | 按钮组 | **步骤配置** / **编辑** / **删除**（3个按钮） |

> ⚠️ 操作列有 **3** 个按钮（不是之前假设的 2 个），"步骤配置"按钮在编辑之前

### 新增弹窗（title="新增审批链配置"）

| 字段 | 类型 | placeholder | 默认值 | 说明 |
| --- | :---: | --- | --- | --- |
| 审批链名称 | `<el-input>` | `如：生产日报审批链` | 空 | 必填 |
| 审批链编码 | `<el-input>` | `如：DAILY_REPORT` | 空 | 必填，唯一 |
| 适用部门 | `<el-select>` | — | 空 | 选项含"鞍集（凌源）新能源科技有限公司"+测试脏数据 |
| 状态 | `<el-switch>` | — | **启用** (on) | 默认开启 |
| 备注 | `<el-textarea>` | `可选备注` | 空 | 选填 |

### 编辑弹窗（title="修改审批链配置"，字段同上，带回显值）

以"承包商入场审批"为例的回显值：
- 审批链名称 = `承包商入场审批`
- 审批链编码 = `contractor_entry`
- 适用部门 = (空，el-select 未回显)
- 状态 = 启用
- 备注 = `承包商入场申请默认审批链`

### 弹窗 DOM 结构

```
el-overlay (z-index: 2001+):
└── el-dialog:
    ├── el-dialog__header:
    │   ├── el-dialog__title: "新增审批链配置" / "修改审批链配置"
    │   └── el-dialog__headerbtn (×关闭)
    ├── el-dialog__body:
    │   └── el-form:
    │       ├── el-row:
    │       │   ├── el-col-12: el-form-item > label "审批链名称" > el-input > input
    │       │   └── el-col-12: el-form-item > label "审批链编码" > el-input > input
    │       └── el-row:
    │           ├── el-col-12: el-form-item > label "适用部门" > el-select
    │           ├── el-col-12: el-form-item > label "状态" > el-switch
    │           └── el-col-24: el-form-item > label "备注" > el-textarea > textarea
    └── el-dialog__footer:
        ├── button.el-button--primary: "确认"
        └── button.el-button: "取消"
```

---

## 关键定位策略

| 操作 | 方法 | 策略 |
| --- | --- | --- |
| 点击新增 | `click_add()` | JS 遍历 button textContent 匹配"新增"/"添加"/"新建" |
| 弹窗检测 | CSS | `.el-dialog:not([style*="display: none"])` |
| 弹窗表单字段 | `_find_field_in_dialog(keyword)` | JS 遍历 `.el-form-item__label` 匹配 label 文本 |
| 弹窗确认 | `dialog_confirm()` | JS 在 dialog 内找 `button.el-button--primary` |
| 弹窗取消 | `dialog_cancel()` | JS 在 dialog 内找 textContent 含"取消"的 button |
| 编辑行 | `click_row_action(1, "编辑")` | 操作列 3 个按钮中找"编辑" |
| 删除行 | `click_row_action(1, "删除")` | 操作列 3 个按钮中找"删除" |
| 步骤配置行 | `click_row_action(1, "步骤配置")` | 操作列 3 个按钮中找"步骤配置" |

---

## 已识别的 PO 缺失

| 缺失 | 影响 | 优先级 |
|------|------|:--:|
| `input_code(value)` — 按"审批链编码"搜索 | 无法通过编码搜索 | P1 |
| `input_status(value)` — 按"状态"el-select 筛选 | 无法按状态筛选 | P1 |
| `get_table_headers()` 遗漏 checkbox 列 | 列索引偏移 | P2 |
| `click_row_step_config(row)` — "步骤配置"按钮 (CDP) | 无法测试步骤配置功能 | **P0** |
| `get_step_editor()` — 读取步骤配置面板 | 无法验证步骤配置内容 | **P0** |
| `close_step_editor()` — 关闭步骤配置面板 | 无法恢复列表状态 | P1 |

---

## 步骤配置面板 (inline `.step-editor`)

> ⚠️ 关键发现 (2026-06-15 CDP诊断): "步骤配置"不是弹窗/抽屉，是**页面内嵌面板**。
> 且按钮必须通过 CDP `Input.dispatchMouseEvent` 点击（JS/Selenium/ActionChains 均无效）。

### 触发方式

操作列的"步骤配置"按钮 → 页面内嵌展开 `.step-editor` 面板。列表不消失，面板在表格下方或侧边展示。

**唯一有效点击方式**: CDP (Chrome DevTools Protocol)
```python
driver.execute_cdp_cmd('Input.dispatchMouseEvent', {
    'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1
})
driver.execute_cdp_cmd('Input.dispatchMouseEvent', {
    'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1
})
```

### 面板 DOM 结构

```
.step-editor:
├── .step-list
│   ├── .step-card:
│   │   ├── .step-card-header
│   │   │   ├── .step-number: "步骤 1"
│   │   │   └── .step-actions: (删除步骤按钮)
│   │   ├── el-form-item > label "步骤名称" > el-input (职位/角色描述)
│   │   ├── el-form-item > label "审批模式" > el-select (AND / OR 二选一)
│   │   └── el-form-item > label "审批人"
│   │       └── .approver-wrapper:
│   │           ├── .approver-tag.el-tag > .el-tag__content: "系统管理员"
│   │           │   └── .el-tag__close (X 移除按钮)
│   │           └── button: "选择审批人" (弹窗添加人员)
│   ├── .step-card: (同上结构，步骤 2)
│   └── ...
└── .add-step-bar: (添加步骤按钮)
```

### 步骤字段详情

| 字段 | 组件 | DOM 定位 | 说明 |
|------|:---:|------|------|
| 步骤名称 | `<el-input>` | `.step-card input` | 职位/角色描述，如"主管审批""仓管审批""管理员" |
| 审批模式 | `<el-select>` (二选一) | `.step-card .el-select .el-select__selected-item` | AND=会签(全员通过) / OR=或签(任意一人) |
| 审批人 | `.approver-wrapper` 含 el-tag 列表 | `.approver-tag .el-tag__content` | 已选审批人展示为 tag，通过"选择审批人"按钮弹窗添加 |

### 完整步骤数据 (14/14 已诊断)

见上方「环境实际数据」章节的审批流程列，已含全部 14 条链的步骤名称+审批人。诊断数据文件: `tools/diag_steps_detail.json`。
| `get_table_row_count()` 含 checkbox 行 | 行数可能多算 | P3 |

---

## 修复历史

| 轮次 | 问题 | 根因 | 修复 |
|:---:|------|------|------|
| 1 | 点击新增无弹窗 | 路由短路径→完整路径 | sidebar_navigator 修复 |
| 2 | 仍无弹窗 | DIALOG XPath `[last()]` 选到隐藏overlay | 增加 el-drawer 支持 |
| 3 | **真正的根因** | ① XPath span嵌套 ② CSS hidden overlay ③ placeholder≠label | ① JS文本搜索 ② CSS Selector ③ JS label遍历 |

## 已知坑位

1. **6 个 overlay** — XPath `[last()]` 不可靠，用 CSS `:not([style*="display: none"])`
2. **按钮文字可能直接在 `<button>` 中** — 用 JS textContent 不用 XPath span/text()
3. **placeholder ≠ label** — 弹窗"名称" placeholder="如：生产日报审批链"，定位必须用 label 文本
4. **编辑弹窗复用新增弹窗** — title 改变，字段相同
5. **操作列有 3 个按钮** — "步骤配置"/"编辑"/"删除"，`click_first_row_edit()` 需确认匹配到"编辑"而非"步骤配置"
6. **el-select "适用部门"有测试脏数据** — 下拉选项含 `test20260611*新增` 条目，全量回归需处理

