好的，根据你提供的代码和上下文，我将为你输出两个文件：`PAGE_CONTEXT.md` 和 `PAGE_ELEMENT_POSITION.md`。

---

## PAGE_CONTEXT.md

```markdown
# PAGE_CONTEXT — personnel / contractor-personnel

## 基本信息
- **页面ID**：contractor-personnel
- **页面名称**：承包商人员
- **所属模块**：人员管理（personnel）→ 承包商管理
- **页面入口**：左侧菜单 → 人员管理 → 承包商管理 → 承包商人员
- **路由 / 标识**：`#/personnel/contractor`（与承包商单位共用路由，通过侧边栏 nest-menu 切换）
- **自动化代码**：`page/personnel_page/ContractorPersonnelPage.py` + `script/personnel/test_contractor_personnel.py`

## 页面职责
- 展示承包商人员列表，支持按姓名/身份证、所属单位、入场状态搜索。
- 提供承包商人员的新增、编辑、启停用、删除操作。
- **无独立路由**，需通过侧边栏 nest‑menu 项在 `#/personnel/contractor` 下切换内部视图。

## 页面结构
```
┌─────────────────────────────────────────────┐
│  面包屑 & 标签页（如有）                     │
├─────────────────────────────────────────────┤
│  搜索区（el-card 包裹）                     │
│  ├─ 姓名/身份证输入框 (el-input)            │
│  ├─ 所属承包商下拉 (el-select)              │
│  ├─ 入场状态下拉 (el-select)                │
│  └─ [搜索] [重置] 按钮                      │
├─────────────────────────────────────────────┤
│  工具栏                                      │
│  └─ [新增] 按钮                              │
├─────────────────────────────────────────────┤
│  表格区 (el-table)                          │
│  ├─ 姓名 | 身份证号 | 所属单位 | 手机号     │
│  │  入场状态 | 操作（编辑/启停用/删除）     │
│  └─ 分页器 (el-pagination)                  │
└─────────────────────────────────────────────┘
```

## 核心元素清单

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| search-name | 姓名/身份证搜索框 | el-input | 搜索区(card) | placeholder="请输入姓名/身份证" |
| search-unit | 所属承包商下拉 | el-select | 搜索区(card) | 需先有承包商单位数据（依赖前置数据） |
| search-status | 入场状态下拉 | el-select | 搜索区(card) | 选项：未进场/已进场/退场 |
| search-btn | 搜索按钮 | el-button | 搜索区 | 触发表格异步刷新，需等待加载消失 |
| reset-btn | 重置按钮 | el-button | 搜索区 | 清空搜索条件，可能不触发请求 |
| add-btn | 新增按钮 | el-button | 工具栏 | 打开新增弹窗（el-dialog） |
| table | 承包商人员表格 | el-table | 表格区 | card+table 混合布局，数据异步加载 |
| col-name | 姓名列 | text | 表格区 | 第1列，可排序？需要确认 |
| col-idcard | 身份证列 | text | 表格区 | 第2列 |
| col-unit | 所属单位列 | text | 表格区 | 第3列 |
| col-phone | 手机号列 | text | 表格区 | 第4列 |
| col-entry-date | 入场日期列 | text | 表格区 | 第5列（可能格式为 yyyy-MM-dd） |
| col-status | 入场状态列 | el-tag | 表格区 | 第6列，颜色：已进场(绿色)、未进场(灰色)、退场(红色？) |
| col-actions | 操作列 | buttons | 表格区 | 第7列：编辑、启/停用、删除（根据状态显示不同文字） |
| dialog | 新增/编辑弹窗 | el-dialog | 弹窗 | 表单容器，标题可能为“新增人员”或“编辑人员” |
| dialog-name | 姓名输入框 | el-input | 弹窗 | label="姓名"，必填 |
| dialog-idcard | 身份证输入框 | el-input | 弹窗 | label="身份证"，必填 |
| dialog-unit | 所属承包商下拉 | el-select | 弹窗 | label="所属单位"，必填 |
| dialog-job | 岗位输入框 | el-input | 弹窗 | label="岗位" |
| dialog-phone | 手机号输入框 | el-input | 弹窗 | label="手机号" |
| pagination | 分页器 | el-pagination | 表格底部 | 含每页条数选择（default 20）、页码导航、总数显示 |
| sidebar-personnel | 侧边栏-承包商人员 | el-menu-item.nest-menu | 侧边栏 | 无独立href，点击切换视图（嵌套菜单第三级） |
| toast-success | 操作成功提示 | el-message | 全局 | 出现后消失（通常绿色背景） |
| toast-error | 操作失败提示 | el-message | 全局 | 出现后消失（通常红色背景） |
| confirm-dialog | 确认弹窗（停用/删除） | el-message-box | 弹窗 | 标题“确认”类似，有确定/取消按钮 |

