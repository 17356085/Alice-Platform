## 页面分析报告: 访客管理 (personnel/visitor)

根据项目基座的 `SOP` 流程和 `project-profile` 上下文，对 `personnel` 模块下的 `visitor` 页面进行的页面结构分析。

**分析方式**: 基于模块上下文 (MODULE_CONTEXT) 和行业标准经验进行通用化结构推断（因未提供截图/源码）。若需精确的HTML定位器，请提供页面截图或HTML片段。

---

### PAGE_CONTEXT.md

#### 1. 页面整体结构

| 区域 | 布局描述 |
|------|----------|
| **顶部** | 面包屑导航/页面标题 + 操作按钮（新增、批量导入/导出） |
| **主内容区** | 分为两个主要区域: **搜索/筛选区** 和 **数据表格区** |
| **右侧/下层** | 分页组件与数据统计信息 |

#### 2. 搜索/筛选区

| 元素ID | 元素描述 | 控件类型 (Element Plus) | 所在区域 | 备注/定位思路 |
|--------|----------|--------------------------|----------|--------------|
| `search_visitorName` | 访客姓名/单位 | `el-input` | 搜索区 | 标签为“访客姓名” |
| `search_phone` | 手机号 | `el-input` | 搜索区 | 支持模糊搜索 |
| `search_status` | 来访状态 | `el-select` | 搜索区 | 下拉选项：待访、在访、已离场 |
| `search_visitDate` | 来访日期范围 | `el-date-picker (daterange)` | 搜索区 | 标签为“来访时间” |
| `search_interviewer` | 被访人 | `el-input` | 搜索区 | 标签为“被访人” |
| `btn_search` | 查询按钮 | `el-button` | 搜索区 | 文字: “搜索” / 图标: 搜索 |
| `btn_reset` | 重置按钮 | `el-button` | 搜索区 | 文字: “重置” |
| `btn_add` | 新增访客 | `el-button (primary)` | 页面顶部/工具栏 | **权限点: 新增** |
| `btn_import` | 批量导入 | `el-button` | 页面顶部/工具栏 | 权限点: 导入 |
| `btn_export` | 导出 | `el-button` | 页面顶部/工具栏 | 权限点: 导出 |

#### 3. 表格/列表区

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| `table_visitor` | 访客列表表格 | `el-table` | 主内容区 | 表格体 |
| `col_index` | 序号 | `el-table-column (type="index")` | 表格列 | 自动编号 |
| `col_visitorName` | 访客姓名 | `el-table-column` | 表格列 | 文本 |
| `col_company` | 所属单位 | `el-table-column` | 表格列 | 文本 |
| `col_phone` | 手机号 | `el-table-column` | 表格列 | 文本，脱敏展示 |
| `col_interviewer` | 被访人 | `el-table-column` | 表格列 | 文本 |
| `col_visitPurpose` | 来访事由 | `el-table-column` | 表格列 | 文本 |
| `col_visitTime` | 来访时间 | `el-table-column` | 表格列 | 日期时间格式 |
| `col_leaveTime` | 离场时间 | `el-table-column` | 表格列 | 日期时间，空值展示“-” |
| `col_status` | 状态 | `el-table-column` | 表格列 | 标签：待访(灰色)/在访(蓝色)/已离场(绿色) |
| `col_action` | 操作 | `el-table-column (fixed="right")` | 表格列 | 见下表 |
| `row_action_edit` | 编辑 | `el-button (text)` | 操作列 | **权限点: 编辑** |
| `row_action_view` | 查看 | `el-button (link)` | 操作列 | 详情弹窗 |
| `row_action_delete` | 删除 | `el-button (text, danger)` | 操作列 | **权限点: 删除**，需二次确认 |
| `row_action_force_logout` | 强制离场 | `el-button (text)` | 操作列 | 仅“在访”状态展示 |

**滚动/加载**: 表格默认支持按行滚动，无虚拟滚动。

#### 4. 分页区

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| `pagination` | 分页器 | `el-pagination` | 表格底部 | 位于页面右下方 |
| `pagination_total` | 总条数 | `el-pagination / total` | 分页栏 | 显示“共 XX 条” |
| `pagination_pageSize` | 每页条数 | `select` | 分页栏 | 选项: 10 / 20 / 50 / 100 |
| `pagination_goto` | 跳转页 | `el-pagination / jumper` | 分页栏 | 可接受输入页码 |

#### 5. 弹窗/对话框

**5.1 新增访客弹窗**

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| `dialog_add` | 新增访客弹窗 | `el-dialog` | 弹窗层 | 标题: “新增访客”|
| `form_add_visitorName` | 访客姓名 | `el-input` | 弹窗表单 | 必填 |
| `form_add_company` | 所属单位 | `el-input` | 弹窗表单 | 必填 |
| `form_add_phone` | 手机号 | `el-input` | 弹窗表单 | 必填，需校验格式 |
| `form_add_idCard` | 身份证号 | `el-input` | 弹窗表单 | 选填 |
| `form_add_interviewer` | 被访人 | `el-select` / `el-autocomplete` | 弹窗表单 | 可从员工列表选择 |
| `form_add_visitPurpose` | 来访事由 | `el-textarea` / `el-input` | 弹窗表单 | 选填 |
| `form_add_visitDate` | 来访时间 | `el-date-picker` | 弹窗表单 | 默认当前时间，可修改 |
| `btn_dialog_add_confirm` | 提交按钮 | `el-button (primary)` | 弹窗底部 | 文字: “确认” |
| `btn_dialog_add_cancel` | 取消按钮 | `el-button` | 弹窗底部 | 文字: “取消” |

