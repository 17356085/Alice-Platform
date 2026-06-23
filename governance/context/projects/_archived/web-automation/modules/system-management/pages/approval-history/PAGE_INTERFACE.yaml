## 模块：workflow / 页面：approval-history

> 由于未提供页面截图或 HTML 源码，以下分析基于常见审批历史页面的结构假设（Element Plus + Vue3）。实际使用时请根据真实页面调整。

---

### PAGE_CONTEXT.md（页面元素清单）

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| filter-approval-name | 审批流程名称搜索输入框 | `el-input` | 搜索区 | 模糊匹配 |
| filter-applicant | 申请人搜索输入框 | `el-input` | 搜索区 | 支持按姓名/工号检索 |
| filter-approval-status | 审批状态下拉筛选 | `el-select` | 搜索区 | 选项：全部/待审批/已通过/已驳回/已撤回 |
| filter-date-range | 申请时间范围选择器 | `el-date-picker` (daterange) | 搜索区 | 类型：daterange |
| btn-search | 搜索按钮 | `el-button` (primary) | 搜索区 | 执行搜索 |
| btn-reset | 重置按钮 | `el-button` (default) | 搜索区 | 清空所有筛选条件 |
| btn-export | 导出审批记录 | `el-button` (text) | 搜索区 | 导出当前筛选结果 |
| table | 审批列表表格 | `el-table` | 主内容区 | 可多选 |
| col-approval-name | 审批流程名称列 | 文本 | 表格 | 可点击跳转详情 |
| col-approval-type | 审批类型列 | 标签（Tag） | 表格 | 如：请假/报销/采购 |
| col-applicant | 申请人列 | 文本 | 表格 | 含头像/姓名 |
| col-apply-time | 申请时间列 | 日期时间 | 表格 | 格式：yyyy-MM-dd HH:mm |
| col-status | 当前状态列 | 状态标签（Tag） | 表格 | 颜色区分：待审批=warning，通过=success，驳回=danger |
| col-process-instance-id | 流程实例ID | 文本 | 表格 | 一般隐藏列，仅调试用 |
| col-actions | 操作列 | 操作按钮组 | 表格 | 包含查看详情/催办/撤回（待审批状态）等 |
| btn-view-detail | 查看详情 | `el-button` (text) | 表格·操作列 | 打开详情弹窗 |
| btn-urge | 催办 | `el-button` (text) | 表格·操作列 | 仅待审批状态显示 |
| btn-revoke | 撤回 | `el-button` (text) | 表格·操作列 | 仅待审批且当前用户发起的状态显示 |
| pagination | 分页组件 | `el-pagination` | 表格底部 | 支持每页条数选择（10/20/50/100） |
| detail-dialog | 审批详情弹窗 | `el-dialog` | 弹窗 | 包含审批进度与表单数据 |
| detail-timeline | 审批进度时间线 | `el-timeline` | 弹窗内容区 | 展示各审批节点与操作人 |
| detail-form-data | 表单数据展示 | `el-descriptions` | 弹窗内容区 | 展示申请表单的字段键值对 |
| detail-btn-close | 关闭详情弹窗按钮 | `el-button` (default) | 弹窗底部 | 关闭弹窗 |
| empty-placeholder | 空数据占位 | `el-empty` | 主内容区 | 查询结果为空时显示 |
| loading-mask | 加载遮罩 | `v-loading` | 主内容区 | 数据加载中时显示 |

---

### PAGE_ELEMENT_POSITION.md（元素定位器设计）

