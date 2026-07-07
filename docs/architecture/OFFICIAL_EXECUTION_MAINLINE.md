# 官方执行主链路

> 状态：Frozen for Phase 1
> 生效日期：2026-07-06
> 适用范围：`CLI`、`Server Execution API`、`Chat`、`SDK`

## 1. 目的

本文档用于正式固化平台的官方执行主链路，作为 Phase 1 的架构冻结基线。

从本文件生效开始：

- 所有新功能都必须优先接入这条主链路
- 所有兼容路径都只能维持，不允许继续扩展职责
- 所有后续 Runtime / Graph / Memory / Replay / MCP / Capability 改造，都以本链路为准

## 2. 官方执行主链路

```text
User Entry
  ↓
Entry Adapter
  ↓
Platform ExecutionService
  ↓
EngineFactory / Engine Registry
  ↓
Unified Runtime Executor
  ↓
Workflow / Graph
  ↓
Capability + Context Assembly
  ↓
Provider / Tool / MCP / Knowledge / Memory
  ↓
Event / Audit / Replay Hooks
  ↓
Execution Result
  ↓
Protocol Adapter Response
```

## 3. 各层职责

### 3.1 User Entry

包括：

- `aitest/cli`
- `aitest/server/api/execution.py`
- `aitest/server/api/chat.py`
- `packages/alice-engine` 对外 SDK 入口

职责：

- 接收用户输入
- 做协议层参数解析
- 不承载执行状态机
- 不直接拼装执行结果语义

### 3.2 Entry Adapter

职责：

- 把 CLI / HTTP / SSE / SDK 输入映射到统一执行请求
- 构建统一 execution context
- 调用 `ExecutionService`

要求：

- 只做适配，不做执行编排
- 不允许新增独立入口逻辑分支

### 3.3 Platform ExecutionService

职责：

- 作为平台级官方执行入口
- 接收统一 context
- 完成生命周期编排
- 触发审计、事件、状态保存
- 选择引擎，不直接承载 graph 业务细节

要求：

- 所有正式执行都应收口到这里
- 不允许上层绕过它直接控制执行器内部细节

### 3.4 EngineFactory / Engine Registry

职责：

- 根据 execution type / graph type / agent mode 返回执行内核
- 隔离入口层与具体执行器的耦合

要求：

- 只做注册与选择
- 不继续增加业务特判

### 3.5 Unified Runtime Executor

职责：

- 承担统一执行语义
- 持有 execution context
- 推进执行状态机
- 对外暴露正式控制接口，例如 `cancel / abort / stop`

要求：

- 不再散落多个“半执行器”
- 不允许上层直接访问私有属性

### 3.6 Workflow / Graph

职责：

- 负责流程编排
- 描述 phase / node / edge / transition
- 不承载入口适配、权限判定、存储细节

要求：

- Graph 只负责编排
- Runtime 负责状态推进

### 3.7 Capability + Context Assembly

职责：

- 构建模型上下文
- 选择 capability
- 组装 memory / knowledge / governance inputs

要求：

- 必须挂在官方主链路上
- 不再以旁路 helper 方式存在

### 3.8 Provider / Tool / MCP / Knowledge / Memory

职责：

- 提供模型调用、工具调用、外部能力、知识检索、记忆检索

要求：

- 全部作为执行依赖层接入
- 不直接主导执行生命周期

### 3.9 Event / Audit / Replay Hooks

职责：

- 记录执行生命周期
- 产生审计与回放数据
- 输出指标和观测事件

要求：

- 事件记录属于主链路正式步骤
- 不允许 silently fail

### 3.10 Execution Result

职责：

- 统一表达成功、失败、取消、中断
- 返回统一 output、error、metadata、event summary

要求：

- 这是唯一官方结果模型
- SSE、CLI、SDK 都应映射自这里

### 3.11 Protocol Adapter Response

职责：

- 把统一结果适配成 HTTP、SSE、CLI、SDK 需要的输出形式

要求：

- 适配层不能重新发明一套结果模型

## 4. 当前认定的官方入口与兼容入口

### 4.1 官方入口

- `CLI -> ExecutionService -> EngineFactory -> Runtime Executor`
- `Server Execution API -> ExecutionService -> EngineFactory -> Runtime Executor`
- `Chat -> Entry Adapter -> ExecutionService -> EngineFactory -> Runtime Executor`
- `SDK -> Public Engine Adapter -> ExecutionService-compatible runtime contract`

### 4.2 兼容入口

以下路径在当前代码库中仍可能存在，但从现在开始只允许收敛，不允许继续扩展：

- 直接实例化 `AgentLoop` 的调用点
- 直接实例化 `SOPRunner` 的调用点
- Chat 内部绕过统一结果模型的流式特判
- SDK 内部 fallback 到非正式串行 graph 的路径

## 5. 明确禁止的做法

- 在 `server/api` 直接编排执行状态机
- 在 `chat` 入口独立维护另一套执行结果语义
- 在入口层直接访问执行器私有属性
- 在 graph 中继续叠加执行控制、副作用存储、入口判断
- 新增 bypass `ExecutionService` 的正式能力接线

## 6. Phase 1 验收要求

Phase 1 完成时，必须达到以下状态：

- CLI、Server、Chat 三条主入口共享统一 execution context
- CLI、Server、Chat 三条主入口共享统一 execution result
- Runtime / Graph / Engine 职责边界与本文档一致
- 兼容路径被标记并纳入收敛计划
- 后续 Capability、Memory、Replay、MCP 接线均不需要再定义第二条执行主链路

## 7. 后续引用要求

后续所有涉及以下主题的设计和 PR，必须引用本文件：

- Runtime 改造
- Graph 改造
- ExecutionService 改造
- Chat 执行链改造
- Replay / Audit 主链路接线
- Capability / Tool / Memory / MCP 接线
