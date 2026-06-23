# TECH_ANALYSIS — sales / contract

> 基于 ContractPage.py 已有代码反向提取 | 2026-06-12
> 页面路由: `#/sales/contract` | PO: `page/sales_page/ContractPage.py` (40KB)

## 分析对象
- 模块：sales（销仓管理）
- 页面：合同管理
- PO 规模：40KB，含状态常量映射 + CSS/XPath 双保险定位器

## Element Plus 组件识别

| 组件类型 | 用途 | 定位特点 |
|----------|------|----------|
| el-form--inline | 搜索区 | 2个 el-input + 2个 el-select + 1个 el-date-picker(range) + 3个 el-button |
| el-input | 合同编号/客户名称搜索 | placeholder="合同编号"/"客户名称" |
| el-select | 产品类型/合同状态筛选 | ⚠️ filterable + Teleport |
| el-date-picker (daterange) | 有效期起止 | placeholder="有效期起"~"有效期止" |
| el-table | 合同列表（8列） | 含 el-progress + el-tag |
| el-progress | 已执行量进度条 | ⚠️ 3s CSS 动画，断言需等动画完成 |
| el-tag | 状态标签 | danger=已终止, success=已完成 |
| el-dialog | 新增/编辑弹窗 | ⚠️ 多弹窗DOM共存 |
| el-pagination | 分页器 | 标准 |

## 定位器设计表（从 ContractPage.py 提取）

### 搜索区

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 合同编号输入(CSS) | CSS | `input[placeholder="合同编号"]` | A | 语义属性 |
| 合同编号输入(XPath) | XPATH | `//input[@placeholder="合同编号"]` | A | 保底 |
| 客户名称输入(CSS) | CSS | `input[placeholder="客户名称"]` | A | |
| 客户名称输入(XPath) | XPATH | `//input[@placeholder="客户名称"]` | A | |
| 产品类型下拉 | XPATH | `//div[contains(@class,"el-select")][.//div[contains(@class,"el-select__placeholder")]/span[contains(normalize-space(.),"产品类型")]]` | A | 文本匹配 |
| 合同状态下拉 | XPATH | `//div[contains(@class,"el-select")][.//span[contains(normalize-space(.),"合同状态")]]` | A | |
| 有效期起 | CSS | `input[placeholder="有效期起"]` | A | |
| 有效期止 | CSS | `input[placeholder="有效期止"]` | A | |
| 查询按钮(CSS) | CSS | `button.el-button--primary:not(.is-link)` | A | |
| 查询按钮(XPath) | XPATH | `//button[contains(@class,"el-button--primary") and not(contains(@class,"is-link"))]` | A | |
| 重置按钮 | CSS | `button.el-button:not([class*="el-button--"])` | B | |
| 新增按钮 | CSS | `button.el-button--success:not(.is-link)` | A | |

### 表格区

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 表格容器 | CSS | `.el-table` | A | |
| 表格行 | CSS | `.el-table__body-wrapper .el-table__row` | B | 动态渲染 |
| 进度条 | CSS | `.el-progress` / `.el-progress-bar__inner` | B | 3s动画 |
| 状态标签 | CSS | `.el-tag` | B | 颜色映射验证 |
| 操作-详情 | XPATH | `.//button[contains(.,"详情")]` | B | 行内相对 |
| 操作-销售订单 | XPATH | `.//button[contains(.,"销售订单")]` | B | 行内相对 |

### 弹窗区

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 可见弹窗 | CSS | `.el-dialog:not([style*="display: none"])` | B | 排除隐藏 |
| 弹窗标题 | CSS | `.el-dialog__title` | A | |
| 客户下拉 | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//input[@placeholder="请选择客户"]` | B | 级联 |
| 产品下拉 | XPATH | 同上模式，placeholder="产品类型" | B | |
| 合同金额 | XPATH | `//input[@placeholder="合同金额(万元)"]` | A | |
| 合同总量 | XPATH | `//input[@placeholder="合同总量(吨)"]` | A | |
| 生效日期 | XPATH | `//input[@placeholder="生效日期"]` | A | |
| 有效期至 | XPATH | `//input[@placeholder="有效期至"]` | A | |
| 附件上传 | CSS | `.el-upload` | B | |
| 弹窗确定 | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[.//span[text()="确定"]]` | B | |
| 弹窗取消 | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[.//span[text()="取消"]]` | B | |

## 已知技术难题

| 问题 | 影响 | 当前处理 |
|------|------|----------|
| el-progress 3s CSS transition | 断言百分比时值还在过渡中 | 等待 transitionend 或固定延迟后再断言 |
| el-date-picker range Teleport 到 body | is_displayed() 对 body 层面板失效 | 等待面板可见后点击 |
| el-select filterable + Teleport | 弹窗下拉选项 is_displayed 失效 | 用 ElementPlusHelper select_option() |
| 多弹窗DOM共存 | 定位器选到隐藏弹窗 | `:not([style*="display: none"])` 过滤 |
| 客户/合同/订单级联数据依赖 | 新增合同时需先有客户 | `_pick_existing_customer()` 从列表取 |

## 异步等待策略

| 场景 | 等待条件 | 实现 |
|------|----------|------|
| 页面加载 | JS hash 跳转 + 表格出现 | `driver.get(BASE_URL + "#/sales/contract")` + `wait_table_loaded()` |
| 搜索完成 | loading 消失 | `wait_loading_disappear()` |
| 进度条动画 | transition 完成 | `time.sleep(3)` 或 `wait.until` for stable width |
| 弹窗打开 | el-dialog visible | `wait_dialog_visible()` |
| Select 下拉展开 | popper 在 body 层可见 | `WebDriverWait` for `.el-select-dropdown` |
| 日期面板展开 | date-picker panel 可见 | `WebDriverWait` for `.el-picker-panel` |

## 自动化代码映射

- Page Object：`page/sales_page/ContractPage.py`（40KB，状态常量映射，CSS+XPath双保险）
- 测试脚本：`test_contract.py` + `test_contract_display.py` + `test_contract_search.py` + `test_contract_pagination.py` + `test_contract_workflow.py`（5文件）
- conftest：`script/sales/conftest.py`（JS hash 导航 + fixture 工厂 + `CONTRACT_CUSTOMER_NAME` 变量）
- 特殊依赖：ContractPage 引用 ElementPlusHelper 处理 Select

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 | next_phase: Phase 3.5 | next_agent: automation-agent -->
