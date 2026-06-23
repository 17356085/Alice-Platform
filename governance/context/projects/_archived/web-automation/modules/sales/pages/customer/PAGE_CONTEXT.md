# PAGE_CONTEXT — sales / customer

> 从 CustomerPage.py 实际代码提取 | 2026-06-17 | 覆盖过期文档

## 页面信息
- **页面名称**: 客户管理
- **路由**: `#/sales/customer`
- **PO**: `page/sales_page/CustomerPage.py` (继承 BasePage，无 ElementPlusHelper)
- **侧边栏导航**: `navigate_to("销售管理", "客户管理")`
- **页面性质**: CRUD 页面（新增/编辑/查看/资质维护）

## 页面整体结构

顶部全局导航栏 → 左侧菜单 → 主内容区：
1. **搜索/筛选区**: 1 个 el-input (客户名称/编码 二合一) + 2 个 el-select (客户等级/合作状态) + 3 个 el-button (查询/重置/新增客户)
2. **表格区**: el-table 7 列，含客户等级/合作状态标签
3. **分页区**: el-pagination

## 搜索/筛选区

| 元素ID | 描述 | 控件类型 | 定位器 | 等级 |
|:---|:---|:---|:---|:--:|
| `SEARCH_KEYWORD` | 客户名称/编码 | el-input | `//input[@placeholder="客户名称/编码"]` | A |
| `SEARCH_LEVEL` | 客户等级 | el-select | `//div[contains(@class,"el-select")][.//span[contains(normalize-space(.),"客户等级")]]` | A |
| `SEARCH_STATUS` | 合作状态 | el-select | `//div[contains(@class,"el-select")][.//span[contains(normalize-space(.),"合作状态")]]` | A |
| `BTN_SEARCH` | 查询 | el-button (primary) | CSS: `button.el-button--primary:not(.is-link)` / XPATH: `//button[contains(@class,"el-button--primary") and not(contains(@class,"is-link"))]` | A |
| `BTN_RESET` | 重置 | el-button (default) | CSS: `button.el-button:not([class*="el-button--"])` / XPATH: `//button[@class="el-button"]` | B |
| `BTN_ADD` | 新增客户 | el-button (success) | CSS: `button.el-button--success:not(.is-link)` | A |

> **注意**: 按钮文本为"查询"（非"搜索"）。搜索输入框为组合字段（名称/编码二合一，placeholder="客户名称/编码"）。

## 表格区

| 列索引 | COL 常量 | 列名 | 数据类型 | 备注 |
|:--:|:---|:---|:---|:---|
| 1 | `COL_CODE` | 客户编码 | 文本 | — |
| 2 | `COL_NAME` | 客户名称 | 文本 | — |
| 3 | `COL_CONTACT` | 联系人 | 文本 | — |
| 4 | `COL_PHONE` | 联系电话 | 文本 | — |
| 5 | `COL_LEVEL` | 客户等级 | 标签 | `.sales-level-tag--strategic` / `--important` / `--normal` |
| 6 | `COL_STATUS` | 合作状态 | 标签 | `.sales-status-tag--cooperating` / `--terminated` |
| 7 | `COL_OPERATIONS` | 操作 | 按钮组 | 查看 / 编辑 / 资质维护 |

### 行操作
| 操作 | 按钮文本 | 方法 |
|:---|:---|:---|
| 查看 | `查看` | `click_view(identifier)` → 打开"客户详情"弹窗 |
| 编辑 | `编辑` | `click_edit(identifier)` → 打开"编辑客户"弹窗 |
| 资质维护 | `资质维护` | `click_qualification(identifier)` |

> **注意**: 无"删除"按钮。行操作用 `_click_row_action(identifier, button_text)` → XPATH `//tr[...]//button[contains(normalize-space(.),"{text}")]/parent::button`。

### 客户等级标签 CSS
| 等级 | CSS 选择器 |
|:---|:---|
| 战略客户 | `span.sales-level-tag--strategic, span[class*="level"][class*="strategic"]` |
| 重要客户 | `span.sales-level-tag--important, span[class*="level"][class*="important"]` |
| 普通客户 | `span.sales-level-tag--normal, span[class*="level"][class*="normal"]` |

### 合作状态标签 CSS
| 状态 | CSS 选择器 |
|:---|:---|
| 合作中 | `span.sales-status-tag--cooperating, span[class*="status"][class*="cooperating"]` |
| 已终止 | `span.sales-status-tag--terminated, span[class*="status"][class*="terminated"]` |

## 弹窗（新增/编辑/详情）

通过标题区分: "新增客户" / "编辑客户" / "客户详情"。

| 字段 | 定位器 placeholder | 必填 | 备注 |
|:---|:---|:--:|:---|
| 客户编码 | `请输入客户编码` | ✅ | — |
| 客户名称 | `请输入客户名称` | ✅ | — |
| 信用代码 | `请输入18位信用代码` | ✅ | maxlength=18, 格式校验 |
| 客户等级 | `客户等级` (el-select) | ✅ | 弹窗内 select, `_select_dialog_option` 处理 |
| 联系人 | `请输入联系人` | ✅ | — |
| 联系电话 | `请输入联系电话` | ✅ | — |
| 注册地址 | `请输入注册地址` (textarea) | ✅ | maxlength=500 |
| 合作状态 | `合作状态` (el-select) | ✅ | 弹窗内 select |
| 财务联系人 | `请输入财务联系人` | ❌ | — |
| 财务电话 | `请输入财务电话` | ❌ | — |
| 备注 | `请输入备注信息` (textarea) | ❌ | — |

对话框按钮: "保存" / "取消"

## 页面状态
- **加载中**: `el-loading-mask` + `aria-busy` 检查 (`_wait_loading_gone` 覆盖)
- **空数据**: `el-table__empty-block` / `el-table__empty-text`
- **错误**: `el-message--error` Toast / 表单校验错误 `el-form-item__error`

## 技术难点
- **搜索区 Select**: 使用键盘导航 `_select_by_keyboard(trigger, text)` — ActionChains 点击 wrapper → send_keys → Enter，完全绕过 Teleport popper
- **弹窗 Select**: 使用 `_select_dialog_option(label, text)` — JS 轮询 body 下 popper 强制点击
- **多弹窗 DOM 共存**: Vue keep-alive 不销毁 el-dialog
- **重置**: 使用 JS click（CSS 类可能不够精确）

## 测试文件
`script/sales/test_customer.py`, `test_customer_cdp.py`, `test_customer_cdp_fetch.py`, `test_customer_pagination.py`
