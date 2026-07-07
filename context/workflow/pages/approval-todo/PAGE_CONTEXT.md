好的，我已经收到您提供的 `approval-todo` 页面测试用例。基于此上下文，我将进行页面结构分析并设计页面级测试方案。

---

## TEST_DESIGN.md: 审批待办页面测试设计

### 1. 页面结构与可测试元素分析

根据提供的测试用例上下文，`approval-todo` 页面是一个典型的数据列表与管理页面。其核心DOM结构可划分为以下几个区域：

| 区域 | 主要功能 | 关键可测试元素 (基于上下文推断) | 测试关注点 |
| :--- | :--- | :--- | :--- |
| **筛选器区域** | 数据查询与重置 | - 流程类型下拉框：`[data-testid=“filter-processType“]` <br>- 状态下拉框：`[data-testid=“filter-status“]` <br>- 关键词输入框：`[data-testid=“filter-keyword“]` (推断) <br>- 日期选择器：`[data-testid=“filter-startDate“]`, `[data-testid=“filter-endDate“]` <br>- 操作按钮：查询按钮、重置按钮 (需明确`data-testid`) | 值的选择、输入、清空、重置；查询/重置后的数据联动 |
| **表格操作区域** | 数据展示与选择 | - 全选复选框：`[data-testid=“checkbox-selectAll“]` <br>- 行复选框： (需明确选择器，如 `.ant-table-row input[type=“checkbox“]`) <br>- 操作列按钮：`同意`、`拒绝`、`详情` (需明确每行操作按钮的选择器) | 全选/半选/不选状态切换；单条记录操作（同意、拒绝、跳转详情） |
| **批量操作区域** | 对选中数据批量处理 | - `批量同意`按钮：`[data-testid=“btn-batch-approve“]` <br>- `批量拒绝`按钮：`[data-testid=“btn-batch-reject“]` <br>- `批量转办`按钮：`[data-testid=“btn-batch-transfer“]` | 按钮启用/禁用状态随选择变化；批量操作流程（确认弹窗、Loading、成功提示） |
| **分页区域** | 数据翻页与导航 | - `上一页`按钮：`.ant-pagination-prev` <br>- `下一页`按钮：`.ant-pagination-next` <br>- 页码指示器：`.ant-pagination-item` <br>- 总条数文本：`.ant-pagination-total-text` | 翻页前后数据变化；首页/末页按钮状态；总条数准确性 |
| **状态反馈区域** | 临时反馈 | - `Loading`状态：`.ant-spin-spinning` <br>- 成功提示：`.ant-message-success` <br>- 空状态：`.ant-empty` 或 `[data-testid=“empty-state“]` | 异步操作期间的反馈；操作结果提示；无数据时的友好展示 |

### 2. 测试数据设计

为确保测试可重复且可靠，需准备或模拟以下测试数据集：

1.  **核心数据集 (基础)**：包含至少10-15条待办记录，覆盖不同的 `流程类型`（如：`请假申请`，`报销审批`）、`状态`（如：`待我审批`，`已同意`，`已拒绝`）、`创建日期`（跨月份）。
2.  **分页数据集**：确保总条数超过单页显示条数（如：总数为15条，每页10条），以满足 `AT-PAGE-01` 等分页测试。
3.  **特定操作数据集**：为批量操作（`AT-BATCH-*`）和单条操作（`AT-SIGN-*`）用例，需确保有**状态为`待我审批`** 的记录。可考虑创建独立数据集或在测试前通过接口/数据库预置。

**数据管理策略**：
- **测试前初始化**：对于 `AT-FLT-02`，`AT-FLT-03` 等依赖特定数据状态的用例，建议在用例执行前通过API直接创建或设置数据，确保测试环境确定性。
- **测试后清理**：在执行了数据变更的用例（如同意、拒绝操作）后，需要有机制恢复数据原始状态，避免用例间干扰。可通过重置测试数据库或使用专门的“测试后重置”API实现。

### 3. 核心验证点设计

基于测试用例，提炼出以下核心、可自动化的验证点：

| 验证维度 | 验证点描述 | 推荐的实现思路/断言 |
| :--- | :--- | :--- |
| **元素状态** | 按钮的启用/禁用状态 (`disabled`) | `expect(button).toHaveAttribute(‘disabled‘)` 或 `expect(button).toBeDisabled()` |
| **元素状态** | 表头复选框的 `indeterminate` (半选) 属性 | `page.evaluate(() => element.indeterminate)` |
| **元素值** | 下拉框、输入框、日期选择器的当前值 | `expect(input).toHaveValue(‘xxx‘)` <br> `expect(select).toHaveText(‘xxx‘)` |
| **数据内容** | 表格特定行/列的数据 | `expect(page.locator(‘.ant-table-row‘).nth(n).locator(‘td‘).nth(m)).toHaveText(‘预期内容‘)` |
| **数据量** | 分页器显示的总条数 | `expect(page.locator(‘.ant-pagination-total-text‘)).toContainText(‘共 15 条‘)` |
| **UI反馈** | `Loading`状态的出现与消失 | `await expect(page.locator(‘.ant-spin-spinning‘)).toBeVisible()` <br> `await expect(page.locator(‘.ant-spin-spinning‘)).toBeHidden()` |
| **UI反馈** | 成功/错误消息的显示 | `await expect(page.locator(‘.ant-message-success‘)).toBeVisible()` |
| **UI反馈** | 空状态插图的显示 | `await expect(page.locator(‘.ant-empty‘)).toBeVisible()` |
| **数据变更** | 操作后，特定记录从列表中消失或状态更新 | 操作前后，对表格内容进行两次断言，对比差异 |
| **URL变更** | 点击“详情”后跳转，并携带正确参数 | `await expect(page).toHaveURL(/detail\/?id=123/)` |

### 4. 测试策略与风险考量

1.  **测试稳定性**：
    - **定位器优先级**：优先使用 `data-testid`，其次考虑稳定且唯一的CSS选择器（如 `.ant-table-tbody .ant-table-row:nth-child(1) td:nth-child(2)`），避免依赖动态生成或无意义的类名。
    - **异步等待**：所有涉及数据刷新的操作（查询、翻页、批量操作）后，必须等待表格`Loading`状态消失或特定请求响应完成，再进行下一步断言。
    - **操作前状态确认**：在执行批量操作或单条操作前，显式断言目标按钮可点击，避免因前置条件失败导致后续步骤无效。

2.  **数据隔离与冲突**：
    - 并发执行多条测试用例时，需确保它们操作的数据互不干扰。建议通过为测试用例分配不同的数据ID范围或使用独立的测试用户/工作区来实现数据隔离。

3.  **环境依赖**：
    - 页面功能可能依赖后端API。测试方案中应考虑Mock API响应（例如，使用MSW或Playwright的`route`）来模拟网络延迟、错误或特定数据，使前端测试在后端不稳定时也能运行。

4.  **未覆盖的潜在风险场景**：
    - **极端输入**：关键词输入超长字符串、特殊字符、SQL注入尝试等。
    - **快速连续操作**：在批量操作的`Loading`期间，再次点击按钮，应无响应或防止重复提交。
    - **网络异常**：在操作过程中模拟网络中断，验证错误提示和页面恢复能力。
    - **权限校验**：验证无权限的用户无法看到操作按钮或执行操作后收到权限错误提示。

**总结**：本测试设计基于提供的用例，对`approval-todo`页面进行了结构化分析，明确了可测试元素、测试数据管理策略和核心验证点。此方案为后续编写具体测试脚本提供了清晰的指导，同时指出了为提升测试健壮性所需关注的稳定性、数据隔离及边界风险场景。