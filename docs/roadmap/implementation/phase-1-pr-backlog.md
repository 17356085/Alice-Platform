# Phase 1 PR Backlog

Phase 1 目标：统一执行内核，收敛 Execution Context / Result / Status，压实 Engine / Runtime / Graph 边界，为后续 Capability / Memory / Replay / MCP 接线提供稳定主链路。

说明：

- 本阶段已按“连续实现 + 保留原 PR 主题边界”的方式完成主链路收敛。
- 实际提交时仍建议按原任务卡拆分提交历史；本次工作是一次性把 Phase 1 所需代码与文档全部补齐。

## PH1-PR-1.1
- Status: Done
- Tracking ID: PH1-PR-1.1
- Owner: TL
- ETA: 1 day
- 标题：冻结官方执行主链路文档
- 目标：明确唯一主链路与入口职责
- 模块：`docs/architecture` `docs/audit`
- 风险：低
- 依赖：无
- 完成标准：
  - 文档明确 CLI / Server / Chat / SDK 各自角色
  - 标记兼容层与待废弃路径
  - 团队对 Phase 1 统一方向达成共识
  - 已完成：主链路文档已固化，并挂接到 Architecture Overview 与 Freeze 文档

## PH1-PR-1.2
- Status: Done
- Tracking ID: PH1-PR-1.2
- Owner: Runtime Owner
- ETA: 1 day
- 标题：引入 Execution Context / Result 契约占位
- 目标：建立统一契约入口，不改核心行为
- 模块：`packages/alice-engine` `aitest/platform` `aitest/server/api`
- 风险：低
- 依赖：PH1-PR-1.1
- 完成标准：
  - 存在最小统一 context / result 定义
  - 主路径行为不变
  - 不引入新状态来源

## PH1-PR-2.1
- Status: Done
- Tracking ID: PH1-PR-2.1
- Owner: Runtime Owner
- ETA: 2 days
- 标题：定义统一 Execution Context 模型
- 目标：收敛输入与运行态上下文
- 模块：`packages/alice-engine/alice_engine/core` `packages/alice-engine/alice_engine/workflow`
- 风险：中
- 依赖：PH1-PR-1.2
- 完成标准：
  - 字段清单明确
  - context 分层清晰
  - 不再新增匿名 dict contract

## PH1-PR-2.2
- Status: Done
- Tracking ID: PH1-PR-2.2
- Owner: Platform Owner
- ETA: 1 day
- 标题：Server / CLI 接入统一 Context
- 目标：外层入口统一构造 context
- 模块：`aitest/server/api/execution.py` `aitest/platform/execution_service.py` `aitest/cli`
- 风险：中
- 依赖：PH1-PR-2.1
- 完成标准：
  - Server / CLI 走同一 context 构建流程
  - 参数映射规则清晰
  - 主路径可运行

## PH1-PR-2.3
- Status: Done
- Tracking ID: PH1-PR-2.3
- Owner: Runtime Owner
- ETA: 2 days
- 标题：执行器改为消费统一 Context
- 目标：执行内核关键节点改为从 context 取值
- 模块：`packages/alice-engine/alice_engine/core/executor.py` `packages/alice-engine/alice_engine/workflow`
- 风险：中
- 依赖：PH1-PR-2.1
- 完成标准：
  - 核心执行路径消费统一 context
  - 不再依赖多个并行输入源
  - 回归通过

## PH1-PR-3.1
- Status: Done
- Tracking ID: PH1-PR-3.1
- Owner: Runtime Owner
- ETA: 2 days
- 标题：定义统一 Execution Result 模型
- 目标：统一输出结构与错误模型
- 模块：`packages/alice-engine` `aitest/platform`
- 风险：中
- 依赖：PH1-PR-2.3
- 完成标准：
  - result 结构明确
  - 成功/失败/取消/中断语义统一
  - 为审计与回放留扩展位

## PH1-PR-3.2
- Status: Done
- Tracking ID: PH1-PR-3.2
- Owner: Platform Owner
- ETA: 1 day
- 标题：统一 Server / SSE / CLI 输出适配
- 目标：外部消费统一结果结构
- 模块：`aitest/server/api` `aitest/cli` `aitest/web/src/api`
- 风险：中
- 依赖：PH1-PR-3.1
- 完成标准：
  - SSE 与最终结果结构一致
  - CLI 不再自拼结果
  - 旧字段有兼容策略

