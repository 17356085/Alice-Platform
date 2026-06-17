好的，遵照您的指示，我将基于“实验室”模块下的“气体分析报告”页面，进行专业的页面结构分析和元素定位器设计。

---

### **Phase 1: PAGE_CONTEXT.md 页面结构分析**

基于对“气体分析报告”这类页面的通用理解，以及实验室信息管理系统的常见布局，我假设该页面具备以下典型功能区域。请在实际操作时提供截图或HTML源码进行修正和补充。

---

## `PAGE_CONTEXT.md`

### 1. 页面整体结构

页面布局为典型的“顶部搜索区 + 中部表格区 + 底部分页区”结构。左侧可能包含模块菜单（由 Lab 主框架管理，非此页面独有）。

- **顶部区域**: 存放页面标题“气体分析报告”及关键操作按钮，如“新建报告”、“导出”等。
- **中间区域**: 主要的搜索筛选区，包含按条件过滤报告的表单控件。
- **主体区域**: 用于展示气体分析报告列表的表格组件。
- **底部区域**: 包含标准的分页控制器。

### 2. 搜索/筛选区

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| `search-reportNo` | 报告编号输入框 | `el-input` | 搜索区 | 文本输入，用于模糊或精确搜索 |
| `search-sampleName` | 样本名称输入框 | `el-input` | 搜索区 | 文本输入 |
| `search-startDate` | 创建日期-开始日期 | `el-date-picker` | 搜索区 | 日期范围选择器的开始日期 |
| `search-endDate` | 创建日期-结束日期 | `el-date-picker` | 搜索区 | 日期范围选择器的结束日期 |
| `search-status` | 报告状态下拉选择 | `el-select` | 搜索区 | 选项：(全部/待审核/已审核/已归档) |
| `search-btnQuery` | 查询按钮 | `el-button` | 搜索区 | 触发搜索动作，`type="primary"` |
| `search-btnReset` | 重置按钮 | `el-button` | 搜索区 | 重置所有搜索条件为默认值 |
| `search-btnCreate` | 新建报告按钮 | `el-button` | 搜索区 | 跳转或打开新建报告页面/弹窗 |
| `search-btnExport` | 导出按钮 | `el-button` | 搜索区 | 导出当前列表数据 |

### 3. 表格/列表区

| 元素ID | 元素描述 | 列数据类型 | 所在区域 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| `th-reportNo` | 报告编号 | 文本（可点击跳转） | 表格头部 | 通常带超链接样式 |
| `th-sampleName` | 样本名称 | 文本 | 表格头部 | |
| `th-sampleType` | 样本类型 | 文本/标签 | 表格头部 | |
| `th-testItems` | 检测项目 | 文本 | 表格头部 | 可能包含多个项目名 |
| `th-creator` | 创建人 | 文本 | 表格头部 | |
| `th-createDate` | 创建日期 | 日期 (YYYY-MM-DD) | 表格头部 | |
| `th-status` | 报告状态 | 标签 (Tag) | 表格头部 | 不同状态颜色不同 |
| `th-operations` | 操作 | 操作按钮组 | 表格头部 | |
| `cell-view` | 查看操作按钮 | `el-button` (text/link) | 表格列-操作 | 打开报告详情 |
| `cell-edit` | 编辑操作按钮 | `el-button` (text/link) | 表格列-操作 | 编辑报告（可能受状态限制） |
| `cell-delete` | 删除操作按钮 | `el-button` (text/link) | 表格列-操作 | 删除报告（需二次确认） |
| `cell-approve` | 审核操作按钮 | `el-button` (text/link) | 表格列-操作 | 状态为“待审核”时显示 |

### 4. 分页区

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| `pagination` | 分页组件 | `el-pagination` | 表格底部 | |
| `pagination-total` | 总记录数 | 文本 | 分页器内部 | 显示“共 xx 条” |
| `pagination-sizes` | 每页条数选择器 | `el-select` | 分页器内部 | 选项：[10, 20, 50, 100] |
| `pagination-prev` | 上一页按钮 | `el-button` | 分页器内部 | |
| `pagination-next` | 下一页按钮 | `el-button` | 分页器内部 | |
| `pagination-pager` | 页码按钮 | `el-button` | 分页器内部 | 动态生成 |

### 5. 弹窗/对话框

#### 5.1 新建/编辑报告弹窗 (`dialog-createEditReport`)

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| `dialog-title` | 弹窗标题 | 文本 | 弹窗头部 | “新建报告” / “编辑报告” |
| `dialog-sampleName` | 样本名称 | `el-input` 或 `el-select` | 弹窗-表单 | |
| `dialog-project` | 项目/合同号 | `el-input` | 弹窗-表单 | |
| `dialog-testItems` | 检测项目 | `el-checkbox-group` / `el-select` | 弹窗-表单 | 多选 |
| `dialog-remark` | 备注 | `el-input` (textarea) | 弹窗-表单 | |
| `dialog-btnSave` | 保存按钮 | `el-button` (`primary`) | 弹窗-底部 | 提交表单 |
| `dialog-btnCancel` | 取消按钮 | `el-button` | 弹窗-底部 | 关闭弹窗 |

#### 5.2 删除确认弹窗 (`dialog-confirmDelete`)

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| `dialog-title` | 弹窗标题 | 文本 | 弹窗头部 | “提示”或“确认删除” |
| `dialog-body` | 提示内容 | 文本 | 弹窗-内容 | “确定要删除报告 [报告编号] 吗？” |
| `dialog-btnConfirm` | 确认按钮 | `el-button` (`primary`) | 弹窗-底部 | |
| `dialog-btnCancel` | 取消按钮 | `el-button` | 弹窗-底部 | |

