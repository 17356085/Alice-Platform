# TECH_ANALYSIS — sales / customer

> 基于 CustomerPage.py 已有代码反向提取 | 2026-06-12
> 页面路由: `#/sales/customer` | PO: `page/sales_page/CustomerPage.py` (44KB)

## 分析对象
- 模块：sales（销仓管理）
- 页面：客户管理
- PO 规模：44KB，定位器 A/B/C 三级 + 双保险（CSS + XPath）

## Element Plus 组件识别

| 组件类型 | 用途 | 定位特点 |
|----------|------|----------|
| el-form--inline | 搜索区容器 | 2个 el-select + 1个 el-input + 3个 el-button |
| el-select | 客户等级/合作状态筛选 | ⚠️ filterable + Teleport → body 层渲染，需等待可见 |
| el-input | 客户名称/编码搜索框 | placeholder="客户名称/编码" |
| el-table | 客户列表（7列） | 操作列含 查看/编辑/资质维护 三个按钮 |
| el-dialog | 新增/编辑/详情弹窗 | ⚠️ 多弹窗DOM共存，需 `:not([style*="display: none"])` 排除隐藏 |
| el-pagination | 分页器 | 标准 Element Plus 分页 |
| el-tag | 客户等级/合作状态标签 | 等级 A/B/C 可能用不同颜色 |
| el-textarea | 注册地址/客户备注 | maxlength=500 |

## 定位器设计表（从 CustomerPage.py 提取）

### 搜索区

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 搜索输入框 | XPATH | `//input[@placeholder="客户名称/编码"]` | A | placeholder 语义定位 |
| 客户等级下拉触发 | XPATH | `//div[contains(@class,"el-select")][.//span[contains(normalize-space(.),"客户等级")]]` | A | 文本匹配 |
| 合作状态下拉触发 | XPATH | `//div[contains(@class,"el-select")][.//span[contains(normalize-space(.),"合作状态")]]` | A | 文本匹配 |
| 查询按钮(CSS) | CSS | `button.el-button--primary:not(.is-link)` | A | 工具栏唯一 primary 按钮 |
| 查询按钮(XPath) | XPATH | `//button[contains(@class,"el-button--primary") and not(contains(@class,"is-link"))]` | A | 双保险保底 |
| 重置按钮(CSS) | CSS | `button.el-button:not([class*="el-button--"])` | B | 仅 el-button 无修饰符 |
| 重置按钮(XPath) | XPATH | `//button[contains(@class,"el-button") and not(contains(@class,"el-button--"))]` | B | 双保险保底 |
| 新增客户按钮 | CSS | `button.el-button--success:not(.is-link)` | A | success 绿色按钮 |

### 表格区

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 表格容器 | CSS | `.el-table` | A | |
| 表格行 | CSS | `.el-table__body-wrapper .el-table__row` | B | 动态渲染 |
| 操作-查看 | XPATH | `.//button[contains(.,"查看")]` | B | 行内相对定位 |
| 操作-编辑 | XPATH | `.//button[contains(.,"编辑")]` | B | 行内相对定位 |
| 操作-删除 | XPATH | `.//button[contains(.,"删除")]` | B | 行内相对定位 |
| 操作-资质维护 | XPATH | `.//button[contains(.,"资质维护")]` | B | 行内相对定位 |

### 弹窗区

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 弹窗容器 | CSS | `.el-dialog:not([style*="display: none"])` | B | 排除隐藏弹窗 |
| 弹窗标题 | CSS | `.el-dialog__title` | A | |
| 客户编码输入 | XPATH | `//input[@placeholder="客户编码"]` | A | 弹窗内 |
| 客户名称输入 | XPATH | `//input[@placeholder="客户名称"]` | A | 弹窗内 |
| 信用代码输入 | XPATH | `//input[@placeholder="统一社会信用代码"]` | A | maxlength=18 |
| 客户等级下拉 | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//input[@placeholder="客户等级"]` | B | 弹窗内 |
| 联系人输入 | XPATH | `//input[@placeholder="联系人"]` | A | |
| 联系电话输入 | XPATH | `//input[@placeholder="联系电话"]` | A | |
| 注册地址 | XPATH | `//textarea[@placeholder="注册地址"]` | A | maxlength=500 |
| 合作状态下拉 | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//input[@placeholder="合作状态"]` | B | 弹窗内 |
| 财务联系人 | XPATH | `//input[@placeholder="财务联系人"]` | A | 非必填 |
| 财务电话 | XPATH | `//input[@placeholder="财务电话"]` | A | 非必填 |
| 客户备注 | XPATH | `//textarea[@placeholder="客户备注"]` | A | 非必填 |
| 弹窗确定 | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[.//span[text()="确定"]]` | B | |
| 弹窗取消 | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[.//span[text()="取消"]]` | B | |

### 分页区

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 分页器 | CSS | `.el-pagination` | A | |
| 总条数 | CSS | `.el-pagination__total` | B | |
| 每页条数 | CSS | `.el-pagination__sizes .el-select` | B | |

## 已知技术难题

| 问题 | 影响 | 当前处理 |
|------|------|----------|
| Element Plus Select popper Teleport 到 body | is_displayed() 对 body 层选项失效，弹窗新增/编辑不可靠 | test_customer.py 中新增/编辑/必填校验标记为 `TODO: 依赖弹窗下拉交互fix` |
| Vue SPA keep-alive 标签页切换 DOM 刷新 | StaleElementReferenceException | `retry_on_stale(max_retries=2)` 装饰器处理 |
| 多弹窗共存于 DOM（display:none） | 定位器可能选到隐藏弹窗 | 用 `:not([style*="display: none"])` 排除 |
| el-tag 等级标签 | 定位和文本提取不稳定 | 用表格列索引 + get_column_data() |

## 异步等待策略

| 场景 | 等待条件 | 实现 |
|------|----------|------|
| 页面加载 | JS hash 跳转完成 + 表格出现 | `driver.get(BASE_URL + "#/sales/customer")` + `wait_table_loaded()` |
| 搜索完成 | loading 遮罩消失 + 表格行渲染 | `wait_loading_disappear()` + `WebDriverWait` for rows |
| 弹窗打开 | el-dialog visible | `wait_dialog_visible()` |
| 弹窗关闭 | el-dialog invisible | `wait.until(EC.invisibility_of_element_located(DIALOG))` |
| Select 下拉展开 | popper 出现在 body 层 | `WebDriverWait` for `.el-select-dropdown` in body |
| 表格刷新 | loading 消失 | `wait_loading_disappear()` |

## 自动化代码映射

- Page Object：`page/sales_page/CustomerPage.py`（44KB，A/B/C三级定位器，CSS+XPath双保险）
- 测试脚本：`script/sales/test_customer.py`（页面展示/搜索/分页）+ `test_customer_cdp.py` + `test_customer_cdp_fetch.py` + `test_customer_pagination.py`
- conftest：`script/sales/conftest.py`（JS hash 导航 + fixture 工厂模式）
- 已知暂不执行：弹窗新增/编辑/必填校验（Element Plus Select Teleport 渲染时序问题）

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 | next_phase: Phase 3.5 | next_agent: automation-agent -->
