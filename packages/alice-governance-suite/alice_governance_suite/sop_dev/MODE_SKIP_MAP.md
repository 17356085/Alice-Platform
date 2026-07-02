# MODE_SKIP_MAP — 模式跳过规则

> 来源: `aitest/graphs_dev/state_dev.py` → `DEV_MODE_SKIP_MAP`
> 路由逻辑: `aitest/graphs_dev/sop_graph_dev.py` → `dev_route_next_phase()`

## 模式完整列表

Dev SOP 支持 7 种运行模式（`DevSOPMode`），每种模式跳过不同的 Phase：

| Mode | 类型 | 跳过 Phase | 源代码定义 |
|------|------|-----------|-----------|
| `full` | 全流程 | 无 | `[]` |
| `resume` | 续跑 | 无（从已完成 Phase 后继续） | `[]` |
| `status` | 状态查看 | 无（但 entry 后直接 exit） | `[]` |
| `from-architecture` | 架构起点 | Plan, Requirements | `["Plan", "Requirements"]` |
| `from-frontend` | 前端起点 | Plan, Requirements, Architecture, Component Design | `["Plan", "Requirements", "Architecture", "Component Design"]` |
| `from-backend` | 后端起点 | Plan, Requirements, Architecture, Component Design, Frontend Impl | `["Plan", "Requirements", "Architecture", "Component Design", "Frontend Impl"]` |
| `review-only` | 仅审查 | Plan, Requirements, Architecture, Component Design, Frontend Impl, Backend Impl | `["Plan", "Requirements", "Architecture", "Component Design", "Frontend Impl", "Backend Impl"]` |

## 三种无跳过模式的区别

### `full`
- **行为**: 从头执行全部 10 Phase（Plan → Build）
- **跳过**: 无
- **Debug & Fix**: 条件触发（Code Review 发现 issues）
- **适用**: 新项目/新模块从零开始

### `resume`
- **行为**: 从上次中断处继续。`completed_phases` 中已完成的 Phase 会被跳过
- **跳过**: 空列表（由 `dev_route_next_phase()` 运行时判断 `phase in completed`）
- **Debug & Fix**: 条件触发
- **适用**: 中断后恢复（如 API 调用失败、超时后的续跑）

### `status`
- **行为**: **特殊** — entry node 检测到 `mode == "status"` 后直接路由到 exit，不进入任何 Agent
- **跳过**: 空列表（但实际全部跳过）
- **路由代码**: `if state.get("mode") == "status": return "exit"`
- **适用**: 查看指定 `run_id` 的运行状态和已完成 Phase

## 各模式使用场景

### `from-architecture`

**场景**: 项目已有明确的需求文档或 PRD，不需要 AI 重新做需求分析。

**执行流程**:
```
entry → Architecture → Component Design → Frontend Impl → Backend Impl
      → Code Review → Dev Test → (Debug & Fix?) → Build
```

**适用情况**:
- 人工已写好需求规格和项目计划
- 已有外部 PRD 文档
- 快速原型验证（跳过规划直奔架构）

### `from-frontend`

**场景**: 架构和需求已定，直接开始前端实现。

**执行流程**:
```
entry → Frontend Impl → Backend Impl → Code Review → Dev Test
      → (Debug & Fix?) → Build
```

**适用情况**:
- 已有人工设计的架构文档（COMPONENT_TREE.md 等）
- 已有组件设计稿
- 前端开发者快速上手

### `from-backend`

**场景**: 已有完整的前端代码，仅需后端开发和后续流程。

**执行流程**:
```
entry → Backend Impl → Code Review → Dev Test → (Debug & Fix?) → Build
```

**适用情况**:
- 前端已实现完成
- 只需要后端 API 开发
- API-first 开发模式（后端补充前端已有的接口）

### `review-only`

**场景**: 代码已由人工编写完毕，仅需 AI 审查 + 测试 + 构建。

**执行流程**:
```
entry → Code Review → Dev Test → (Debug & Fix?) → Build
```

**适用情况**:
- PR 审查自动化
- 代码质量门禁
- 已有完整代码，补充审查和测试

## 模式选择决策树

```
需要完整从零开发？
  ├─ 是 → mode=full
  └─ 否 → 已有哪些阶段产出？
            ├─ 已有需求文档 → mode=from-architecture
            ├─ 已有架构设计 → mode=from-frontend
            ├─ 已有前端代码 → mode=from-backend
            ├─ 已有完整代码，只需审查 → mode=review-only
            └─ 中断恢复 → mode=resume（需提供 run_id）
```

## mode=status 特殊行为

`status` 模式是唯一的**非执行模式**。它在 `sop_graph_dev.py` 中有显式路由：

```python
def dev_route_next_phase(state: dict) -> str:
    if state.get("fatal_error"):
        return "exit"
    if state.get("mode") == "status":
        return "exit"       # ← 直接退出，不进入任何 Agent
```

使用方式：
```bash
aitest graph run-dev --mode=status --run-id=<上次run_id>
```

返回当前 state 包含：`completed_phases`、`failed_phases`、`status`、`fatal_error`。

## 与 pipeline_router.py 的分工

> [待补充：Aperant 迁移引入的 `pipeline_router.py` 与 `DEV_MODE_SKIP_MAP` 的分工关系尚未定义。预期 `pipeline_router.py` 负责 ComplexityRouting（SIMPLE/STANDARD/COMPLEX 三档路由），`MODE_SKIP_MAP` 负责用户指定的模式跳过。两者在不同层面工作——一个基于复杂度自动决策，一个由用户显式选择。]

## 相关文档

- Phase 定义: [CANONICAL_PHASES.md](CANONICAL_PHASES.md)
- 路由逻辑: `aitest/graphs_dev/sop_graph_dev.py` → `dev_route_next_phase()`
- 状态定义: `aitest/graphs_dev/state_dev.py` → `DEV_MODE_SKIP_MAP` + `DevSOPMode`
