# Phase 8: Dev Test（开发测试）

## 概述

- **编号**: 8 / 10
- **目标**: 为前端和后端代码生成单元测试和集成测试，确保代码覆盖率达标
- **执行 Agent**: `dev-test-agent`（测试 Agent）
- **阶段分组**: 验证阶段

## 输入条件

- Phase 7 Code Review 完成（代码已审查，无论审查结果如何）
- Phase 5 Frontend Impl + Phase 6 Backend Impl：代码已存在
- [待补充：需定义 dev-test-agent 从上游 agents 的 `agent_outputs` 中读取哪些字段]

## 执行步骤

由 Agent Loop 驱动，`dev-test-agent` 按以下 Skill 链执行：

1. `test-dev/unit-test-generator` — 为关键函数/方法生成单元测试
2. `test-dev/integration-test-generator` — 为 API 端点生成集成测试
3. `test-dev/coverage-checker` — 运行测试并检查覆盖率

## 涉及 Skills

| Skill ID | 文件路径 | 描述 | 依赖 |
|----------|---------|------|------|
| `test-dev/unit-test-generator` | `governance/skills-dev/test-dev/unit-test-generator.md` | 单元测试生成 | — |
| `test-dev/integration-test-generator` | `governance/skills-dev/test-dev/integration-test-generator.md` | 集成测试生成 | — |
| `test-dev/coverage-checker` | `governance/skills-dev/test-dev/coverage-checker.md` | 覆盖率检查 | — |

## 产出物规范

| 产出物 | 路径模板 | 验证规则 |
|--------|---------|----------|
| 单元测试 | `tests/test_*.py` | pytest 可执行，覆盖核心逻辑 |
| 集成测试 | `tests/integration/test_*.py` | API 端点集成测试 |
| 覆盖率报告 | `{module}/COVERAGE_REPORT.md` | [待补充：需定义覆盖率阈值] |

## 门禁条件

进入 Phase 10 (Build) 前必须满足。注意：Phase 9 (Debug & Fix) 条件触发，可能被跳过。

- [ ] **单元测试可运行**: `pytest tests/unit/ -q` 无 crash
- [ ] **集成测试可运行**: `pytest tests/integration/ -q` 无 crash
- [ ] **覆盖率 ≥ 阈值**:
  - 后端: ≥70% 行覆盖率（关键业务逻辑 ≥85%）
  - 前端: 暂不强制（vitest 待后续集成）
- [ ] **COVERAGE_REPORT.md** 存在且包含：
  - 总体覆盖率百分比
  - 未覆盖的模块/函数清单
  - 关键路径覆盖率

`check_sop_gate_dev.py --agent dev-test-agent` 检查项:
- COVERAGE_REPORT.md 存在于 artifacts 目录

## 跳过条件

此 Phase 在以下模式中被跳过：

| Mode | 跳过? | 说明 |
|------|-------|------|
| `full` | 否 | — |
| `resume` | 否* | 若已完成则跳过 |
| `status` | 是 | entry 后直接 exit |
| `from-architecture` | 否 | — |
| `from-frontend` | 否 | — |
| `from-backend` | 否 | — |
| `review-only` | 否 | Code Review 后进入 Dev Test |

## Agent 详情

- **Agent ID**: `dev-test-agent`
- **System Prompt Role**: 资深测试工程师
- **模型层级**: [待补充：agent-definitions-dev.yaml 中未指定 model_tier]
- **上下文文件**: `shared-language`, `coding-standards`
- **边界**: 不修改源文件、不部署

## 常见问题 / 故障排除

- [待补充：根据实践经验积累]

## 相关文档

- Phase 定义: [../CANONICAL_PHASES.md](../CANONICAL_PHASES.md)
- Agent 映射: [../AGENT_PHASE_MAP.md](../AGENT_PHASE_MAP.md)
- Agent 定义: `governance/agents/agent-definitions-dev.yaml` → `dev-test-agent`
- Code Review: [07-code-review.md](07-code-review.md)
- Debug & Fix: [09-debug-fix.md](09-debug-fix.md)