## 关键交互流程
1. **导航**：展开"人员管理"→展开"承包商管理"→点击"承包商人员"→等待表格加载（等待 el-table 出现及 loading 消失）。
2. **搜索**：在card搜索区输入条件 → 点击[搜索] → 表格异步刷新（等待 loading 消失，检查数据变更）。
3. **新增**：点击[新增] → 弹窗 → 选择所属承包商 + 填写人员信息 → 点击[保存]（弹窗的 primary 按钮）→ 弹窗关闭 → 表格刷新（显示 toast 成功）。
4. **编辑**：点击行内[编辑] → 同新增弹窗（预填数据） → 修改后保存 → 同新增。
5. **启/停用**：点击[停用]（当前启用）或[启用]（当前停用） → 确认弹窗（el-message-box） → 点击[确定] → 表格刷新，状态列变化。
6. **删除**：点击[删除] → 确认弹窗 → 点击[确定] → 表格刷新，该行消失。

## 权限与角色（基于项目常见模式推断，需确认）
| 权限标识 | 功能 | 可见角色 |
|----------|------|----------|
| `personnel:contractor:person:list` | 查看列表 | admin, contractor_admin |
| `personnel:contractor:person:create` | 新增 | admin, contractor_admin |
| `personnel:contractor:person:edit` | 编辑 | admin, contractor_admin |
| `personnel:contractor:person:delete` | 删除 | admin (仅管理员) |
| `personnel:contractor:person:status` | 启停用 | admin, contractor_admin |
| 侧边栏菜单可见性 | 访问页面 | 拥有上述任一权限的角色 |

> **说明**：权限标识符为推测，实际需在系统管理-角色管理中确认。

## 等待策略标注
| 场景 | 等待条件 | 超时 |
|------|---------|------|
| 页面加载（导航后） | el-table 出现且 loading 消失（`wait_vue_stable()` 内含） | 15s |
| 搜索/新增/编辑/删除后 | loading 消失 + 表格数据变化（行数或内容非空） | 10s |
| 弹窗打开 | el-dialog 可见（`visibility_of_element_located`） | 5s |
| 弹窗关闭 | el-dialog 不存在（`invisibility_of_element_located`） | 5s |
| toast 出现 | el-message__content 可见（可同步读取文本） | 3s |
| 确认弹窗 | el-message-box 可见（`visibility_of_element_located`） | 5s |
```

---

## PAGE_ELEMENT_POSITION.md

```markdown
# PAGE_ELEMENT_POSITION — personnel / contractor-personnel

> **定位器优先级说明**：
> - **A级**：基于 data-testid、唯一 id、name、placeholder（最稳定）
> - **B级**：基于稳定 CSS class 组合（需验证 class 不随版本变化）
> - **C级**：XPath（含文本匹配、关系定位，作为保底）

## 搜索区元素

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|--------|----------|--------|-----------|----------|
| search-name | **A级**（placeholder） | `(By.CSS_SELECTOR, 'input[placeholder*="姓名"]')` 或 `(By.XPATH, '//input[contains(@placeholder,"姓名")]')` | A | B级：`(By.CSS_SELECTOR, '.el-card input[type="text"]')` |
| search-unit | **B级**（form 内唯一 select） | `(By.CSS_SELECTOR, '.el-card .el-select:first-of-type')` | B | C级：`(By.XPATH, '//div[contains(@class,"el-card")]//div[contains(@class,"el-select")][.//label[contains(.,"所属承包商")]]')` |
| search-status | **B级**（form 内第二个 select） | `(By.CSS_SELECTOR, '.el-card .el-select:nth-of-type(2)')` | B | C级：`(By.XPATH, '//div[contains(@class,"el-card")]//div[contains(@class,"el-select")][.//label[contains(.,"入场状态")]]')` |
| search-btn | **A级**（按钮文本） | `(By.XPATH, '//button[contains(@class,"el-button") and .//span[text()="搜索"]]')` | A | B级：`(By.CSS_SELECTOR, '.el-card .el-button--primary')` |
| reset-btn | **A级**（按钮文本） | `(By.XPATH, '//button[contains(@class,"el-button") and .//span[text()="重置"]]')` | A | B级：`(By.CSS_SELECTOR, '.el-card .el-button:not(.el-button--primary)')` |

