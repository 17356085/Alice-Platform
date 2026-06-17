# PAGE_ELEMENT_POSITION — sales / customer

> 从 CustomerPage.py 实际定位器提取 | 2026-06-17

## 搜索区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 客户名称/编码 | XPATH | `//input[@placeholder="客户名称/编码"]` | A | 组合输入框 |
| 客户等级下拉 | XPATH | `//div[contains(@class,"el-select")][.//span[contains(normalize-space(.),"客户等级")]]` | A | 键盘导航选择 |
| 合作状态下拉 | XPATH | `//div[contains(@class,"el-select")][.//span[contains(normalize-space(.),"合作状态")]]` | A | 键盘导航选择 |
| 查询按钮 | CSS | `button.el-button--primary:not(.is-link)` | A | — |
| 查询按钮 | XPATH | `//button[contains(@class,"el-button--primary") and not(contains(@class,"is-link"))]` | A | fallback |
| 重置按钮 | CSS | `button.el-button:not([class*="el-button--"])` | B | JS click |
| 重置按钮 | XPATH | `//button[@class="el-button"]` | B | fallback |
| 新增客户 | CSS | `button.el-button--success:not(.is-link)` | A | — |
| 新增客户 | XPATH | `//button[contains(@class,"el-button--success") and not(contains(@class,"is-link"))]` | B | fallback |

## 表格区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 表头 | XPATH | `//div[contains(@class,"el-table__header-wrapper")]//th//div[@class="cell"]` | A | |
| 数据行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | A | |
| 空数据 | CSS | `.el-table__empty-block, .el-table__empty-text` | A | |
| 总条数 | CSS | `.el-pagination__total` | A | |
| 下一页 | CSS | `.el-pagination .btn-next:not([disabled])` | A | |
| 上一页 | CSS | `.el-pagination .btn-prev:not([disabled])` | A | |
| 每页条数 | CSS | `.el-pagination__sizes .el-select` | B | |

## 行操作

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 行操作按钮 | XPATH (模板) | `//tr[.//td[contains(normalize-space(.),"{identifier}")]]//button[contains(normalize-space(.),"{text}")]` | A | `_click_row_action()` |
| 查看 | XPATH | `//tr[...]//button[contains(normalize-space(.),"查看")]` | A | |
| 编辑 | XPATH | `//tr[...]//button[contains(normalize-space(.),"编辑")]` | A | |
| 资质维护 | XPATH | `//tr[...]//button[contains(normalize-space(.),"资质维护")]` | A | |

## 客户等级标签

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 战略客户 | CSS | `span.sales-level-tag--strategic, span[class*="level"][class*="strategic"]` | B |
| 重要客户 | CSS | `span.sales-level-tag--important, span[class*="level"][class*="important"]` | B |
| 普通客户 | CSS | `span.sales-level-tag--normal, span[class*="level"][class*="normal"]` | B |

## 合作状态标签

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 合作中 | CSS | `span.sales-status-tag--cooperating, span[class*="status"][class*="cooperating"]` | B |
| 已终止 | CSS | `span.sales-status-tag--terminated, span[class*="status"][class*="terminated"]` | B |

## 弹窗区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 弹窗容器 | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))][.//span[contains(@class,"el-dialog__title") and contains(text(),"客户")]]` | B | 多弹窗共存 |
| 新增标题 | XPATH | `//span[contains(@class,"el-dialog__title") and contains(text(),"新增客户")]` | A | |
| 编辑标题 | XPATH | `//span[contains(@class,"el-dialog__title") and contains(text(),"编辑客户")]` | A | |
| 详情标题 | XPATH | `//span[contains(@class,"el-dialog__title") and contains(text(),"客户详情")]` | A | |
| 客户编码 | CSS | `input[placeholder="请输入客户编码"]` | A | |
| 客户名称 | CSS | `input[placeholder="请输入客户名称"]` | A | |
| 信用代码 | CSS | `input[placeholder="请输入18位信用代码"]` | A | maxlength=18 |
| 联系人 | CSS | `input[placeholder="请输入联系人"]` | A | |
| 联系电话 | CSS | `input[placeholder="请输入联系电话"]` | A | |
| 注册地址 | CSS | `textarea[placeholder="请输入注册地址"]` | A | maxlength=500 |
| 财务联系人 | CSS | `input[placeholder="请输入财务联系人"]` | B | 非必填 |
| 财务电话 | CSS | `input[placeholder="请输入财务电话"]` | B | 非必填 |
| 备注 | CSS | `textarea[placeholder="请输入备注信息"]` | B | 非必填 |
| 保存按钮 | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[contains(@class,"el-button--primary")]//span[contains(text(),"保存")]/parent::button` | A | |
| 取消按钮 | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[contains(@class,"el-button") and not(contains(@class,"el-button--primary"))]//span[contains(text(),"取消")]/parent::button` | A | |

## 弹窗 Select (body 下 popper)

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 下拉面板 | XPATH | `//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]` | B | `_wait_dropdown_ready()` |
| 选项 | XPATH | `//li[contains(@class,"el-select-dropdown__item")][normalize-space(.)="{text}"]` | B | `_click_dropdown_option()` |

## 搜索区 Select 操作方式

搜索区 Select 使用 `_select_by_keyboard(trigger_locator, text)`:
1. 点击 trigger → 打开下拉
2. `_wait_dropdown_ready()` 等待 popper 出现
3. ActionChains: 点击 wrapper → send_keys → Enter
完全绕过 Teleport popper 的 `is_displayed()` 问题。

## 弹窗 Select 操作方式

弹窗 Select 使用 `_select_dialog_option(label, text)`:
1. `_wait_dialog_ready()` 等待弹窗
2. `_get_dialog_form_item(label)` 定位表单项
3. `_click_select_trigger()` 点击打开
4. JS 轮询 body 下 popper 中选项并 `arguments[0].click()` 强制点击

## 等待策略

| 场景 | 条件 | 超时 |
|:---|:---|:--:|
| 页面加载 | `_wait_page_ready()` → loading + aria-busy + table | 20s |
| 搜索刷新 | `wait_vue_stable()` | 10s |
| 弹窗打开 | `_wait_dialog_ready()` 轮询 dialog + input 渲染 | 10s |
| 弹窗关闭 | `invisibility_of_element_located` | 5s |
| 下拉选项 | `_wait_dropdown_ready()` 轮询 popper visible | 5s |
| Toast | `get_toast()` → `wait_for_toast_text()` | 5s |
