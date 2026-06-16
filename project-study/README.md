# Project Study — 鞍集涂源管理系统 Agent 体系逆向拆解

> 从教学角度对当前项目的 Agent 工程体系进行逆向分析。
> 不优化项目，只分析设计思想。

## 文档索引

建议按以下顺序阅读：

| # | 文档 | 核心问题 | 预计阅读 |
|---|------|---------|:---:|
| 1 | [AI_ENGINEERING_LANDSCAPE.md](AI_ENGINEERING_LANDSCAPE.md) | 项目→AI 工程体系全映射。先建立全局坐标系 | 25 min |
| 2 | [AGENT_ARCHITECTURE_REVERSE_ENGINEERING.md](AGENT_ARCHITECTURE_REVERSE_ENGINEERING.md) | 8 个 Agent 为什么存在？各自属于什么 Agent 模式？ | 20 min |
| 3 | [AGENT_DESIGN_PATTERNS.md](AGENT_DESIGN_PATTERNS.md) | 9 种 Agent 设计模式在项目中的工程落地 | 25 min |
| 4 | [LANGGRAPH_REVERSE_ENGINEERING.md](LANGGRAPH_REVERSE_ENGINEERING.md) | 20+ 个 LangGraph 节点→概念映射（State/Node/Edge/Checkpoint/HITL） | 30 min |
| 5 | [SKILL_ENGINEERING_ANALYSIS.md](SKILL_ENGINEERING_ANALYSIS.md) | 24 个 Skill 逐一分析（职责/单一职责/复用价值/分类） | 20 min |

## 阅读路线

```
快速入门（1 小时）:
  AI_ENGINEERING_LANDSCAPE.md → AGENT_ARCHITECTURE_REVERSE_ENGINEERING.md

深度学习（2 小时）:
  按 1→2→3→4→5 顺序通读

针对性学习:
  想学 Agent 模式 → AGENT_DESIGN_PATTERNS.md
  想学 LangGraph → LANGGRAPH_REVERSE_ENGINEERING.md
  想学 Skill 工程 → SKILL_ENGINEERING_ANALYSIS.md
  想做技术选型 → AI_ENGINEERING_LANDSCAPE.md
```

## 关键结论速览

- **9 种** Agent 设计模式在项目中落地（ReAct、Plan & Execute、Supervisor、Router、Reflection、Multi-Agent、Hierarchical、State Machine、HITL）
- **四层** LangGraph 架构（顶层 Supervisor + Bug Analysis SubGraph + Execution/Report/Knowledge SubGraphs + AgentLoop 节点）
- **24 个** Skill 归入 6 种类型（Analysis/Generation/Strategy/Validation/Synthesis/Knowledge）
- **AI 工程 10 大领域** 中 7 个深度掌握、3 个良好掌握、0 个缺失
- **最大短板**: 系统化 Agent 评估 + 全链路可观测性

---

> 生成日期: 2026-06-14 · 基于项目 v2.0 Agent 体系 · 纯教学用途
