# Execution Kernel Contract

> 状态：Phase 7.1 Frozen Boundary
> 适用范围：`packages/alice-engine`、`aitest/platform`

## 1. 目的

在切换 SDK 与 Platform 的真实执行路径之前，先固定一个公开、稳定、可测试的执行内核边界。

这一步只定义契约，不要求立刻替换 `Engine.run()` 或 `ExecutionService` 的现有实现。

## 2. 公开类型

`alice_engine.kernel` 公开以下最小契约：

- `KernelExecutionRequest`
  - Kernel 的最小输入模型
  - 持有共享 `ExecutionContext`
  - 允许附带 `kind / project_path / run_id / checkpoint_thread_id / metadata`
- `ExecutionKernel`
  - `execute(request) -> ExecutionResult`
  - `execute_async(request) -> ExecutionResult`
- `ExecutionResult`
  - 继续作为唯一官方结果模型

## 3. 职责边界

### 3.1 Standalone Facade (`alice_engine.Engine`)

负责：

- `Project` 解析
- 本地默认 ports / stores / event bus 装配
- 将 SDK 用户输入映射为 `KernelExecutionRequest`
- 把统一结果投影为 SDK `RunResult`

不负责：

- 自己维护另一套执行主链
- 长期继续依赖 `_internal.graph` 作为公开行为根基

### 3.2 Platform Facade (`aitest.platform.ExecutionService`)

负责：

- Scope / Workspace / Org 校验
- `ExecutionRequest` / `Run` 生命周期
- 幂等、队列、审计、计费、Webhook、平台事件
- 将平台输入映射为同一个 `KernelExecutionRequest`

不负责：

- 重新实现执行语义
- 把平台控制面语义塞进 SDK Kernel

### 3.3 Execution Kernel

负责：

- 统一执行语义
- 选择并推进 Agent / SOP 执行
- 产出统一 `ExecutionResult`

不负责：

- 平台租户模型
- 平台数据库、HTTP、SSE、CLI 投影
- 平台审计、计费和运营指标语义

## 4. 后续顺序

- `PH7-PR-7.2`
  - 让 standalone SDK `Engine` 调用公开 Kernel
- `PH7-PR-7.3`
  - 让 Platform `ExecutionService` 调用同一 Kernel
- `PH7-PR-7.4`
  - 逐步把动态 `platform_bridge` 替换为显式 Port 注入
