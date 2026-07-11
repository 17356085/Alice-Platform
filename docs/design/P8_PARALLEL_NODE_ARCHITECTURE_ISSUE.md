# P8 Parallel 节点实现 — 架构问题说明

> **日期**: 2026-07-11  
> **状态**: 部分完成（有架构限制）

---

## 实现内容

在 `aitest/platform/workflow_executor.py` 中实现了 `execute_parallel_node()` 的基础框架：

- ✅ 使用 Python `ThreadPoolExecutor` 实现并行执行
- ✅ 支持 `max_concurrency` 并发控制
- ✅ 结果聚合（成功/失败统计）
- ⚠️ **架构限制**: 无法访问 workflow graph 来执行子节点

---

## 架构问题

### 问题描述

当前 `NodeExecutor` 设计为**静态方法**，不持有 `workflow` 或 `executor` 引用：

```python
class NodeExecutor:
    @staticmethod
    def execute_agent_node(node, runtime, state): ...
    
    @staticmethod
    def execute_parallel_node(node, runtime, state):
        # ❌ 无法访问 workflow.nodes 来查找子节点
        # ❌ 无法递归调用 executor.execute_node() 来执行子节点
        parallel_nodes = node.metadata.get("parallel_nodes", [])  # 只有 ID 列表
        # 但没有办法根据 ID 找到实际的 WorkflowNode 对象并执行
```

### 根本原因

`WorkflowExecutor` 使用 LangGraph 构建图，每个节点被包装为 lambda 函数：

```python
# workflow_executor.py:269
for node in self.workflow.nodes:
    node_func = self._make_node_func(node)
    builder.add_node(node.node_id, node_func)
```

但 `execute_parallel_node()` 需要**在运行时动态执行其他节点**，这与 LangGraph 的图构建模式冲突。

---

## 两种解决方案

### 方案 1: 重构 NodeExecutor 为实例方法（推荐）

**思路**: 让 `NodeExecutor` 持有 `WorkflowExecutor` 引用，能够查找和执行子节点。

```python
class NodeExecutor:
    def __init__(self, executor: WorkflowExecutor):
        self.executor = executor
    
    def execute_parallel_node(self, node, runtime, state):
        parallel_nodes = node.metadata.get("parallel_nodes", [])
        
        results = {}
        with ThreadPoolExecutor(max_workers=max_concurrency) as pool:
            for sub_node_id in parallel_nodes:
                # ✅ 从 executor.workflow.nodes 查找子节点
                sub_node = self.executor.find_node(sub_node_id)
                
                # ✅ 递归执行子节点
                future = pool.submit(self.executor.execute_single_node, sub_node, runtime, state)
                results[sub_node_id] = future
        
        return self._merge_results(results)
```

**优点**:
- 简单直接
- 符合 OOP 设计
- 能够递归执行任意节点类型

**缺点**:
- 需要重构现有代码（`NodeExecutor` 从静态改为实例）

---

### 方案 2: 使用 LangGraph Send() API（复杂但正确）

**思路**: 在图构建阶段处理 parallel 节点，而非运行时。

```python
class WorkflowExecutor:
    def build_graph(self):
        builder = StateGraph(WorkflowState)
        
        for node in self.workflow.nodes:
            if node.type == "parallel":
                # ✅ 构建 fan-out / fan-in 子图
                self._add_parallel_subgraph(builder, node)
            else:
                builder.add_node(node.node_id, self._make_node_func(node))
    
    def _add_parallel_subgraph(self, builder, parallel_node):
        """为 parallel 节点添加 fan-out + fan-in 子图"""
        # 1. 添加 fan-out 节点
        def fanout(state):
            parallel_nodes = parallel_node.metadata["parallel_nodes"]
            return [Send(sub_id, state) for sub_id in parallel_nodes]
        
        builder.add_conditional_edges(parallel_node.node_id, fanout, parallel_nodes)
        
        # 2. 所有并行分支汇聚到 merge 节点
        merge_node_id = f"{parallel_node.node_id}_merge"
        builder.add_node(merge_node_id, self._make_merge_func(parallel_node))
        
        for sub_id in parallel_nodes:
            builder.add_edge(sub_id, merge_node_id)
```

**优点**:
- 符合 LangGraph 设计哲学
- 真正的并行执行（LangGraph 内部优化）

**缺点**:
- 实现复杂
- 需要改变图构建逻辑
- parallel_nodes 必须是已定义的节点（不能动态创建）

---

## 当前实现的权宜之计

当前代码使用 `ThreadPoolExecutor` 框架，但**无法真正执行子节点**：

```python
def execute_子节点(sub_node_id: str):
    # ❌ 只能返回占位结果
    return sub_node_id, {"success": True, "node_id": sub_node_id}
```

这是一个**半成品**，能够演示并行执行框架，但不能实际运行子节点。

---

## 推荐行动

### 短期（1 天）
- 实现**方案 1**：重构 `NodeExecutor` 为实例方法
- 添加 `WorkflowExecutor.find_node()` 方法
- 添加 `WorkflowExecutor.execute_single_node()` 方法

### 中期（2-3 天）
- 实现**方案 2**：使用 LangGraph Send() API
- 参考 `alice_engine.workflow.parallel` 的完整实现
- 支持动态子图构建

---

## 测试策略

### 单元测试（当前可以写）
- ✅ 测试并发控制（max_concurrency）
- ✅ 测试结果聚合（成功/失败统计）
- ✅ 测试错误处理（部分节点失败）

### 集成测试（需要方案 1 或 2）
- ⏸️ 测试真实子节点执行
- ⏸️ 测试嵌套 parallel 节点
- ⏸️ 测试 parallel + human_gate 组合

---

## 结论

P8 Parallel 节点**框架已实现**，但因架构限制无法真正执行子节点。

**建议**: 优先实现方案 1（重构 NodeExecutor），因为工作量小且符合 OOP 设计。方案 2 可作为未来优化方向。

**当前状态**: 可以通过占位测试验证并行框架，但无法用于生产环境。
