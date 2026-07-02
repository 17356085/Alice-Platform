# Dev SOP — 开发标准操作流程

> 治理文档 · 来源: `aitest/graphs_dev/state_dev.py` + `aitest/graphs_dev/sop_graph_dev.py`
> Agent 定义: `governance/agents/agent-definitions-dev.yaml`
> 最后更新: 2026-06-24

## 概述

Dev SOP（开发标准操作流程）是 AITest 平台对自身开发过程的结构化治理规范。它定义了一条从项目规划到构建部署的 **10 Phase 流水线**，由 **9 个专用 Agent** 顺序（部分条件）执行。每个 Phase 有明确的输入条件、执行步骤、产出物和门禁。

### 目的

1. **规范化**：AI 辅助开发遵循一致的流程，减少随意性
2. **可追溯**：每个 Phase 的产出物形成完整的开发链路文档
3. **质量保障**：内置 Code Review + Dev Test + Debug & Fix 质量闭环
4. **模式灵活**：7 种运行模式适应不同开发场景（全流程 / 断点续跑 / 局部增量）

### 适用场景

- 新功能/新模块的完整开发
- Bug 修复流程（`debug-agent` 专项）
- 架构变更后的增量实施
- 前端或后端单侧的独立开发
- 仅代码审查 + 测试的门禁检查

### 与测试 SOP 的关系

| 维度 | Dev SOP（本目录） | 测试 SOP（`governance/agents/` + `graphs/`） |
|------|------------------|---------------------------------------------|
| 目标 | 开发 `aitest` 平台自身 | 测试被测系统（鞍集涂源管理系统） |
| Agent 定义 | `agent-definitions-dev.yaml` | `agent-definitions.yaml` |
| Phase 数 | 10 | 9（TLO 8 阶段 + 1 QA Loop） |
| 编排图 | `sop_graph_dev.py` | `sop_graph.py` / `parallel_sop.py` |
| Skill 目录 | `governance/skills-dev/` | `governance/skills/` |
| State | `state_dev.py` (DevSOPState) | `state.py` (SOPState) |

两条工作线共享 `agent_runner.py` 执行引擎和 `llm/` 基础设施层，但在治理层面完全解耦。

## 目录结构

```
governance/sop_dev/
├── README.md                      # 本文件 — 概述
├── CANONICAL_PHASES.md            # 10 Phase 定义 + 依赖关系 + Skill清单
├── AGENT_PHASE_MAP.md             # Agent ↔ Phase 双向映射表
├── MODE_SKIP_MAP.md               # 7 种运行模式的跳过规则
└── phases/
    ├── 00-INDEX.md                # Phase 索引 + 分组
    ├── 01-plan.md                 # Phase 1: Plan
    ├── 02-requirements.md         # Phase 2: Requirements
    ├── 03-architecture.md         # Phase 3: Architecture
    ├── 04-component-design.md     # Phase 4: Component Design
    ├── 05-frontend-impl.md        # Phase 5: Frontend Impl
    ├── 06-backend-impl.md         # Phase 6: Backend Impl
    ├── 07-code-review.md          # Phase 7: Code Review
    ├── 08-dev-test.md             # Phase 8: Dev Test
    ├── 09-debug-fix.md            # Phase 9: Debug & Fix (条件触发)
    └── 10-build.md                # Phase 10: Build
```

## 快速开始

### 启动完整开发流水线

```bash
# 完整流程（Plan → Build）
aitest graph run-dev --mode=full --target=<module>

# 或通过 Python API
python -c "
from aitest.graphs_dev.sop_graph_dev import build_compiled_dev_graph
from aitest.graphs_dev.state_dev import create_initial_state_dev
graph = build_compiled_dev_graph()
state = create_initial_state_dev(module='my-feature', mode='full')
result = graph.invoke(state)
"
```

### 常用模式

```bash
# 仅从架构开始（跳过 Plan + Requirements）
aitest graph run-dev --mode=from-architecture

# 仅代码审查
aitest graph run-dev --mode=review-only

# 续跑（从上次中断位置继续）
aitest graph run-dev --mode=resume --run-id=<上次run_id>
```

### 查看运行状态

```bash
aitest graph run-dev --mode=status --run-id=<run_id>
```

## Phase 流水线总览

```
Plan ──→ Requirements ──→ Architecture ──→ Component Design
                                           ↓
Build ←── Debug & Fix ←── Dev Test ←── Code Review
  ↑         (条件触发)                    ↑      ↑
  │                                      │      │
  └──── Frontend Impl ──────────────────┘      │
        Backend Impl ──────────────────────────┘
```

## 术语

参见 `governance/context/shared-language.md` 中的 Phase、Agent、Skill、SOP 定义。

## 相关文件

- Agent 定义: `governance/agents/agent-definitions-dev.yaml`
- Skill 注册: `governance/skills-dev/skill-registry-dev.yaml`
- 编排图: `aitest/graphs_dev/sop_graph_dev.py`
- 状态定义: `aitest/graphs_dev/state_dev.py`
- 执行引擎: `aitest/agent_runner.py`
- 开发 Agent 生态: [[dev-agent-ecosystem-phase1]]
