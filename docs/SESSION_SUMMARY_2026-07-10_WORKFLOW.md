# Session Summary — Workflow 执行引擎完成（2026-07-10）

> **会话时间**: 2026-07-10  
> **总体进度**: 50% → **57%**（16/28 任务完成）  
> **核心成果**: ✅ Milestone 4 完成（Workflow Builder v1）

---

## 📊 会话成果

本次会话完成了 **Workflow 执行引擎**的完整实现，实现了从 JSON schema 到 LangGraph 的自动转换和执行。

### ✅ 已完成任务

#### 1. 设计 Workflow 执行架构

**分析现有架构**:
- 研究了 `packages/alice-engine/alice_engine/workflow/sop_graph.py` 的 LangGraph 构建模式
- 分析了 `alice_engine/core/agent_loop.py` 的 AgentLoop 协议
- 研究了 `alice_engine/workflow/nodes.py` 的 `make_agent_loop_node()` 模式

**设计决策**:
1. **WorkflowExecutor**: 主执行器，负责从 JSON 构建 LangGraph
2. **NodeExecutor**: 节点执行器工厂，根据 node.type 分发
3. **WorkflowRuntime**: 运行时状态管理器
4. **RetryHandler**: 统一重试逻辑处理器

#### 2. 实现 Workflow 执行引擎

**核心文件**: `aitest/platform/workflow_executor.py`（427 行）

**实现的组件**:

1. **WorkflowState (TypedDict)**
   - `run_id`: 执行 ID
   - `workflow_id`: 工作流 ID
   - `node_outputs`: 节点输出缓存 {node_id: output}
   - `completed_nodes`: 已完成节点列表
   - `error`: 错误信息
   - `metadata`: 元数据

2. **WorkflowRuntime (Dataclass)**
   - 状态管理：`get_node_output()` / `set_node_output()`
   - 状态转换：`to_state()` → WorkflowState
   - 上下文保存：ExecutionContext + params + runtime_config

3. **RetryHandler**
   - 退避计算：exponential (1s, 2s, 4s, 8s...) / linear (1s, 2s, 3s...)
   - 重试判断：`should_retry()` 检查 max_attempts

4. **NodeExecutor**（4 种节点类型）:

   **a. agent 节点** ✅ 完整实现
   - 复用现有 `ExecutionService.execute()`
   - 外层重试循环（根据 retry_policy）
   - 内层不重试（max_retries=1，避免双重重试）
   - 返回格式：`{success, run_id, status, error_message}`

   **b. human_gate 节点** ⚠️ 基础版
   - 当前实现：直接返回 `default_action`
   - 返回格式：`{success: True, action: "approved", comment: "..."}`
   - TODO: WebSocket 推送到 Studio + 等待用户审核

   **c. condition 节点** ✅ 完整实现
   - 表达式求值：支持访问 `node_outputs`
   - 示例：`node_outputs['requirement']['success'] == True`
   - 安全限制：只允许访问 node_outputs（受限 eval）
   - 返回格式：`{success: True, result: bool}`

   **d. parallel 节点** ⏸️ 占位
   - 当前实现：返回占位结果
   - TODO: 使用 LangGraph Send() API 实现并行

5. **WorkflowExecutor**（图构建 + 执行）:

   **图构建算法**:
   ```python
   def build_graph():
       # 1. 添加所有节点（node_func 包装）
       for node in workflow.nodes:
           builder.add_node(node.node_id, _make_node_func(node))
       
       # 2. 检测入口节点（无入边）
       entry_nodes = _find_entry_nodes()
       builder.set_entry_point(entry_nodes[0])
       
       # 3. 添加边
       for edge in workflow.edges:
           if edge.condition == "always":
               builder.add_edge(from, to)
           else:
               builder.add_conditional_edges(from, _make_route_func(edge))
       
       # 4. 出口节点连接到 END
       exit_nodes = _find_exit_nodes()
       for node_id in exit_nodes:
           builder.add_edge(node_id, END)
       
       return builder
   ```

   **条件路由**:
   - `always`: 直接边
   - `approved`: human_gate 审核通过 → 继续
   - `rejected`: human_gate 审核拒绝 → END
   - 自定义表达式：eval 求值 → 根据结果路由

   **执行流程**:
   ```python
   def execute():
       builder = build_graph()
       compiled = builder.compile()
       initial_state = runtime.to_state()
       final_state = compiled.invoke(initial_state)
       return {
           "success": True,
           "completed_nodes": final_state["completed_nodes"],
           "node_outputs": final_state["node_outputs"],
       }
   ```

#### 3. 集成到 RunExecutor

**文件**: `aitest/server/api/run_executor.py` 更新

