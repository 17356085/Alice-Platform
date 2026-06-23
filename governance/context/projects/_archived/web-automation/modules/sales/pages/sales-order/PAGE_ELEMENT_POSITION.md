# PAGE_ELEMENT_POSITION — sales / sales-order

> 从 SalesOrderPage.py 实际定位器提取 | 2026-06-17

## 搜索区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 销售单号 | CSS | `input[placeholder="销售单号"]` | A | |
| 客户名称 | CSS | `input[placeholder="客户名称"]` | A | |
| 产品类型下拉 | XPATH | `//div[contains(@class,"el-select")][.//*[contains(@class,"el-select__placeholder") and contains(.,"产品类型")]]` | B | Teleport popper |
| 开始日期 | CSS | `input[placeholder="开始日期"]` | B | el-date-picker |
| 结束日期 | CSS | `input[placeholder="结束日期"]` | B | el-date-picker |
| 查询按钮 | XPATH | `//button[contains(@class,"el-button--primary")]//span[contains(normalize-space(.),"查询")]/parent::button` | A | 与新增按钮同 class，用文本区分 |
| 查询按钮 | CSS | `.el-button--primary` | B | fallback |
| 重置按钮 | XPATH | `//button[not(contains(@class,"el-button--primary"))]//span[contains(normalize-space(.),"重置")]/parent::button` | A | |
| 重置按钮 | CSS | `button.el-button:not(.el-button--primary)` | B | fallback |
| 新增销售 | XPATH | `//button[contains(@class,"el-button")]//span[contains(normalize-space(.),"新增销售")]/parent::button` | A | 4级降级 |
| 新增销售 | XPATH | `//button[contains(.,"新增销售")]` | B | fallback |
| 新增销售 | CSS | `button.el-button--primary` | C | 文本兜底 |

## 表格区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 数据行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | A | |
| 单号按钮 | XPATH | `.//button[contains(@class,"el-button--text")]` | B | 第1列，可点击跳转 |
| 产品标签 | CSS | `td:nth-child(3) .cell span.el-tag` | B | LNG=primary, 焦油=warning |
| 详情按钮 | XPATH | `.//button[contains(.,"详情")]` | A | per-row |
| 总条数 | CSS | `.el-pagination__total` | A | |
| 下一页 | CSS | `.el-pagination .btn-next:not([disabled])` | A | |
| 上一页 | CSS | `.el-pagination .btn-prev:not([disabled])` | A | |

## 弹窗区（新增销售）

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 客户下拉 | XPATH | `//input[@placeholder="请选择客户"]` | A | filterable + 级联触发 |
| 净重输入 | XPATH | `//input[@placeholder="净重(吨)"]` | A | 委托 `fill_dialog_input("净重", value)` |
| 车牌号输入 | XPATH | `//input[@placeholder="车牌号"]` | A | 委托 `fill_dialog_input("车牌号", value)` |
| 关联合同下拉 | XPATH | `//input[@placeholder="请选择关联合同"]` | A | 级联过滤，`select_contract_in_dialog()` |
| 保存按钮 | XPATH | BasePage 通用: `//div[contains(@class,"el-dialog")...]//button[contains(@class,"el-button--primary")]` | A | `click_dialog_save()` |
| 取消按钮 | XPATH | BasePage 通用: `//div[contains(@class,"el-dialog")...]//button[not(...)]//span[contains(normalize-space(.),"取消")]` | A | `click_dialog_cancel()` |

## 弹窗 Select 级联操作方式

`select_contract_in_dialog(search_text)`:
1. 定位弹窗表单项 (label 文本匹配)
2. ActionChains 点击 el-select 打开下拉
3. 逐字符 send_keys 过滤选项
4. 点击第一个可用选项
5. 点击弹窗标题关闭下拉（防止遮挡）

## 产品类型标签

| 产品 | CSS 类 | 语义 |
|:---|:---|:---|
| LNG | `el-tag--primary` | 蓝色 |
| 焦油 | `el-tag--warning` | 橙色 |

获取: `get_product_tag_type(row)` 解析 CSS 类名 → `get_product_tag_text(row)` 获取文本。

## 表格列数据

`get_column_data(col)` 两种方式:
1. JS 一次性提取所有行文本 (方法1, 快速)
2. Selenium 逐行兜底 (方法2, 稳定)

## 超卖防护

`try_oversell(customer, contract, oversized_qty)`:
1. 填写客户 + 合同 + 超量净重
2. 点击保存
3. 检查表单错误 (`get_form_error_text()`) + Toast 错误 + 弹窗状态

## 等待策略

| 场景 | 条件 | 超时 |
|:---|:---|:--:|
| 页面加载 | `_wait_page_ready()` → loading + Vue stable + table | 15s |
| 搜索刷新 | `wait_vue_stable()` | 10s |
| 弹窗打开 | `_wait_dialog_ready()` 轮询 dialog + input | 10s |
| 弹窗关闭 | `invisibility_of_element_located` | 5s |
| 下拉选项 | 轮询 popper visible | 5s |
| Toast | `click_dialog_save()` 返回 toast text | 5s |
