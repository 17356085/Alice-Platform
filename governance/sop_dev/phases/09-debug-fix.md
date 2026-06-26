# Phase 9: Debug & Fix（调试修复）

> ⚠️ **条件触发 Phase** — 此 Phase 不是每次都执行。仅当 Phase 7 (Code Review) 发现 issues 时才进入。

## 概述

- **编号**: 9 / 10
- **目标**: 对 Code Review 发现的问题进行错误定位、根因分析和修复建议，支持最多 3 轮修复迭代
- **执行 Agent**: `debug-agent`（调试 Agent）
- **阶段分组**: 修复阶段

## 输入条件

- **必要条件**: Phase 7 Code Review 输出 `review_has_issues == true`
  - 在 `dev_route_next_phase()` 中通过以下逻辑判断：
    ```python
    review_result = agent_outputs.get("review-agent", {})
    has_issues = isinstance(review_result, dict) and not review_result.get("success", True)
    ```
  - 若 `has_issues == False`，跳过此 Phase，直接进入 Phase 10 Build
- Phase 5-6 源代码：前端/后端代码已存在
- [待补充：需定义 debug-agent 从 review-agent 的 `agent_outputs` 中读取哪些字段]

## 条件触发逻辑

```
Phase 7 Code Review 完成
        │
        ├── success=true (无问题)
        │       └──→ 跳过 Phase 9 → Phase 10 Build
        │
        └── success=false (有问题)
                └──→ 进入 Phase 9 Debug & Fix
                        │
                        ├── ≤3 轮修复 → 修复成功 → Phase 10 Build
                        └── 3 轮仍未修复 → 标记 failed_phases → Phase 10 Build
```

> **最大轮次**: 3 轮。超过 3 轮仍未解决问题，标记 Phase 为 failed 并继续 Build。

## 执行步骤

由 Agent Loop 驱动，`debug-agent` 按以下 Skill 链执行：

1. `debug/error-locator` — 定位错误来源（文件 + 行号）
2. `debug/stack-trace-analyzer` — 分析堆栈跟踪
3. `debug/fix-suggester` — 生成修复建议（不直接修改文件）
4. `debug/regression-verifier` — 验证修复不引入新问题
5. `automation/prompt-engineering-expert` — Prompt 自优化

**两种模式**:
- `diagnose` — 仅定位和分析（不生成修复方案）
- `fix` — 完整诊断→修复→验证循环（≤3 轮）【默认】

## 涉及 Skills

| Skill ID | 文件路径 | 描述 | 依赖 |
|----------|---------|------|------|
| `debug/error-locator` | `governance/skills-dev/debug/error-locator.md` | 错误定位 | — |
| `debug/stack-trace-analyzer` | `governance/skills-dev/debug/stack-trace-analyzer.md` | 堆栈分析 | — |
| `debug/fix-suggester` | `governance/skills-dev/debug/fix-suggester.md` | 修复建议 | — |
| `debug/regression-verifier` | `governance/skills-dev/debug/regression-verifier.md` | 回归验证 | — |
| `automation/prompt-engineering-expert` | `governance/skills-dev/automation/prompt-engineering-expert.md` | PE 技术应用 | `review/prompt-engineering` |

## 产出物规范

| 产出物 | 路径模板 | 验证规则 |
|--------|---------|----------|
| ERROR_DIAGNOSIS.md | `{module}/ERROR_DIAGNOSIS.md` | [待补充：需定义诊断报告的最小结构] |
| STACK_ANALYSIS.md | `{module}/STACK_ANALYSIS.md` | [待补充：需定义堆栈分析的最小结构] |
| FIX_PROPOSAL.md | `{module}/FIX_PROPOSAL.md` | [待补充：需定义修复建议的最小结构] |
| REGRESSION_REPORT.md | `{module}/REGRESSION_REPORT.md` | [待补充：需定义回归验证的最小结构] |

## 门禁条件

**条件触发 Phase**: 仅当 `review-agent` 输出 `success=false` 时执行。最多 3 轮修复。

- [ ] **ERROR_DIAGNOSIS.md** 存在且：
  - 每个 Review issue 有 文件路径 + 行号 + 错误类型
  - 覆盖所有 `agent_outputs["review-agent"].issues`
- [ ] **FIX_PROPOSAL.md** 存在且：
  - 每个 issue 有 修复方案 + 风险等级
  - 标记 `diagnose` 或 `fix` 模式
- [ ] **REGRESSION_REPORT.md** 存在（第 2+ 轮时）：
  - 确认本轮修复未引入新问题
- [ ] **轮次限制**: ≤3 轮。超过 3 轮仍有问题 → Phase 标记 `failed`，继续 Build

**退出条件**:
- 修复轮次 ≤3 且所有问题解决 → Phase `completed`
- 修复轮次 >3 仍有未解决问题 → Phase `failed`，Build 报告记录未解决 issues

`check_sop_gate_dev.py --agent debug-agent` 检查项:
- ERROR_DIAGNOSIS.md, STACK_ANALYSIS.md, FIX_PROPOSAL.md, REGRESSION_REPORT.md 存在于 artifacts 目录

## 跳过条件

此 Phase 在以下条件下被跳过：

| 条件 | 跳过? | 说明 |
|------|-------|------|
| `review_has_issues == false` | **是** | Code Review 未发现问题，自动跳过 |
| `review_has_issues == true` | 否 | Code Review 发现问题，必须执行 |
| `mode == "status"` | 是 | entry 后直接 exit |

> **注意**: MODE_SKIP_MAP 中不包含 Debug & Fix——它的跳过由运行时 `review_has_issues` 决定，非模式决定。

## Agent 详情

- **Agent ID**: `debug-agent`
- **System Prompt Role**: 资深调试专家
- **模型层级**: [待补充：agent-definitions-dev.yaml 中未指定 model_tier]
- **上下文文件**: `shared-language` [待补充：是否还需要其他上下文文件]
- **边界**: 不直接修改文件（只建议修复）、修复需人工确认、最多 3 轮修复

## 常见问题 / 故障排除

- **Q**: 3 轮修复后仍未解决，下一步怎么办？
- **A**: [待补充：需定义升级路径——人工介入 / 标记 known issue / 降级处理]
- **Q**: debug-agent 的修复建议与实际代码不符？
- **A**: [待补充]
- **Q**: REGRESSION_REPORT.md 发现新引入的问题？
- **A**: [待补充：是否需要新一轮修复循环]

## 相关文档

- Phase 定义: [../CANONICAL_PHASES.md](../CANONICAL_PHASES.md)
- Agent 映射: [../AGENT_PHASE_MAP.md](../AGENT_PHASE_MAP.md)
- Agent 定义: `governance/agents/agent-definitions-dev.yaml` → `debug-agent`
- Code Review (触发源): [07-code-review.md](07-code-review.md)
- Build (下一 Phase): [10-build.md](10-build.md)