| 元素ID | 定位策略 | 定位值（建议） | 稳定性评级 | 备用方案 |
|--------|----------|----------------|------------|----------|
| filter-approval-name | `placeholder` | `请输入流程名称` | A | CSS: `.search-form .el-input__inner` (配合位置) |
| filter-applicant | `placeholder` | `请输入申请人` | A | CSS: `.search-form .el-input` (第2个) |
| filter-approval-status | `el-select` 关联的 `el-select-dropdown` | 使用 `el-select` 的 `aria-label` 或 `data-testid` (需开发添加) | B（建议提升至A） | XPath: `//label[contains(text(),'审批状态')]/following-sibling::div//input` |
| filter-date-range | `class` + `placeholder` | `.el-date-editor--daterange` 中的第一个 `input` | B | XPath: `//input[@placeholder='开始日期']` |
| btn-search | `text()` + `button type` | `XPath: //button[contains(text(), '搜索')]` | A（文字稳定） | CSS: `.search-form .el-button--primary` |
| btn-reset | `text()` | `XPath: //button[span[contains(text(),'重置')]]` | A | CSS: `.search-form .el-button:not(.el-button--primary)` |
| btn-export | `text()` | `XPath: //button[contains(text(), '导出')]` | A | CSS: `.el-button--text` (需确认包含文字) |
| table | `class` | `CSS: .el-table` | B | 无备用 |
| col-approval-name | `class` + `index` | `CSS: .el-table__body-wrapper tbody tr td:nth-child(1) a` | B | XPath: `//table//tr[1]/td[1]/a` (动态行数需注意) |
| col-approval-type | `class` + `index` | `CSS: .el-table__body-wrapper tbody tr td:nth-child(2) .el-tag` | B | XPath: `//table//tr[1]/td[2]//span[@class='el-tag']` |
| col-applicant | `class` + `index` | `CSS: .el-table__body-wrapper tbody tr td:nth-child(3)` | B | XPath: `//table//tr[1]/td[3]` |
| col-apply-time | `class` + `index` | `CSS: .el-table__body-wrapper tbody tr td:nth-child(4)` | B | XPath: `//table//tr[1]/td[4]` |
| col-status | `class` + `index` | `CSS: .el-table__body-wrapper tbody tr td:nth-child(5) .el-tag` | B | XPath: `//table//tr[1]/td[5]//span` |
| btn-view-detail | `text()` (按钮文字) | `XPath: //button[contains(@class, 'el-button--text') and contains(., '详情')]` | A | CSS: `.el-table__body-wrapper .el-button--text` (结合上下文) |
| btn-urge | `text()` | `XPath: //button[contains(@class, 'el-button--text') and contains(., '催办')]` | A | CSS: `.el-table__body-wrapper .el-button--text` (需区分) |
| btn-revoke | `text()` | `XPath: //button[contains(@class, 'el-button--text') and contains(., '撤回')]` | A | CSS: `.el-table__body-wrapper .el-button--text` (需区分) |
| pagination | `class` | `CSS: .el-pagination` | B | 无备用 |
| detail-dialog | `class` + `aria-label` 或 `role` | `CSS: .el-dialog` (可见时) | B | XPath: `//div[@role='dialog' and contains(@class, 'el-dialog') and contains(., '审批详情')]` |
| detail-timeline | `class` | `CSS: .el-timeline` | B | 无备用 |
| detail-form-data | `class` | `CSS: .el-descriptions` | B | 无备用 |
| detail-btn-close | `text()` | `XPath: //div[@role='dialog']//button[contains(text(), '关 闭')]` | A（文字稳定） | CSS: `.el-dialog__footer .el-button--default` |
| empty-placeholder | `class` | `CSS: .el-empty` | B | 无备用 |
| 加载遮罩 | `class` (v-loading 生成) | `CSS: .el-loading-mask` | B | 无备用 |

> **备注**：
> - 所有A级定位器建议开发添加 `data-testid` 属性以提升稳定性。
> - 表格行定位需配合动态索引处理（WebDriverWait + 行数判断）。
> - 弹窗内容（时间线、表单数据）在对话框关闭后从DOM中移除，交互前需等待 `DIALOG` 可见。
> - 催办/撤回按钮按状态显示，需检查 `el-popover` 的自定义气泡确认框（如有）。

---

### 等待策略建议

| 场景 | 等待条件 | 方法 |
|------|----------|------|
| 页面加载完成 | 表格可见 + loading消失 | `wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.el-table')))` + `wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.el-loading-mask')))` |
| 搜索后等待结果刷新 | 表格数据更新（可等待旧行消失或新行出现） | `wait.until(EC.staleness_of(old_row))` 或 `wait.until(lambda d: driver.execute_script("return document.readyState") == 'complete')` |
| 弹窗打开 | 对话框可见 | `wait.until(EC.visibility_of_element_located(DIALOG))` (DIALOG定位器见BasePage) |
| 弹窗关闭 | 对话框不可见 | `wait.until(EC.invisibility_of_element_located(DIALOG))` |
| 筛选下拉选项加载 | 下拉面板可见 | `wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.el-popper')))` (teleport到body) |
| 导出完成 | 导出按钮可点击 + 下载完成（如需要） | 建议使用非侵入式等待，如轮询文件是否存在 |

---

> **下一步**：根据实际页面截图或HTML源码调整上下元素。  
> 如需生成 `PAGE_INTERFACE.yaml`（供 automation-agent 消费），请执行：  
> `python tools/generate_page_interface.py --module workflow --page approval-history`