**5.2 查看详情弹窗**
考虑为只读模态框，展示上述所有表单数据的文本版本。标题: “访客详情”。

**5.3 删除确认弹窗**

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| `dialog_delete` | 删除确认框 | `el-message-box` | 弹窗层 | 标题: “确认删除” |
| `dialog_delete_content` | 提示文本 | `text` | 弹窗内容 | “确定要删除该访客记录吗？” |
| `btn_dialog_delete_confirm` | 确认删除 | `el-button (danger)` | 弹窗 | 文字: “确认” |
| `btn_dialog_delete_cancel` | 取消 | `el-button` | 弹窗 | 文字: “取消” |

#### 6. 页面状态

| 状态 | UI表现 | 备注 |
|------|--------|------|
| **加载中** | 表格区域显示骨架屏 (`el-skeleton`) 或旋转加载图标 (`el-loading`) | WebDriverWait 等待 `el-loading-mask` 消失 |
| **空数据** | 表格内显示 `<el-empty>` 组件，文案: “暂无访客记录” | 左侧无任何数据 |
| **查询无结果** | 表格内显示 `<el-empty>` 组件，文案: “未找到相关访客” | 搜索后无匹配 |
| **网络错误** | 全局 `el-message` 或 `el-alert`: "获取访客列表失败，请稍后重试" | 通常伴随重试按钮 |

#### 7. 权限点

| 元素描述 | 权限点标识 | 控制方式 |
|----------|------------|----------|
| 新增按钮 | `btn_add` | 角色/权限: `add`，不可见或 `disabled` |
| 编辑按钮 | `row_action_edit` | 角色/权限: `edit`，不可见 |
| 删除按钮 | `row_action_delete` | 角色/权限: `delete`，不可见 |
| 导入按钮 | `btn_import` | 角色/权限: `import` |
| 导出按钮 | `btn_export` | 角色/权限: `export` |
| 批量操作 | `batch_delete` | 表格左侧批量勾选，仅在拥有删除权限时可见 |

---

### PAGE_ELEMENT_POSITION.md (初版)

**注意**: 因暂无源码，以下定位器基于 **Element Plus 最佳实践** 和 Element Plus 默认组件结构推断。实际应以页面DOM为准。

| 逻辑元素ID | 定位策略 | 定位值 (示例) | 稳定性 | 备用定位方案 |
|------------|----------|---------------|--------|-------------|
| `btn_search` | A级 - CSS | `#search-ref > .el-form > .el-button--primary` 或 `button:has-text("搜索")` (Playwright) | 中等 | B级: CSS `.el-form .el-button--primary`; C级: XPath `//button[contains(text(),"搜索")]` |
| `search_phone` | A级 - CSS | `input[placeholder="手机号"]` or `input[aria-label="手机号"]` | **高** | B级: CSS `.el-input-group__input input` |
| `table_visitor` | A级 - CSS | `.el-table` | 高 | B级: `.visitor-table` (若自定义了类名) |
| `dialog_add` | A级 - CSS | `div[aria-label="新增访客"]` (来自 `el-dialog` 的 title) | 高 | B级: `.el-dialog`; C级: XPath `//div[@aria-label="新增访客"]` |
| `form_add_phone` | A级 - CSS | `input[placeholder="请输入手机号"]` | 高 | B级: `.el-form-item:has(.el-input) input` |
| `row_action_delete` | B级 - CSS | `.el-table__row .el-button--danger` | 中等 | C级: XPath `//tr[contains(@class,"el-table__row")]//button[contains(text(),"删除")]` (相对定位，基于父行) |
| `btn_dialog_delete_confirm` | A级 - CSS | `button.el-message-box__btn:has-text("确认")` | 中等 | B级: XPath `//div[@role="alertdialog"]//button[contains(text(),"确认")]` |

**关键设计原则**:
1.  **桌面端优先**: 所有元素默认在 `992px` 以上设计。
2.  **按钮可见性/可点击性**: 使用 `wait_for_visibility` + `wait_for_clickable`。对于 `v-if` 组件，优先等待父容器加载。
3.  **WebDriverWait 策略**:
    - 页面加载: 等待 `el-loading-mask` 消失 (`visibility_of_element_located` / or `invisibility_of_element`)
    - 弹窗出现: 等待 `.el-dialog__wrapper` 可见
    - 表格加载: 等待 `.el-table__body tbody tr` 可见
    - 异步请求: 等待网络空闲或特定元素出现

**结论**: 页面元素已完成标准化分析。下一步：将 `PAGE_ELEMENT_POSITION.md` 传入 `skills/testcase-design.md` 生成测试用例。