**execute_workflow() 完整实现**:
```python
async def execute_workflow(...):
    # 1. 加载 Workflow 定义
    workflow_obj = store.get_workflow(target_id)
    
    # 2. 创建 Run 记录
    run_id = f"run_{uuid.uuid4().hex[:16]}"
    run_store.create_run(run_id, ...)
    
    # 3. 执行 Workflow
    wf_runtime = WorkflowRuntime(run_id, workflow_id, ctx, params, runtime_config)
    executor = WorkflowExecutor(workflow_obj.graph, wf_runtime)
    result = executor.execute()
    
    # 4. 更新 Run 状态
    if result["success"]:
        run_store.update_run_status(run_id, "completed")
    else:
        run_store.update_run_status(run_id, "failed", error_message=result["error"])
    
    # 5. 返回结果
    return {
        "run_id": run_id,
        "status": "completed" / "failed",
        "workflow_result": {
            "completed_nodes": [...],
            "node_outputs": {...},
        },
        "metrics": {"duration_ms": ..., ...}
    }
```

**关键改进**:
- 从占位实现（返回 pending）→ 完整实现（实际执行）
- 集成 WorkflowExecutor
- 返回详细的 workflow_result（completed_nodes + node_outputs）

#### 4. 端到端测试

**文件**: `tests/test_workflow_executor.py`（新增）

**测试场景**:
1. **简单 Workflow**: requirement-agent → test-design-agent
2. **HITL Workflow**: agent → human_gate → agent
3. **条件 Workflow**: agent → condition → agent
4. **重试 Workflow**: 带 retry_policy 的 Agent 节点

**测试工具函数**:
- `create_test_workflows()`: 创建 4 个测试 Workflow 到数据库
- `test_simple_workflow()`: 验证基础执行流程
- `test_hitl_workflow()`: 验证 human_gate 节点（default_action）
- `test_condition_workflow()`: 验证条件分支

#### 5. 设计文档

**文件**: `docs/workflow_executor_design.md`（新增）

**文档内容**:
- 架构概览（4 层组件）
- 核心组件说明（WorkflowExecutor / NodeExecutor / WorkflowRuntime / RetryHandler）
- 状态传递机制（WorkflowState / 节点输出格式）
- 条件路由规则（always / approved / rejected / 自定义表达式）
- Agent 节点执行流程图
- 图构建算法（入口/出口检测）
- 集成到 RunExecutor 的流程
- 未来改进（WebSocket HITL / Parallel 节点 / 断点续传 / Token 聚合）
- 测试计划

---

## 📁 文件变更统计

### 新增文件 (3 个)

```
aitest/platform/workflow_executor.py              # 执行引擎核心（427 行）
docs/workflow_executor_design.md                   # 设计文档
tests/test_workflow_executor.py                    # 端到端测试
```

### 修改文件 (2 个)

```
aitest/server/api/run_executor.py                  # execute_workflow() 完整实现
docs/MASTER_ROADMAP.md                              # 进度更新（54% → 57%）
```

---

## 🏗️ 架构亮点

### 1. 声明式工作流定义

**从 Python 代码**:
```python
# sop_graph.py (硬编码)
builder.add_node("requirement", make_agent_loop_node("requirement-agent"))
builder.add_node("design", make_agent_loop_node("test-design-agent"))
builder.add_edge("requirement", "design")
```

**到 JSON Schema**:
```json
{
  "nodes": [
    {"node_id": "requirement", "type": "agent", "agent_id": "requirement-agent"},
    {"node_id": "design", "type": "agent", "agent_id": "test-design-agent"}
  ],
  "edges": [
    {"from": "requirement", "to": "design", "condition": "always"}
  ]
}
```

**优势**:
- 可序列化：存储到数据库
- 可版本化：支持多版本管理
- 可验证：静态校验（P8-3）
- 可视化：未来可生成 Workflow 编辑器 UI

### 2. 自动图构建

**智能检测**:
- 入口节点：`all_nodes - nodes_with_incoming_edges`
- 出口节点：`all_nodes - nodes_with_outgoing_edges`
- 自动连接到 END

**条件路由分发**:
```python
if edge.condition == "always":
    builder.add_edge(from, to)
else:
    builder.add_conditional_edges(from, route_func, {to: to, END: END})
```

### 3. 统一重试机制

**外层重试**（WorkflowExecutor）:
```python
policy = node.retry_policy or RetryPolicy(max_attempts=1)
for attempt in range(1, policy.max_attempts + 1):
    try:
        result = execute_service.execute(...)
        return result
    except Exception as e:
        if attempt < policy.max_attempts:
            backoff = calculate_backoff(attempt, policy)
            time.sleep(backoff)
```

**内层不重试**（ExecutionService）:
```python
svc.execute(..., max_retries=1)  # 避免双重重试
```

### 4. 节点间状态传递

**WorkflowState 作为图状态**:
- 每个节点更新 `node_outputs[node_id]`
- 下游节点通过 `state["node_outputs"]["upstream_id"]` 访问
- 条件节点可访问任意上游输出

**示例**:
```python
# condition 节点表达式
"node_outputs['requirement']['success'] == True"

# 路由函数求值
allowed_globals = {
    "__builtins__": {},
    "node_outputs": state.get("node_outputs", {}),
}
result = eval(edge.condition, allowed_globals, {})
```

---

## 🎯 关键成就

