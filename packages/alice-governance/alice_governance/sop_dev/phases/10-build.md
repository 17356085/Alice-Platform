# Phase 10: Build（构建部署）

## 概述

- **编号**: 10 / 10
- **目标**: 执行类型检查、Lint、测试运行和打包构建，完成开发流水线的最后一环
- **执行 Agent**: `build-agent`（构建 Agent）
- **阶段分组**: 交付阶段

## 输入条件

- Phase 8 Dev Test 完成（测试已运行）
- Phase 9 Debug & Fix 完成或已跳过
- 所有代码（前端 + 后端 + 测试）已就绪
- [待补充：需定义 build-agent 从上游 agents 的 `agent_outputs` 中读取哪些字段]

> 注意：即使 Phase 9 Debug & Fix 失败（3 轮未修复），Build Phase 仍会执行——构建报告将包含未解决的 issues。

## 执行步骤

由 Agent Loop 驱动，`build-agent` 按以下 Skill 链执行：

1. `build/type-checker` — 类型检查（TypeScript `tsc --noEmit` + Python `mypy`）
2. `build/lint-executor` — Lint 执行（ESLint + Ruff/Flake8）
3. `build/test-runner` — 运行全部测试（单元 + 集成）
4. `build/package-bundler` — 打包构建（前端 `vite build` + 后端依赖检查）

## 涉及 Skills

| Skill ID | 文件路径 | 描述 | 依赖 |
|----------|---------|------|------|
| `build/type-checker` | `governance/skills-dev/build/type-checker.md` | 类型检查 | — |
| `build/lint-executor` | `governance/skills-dev/build/lint-executor.md` | Lint 执行 | — |
| `build/test-runner` | `governance/skills-dev/build/test-runner.md` | 测试运行（需人工确认） | — |
| `build/package-bundler` | `governance/skills-dev/build/package-bundler.md` | 打包构建 | — |

## 产出物规范

| 产出物 | 路径模板 | 验证规则 |
|--------|---------|----------|
| BUILD_REPORT.md | `{module}/BUILD_REPORT.md` | [待补充：需定义构建报告的最小结构] |
| TEST_RESULTS.md | `{module}/TEST_RESULTS.md` | [待补充：需定义测试结果汇总格式] |

### Build 报告应包含

- 类型检查结果（通过/失败项）
- Lint 检查结果（errors/warnings 数量）
- 测试运行结果（通过/失败/跳过数 + 覆盖率）
- 打包结果（产物大小、构建时间）
- 未解决的 issues（来自 Phase 9 Debug & Fix）

## 门禁条件

最终 Phase — 全部通过后流水线完成。即使 Debug & Fix 有未解决 issues，Build 仍执行。

- [ ] **`tsc --noEmit` 通过**（前端，0 error）
- [ ] **ESLint 通过**（前端，0 error）
- [ ] **`ruff check` 通过**（后端 Python，0 error；若未配置 Ruff 则跳过）
- [ ] **所有测试通过**: `pytest -q` 退出码 0
- [ ] **BUILD_REPORT.md** 存在且包含：
  - 类型检查结果、Lint 结果、测试结果（pass/fail/skip 数 + 覆盖率）
  - 打包产物大小 + 构建时间
  - 未解决的 issues（来自 Phase 9 Debug & Fix，如有）
- [ ] **TEST_RESULTS.md** 存在且包含：
  - 总测试数 / 通过 / 失败 / 跳过
  - 失败用例清单（名称 + 错误摘要）

**最终状态判定** (由 `exit_node` 执行):
- 全部 Phase 成功 → `completed`
- 部分 Phase 失败但 Build 通过 → `completed_with_issues`
- 致命错误 → `failed`

`check_sop_gate_dev.py --agent build-agent` 检查项:
- BUILD_REPORT.md, TEST_RESULTS.md 存在于 artifacts 目录

## 最终状态

此 Phase 完成后，`exit_node` 根据运行结果设置最终状态：

```python
if fatal:
    final_status = "failed"
elif failed:
    final_status = "completed_with_issues"
else:
    final_status = "completed"
```

| 最终状态 | 含义 |
|---------|------|
| `completed` | 全部 Phase 成功完成 |
| `completed_with_issues` | 部分 Phase 失败但已完成（有未解决 issues） |
| `failed` | 致命错误，流程中止 |

## 跳过条件

| Mode | 跳过? | 说明 |
|------|-------|------|
| `full` | 否 | — |
| `resume` | 否* | 若已完成则跳过 |
| `status` | 是 | entry 后直接 exit |
| 所有其他模式 | 否 | Build 是最终 Phase，不可跳过 |

## Agent 详情

- **Agent ID**: `build-agent`
- **System Prompt Role**: 资深 DevOps 工程师
- **模型层级**: [待补充：agent-definitions-dev.yaml 中未指定 model_tier]
- **上下文文件**: `shared-language` [待补充：是否还需要其他上下文文件]
- **边界**: 不修改源代码、不部署到生产

## 常见问题 / 故障排除

- **Q**: 构建通过但前序 Phase 有未解决的 issues？
- **A**: 最终状态为 `completed_with_issues`。issues 记录在 BUILD_REPORT.md 中。
- **Q**: `build/test-runner` 需要人工确认？
- **A**: 是的——`skill-registry-dev.yaml` 中 `build/test-runner` 标记 `needs_confirm: true`，需要人工批准。
- **Q**: 构建失败后如何重试？
- **A**: [待补充：需定义构建失败的重试/续跑策略]

## 相关文档

- Phase 定义: [../CANONICAL_PHASES.md](../CANONICAL_PHASES.md)
- Agent 映射: [../AGENT_PHASE_MAP.md](../AGENT_PHASE_MAP.md)
- Agent 定义: `governance/agents/agent-definitions-dev.yaml` → `build-agent`
- 上一 Phase: [09-debug-fix.md](09-debug-fix.md) 或 [08-dev-test.md](08-dev-test.md)
