# Phase 7: Code Review（代码评审）

## 概述

- **编号**: 7 / 10
- **目标**: 对前端和后端代码进行全面审查——代码质量、性能、安全、前后端一致性
- **执行 Agent**: `review-agent`（代码审查 Agent）
- **阶段分组**: 验证阶段

> ⚠️ **关键作用**: 此 Phase 的输出 `review_has_issues` 决定 Phase 9 (Debug & Fix) 是否触发。

## 输入条件

- Phase 5 Frontend Impl 完成：前端代码已生成
- Phase 6 Backend Impl 完成：后端代码已生成
- [待补充：需定义 review-agent 从前端/后端 agent 的 `agent_outputs` 中读取哪些字段]

## 执行步骤

由 Agent Loop 驱动，`review-agent` 按以下 Skill 链执行：

### v2.0: 规则驱动审查流程

1. **规则匹配** — `RuleConfig.match_for_files(changed_files)` 获取适用规则
2. **文件打包** — `FileBundler.bundle(changed_files)` 将关联文件分组
3. **Diff 提取** — `DiffFirstReviewAdapter.prepare_review_input()` 获取 diff + 规则 + 分组
4. **Prompt 构建** — `build_review_prompt()` 注入规则指令到审查 prompt
5. **LLM 审查** — 带规则上下文的深度审查
6. **位置校正** — `PositionVerifier.verify_issues()` 验证行号准确性

### 传统 Skill 链 (与规则审查并行)

1. `code-review/source-code-reviewer` — 源代码审查 (已注入规则指令)
2. `code-review/consistency-enforcer` — 前后端一致性检查
3. `code-review/performance-analyzer` — 性能分析
4. `code-review/security-scanner` — 安全扫描
5. `automation/prompt-engineering-expert` — Prompt 自优化

**输出数据流**:
```
review-agent 输出 → agent_outputs["review-agent"]
  ├── success: bool         ← 决定 Debug & Fix 是否触发
  ├── issues: list          ← 问题列表 (已校正行号)
  ├── reports: dict         ← 各项报告引用
  └── rules_applied: list   ← 已应用的规则列表
```

## 涉及 Skills

| Skill ID | 文件路径 | 描述 | 依赖 |
|----------|---------|------|------|
| `code-review/source-code-reviewer` | `governance/skills-dev/code-review/source-code-reviewer.md` | 源代码审查 | — |
| `code-review/performance-analyzer` | `governance/skills-dev/code-review/performance-analyzer.md` | 性能分析 | — |
| `code-review/security-scanner` | `governance/skills-dev/code-review/security-scanner.md` | 安全扫描 | — |
| `code-review/consistency-enforcer` | `governance/skills-dev/code-review/consistency-enforcer.md` | 一致性检查 | — |
| `automation/prompt-engineering-expert` | `governance/skills-dev/automation/prompt-engineering-expert.md` | PE 技术应用 | `review/prompt-engineering` |

## 产出物规范

| 产出物 | 路径模板 | 验证规则 |
|--------|---------|----------|
| CODE_REVIEW.md | `{module}/CODE_REVIEW.md` | [待补充：需定义审查报告的最小结构] |
| PERFORMANCE_REPORT.md | `{module}/PERFORMANCE_REPORT.md` | [待补充：需定义性能报告的最小结构] |
| SECURITY_REPORT.md | `{module}/SECURITY_REPORT.md` | [待补充：需定义安全报告的最小结构] |
| CONSISTENCY_REPORT.md | `{module}/CONSISTENCY_REPORT.md` | [待补充：需定义一致性报告的最小结构] |

## 门禁条件

进入 Phase 8 (Dev Test) 前必须满足。**此 Phase 的 `success` 字段决定 Phase 9 (Debug & Fix) 是否触发。**

- [ ] **CODE_REVIEW.md** 存在且：
  - 覆盖所有已修改文件（前端 `.vue/.ts` + 后端 `.py`）
  - 每个问题有 严重级别(severity) + 文件路径 + 行号
- [ ] **SECURITY_REPORT.md** 存在且：
  - 0 critical 级别漏洞（critical >0 → `success=false`）
  - high 级别漏洞 ≤3 个（超过 → `success=false`）
- [ ] **CONSISTENCY_REPORT.md** 存在且：
  - 确认前端调用后端所有 API 契约匹配（method, path, request/response type）
- [ ] **PERFORMANCE_REPORT.md** 存在且：
  - N+1 查询检查、不必要的 re-render 检查
- [ ] `agent_outputs["review-agent"].success` 明确为 `true` 或 `false`

**输出判定规则**:
- `success=true` → 跳过 Phase 9 (Debug & Fix)，直接进入 Dev Test
- `success=false` → 触发 Phase 9 (Debug & Fix)，≤3 轮修复

`check_sop_gate_dev.py --agent review-agent` 检查项:
- CODE_REVIEW.md, PERFORMANCE_REPORT.md, SECURITY_REPORT.md, CONSISTENCY_REPORT.md 存在于 artifacts 目录

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
| `review-only` | 否 | 从 Code Review 开始 |
| `review-only`（后续） | 否 | Dev Test + (Debug & Fix?) + Build 仍执行 |

## Agent 详情

- **Agent ID**: `review-agent`
- **System Prompt Role**: 资深 Code Reviewer + 质量架构师
- **模型层级**: [待补充：agent-definitions-dev.yaml 中未指定 model_tier]
- **上下文文件**: `shared-language`, `coding-standards`
- **边界**: 不修改代码（只报告）、不执行构建

## 常见问题 / 故障排除

- **Q**: review-agent 误报（false positive）如何处理？
- **A**: [待补充：需定义 false positive 的上报和豁免机制]
- **Q**: 审查结果 `success=false` 但实际无实质问题？
- **A**: [待补充]

## 相关文档

- Phase 定义: [../CANONICAL_PHASES.md](../CANONICAL_PHASES.md)
- Agent 映射: [../AGENT_PHASE_MAP.md](../AGENT_PHASE_MAP.md)
- Agent 定义: `governance/agents/agent-definitions-dev.yaml` → `review-agent`
- Debug & Fix Phase: [09-debug-fix.md](09-debug-fix.md)（由本 Phase 触发）