## 工具栏

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|--------|----------|--------|-----------|----------|
| add-btn | **A级**（按钮文本） | `(By.XPATH, '//button[contains(@class,"el-button") and .//span[text()="新增"]]')` | A | B级：`(By.CSS_SELECTOR, '.el-button--primary:not(.el-card .el-button--primary)')`（注意与搜索按钮区分） |

## 表格区

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|--------|----------|--------|-----------|----------|
| table | **B级**（class） | `(By.CSS_SELECTOR, '.el-table')`（页面唯一的表格） | B | C级：`(By.XPATH, '//div[contains(@class,"el-table")]')` |
| col-name | 列索引 | `COL_NAME = 1`（配合 get_column_data） | A | 无备用（列索引固定）|
| col-idcard | 列索引 | `COL_ID_CARD = 2` | A | |
| col-unit | 列索引 | `COL_UNIT = 3` | A | |
| col-phone | 列索引 | `COL_PHONE = 4` | A | |
| col-entry-date | 列索引 | `COL_ENTRY_DATE = 5` | A | |
| col-status | 列索引 + 内部标签 | `COL_STATUS = 6`；状态标签可用：`(By.XPATH, '//tr[1]/td[6]//span[contains(@class,"el-tag")]')` | B | |
| col-actions | 列索引 | `COL_OPERATIONS = 7` | A | 行内按钮定位器见下 |

## 行内操作按钮

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|--------|----------|--------|-----------|----------|
| table-edit-btn | **A级**（文本） | `(By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[text()="编辑"]]')` | A | B级：`(By.CSS_SELECTOR, '.el-table__row .el-button--text .el-icon-edit')`（需确认图标） |
| table-toggle-status-btn | **A级**（文本） | `(By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[text()="停用" or text()="启用"]]')` | A | B级：同上，但文字不同 |
| table-delete-btn | **A级**（文本） | `(By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[text()="删除"]]')` | A | B级：`(By.CSS_SELECTOR, '.el-table__row .el-button--danger')` |

## 弹窗（新增/编辑）

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|--------|----------|--------|-----------|----------|
| dialog | **B级**（class） | `(By.CSS_SELECTOR, '.el-dialog[aria-label*="人员"]')`（匹配标题） | B | C级：`(By.XPATH, '//div[contains(@class,"el-dialog")]//span[contains(text(),"人员")]/ancestor::div[contains(@class,"el-dialog")]')` |
| dialog-name | **A级**（label 关联） | `(By.XPATH, '//label[text()="姓名"]/following-sibling::div//input')` | A | B级：`(By.CSS_SELECTOR, '.el-dialog .el-form-item:first-child input')` |
| dialog-idcard | **A级**（label 关联） | `(By.XPATH, '//label[text()="身份证"]/following-sibling::div//input')` | A | B级：`(By.CSS_SELECTOR, '.el-dialog .el-form-item:nth-child(2) input')` |
| dialog-unit | **B级**（label 关联） | `(By.XPATH, '//label[text()="所属单位"]/following-sibling::div//div[contains(@class,"el-select")]')` | B | C级：`(By.XPATH, '//div[contains(@class,"el-dialog")]//div[contains(@class,"el-select")][.//label[contains(.,"所属单位")]]')` |
| dialog-job | **A级**（label 关联） | `(By.XPATH, '//label[text()="岗位"]/following-sibling::div//input')` | A | B级：`(By.CSS_SELECTOR, '.el-dialog .el-form-item:nth-child(4) input')`（假设顺序） |
| dialog-phone | **A级**（label 关联） | `(By.XPATH, '//label[text()="手机号"]/following-sibling::div//input')` | A | B级：`(By.CSS_SELECTOR, '.el-dialog .el-form-item:nth-child(5) input')`（假设顺序） |
| dialog-save | **A级**（按钮文本） | `(By.XPATH, '//div[contains(@class,"el-dialog")]//button[.//span[text()="确 定"] or .//span[text()="保存"]]')` | A | B级：`(By.CSS_SELECTOR, '.el-dialog .el-button--primary')` |
| dialog-cancel | **A级**（按钮文本） | `(By.XPATH, '//div[contains(@class,"el-dialog")]//button[.//span[text()="取 消"]]')` | A | B级：`(By.CSS_SELECTOR, '.el-dialog .el-button:not(.el-button--primary)')` |

