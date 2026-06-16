---
name: full-sop
description: 端到端 SOP 编排器 — 委托 aitest graph run CLI (LangGraph) 执行完整 9-Phase 流水线。当用户说"测XX"/"自动化XX"/"给XX写测试"时强制使用。
source: governance/agents/agent-definitions.yaml
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Skill, Agent, WebFetch
---

# /full-sop — SOP 编排器

委托 Python LangGraph 引擎 (`aitest graph run --non-interactive`) 执行完整 SOP 流水线。

## 架构

```
/full-sop module=X
  → full-sop.workflow.js (本 Skill)
    → Bash: aitest graph run --module=X --non-interactive
      → sop_graph.py (LangGraph 9-Phase 状态机)
        → AgentLoop.run() → run_skill() → Anthropic API
      → JSON 结果
    → 展示给用户
```

**不再是 Claude 调 Claude**。编排引擎是 Python LangGraph，LLM 调用走 `run_skill()` → Anthropic API。

## 流水线（与 CANONICAL_PHASES 对齐）

| Phase | 执行方式 | 产出 |
|-------|---------|------|
| Preflight | preflight_node (文件扫描, 0 token) | 页面发现 + mode 推荐 |
| Project Init | AgentLoop → Claude API | PROJECT_CONTEXT.md |
| Requirement | AgentLoop → Claude API | MODULE_CONTEXT.md |
| Test Design | AgentLoop → Claude API (per page) | PAGE_CONTEXT, RISK_MODEL, TEST_CASES |
| Automation | AgentLoop → Claude API (per page) | TECH_ANALYSIS, PageObject, test_*.py |
| Execute & Debug | AgentLoop + subprocess | pytest + allure-results |
| Bug Analysis | AgentLoop (conditional) | 根因分析 + auto-fix + retry |
| Data Sanitization | scan_and_clean.py (0 token) | 残留数据清理 |
| Report | AgentLoop → Claude API | TEST_SUMMARY.md |
| Knowledge | AgentLoop → Claude API | known-issues.yaml 更新 |

## 模式

| mode | 行为 |
|------|------|
| `full` | 从头执行 (默认) |
| `resume` | 断点续跑 — LangGraph checkpoint (SQLite) 自动恢复 |
| `status` | 仅查看进度 (不调 Python，快速) |
| `from-requirement` / `from-test-design` / `from-automation` | 跳过前置 Phase |

## 能力

- ✅ LangGraph 状态机 (9 Phase 自动遍历)
- ✅ SQLite checkpoint 断点续跑
- ✅ Gate 门禁检查 (check_sop_gate.py)
- ✅ code-consistency: mechanical grep + LLM review
- ✅ mtime 缓存 TTL
- ✅ SOP_STATUS JSON + checkpoint 双写
- ⚠️ HITL: `--non-interactive` 模式自动批准（Claude Code 路径无交互终端）

## 边界

- ✅ 编排全部 8 Agent + 门禁 + 失败路由 + 修复循环 + 数据清理
- ❌ 不替代子 Agent 逻辑, 不跨模块
- ⚠️ HITL 自动批准（非交互模式）。如需人工审批，在终端运行 `aitest graph run`（交互模式）

完整定义: `governance/agents/full-sop.workflow.js`, `aitest/graphs/sop_graph.py`
