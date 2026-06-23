# TECH_ANALYSIS — equipment / maintenance

> 从现有 MaintenancePage.py 代码提取定位器 | 2026-06-11
> 页面类型: 标准 el-table CRUD + 搜索表单 + 弹窗（role="dialog"）

## Element Plus 组件识别

| 组件 | 用途 | 定位特点 |
|------|------|----------|
| el-form (inline) | 搜索区表单 | .search-wrapper 内，2个el-select+按钮 |
| el-select | 维保类型/状态下拉 | 标准 select，可复用 ElementPlusHelper |
| el-button | 搜索/重置/新增计划 | 标准按钮，文本匹配 |
| el-table | 维保计划数据表格 | 多列，无 fixed="right"（无克隆问题） |
| el-pagination | 分页器 | 标准 |
| el-overlay-dialog | 新增/编辑弹窗 | ⚠️ 使用 role="dialog" 而非 el-dialog class |

## 定位器设计表

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 搜索区容器 | CSS | `.search-wrapper` | A | 作用域限定 |
| 维保类型下拉 | CSS | `.search-wrapper .el-select__wrapper` | B | 第一个select，按索引区分 |
| 状态下拉 | CSS | `.search-wrapper .el-select__wrapper` | B | 第二个select |
| 搜索按钮 | XPATH | `//button[.//span[text()='搜索']]` | A | |
| 重置按钮 | XPATH | `//button[.//span[text()='重置']]` | A | |
| 新增计划按钮 | XPATH | `//button[.//span[text()='新增计划']]` | A | |
| 表格容器 | CSS | `.table-wrapper .el-table` | A | |
| 表格行 | CSS | `.el-table__body-wrapper .el-table__row` | B | |
| 编辑按钮(行内) | XPATH | `.//button[contains(.,'编辑')]` | B | per-row |
| 生成任务按钮(行内) | XPATH | `.//button[contains(.,'生成任务')]` | B | |
| 弹窗 | CSS | `.el-overlay-dialog[role="dialog"]` | A | ⚠️ 覆盖 BasePage.DIALOG |
| 弹窗标题 | CSS | `.el-overlay-dialog[role="dialog"] .el-dialog__title` | A | |
| 弹窗保存 | CSS | `.el-overlay-dialog[role="dialog"] .el-button--primary` | A | |
| 弹窗取消 | CSS | `.el-overlay-dialog[role="dialog"] .el-button:not(.el-button--primary)` | B | |
| 弹窗保存(XPATH) | XPATH | `//div[contains(@class,"el-overlay-dialog")][@role="dialog"]//button[contains(@class,"el-button--primary")]` | A | 保底 |
| 弹窗取消(XPATH) | XPATH | `//div[contains(@class,"el-overlay-dialog")][@role="dialog"]//button[not(contains(@class,"el-button--primary"))]//span[contains(.,"取消")]` | A | 保底 |
| 分页器 | CSS | `.el-pagination` | A | |

## 异步等待策略

| 场景 | 等待条件 | 实现 |
|------|----------|------|
| 页面加载 | 表格出现 | `wait_table_loaded()` (BasePage) |
| 页面加载 | 搜索区出现 | `WebDriverWait(driver, 30).until(EC.presence_of_element_located(SEARCH_WRAPPER))` |
| 搜索完成 | loading 消失 | `wait_loading_disappear()` |
| 弹窗打开 | dialog visible | `visibility_of_element_located(DIALOG)` |
| 弹窗关闭 | dialog invisible | `invisibility_of_element_located(DIALOG)` |

## 已知技术难点

| 问题 | 影响 | 处理 |
|------|------|------|
| 弹窗使用 role="dialog" 非 el-dialog class | BasePage.DIALOG 通用定位器不可用 | MaintenancePage 覆盖 DIALOG/DialogTitle/DialogSave |
| 页面加载较慢 | 30s 超时风险 | WebDriverWait timeout 设为 30s |
| Vue Router 可能未生效 | navigate_to() 不可靠 | 回退为侧边栏导航 |
| 无 fixed 列克隆 | 无 EP-006 问题 | 不需要 TABLE_BODY 隔离 |

## 代码映射

- Page Object: `page/equipment_page/MaintenancePage.py`
- 测试脚本: `script/equipment/test_maintenance_management.py`
- conftest: `script/equipment/conftest.py`
- 状态按钮映射: `STATUS_BUTTON_MAP = {"待执行": ["编辑","生成任务"], "已完成": ["查看"]}`

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 | next_phase: Phase 3.5/4 | next_agent: automation-agent -->
