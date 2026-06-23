# PAGE_ELEMENT_POSITION — sales / contract

> 从 ContractPage.py 实际定位器提取 | 2026-06-17

## 搜索区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 合同编号 | CSS | `input[placeholder="合同编号"]` | A | `_fill_vue_input` JS 注入 |
| 合同编号 | XPATH | `//input[@placeholder="合同编号"]` | A | fallback |
| 客户名称 | CSS | `input[placeholder="客户名称"]` | A | `_fill_vue_input` JS 注入 |
| 客户名称 | XPATH | `//input[@placeholder="客户名称"]` | A | fallback |
| 产品类型下拉 | XPATH | `//div[contains(@class,"el-select")][.//div[contains(@class,"el-select__placeholder")]/span[contains(normalize-space(.),"产品类型")]]` | B | Teleport popper |
| 合同状态下拉 | XPATH | `//div[contains(@class,"el-select")][.//div[contains(@class,"el-select__placeholder")]/span[contains(normalize-space(.),"合同状态")]]` | B | Teleport popper |
| 有效期起 | CSS | `input[placeholder="有效期起"]` | B | el-date-picker |
| 有效期止 | CSS | `input[placeholder="有效期止"]` | B | el-date-picker |
| 查询按钮 | XPATH | `//button[contains(@class,"el-button--primary")]//span[contains(normalize-space(.),"查询")]/parent::button` | A | 4层降级策略 |
| 查询按钮 | CSS | `button.el-button--primary:not(.is-link)` | B | fallback |
| 重置按钮 | XPATH | `//button[not(contains(@class,"el-button--primary"))]//span[contains(normalize-space(.),"重置")]/parent::button` | A | 3层降级 |
| 重置按钮 | CSS | `button.el-button:not([class*="el-button--"])` | B | fallback |
| 新增合同 | XPATH | `//button[contains(@class,"el-button")]//span[contains(normalize-space(.),"新增合同")]/parent::button` | A | JS优先 |
| 新增合同 | CSS | `button.el-button--success:not(.is-link)` | B | fallback |

## 表格区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 进度条 (百分比) | CSS | `.el-progress-bar__inner` | B | 3s CSS动画，需等待宽度稳定 |
| 进度文本 | CSS | `tr.el-table__row td:nth-child(5) .cell span.text-xs` | B | 如 "65.0%" |
| 状态标签-已终止 | CSS | `span.el-tag--danger` | B | 红色 |
| 状态标签-已完成 | CSS | `span.el-tag--success` | B | 绿色 |
| 详情按钮 | XPATH | `//button[contains(.,"详情")]` | A | per-row |
| 销售订单按钮 | XPATH | `//button[contains(.,"销售订单")]` | A | per-row，仅生效中状态显示 |

## 弹窗区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 客户下拉 | XPATH | `//input[@placeholder="请选择客户"]` | B | filterable + Teleport |
| 产品类型下拉 | XPATH | placeholder="产品类型" 模式 | B | 弹窗内 |
| 合同金额 | XPATH | `//input[@placeholder="合同金额(万元)"]` | B | |
| 合同总量 | XPATH | `//input[@placeholder="合同总量(吨)"]` | B | |
| 生效日期 | XPATH | `//input[@placeholder="生效日期"]` | B | |
| 有效期至 | XPATH | `//input[@placeholder="有效期至"]` | B | |
| 附件上传 | CSS | `.el-upload` | B | |
| 确定按钮 | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[.//span[text()="确定"]]` | A | |
| 取消按钮 | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[.//span[text()="取消"]]` | A | |

## 弹窗 Select 选项 (在 body 下的 popper 中)

| 元素 | 定位值 | 等级 |
|------|--------|:--:|
| 下拉面板 | `//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]` | B |
| 选项 | `//li[contains(@class,"el-select-dropdown__item")][normalize-space(.)="{text}"]` | B |

## 等待策略

| 场景 | 条件 | 超时 |
|:---|:---|:--:|
| 页面加载 | `_wait_page_ready()` → loading gone + Vue stable + table ready | 15s |
| 搜索刷新 | `wait_vue_stable()` 等待 Vue 重新渲染 | 10s |
| 弹窗打开 | `_wait_dialog_ready()` 轮询 dialog 出现 + input 渲染 | 10s |
| 弹窗关闭 | `invisibility_of_element_located` (dialog) | 5s |
| 下拉选项 | `_wait_dropdown_ready()` 轮询 popper visible | 5s |
| Toast | `get_toast()` → `wait_for_toast_text()` | 5s |
| 进度条动画 | 等待 `el-progress-bar__inner` width 稳定 | 5s |