## 分页区

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|--------|----------|--------|-----------|----------|
| pagination-container | **B级**（class） | `(By.CSS_SELECTOR, '.el-pagination')` | B | C级：`(By.XPATH, '//div[contains(@class,"el-pagination")]')` |
| page-size-select | **B级**（class） | `(By.CSS_SELECTOR, '.el-pagination .el-select .el-select__wrapper')` | B | C级：`(By.XPATH, '//div[contains(@class,"el-pagination")]//div[contains(@class,"el-select")]')` |
| page-size-option | **C级**（动态选项） | `(By.XPATH, '//li[contains(@class,"el-select-dropdown__item") and contains(., "{size}")]')` 动态格式化 | C | B级：可使用 `select_by_visible_text` 方法 |
| next-page-btn | **B级**（class） | `(By.CSS_SELECTOR, '.el-pagination .btn-next')` | B | C级：`(By.XPATH, '//button[contains(@class,"btn-next")]')` |
| prev-page-btn | **B级**（class） | `(By.CSS_SELECTOR, '.el-pagination .btn-prev')` | B | C级：`(By.XPATH, '//button[contains(@class,"btn-prev")]')` |
| current-page | **B级**（class） | `(By.CSS_SELECTOR, '.el-pagination .el-pager li.is-active')` | B | C级：`(By.XPATH, '//li[contains(@class,"is-active")]')` |
| total-text | **B级**（class） | `(By.CSS_SELECTOR, '.el-pagination .el-pagination__total')` | B | C级：`(By.XPATH, '//span[contains(@class,"el-pagination__total")]')` |

## 侧边栏导航

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|--------|----------|--------|-----------|----------|
| sidebar-personnel | **A级**（文本匹配） | `(By.XPATH, '//li[contains(@class,"el-menu-item")][normalize-space(.)="承包商人员"]')` | A | B级：`(By.CSS_SELECTOR, '.el-menu-item.is-active')`（但可能多个非活跃态，需配合上下文） |

## Toast / 确认弹窗

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|--------|----------|--------|-----------|----------|
| toast-success | **B级**（class） | `(By.CSS_SELECTOR, '.el-message--success .el-message__content')` | B | C级：`(By.XPATH, '//div[contains(@class,"el-message--success")]//p[contains(@class,"el-message__content")]')` |
| toast-error | **B级**（class） | `(By.CSS_SELECTOR, '.el-message--error .el-message__content')` | B | C级同上 |
| confirm-dialog | **B级**（class） | `(By.CSS_SELECTOR, '.el-message-box')` | B | C级：`(By.XPATH, '//div[contains(@class,"el-message-box")]')` |
| confirm-ok | **A级**（按钮文本） | `(By.XPATH, '//div[contains(@class,"el-message-box")]//button[.//span[text()="确定"]]')` | A | B级：`(By.CSS_SELECTOR, '.el-message-box .el-button--primary')` |
| confirm-cancel | **A级**（按钮文本） | `(By.XPATH, '//div[contains(@class,"el-message-box")]//button[.//span[text()="取消"]]')` | A | B级：`(By.CSS_SELECTOR, '.el-message-box .el-button:not(.el-button--primary)')` |

## 等待策略映射（与定位器配合使用）

| 场景 | WebDriverWait 条件 | 涉及的定位器 |
|------|--------------------|-------------|
| 等待弹窗出现 | `EC.visibility_of_element_located(dialog)` | dialog |
| 等待弹窗消失 | `EC.invisibility_of_element_located(dialog)` | dialog |
| 等待 Toast 出现 | `EC.visibility_of_element_located(toast-success 或 toast-error)` | toast-* |
| 等待确认弹窗出现 | `EC.visibility_of_element_located(confirm-dialog)` | confirm-dialog |
| 等待分页更新（点击下一页后） | `EC.staleness_of(<某行>)` 或 `text_to_be_present_in_element(current-page, "2")` | current-page |
| 等待表格加载（导航后） | `EC.presence_of_element_located(table)` + `wait_vue_stable()` | table |
| 等待搜索/操作后表格刷新 | `EC.invisibility_of_element_located((By.CSS_SELECTOR, '.el-loading-mask'))` 或 `EC.presence_of_element_located(table)` 结合行数变化 | table |

> **说明**：以上定位器均基于当前 Page Object 代码与 Element Plus 默认结构设计。若使用 data-testid 属性进行增强（A 级），需开发配合在关键元素上添加 `data-testid` 属性，例如：
> - 搜索输入框：`data-testid="personnel-search-name"`
> - 表格：`data-testid="personnel-table"`
> - 弹窗：`data-testid="personnel-dialog"`
> 建议在后续迭代中推动前后端添加，以提高稳定性。
```

---

以上两份文件可以直接放入 `governance/context/projects/web-automation/modules/personnel/pages/contractor-personnel/` 目录。如果有需要调整的细节（例如权限标识符的确认、具体列索引与实际 DOM 的校对），请告知。