### 6. 页面状态

| 元素ID | 元素描述 | 出现时机 | 备注 |
| :--- | :--- | :--- | :--- |
| `state-loading` | 加载中骨架屏/loading动画 | 查询数据时 | `v-loading` 指令 |
| `state-empty` | 空数据提示 | 列表无数据时 | `el-empty` 组件，“暂无数据” |
| `state-error-toast` | 请求失败Toast提示 | 网络错误或服务异常 | `this.$message.error()` |
| `state-uploading` | 文件上传进度条 | 附件上传时 | 如果有附件上传功能 |

### 7. 权限点

| 元素ID | 权限点描述 | 可能的表现形式 |
| :--- | :--- | :--- |
| `p-createReport` | 新建报告 | “新建报告”按钮的显示/隐藏或置灰 |
| `p-editReport` | 编辑报告 | “编辑”操作按钮的显示/隐藏或置灰 |
| `p-deleteReport` | 删除报告 | “删除”操作按钮的显示/隐藏或置灰 |
| `p-approveReport` | 审核报告 | “审核”操作按钮的显示/隐藏或置灰 |
| `p-exportData` | 导出数据 | “导出”按钮的显示/隐藏或置灰 |

---

### **Phase 2: PAGE_ELEMENT_POSITION.md 元素定位器设计**

#### 定位策略说明

- **A级 (稳定)**: 优先使用`data-testid`属性（如`data-testid="search-sampleName"`），其次使用唯一的`id`、`name`、`placeholder`。假设开发团队已按规范添加`data-testid`。
- **B级 (较稳定)**: 使用CSS Selector。基于Element Plus的命名约定进行构建，例如`aria-label`、`class`组合。
- **C级 (备选)**: 使用XPath。作为最后手段，用于处理动态ID或复杂嵌套，优先使用相对路径和文本匹配。

#### 元素定位器表

| 元素ID | 定位策略 | 定位值 (示例) | 稳定性评级 | 备用方案 (C级) |
| :--- | :--- | :--- | :--- | :--- |
| `search-reportNo` | A | `[data-testid="search-reportNo"]` | ★★★★★ | `//input[@placeholder="报告编号"]` |
| `search-sampleName` | A | `[data-testid="search-sampleName"]` | ★★★★★ | `//input[@placeholder="样本名称"]` |
| `search-startDate` | B | `input[placeholder="开始日期"]` | ★★★★☆ | `(//div[contains(@class, 'el-date-editor')])[1]//input` |
| `search-endDate` | B | `input[placeholder="结束日期"]` | ★★★★☆ | `(//div[contains(@class, 'el-date-editor')])[2]//input` |
| `search-status` | A | `[data-testid="search-status"]` | ★★★★★ | `//*[@data-testid="search-status"]//input` |
| `search-status-option` | C | `//div[@id='el-popper-container']//div[contains(@class,'el-select-dropdown__item') and .//span[text()='待审核']]` | ★★★☆☆ | 优先用A或B，C级用于下拉选项点击 |
| `search-btnQuery` | A | `[data-testid="search-btnQuery"]` | ★★★★★ | `//button[contains(@class, 'el-button--primary') and .//span[text()='查询']]` |
| `search-btnReset` | A | `[data-testid="search-btnReset"]` | ★★★★★ | `//button[.//span[text()='重置']]` |
| `search-btnCreate` | A | `[data-testid="search-btnCreate"]` | ★★★★★ | `//button[.//span[text()='新建报告']]` |
| `th-reportNo` (表头) | B | `th[data-prop="reportNo"]` | ★★★★☆ | `//div[contains(@class,'el-table__header-wrapper')]//th[.//span[text()='报告编号']]` |
| `cell-view` | B | `button[data-testid^="view-"]` | ★★★★☆ | `(//div[contains(@class,'el-table__body-wrapper')])[1]//tr[1]//button[.//span[text()='查看']]` |
| `cell-edit` | B | `button[data-testid^="edit-"]` | ★★★★☆ | `(//div[contains(@class,'el-table__body-wrapper')])[1]//tr[1]//button[.//span[text()='编辑']]` |
| `dialog-btnSave` | A | `[data-testid="dialog-btnSave"]` | ★★★★★ | `//div[contains(@class, 'el-dialog')]//button[contains(@class,'el-button--primary')]` |
| `pagination` | B | `div.el-pagination` | ★★★★☆ | `//div[contains(@class, 'el-pagination')]` |
| `state-empty` | B | `div.el-empty__description` | ★★★★☆ | `//div[contains(text(), '暂无数据')]` |

---

### **等待策略与注意事项**

1.  **搜索后等待**: 点击“查询”后，应等待表格数据刷新。最佳实践是等待表格的加载状态消失，或等待第一个数据行的某个特定文本出现。
    - `WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-loading-mask")))`
2.  **弹窗等待**: 点击“新建”或“编辑”后，应等待 `el-dialog` 元素的 `displayed` 状态变为 `true`。
    - `WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".el-dialog"))))`
3.  **Select下拉框**: `el-select` 的选项是 Teleport 到 `#app` 或 `body` 的。在点击触发下拉后，需要等待 `el-select-dropdown` 出现在 DOM 中并可见，然后再进行选择。**强烈建议为下拉框选项部分使用C级定位器**。
4.  **时间选择器**: `el-date-picker` 交互复杂。点击输入框 -> 等待日期面板出现 -> 选择年/月 -> 选择日。每一步都需要显式等待。
5.  **Toast消息**: 确认操作后，应等待 `el-message` 组件出现并消失，完成后才能进行下一步操作。
    - `WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".el-message--success")))`