1. **Milestone 4 完成**: Workflow Builder v1 所有核心功能就绪
2. **P8-1 完整实现**: 从 JSON schema 到 LangGraph 的完整执行引擎
3. **P8-2 基础版完成**: human_gate 节点可用（WebSocket 推送待后续实现）
4. **总进度突破 57%**: 16/28 任务完成

---

## ⚠️ 技术债务

### 1. Human Gate WebSocket 推送（P8-2 待完善）

**当前**: 返回 `default_action`  
**目标**: WebSocket 推送到 Studio + 用户审核

**实现思路**:
```python
async def execute_human_gate_node(node, runtime, state):
    # 1. 推送到 WebSocket
    await websocket.send_json({
        "type": "human_gate",
        "run_id": runtime.run_id,
        "node_id": node.node_id,
        "prompt": node.prompt,
    })
    
    # 2. 等待响应（带超时）
    response = await asyncio.wait_for(
        websocket.receive_json(),
        timeout=node.timeout_seconds
    )
    
    # 3. 超时则返回 default_action
    return response or {"action": node.default_action}
```

### 2. Parallel 节点并行执行

**当前**: 串行执行占位  
**目标**: 使用 LangGraph Send() API

**参考**: `aitest/graphs/parallel_sop.py`

```python
from langgraph.constants import Send

def execute_parallel_node(node, runtime, state):
    parallel_nodes = node.metadata.get("parallel_nodes", [])
    return [Send(node_id, state) for node_id in parallel_nodes]
```

### 3. Token/Cost 聚合

**当前**: metrics 返回 0  
**目标**: 聚合所有 Agent 节点的 token 使用和成本

```python
def aggregate_metrics(node_outputs):
    total_tokens = sum(
        output.get("tokens_used", 0)
        for output in node_outputs.values()
        if output.get("success")
    )
    return {"tokens_used": total_tokens, ...}
```

### 4. Workflow 断点续传

**当前**: 每次全新执行  
**目标**: 支持从中断点恢复

**实现思路**:
- WorkflowRuntime 持久化到数据库
- LangGraph checkpointer 保存中间状态
- 恢复时跳过已完成节点

---

## 🔄 待实现功能（占位）

| 功能 | 状态 | 优先级 |
|------|------|--------|
| **Skill 独立执行** | 占位 | P2 |
| **Evaluation 执行引擎** | 占位 | P2 |
| **WebSocket HITL** | 基础版 | P3 |
| **Parallel 并行执行** | 占位 | P3 |
| **Workflow 断点续传** | 未实现 | P4 |

---

## 📊 里程碑进度

| 里程碑 | 状态 | 完成度 |
|--------|------|--------|
| Milestone 1: 解除阻塞 | ✅ | 100% |
| Milestone 2: Run 资源可用 | ✅ | 100% (Phase 1-5) |
| Milestone 3: 质量闭环打通 | ✅ | 100% |
| **Milestone 4: Workflow Builder v1** | **✅** | **100%** (P8-1 ✅ P8-3 ✅ P8-2 基础版 ✅) |
| Milestone 5: 生产就绪 | ⏸️ | 0% |

---

## 🎯 下次会话建议

### 选项 1: 完成 P7-1（API 路由资源化）
- 13 个 router 迁移到 `/api/v1/`
- 前端 API 调用更新
- 保持向后兼容

### 选项 2: 开始阶段 5（外部依赖资源化）
- P6-1: ModelProvider 资源化
- P6-5: Secret Manager
- P6-2: MCPServer 资源化

### 选项 3: 前端 IA 重组（P2-6）
- 19 个 Views → 5-resource 模型
- 全局导航 vs Project 内导航分离

### 选项 4: 完善 Workflow 功能
- WebSocket HITL 完整实现
- Parallel 节点并行执行
- Token/Cost 聚合

---

## 🚀 启动命令

```bash
# 查看当前进度
cat docs/MASTER_ROADMAP.md

# 选项 1: API 路由资源化
请完成 P7-1：13 个 router 迁移到 /api/v1/

# 选项 2: 外部依赖资源化
请开始阶段 5：实现 P6-1 ModelProvider 资源化

# 选项 3: 前端 IA 重组
请开始 P2-6：19 个 Views 合并为 5-resource 模型

# 选项 4: 完善 Workflow 功能
请实现 WebSocket HITL：human_gate 节点推送到 Studio
```

---

## 总结

本次会话高效完成了 **Workflow 执行引擎**的完整实现，从 JSON schema 到 LangGraph 的自动转换和执行。核心成就：

1. **架构清晰**: WorkflowExecutor / NodeExecutor / WorkflowRuntime / RetryHandler 四层架构
2. **功能完整**: 支持 agent / human_gate / condition 节点（parallel 占位）
3. **代码质量**: 427 行核心代码 + 完整设计文档 + 端到端测试
4. **向后兼容**: 不影响现有 sop_graph.py 的执行逻辑

**Milestone 4 已完成**，总进度达到 **57%**（16/28 任务），为后续工作奠定了坚实基础。
