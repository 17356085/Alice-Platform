# TECH_ANALYSIS — system-role / role-list

> 基于 RoleManagePage.py 重构版 + PAGE_CONTEXT | 2026-06-12
> 路由: `#/system/role` | PO: `page/system_page/RoleManagePage.py`
> 特点：RBAC核心 + 权限分配弹窗(自定义perm-group组件) + 分配用户双栏穿梭

## Element Plus 组件识别

| 组件类型 | 用途 | 定位特点 |
|----------|------|----------|
| el-form--inline | 搜索区 | 2个el-input + 1个el-select + 2个el-button |
| el-input | 角色名称/编码搜索 | placeholder="请输入角色名称"/"请输入角色编码" |
| el-select | 状态筛选 | label="状态"关联 |
| el-table | 角色列表（6列） | 操作列含权限分配/分配用户/编辑/删除 |
| el-dialog | 新增/编辑/权限分配/分配用户弹窗 | ⚠️ 多弹窗DOM共存，使用 `[last()]` 选取最新 |
| el-radio-group | 新增/编辑弹窗内状态选择 | 启用/停用 |
| el-checkbox-group | 权限分配弹窗 | 自定义perm-group，500+checkbox |
| el-transfer | 分配用户弹窗 | 双栏穿梭框 |
| el-pagination | 分页器 | 标准 |

## 定位器设计表（从 RoleManagePage.py 提取）

### 搜索区

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 角色名称输入 | XPATH | `//input[@placeholder="请输入角色名称"]` | A | placeholder语义 |
| 角色编码输入 | XPATH | `//input[@placeholder="请输入角色编码"]` | A | placeholder语义 |
| 状态下拉 | XPATH | `//*[normalize-space(.)="状态"]/ancestor::div[contains(@class,"el-form-item")]//div[contains(@class,"el-select")]` | B | ⚠️ 异步DOM，StaleElement风险 |
| 搜索按钮 | XPATH | `//button[.//span[normalize-space(.)="搜索"]]` | A | |
| 重置按钮 | XPATH | `//button[.//span[normalize-space(.)="重置"]]` | A | |

### 工具栏

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 新增按钮 | XPATH | `//button[.//span[normalize-space(.)="新增"]]` | A | |
| 编辑按钮 | XPATH | `//button[.//span[normalize-space(.)="修改"]]` | A | |
| 删除按钮 | XPATH | `//button[.//span[normalize-space(.)="删除"]]` | A | |

### 表格区

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 表格行 | XPATH | `//tr[contains(@class, "el-table__row")]` | B | |
| 表头 | XPATH | `//div[contains(@class,"el-table__header-wrapper")]//th//div` | A | |
| 分页器 | CSS | `.el-pagination` | A | |
| 下一页 | CSS | `.el-pagination .btn-next` | B | 有多fallback |

### 弹窗区（使用 `(//div[contains(@class,"el-dialog")])[last()]` 选取最新弹窗）

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 弹窗标题 | XPATH | `(//div[contains(@class,"el-dialog")])[last()]//span[contains(@class,"el-dialog__title")]` | B | |
| 弹窗-角色名 | XPATH | `//div[contains(@class,"el-dialog")]//input[@placeholder="请输入角色名称"]` | A | |
| 弹窗-角色编码 | XPATH | `//div[contains(@class,"el-dialog")]//input[@placeholder="请输入角色编码"]` | A | |
| 弹窗-显示顺序 | XPATH | label含"显示顺序"的form-item内input | B | 动态label定位 |
| 弹窗-备注 | XPATH | label含"备注"的form-item内textarea | B | |
| 弹窗-启用 | XPATH | `(//div[contains(@class,"el-dialog")])[last()]//label[.//span[normalize-space(.)="启用"]]` | B | radio |
| 弹窗-停用 | XPATH | `(//div[contains(@class,"el-dialog")])[last()]//label[.//span[normalize-space(.)="停用"]]` | B | radio |
| 弹窗-确定 | XPATH | `(//div[contains(@class,"el-dialog")])[last()]//button[.//span[normalize-space(.)="确定"]]` | B | |
| 弹窗-取消 | XPATH | `(//div[contains(@class,"el-dialog")])[last()]//button[.//span[normalize-space(.)="取消"]]` | B | |

### Toast/消息

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| Toast消息 | XPATH | `(//*[contains(@class,"el-message__content") and normalize-space(.)!=""])[last()]` | B | ⚠️ 可能为空 |
| 表单错误 | CSS | `.el-form-item__error` | A | |

## 已知技术难题

| 问题 | 影响 | 当前处理 |
|------|------|----------|
| 状态下拉DOM异步刷新 | StaleElementReferenceException，1个用例失败 | 需用WebDriverWait等待DOM稳定 |
| `wait_table_ready()` 方法不存在 | 4个用例失败（方法名拼写错误） | 改为 `wait_page_ready()`（1行修复） |
| 编辑保存后Toast为空 | 1个用例失败 | 排查弹窗关闭→Toast出现时序 |
| 权限分配弹窗自定义perm-group组件 | 500+checkbox，定位困难 | 待分析HTML结构 |
| 多弹窗DOM共存 | `[last()]`选取最新，但关闭弹窗DOM可能未移除 | teardown中主动关闭残留弹窗 |

## 异步等待策略

| 场景 | 等待条件 | 实现 |
|------|----------|------|
| 页面加载 | 表格出现 | `wait_page_ready()` (修复后) |
| 搜索完成 | loading消失 | `_wait_loading_gone()` |
| 状态下拉 | DOM稳定后再操作 | `WebDriverWait` + 额外延迟 |
| 弹窗打开 | el-dialog visible | `WebDriverWait` for dialog |
| 弹窗关闭 | dialog invisible | `wait.until(EC.invisibility_of_element_located)` |
| Toast出现 | el-message__content 可见 | `WebDriverWait` |

## 自动化代码映射

- PO：`page/system_page/RoleManagePage.py`（重构版，继承BasePage，去绝对XPath，去time.sleep）
- 测试：`script/system/test_role_management.py`（15用例，P0:3 + P1:8 + P2:4）
- conftest：`script/system/conftest.py`
- 当前通过率：46.7%（7/15），6 failed待修复

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 | next_phase: Phase 3.5 | next_agent: automation-agent -->