## PH1-PR-3.3
- Status: Done
- Tracking ID: PH1-PR-3.3
- Owner: Runtime Owner
- ETA: 1 day
- 标题：统一状态映射与生命周期枚举
- 目标：收敛状态语义
- 模块：`packages/alice-engine` `aitest/platform`
- 风险：中
- 依赖：PH1-PR-3.1
- 完成标准：
  - 同义状态合并
  - 状态迁移路径明确
  - 生命周期测试可追踪

## PH1-PR-4.1
- Status: Done
- Tracking ID: PH1-PR-4.1
- Owner: Runtime Owner
- ETA: 1 day
- 标题：公开中止与控制接口
- 目标：替代对私有属性的跨层访问
- 模块：`packages/alice-engine/alice_engine/core/executor.py` `aitest/platform/execution_service.py`
- 风险：中
- 依赖：PH1-PR-2.3
- 完成标准：
  - 提供正式 cancel / abort / stop 接口
  - 不再直接读写私有属性
  - 运行中止场景可验证

## PH1-PR-4.2
- Status: Done
- Tracking ID: PH1-PR-4.2
- Owner: Platform Owner
- ETA: 2 days
- 标题：清理危险跨层访问点
- 目标：移除最危险的隐藏依赖
- 模块：`aitest/platform` `packages/alice-engine`
- 风险：中
- 依赖：PH1-PR-4.1
- 完成标准：
  - 已识别关键跨层访问被移除或封装
  - 主路径不回归
  - 有针对性回归测试

## PH1-PR-5.1
- Status: Done
- Tracking ID: PH1-PR-5.1
- Owner: Graph Owner
- ETA: 2 days
- 标题：Graph 只保留编排职责
- 目标：从 Graph 中移除执行控制副作用
- 模块：`aitest/graphs` `aitest/graphs_dev` `packages/alice-engine/alice_engine/workflow`
- 风险：高
- 依赖：PH1-PR-3.3 PH1-PR-4.2
- 完成标准：
  - Graph 聚焦编排
  - 不再承载入口适配与控制逻辑
  - 图执行回归通过

## PH1-PR-5.2
- Status: Done
- Tracking ID: PH1-PR-5.2
- Owner: Runtime Owner
- ETA: 2 days
- 标题：Runtime 收口状态推进职责
- 目标：把状态推进集中到 Runtime
- 模块：`packages/alice-engine/alice_engine/core` `packages/alice-engine/alice_engine/workflow/state.py`
- 风险：高
- 依赖：PH1-PR-5.1
- 完成标准：
  - 状态推进集中
  - 异常路径可追踪
  - 多点写状态减少

## PH1-PR-5.3
- Status: Done
- Tracking ID: PH1-PR-5.3
- Owner: Runtime Owner
- ETA: 2 days
- 标题：Engine 收口调度与驱动职责
- 目标：Engine 不再承担过多业务判断
- 模块：`packages/alice-engine/alice_engine/core/executor.py` `aitest/platform/execution_service.py`
- 风险：高
- 依赖：PH1-PR-5.2
- 完成标准：
  - Engine / Runtime / Graph 职责清晰
  - 主链路集成测试通过
  - 不引入新的循环依赖

## PH1-PR-6.1
- Status: Done
- Tracking ID: PH1-PR-6.1
- Owner: Platform Owner
- ETA: 2 days
- 标题：收敛执行状态主来源
- 目标：明确 source of truth
- 模块：`aitest/platform` `packages/alice-engine` checkpoint / run store / sop status 相关模块
- 风险：高
- 依赖：PH1-PR-5.3
- 完成标准：
  - 代码与文档明确主状态来源
  - 不再多头写状态
  - 为 replay / audit 预留稳定挂载点

## PH1-PR-6.2
- Status: Done
- Tracking ID: PH1-PR-6.2
- Owner: Platform Owner
- ETA: 1 day
- 标题：入口层彻底适配化
- 目标：CLI / Server / Chat 只做 adapter
- 模块：`aitest/server/api` `aitest/cli` `aitest/platform/execution_service.py`
- 风险：中
- 依赖：PH1-PR-6.1
- 完成标准：
  - 入口层不再含核心执行逻辑
  - 新入口可复用统一执行服务
  - 错误与日志责任清楚

## PH1-PR-6.3
- Status: Done
- Tracking ID: PH1-PR-6.3
- Owner: TL
- ETA: 1 day
- 标题：Phase 1 收口与回归基线
- 目标：固化统一主链路基线
- 模块：测试文件 文档文件 少量清理性代码
- 风险：低
- 依赖：PH1-PR-6.2
- 完成标准：
  - CLI / Server / Chat 三条主路径行为一致
  - context / result / status / control 全部落地
  - 可平滑进入 Phase 2
