## 无法完成任务：缺少必需输入

两个 RAG 工具均返回 `No available provider`，这意味着当前环境中知识库服务不可用。同时，生成 Pinia store 所必需的 **两个核心输入文档** 均未提供：

| 必需输入 | 状态 |
|---------|------|
| `DATA_FLOW.md` | ❌ 未提供 |
| `API_CONTRACTS.md` | ❌ 未提供 |

### 为什么无法"基于结果继续"

- `DATA_FLOW.md` — 定义 state 结构、数据流向、组件间数据依赖关系。没有它，无法确定 store 中应该有哪些 `ref`/`reactive` 状态。
- `API_CONTRACTS.md` — 定义端点 URL、请求/响应类型、错误模型。没有它，`async actions` 中的 `fetch*` 函数签名和返回类型无法确定。
- RAG 知识库不可用 — 无法从 `business_rules` 或 `ui_patterns` 回退查询任何上下文。

### 建议的下一步

请提供以下任一条件，我可以立即生成代码：

1. **直接提供** `DATA_FLOW.md` 和 `API_CONTRACTS.md` 的内容（粘贴或引用文件路径）。
2. **简要描述** 需要管理的实体（如 `User`、`Product`）、API 端点（如 `GET /api/users`）和页面数据流，我可以据此推断并生成。
3. **修复 RAG provider** 后重新调用，让工具能从知识库自动拉取上下文。

请告诉我你想走哪条路。