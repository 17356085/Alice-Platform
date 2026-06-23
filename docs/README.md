# AITest Platform Documentation

> 本目录为平台文档唯一根目录。所有人力撰写的文档统一在此，按类别放入子目录。

## 目录约定

| 目录 | 用途 | 读者 | 示例 |
|------|------|------|------|
| `architecture/` | 正典平台架构文档（编号系列） | 开发者 | `00-ARCHITECTURE_OVERVIEW.md` |
| `architecture/reviews/` | 历史架构评审报告（只读存档） | 开发者 | `ARCHITECTURE_REVIEW_V2_2026-06-13.md` |
| `adr/` | 架构决策记录（不可变，创建后不修改） | 全团队 | `ADR_001_TLO_DIRECTORY.md` |
| `plans/` | 改进计划 / 路线图 / 解耦方案 | 开发者 | `TLO_DEVELOPMENT_PLAN.md` |
| `guides/` | 操作指南 / 适配指南 | 用户 | `PROMPT_ADAPTATION_GUIDE.md` |
| `integration/` | 外部集成文档 | 开发者 | `MCP_CLIENT_GUIDE.md` |
| `operations/` | 运维规程 / SOP 运维清单 | 运维 | `SOP_DEBT_CHECKLIST.md` |
| `reference/` | 参考材料（命名规范、最佳实践、模型分层） | 全团队 | `NAMING_CONVENTIONS.md` |
| `archive/` | 已归档的历史文档（不再活跃） | — | — |

## 文件命名约定

| 类型 | 格式 | 示例 |
|------|------|------|
| 正典架构 | `NN-TOPIC.md`（双数字编号） | `00-ARCHITECTURE_OVERVIEW.md` |
| ADR | `ADR_NNN_SHORT_DESC.md` | `ADR_001_TLO_DIRECTORY.md` |
| 计划/评审 | `TOPIC_DATE.md`（日期 `YYYY-MM-DD`） | `HITL_EXPANSION_PLAN.md` 或 `ARCHITECTURE_REVIEW_V2_2026-06-13.md` |
| 指南/参考 | `TOPIC.md`（无日期，描述性标题） | `NAMING_CONVENTIONS.md` |

## 文档生命周期

```
Draft → Active → Archived
  │        │         │
  │        │         └─ 不再活跃的计划/过时的评审 → archive/
  │        └─ 审核通过，去掉 '状态: draft'，持续更新
  └─ 新建时标注 '状态: draft'，PR 审核
```

- **ADR**: 特殊——创建后不可变。如需推翻，写新的 ADR 引用旧的。
- **Archived**: `archive/` 目录存放。不删除，保留历史参考。

## governance/ 与 docs/ 的边界

| | `docs/` | `governance/` |
|---|---|---|
| **类型** | 人力撰写的文档 | 机器消费的运行时定义 |
| **读者** | 人（开发者、用户） | 平台引擎（Python、Agent） |
| **内容** | 架构、计划、ADR、指南、参考 | Agent 定义、Skill 提示、配置、产物 |
| **更新方式** | 手动编辑 | 平台运行时读写 / 手动定义 |
| **示例** | `00-ARCHITECTURE_OVERVIEW.md` | `agents/knowledge-agent.md`, `context/environments.yaml` |

### 快速判断：该放哪？

- "这篇文章解释平台怎么设计/怎么用" → `docs/`
- "这个文件是 Agent/Skill/配置运行时需要读的" → `governance/`
- "这是关于某个测试项目（ZJSN 等）的文档" → 项目 `.tlo/` 目录

## 当前文档索引

### architecture/
- `00-ARCHITECTURE_OVERVIEW.md` — AITest v1.0 平台架构总览
- `01-CAPABILITY_ROUTER.md` — 统一能力路由层
- `02-PROVIDER_RELIABILITY.md` — Provider 可靠性设计
- `03-CONTEXT_WINDOW.md` — 上下文窗口管理
- `04-TESTING_MEMORY.md` — 测试记忆系统
- `05-COMPLEXITY_ROUTING.md` — 复杂度路由
- `06-SECURITY_LAYER.md` — 安全层设计
- `07-MIGRATION_PLAN.md` — v1.0 迁移计划

### architecture/reviews/
- 历史架构评审报告（8 份，2026-06-13 ~ 06-14）

### adr/
- `ADR_001_TLO_DIRECTORY.md` — 项目上下文跟随项目
- `DOT_TLO_PROPOSAL.md` — .tlo/ 方案提案
- `DOT_TLO_REVIEW.md` — .tlo/ 方案评审
- `DOT_TLO_TEAM_TRADEOFF.md` — .tlo/ 团队使用场景分析

### plans/
- 当前活跃计划及历史改进方案（17 份）

### guides/
- `PROMPT_ADAPTATION_GUIDE.md` — Prompt 适配指南

### integration/
- `MCP_CLIENT_GUIDE.md` — MCP 客户端指南
- `MIGRATION_MAP.md` — 迁移映射

### operations/
- `FULLSOP_SPLIT_PLAN.md` — Full SOP 拆分计划
- `PHASE_PLAN.md` — Phase 规划
- `SOP_DEBT_CHECKLIST.md` — SOP 债务清单

### reference/
- `AGENT_SKILL_FULL_MAP.md` — Agent-Skill 全景图
- `NAMING_CONVENTIONS.md` — 命名规范
- `MODEL_TIERING.md` — 模型分层
- `CLAUDE_CODE_BEST_PRACTICES.md` — Claude Code 最佳实践
- `SESSION_TEMPLATE.md` — 会话模板
- `routing-guide.md` — 路由指南
