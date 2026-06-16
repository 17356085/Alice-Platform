# TECH_ANALYSIS — system-management / menu-management

> 基于 MenuManagePage.py 重构版 + PAGE_CONTEXT | 2026-06-12
> 路由: `#/system/menu` | PO: `page/system_page/MenuManagePage.py`
> 特点：树形表格(el-table tree) + PC/小程序Tab + 3种菜单类型(M/C/F)

## Element Plus 组件识别

| 组件类型 | 用途 | 定位特点 |
|----------|------|----------|
| el-input | 菜单名称搜索 | `placeholder="请输入菜单名称"` |
| el-radio-button | PC端菜单/小程序菜单Tab | `el-radio-button__inner` 文本匹配 |
| el-table (tree) | 树形表格（8列） | row-key + lazy-load，含展开/折叠箭头 |
| el-dialog | 新增/编辑弹窗 | ⚠️ `[last()]`选取 + fallback链 |
| el-radio-group | 弹窗内菜单类型选择 | 目录(M)/菜单(C)/按钮(F) |
| el-tree-select | 上级菜单选择（树形下拉） | 待确认 |

## 定位器设计表（从 MenuManagePage.py 提取）

### 搜索/工具栏

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 菜单名称输入 | XPATH | `//input[contains(@placeholder, "请输入菜单名称")]` | A | |
| 搜索按钮 | XPATH | `//button[.//span[normalize-space(.)="搜索"]]` | A | |
| 重置按钮 | XPATH | `//button[.//span[normalize-space(.)="重置"]]` | A | |
| PC端菜单Tab | XPATH | `//span[contains(@class,"el-radio-button__inner") and normalize-space(.)="PC端菜单"]/ancestor::label` | A | |
| 小程序菜单Tab | XPATH | `//span[contains(@class,"el-radio-button__inner") and normalize-space(.)="小程序菜单"]/ancestor::label` | A | |
| 新增按钮 | XPATH | `//button[.//span[normalize-space(.)="新增"]]` | A | |
| 展开全部 | XPATH | `//button[.//span[normalize-space(.)="展开全部"]]` | A | |
| 收起全部 | XPATH | `//button[.//span[normalize-space(.)="收起全部"]]` | A | |

### 表格区

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 表头 | XPATH | `//div[contains(@class,"el-table__header-wrapper")]//th//div` | A | |
| 表格行 | XPATH | `//div[contains(@class,"el-table__body-wrapper")]//table/tbody/tr` | B | 树形结构 |
| 首行名称 | XPATH | `(//div[contains(@class,"el-table__body-wrapper")]//table/tbody/tr[1]/td[1]//div[contains(@class,"cell")])[1]` | B | |
| loading遮罩 | CSS | `.el-loading-mask` | A | |

### 弹窗区（`[last()]` + fallback链）

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 弹窗-菜单名称 | XPATH | `(//div[contains(@class,"el-dialog")])[last()]//input[@placeholder="请输入菜单名称"]` | B | |
| 弹窗-菜单类型 | XPATH | `(//div[contains(@class,"el-dialog")])[last()]//label[contains(@class,"el-radio")]` | B | 3个radio |
| 弹窗-确定 | XPATH | `(//div[contains(@class,"el-dialog")])[last()]//button[.//span[normalize-space(.)="确定"]]` | B | 有4个fallback |
| 弹窗-取消 | XPATH | `(//div[contains(@class,"el-dialog")])[last()]//button[.//span[normalize-space(.)="取消"]]` | B | |
| MessageBox确定 | XPATH | `(//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))])[last()]//button[.//span[normalize-space(.)="确定"]]` | B | |

## 已知技术难题

| 问题 | 影响 | 当前处理 |
|------|------|----------|
| 树形表格DOM嵌套深 | 行定位需穿透多层div | `el-table__body-wrapper` → `table/tbody/tr` |
| 弹窗确定按钮4个fallback | 不同弹窗状态DOM结构不同 | 4级fallback链：overlay→dialog→footer→primary button |
| PC/小程序Tab切换后树数据异步加载 | 切换Tab后需等待数据刷新 | `wait_page_ready()` + `_wait_loading_gone()` |

## 异步等待策略

| 场景 | 等待条件 | 实现 |
|------|----------|------|
| 页面加载 | 树形表格出现 | `wait_page_ready(timeout=15)` + `_wait_loading_gone()` + `wait_vue_stable()` |
| Tab切换 | loading消失 | `_wait_loading_gone()` |
| 弹窗打开 | el-dialog visible | `WebDriverWait` |
| 弹窗关闭 | dialog invisible | `EC.invisibility_of_element_located` |

## 自动化代码映射

- PO：`page/system_page/MenuManagePage.py`（重构版，继承BasePage，去绝对XPath，去time.sleep）
- 测试：`script/system/test_menu_management.py`（18条用例）
- conftest：`script/system/conftest.py`

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 | next_phase: Phase 3.5 | next_agent: automation-agent -->
