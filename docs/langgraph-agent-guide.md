# 如何用 LangGraph 搭建一个 Agent 系统

> 结合 aitest 项目已学的概念，解释 Agent 的实现原理。不含代码 demo，纯文档。

---

## 一、什么是 LangGraph Agent

LangGraph Agent 的本质是 **ReAct 循环**（Reasoning + Acting）：

1. **Think（思考）**：LLM 读取当前状态（对话历史 + 工具结果），判断下一步——是直接回答用户，还是调用某个工具
2. **Router（路由）**：根据 LLM 的决策，走两个分支
   - LLM 决定直接回答 → 结束
   - LLM 决定调用工具 → 进入执行
3. **Act（执行）**：执行工具，把结果写回状态
4. **回到 Think**：带着工具结果再走一轮思考和判断

这个循环会一直持续，直到 LLM 认为可以给出最终答案。

### 和项目里 SOP 流水线的关系

| | 项目 SOP 流水线 | Agent 模式 |
|---|---|---|
| **节点类型** | 固定：project_agent → requirement_agent → ... → knowledge_agent | 动态：LLM 自己决定要不要调工具、调哪个 |
| **路由策略** | route_next_phase 按阶段顺序推进 | Router 判断消息里有没有 tool_call |
| **循环** | 只在 quality gate 重试时发生 | 核心就是循环：think → act → think → ... |
| **State** | SOPState（20+ 字段，含 phase 状态机） | 最小只需 messages 列表 |

---

## 二、五步搭建法

### Step 1：定义 State

只需要一个核心字段：**对话历史**。

```
AgentState 包含:
  - messages:  Annotated[List, operator.add]  ← 对话历史，Reducer 自动累积
  - 可选: next_step（Router 用的决策字段）
```

**为什么用 `operator.add` 做 Reducer？** —— 每个节点都可能往 messages 里追加消息（HumanMessage、AIMessage、ToolMessage），`operator.add` 保证新消息追加到列表末尾，不会覆盖旧消息。

**为什么不需要项目里那么多字段？** —— Agent 模式不需要 phase 状态机、不需要质量门禁。LLM 自己管理"下一步做什么"的决策，State 只需要够 LLM 做决策的信息：对话历史。

### Step 2：实现 LLM Node（think）

这是 Agent 的大脑。职责：

**输入** → messages 列表（全部对话历史）

**处理** → 调用 LLM，告诉它可用工具列表，让它自主决定是回答还是调工具

**输出** → AIMessage（可能带 `tool_calls` 也可能纯文本回答）

核心逻辑：**把 messages + 工具定义一起传给 LLM，让 LLM 在回复里标出要不要调工具**

LLM 的回复有两种可能：
```
情况 A（直接回答）:
  AIMessage: { content: "答案是 42", tool_calls: [] }

情况 B（要调工具）:
  AIMessage: { content: null, tool_calls: [{ name: "calculator", args: { expr: "21*2" } }] }
```

### Step 3：实现 Tool Node（act）

负责执行 LLM 请求的工具调用。

**输入** → messages 列表（最后一条是含 `tool_calls` 的 AIMessage）

**处理** → 解析 `tool_calls`，逐个执行对应的工具函数

**输出** → ToolMessage（工具执行结果），追加回 messages

```
AIMessage(tool_calls=[{name:"calculator", args:{expr:"21*2"}}])
                              ↓ Tool Node 执行
ToolMessage(tool_call_id=..., content: "42")
                              ↓ 追加回 messages
messages = [..., AIMessage(带tool_calls), ToolMessage("42")]
```

### Step 4：实现 Router

这是 Agent 最关键的逻辑——**add_conditional_edges 判断 LLM 的意图**。

路由函数读取 messages 最后一条：

```
如果最后一条 AIMessage 有 tool_calls → 返回 "tool_node"（去执行工具）
如果最后一条 AIMessage 没有 tool_calls → 返回 "end"（结束）
```

这就是整个 Agent 的决策核心：**一条 if/else**。

### Step 5：编译图并连接

```
StateGraph(AgentState)
  ├── add_node("llm", llm_node)         ← Step 2 的 LLM 节点
  ├── add_node("tool", tool_node)       ← Step 3 的工具节点
  ├── set_entry_point("llm")            ← 从 LLM 开始
  ├── add_conditional_edges("llm", router, route_map)  ← Step 4 的路由
  │     route_map = {"tool_node": "tool_node", "end": END}
  └── add_edge("tool", "llm")           ← 工具执行完回到 LLM（循环！）
```

**关键连线**：`add_edge("tool", "llm")` 制造了循环——工具结果作为新消息回到 LLM，LLM 再判断是否需要继续调工具。

### 执行流程完整走一遍

以用户问"21 * 2 等于多少？"为例：

```
初始 State: messages = [HumanMessage("21 * 2 等于多少?")]

第1轮 LLM Node:
  LLM 读 messages → 判断需要调 calculator → 返回 AIMessage(tool_calls=[calculator("21*2")])
  State: messages = [HumanMessage, AIMessage(with tool_calls)]

Router 判断: 有 tool_calls → 去 tool_node

Tool Node:
  执行 calculator("21*2") → 返回 42
  State: messages = [HumanMessage, AIMessage, ToolMessage("42")]

回到 LLM Node (add_edge(tool→llm)):

第2轮 LLM Node:
  LLM 读 messages（看到了工具结果"42"）→ 判断可以回答了
  → 返回 AIMessage("21乘以2等于42")
  State: messages = [...ToolMessage("42"), AIMessage("21乘以2等于42")]

Router 判断: 没有 tool_calls → END
```

---

## 三、和项目已知概念的对应

结合之前六课学的内容，Agent 模式就是前四课知识的一个特定组合：

| 概念 | 在 Agent 里的用法 | 对应项目代码 |
|------|------------------|------------|
| **State** | messages 列表，用 `operator.add` 累积 | `state.py` 的 `Annotated[List, operator.add]` |
| **Node** | `llm_node`、`tool_node` 两个函数 | `execution_graph.py` 的 `report_entry`、`report_act` |
| **普通边** | `add_edge("tool", "llm")` 制造循环 | `execution_graph.py` 的 `add_edge("act", "exit")` |
| **条件边** | `add_conditional_edges("llm", router, route_map)` 判断分支 | `sop_graph.py` 的 `add_conditional_edges("preflight", route_next_phase, route_map)` |
| **Router** | 检查 messages 最后一条有无 tool_calls | `sop_graph.py` 的 `route_next_phase` |
| **compile** | 编译成可执行图 | 所有 graph 文件的 `.compile()` |

**不需要的概念**：Reducer 自定义函数（用内置 `operator.add` 就够了）、子图嵌套、interrupt/Command、Send 并行——这些都是 Agent 更进一步后才需要的。

---

## 四、和项目 SOP 流水线的本质区别

| 特征 | 项目 SOP 流水线 | Agent（ReAct） |
|------|----------------|---------------|
| 流程 | **固定**：8 个阶段按序执行 | **动态**：LLM 自己决定下一步 |
| 决策者 | Developer（写死的 route_next_phase） | LLM（根据对话历史动态判断） |
| 循环 | 只有 quality gate 重试时出现 | 核心就是循环 |
| 节点数 | 20+ 个节点（含子图） | 最少 2 个节点（llm + tool） |
| 适用场景 | 预定义流程：测试→修复→报告 | 开放式任务：问答、数据分析、工具调度 |
