# TECH_ANALYSIS — sales / sales-order

> 基于 SalesOrderPage.py 已有代码反向提取 | 2026-06-12
> 页面路由: `#/sales/order` | PO: `page/sales_page/SalesOrderPage.py` (31KB)

## 分析对象
- 模块：sales（销仓管理）
- 页面：销售订单
- PO 规模：31KB，CSS+XPath双保险 + 浮点精度处理 + 超卖校验

## Element Plus 组件识别

| 组件类型 | 用途 | 定位特点 |
|----------|------|----------|
| el-form--inline | 搜索区 | 2个 el-input + 2个 el-date-picker + 1个 el-select + 3个 el-button |
| el-input | 销售单号/客户名称搜索 | placeholder="销售单号"/"客户名称" |
| el-select | 产品类型筛选 | ⚠️ filterable + Teleport |
| el-date-picker | 开始日期/结束日期 | placeholder="开始日期"/"结束日期" |
| el-table | 订单列表（8列） | 第1列单号为可点击 el-button, 第3列产品类型为 el-tag |
| el-tag | 产品类型标签 | LNG=primary(蓝), 焦油=warning(橙) |
| el-dialog | 新增/详情弹窗 | ⚠️ 多弹窗DOM共存 |
| el-pagination | 分页器 | 标准 |

## 定位器设计表（从 SalesOrderPage.py 提取）

### 搜索区

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 销售单号输入 | CSS | `input[placeholder="销售单号"]` | A | 语义属性 |
| 客户名称输入 | CSS | `input[placeholder="客户名称"]` | A | |
| 开始日期 | CSS | `input[placeholder="开始日期"]` | A | |
| 结束日期 | CSS | `input[placeholder="结束日期"]` | A | |
| 产品类型下拉 | XPATH | `//div[contains(@class,"el-select")][.//*[contains(@class,"el-select__placeholder") and contains(.,"产品类型")]]` | A | 文本匹配 |
| 查询按钮(CSS) | CSS | `.el-button--primary` | B | 同页可能有多个 primary |
| 查询按钮(XPath) | XPATH | `//button[contains(@class,"el-button--primary")]//span[contains(normalize-space(.),"查询")]/parent::button` | A | 文本保底 |
| 重置按钮 | CSS | `button.el-button:not(.el-button--primary)` | B | |
| 新增按钮 | CSS | `button.el-button--primary` | B | 同查询按钮，需文本区分 |

### 表格区

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 表格容器 | CSS | `.el-table` | A | |
| 表格行 | CSS | `.el-table__body-wrapper .el-table__row` | B | |
| 产品标签 | CSS | `.el-tag` | B | 颜色验证 |
| 单号按钮 | XPATH | `.//button[contains(@class,"el-button--text")]` | B | 行内链接样式 |
| 操作-详情 | XPATH | `.//button[contains(.,"详情")]` | B | |

### 弹窗区

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 可见弹窗 | CSS | `.el-dialog:not([style*="display: none"])` | B | 排除隐藏 |
| 客户下拉 | XPATH | `//input[@placeholder="请选择客户"]` | A | 级联触发 |
| 产品下拉 | XPATH | 同上模式 | B | |
| 净重输入 | XPATH | `//input[@placeholder="净重(吨)"]` | A | |
| 车牌号输入 | XPATH | `//input[@placeholder="车牌号"]` | A | |
| 关联合同下拉 | XPATH | `//input[@placeholder="请选择关联合同"]` | A | 级联过滤 |
| 弹窗确定 | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[.//span[text()="确定"]]` | B | |
| 弹窗取消 | XPATH | 同上模式，text()="取消" | B | |

## 已知技术难题

| 问题 | 影响 | 当前处理 |
|------|------|----------|
| el-select 级联下拉 Teleport | 选客户后合同下拉需异步刷新，is_displayed 对body层选项失效 | ElementPlusHelper select_option() + WebDriverWait |
| 浮点数精度比较 | assert 9.9999 == 10.0000 - 0.0001 可能因浮点误差失败 | 使用 round(x, 4) 统一精度 |
| el-button--primary 多个实例 | 查询按钮和新增按钮都用 primary 类 | XPath 文本匹配保底 |
| 跨PO依赖 | 新增订单需 CustomerPage + ContractPage 提供数据 | conftest 中导入多PO |

## 异步等待策略

| 场景 | 等待条件 | 实现 |
|------|----------|------|
| 页面加载 | JS hash + 表格出现 | `driver.get(BASE_URL + "#/sales/order")` + `wait_table_loaded()` |
| 搜索完成 | loading 消失 | `wait_loading_disappear()` |
| 弹窗打开 | el-dialog visible | `wait_dialog_visible()` |
| 级联下拉刷新 | 合同下拉选项更新 | `WebDriverWait` for option count change |
| Select 下拉展开 | popper body 层可见 | `WebDriverWait` for `.el-select-dropdown` |

## 自动化代码映射

- Page Object：`page/sales_page/SalesOrderPage.py`（31KB，CSS+XPath双保险）
- 测试脚本：`test_sales_order.py` + `test_sales_order_search.py` + `test_sales_order_display.py` + `test_sales_order_crud.py`（4文件）
- conftest：`script/sales/conftest.py`
- 跨PO依赖：test_sales_order.py 同时 import SalesOrderPage + ContractPage + CustomerPage

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 | next_phase: Phase 3.5 | next_agent: automation-agent -->
