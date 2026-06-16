# Agents — AI Agent 层

> **单一事实源**: `governance/agents/agent-definitions.yaml`
> 本文档的 Agent 全景图、Skill 列表、状态表均从 YAML 派生。修改 Agent 定义请编辑 YAML 文件。
> 运行 `python tools/check_agent_drift.py` 检测本文档与 YAML 的不一致。

> Agent 是 Skill 工程的上层抽象。每个 Agent 绑定一个 Skill 集合，可独立完成一类测试开发任务。
> Agent 之间通过 context/ 文档传递状态，不共享会话。

---

## 设计原则

1. **一个 Agent 一类任务**：项目/需求/设计/自动化/执行/诊断/报告/知识，职责不交叉
2. **Agent 通过 Context 链通信**：上游 Agent 产出文档 → 下游 Agent 消费文档
3. **Agent 不持有状态**：每次调用独立，上下文从 context/ 文件加载
4. **Agent = Skill 集合 + 编排规则**：Agent 决定 Skill 的调用顺序和衔接逻辑
5. **唯一写入原则**：Knowledge Agent 是唯一可跨 Agent 写入知识库的 Agent
6. **默认入口唯一**：完整 SOP 默认只能从 `/full-sop` 进入；单个 Agent 仅允许作为编排器内部步骤或明确的补位操作被调用

---

## Agent 全景 (v2.0 — 2026-06-11)

```
                         ┌──────────────────┐
                         │  ① Project Agent  │
                         │  (Phase 0)        │
                         │  项目初始化+索引+审计│
                         └────────┬─────────┘
                                  │ PROJECT_CONTEXT, MODULE_INDEX
                                  ▼
                         ┌──────────────────┐
                         │ ② Requirement    │
                         │    Agent         │
                         │  (Phase 0.5~0.8) │
                         │  模块建模+需求分析  │
                         └────────┬─────────┘
                                  │ MODULE_CONTEXT, REQUIREMENT_ANALYSIS
                                  ▼
                         ┌──────────────────┐
                         │ ③ Test Design    │
                         │    Agent         │
                         │  (Phase 1~2.5)   │
                         │  页面→风险→测试设计 │
                         └────────┬─────────┘
                                  │ PAGE_CONTEXT, RISK_MODEL, TEST_DESIGN, TEST_CASES
                                  ▼
                         ┌──────────────────┐
                         │ ④ Automation     │
                         │    Agent         │
                         │  (Phase 3~4)     │
                         │  技术分析→代码生成  │
                         └────────┬─────────┘
                                  │ TECH_ANALYSIS, AUTO_STRATEGY, PageObject, test_*.py
                                  ▼
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
          ┌──────────────────┐        ┌──────────────────┐
          │ ⑤ Execution      │        │ ⑥ Bug Analysis   │
          │    Agent         │──失败──▶│    Agent         │
          │  (Phase 4.5~7)   │        │  (Phase 4.5~7)   │
          │  执行+报告生成     │        │  根因分析+CI诊断   │
          └────────┬─────────┘        └────────┬─────────┘
                   │ 成功                      │ 根因确认
                   ▼                           ▼
          ┌──────────────────┐        ┌──────────────────┐
          │ ⑦ Report Agent   │        │ ⑧ Knowledge      │◀── 横向贯穿
          │  (Phase 8~9)     │        │    Agent         │   所有 Agent
          │  测试总结+进度汇报 │        │  (Phase 9)       │
          └──────────────────┘        │  知识提取+沉淀+审计│
                                      └──────────────────┘
```

---

## Agent 调用方式

### 方式 A: Skills 斜杠命令（交互式）⭐ 推荐

```
/project-agent       ← 项目初始化/上下文管理/文档审计
/requirement-agent   ← 模块建模/需求分析
/test-design-agent   ← 页面分析/风险建模/测试用例设计
/automation-agent    ← 技术分析/自动化策略/代码生成
/execution-agent     ← 执行测试/报告生成
/bug-analysis-agent  ← Bug根因分析/CI诊断/Jenkins配置
/report-agent        ← 测试总结/进度报告/Excel导出
/knowledge-agent     ← 知识提取/沉淀/审计（横向贯穿）
```

Skill 文件位置: `.claude/skills/<agent-name>/SKILL.md`

### 方式 B: LangGraph 编排（批量/自动化）

```bash
aitest graph run --module=<m> --mode=full
```

P1-1 (2026-06-13): `.workflow.js` 文件已删除，统一使用 LangGraph 引擎。

---

## 当前状态

| Agent | 绑定 Skill | 斜杠命令 | 状态 |
|-------|-----------| :------: | :--: |
| project-agent | project-context-manager + context-sync + completeness-check (★Primary) | ✅ | 🟢 v2.0 |
| requirement-agent | module-modeling + requirement-analysis | ✅ | 🟢 v2.0 |
| test-design-agent | page-analysis + risk-modeling + testcase-design + test-data-generation (+ api-testing + miniapp-testing) | ✅ | 🟢 v2.0 |
| automation-agent | tech-analysis + auto-strategy + page-object-generator + test-script-generator(含conftest) + code-consistency-checker | ✅ | 🟢 v2.0 |
| execution-agent | allure-report-analyzer + excel-exporter (Secondary) | ✅ | 🟢 v2.0 |
| bug-analysis-agent | bug-analysis + ci-pipeline-analysis + jenkinsfile-generator | ✅ | 🟢 v2.0 |
| report-agent | report-generator (test-summary+progress+excel modes) + excel-exporter (★Primary) | ✅ | 🟢 v2.0 |
| knowledge-agent | knowledge-manager (extract+precipitate) + completeness-check (Secondary) | ✅ | 🟢 v2.0 |

### 废弃 Agent (v1.0)

v1.0 的 4 个 Agent (analysis/design/code/diagnosis) 已于 2026-06-12 拆分为 8 个 v2.0 Agent。旧定义文件已于 2026-06-15 清理。

| v1.0 Agent | → v2.0 迁移 |
|------------|------------|
| analysis-agent | → project-agent + requirement-agent + test-design-agent |
| design-agent | → test-design-agent + automation-agent |
| code-agent | → automation-agent |
| diagnosis-agent | → bug-analysis-agent + report-agent + knowledge-agent |

### 文件清单

```
governance/agents/
├── README.md
├── agent-definitions.yaml         ← 单一事实源
├── agent-definitions-dev.yaml     ← 开发 Agent 定义
├── full-sop.workflow.js           ← Claude Code 编排路径
├── project-agent.md
├── requirement-agent.md
├── test-design-agent.md
├── automation-agent.md
├── execution-agent.md
├── bug-analysis-agent.md
├── report-agent.md
├── knowledge-agent.md
└── _archived/                     ← 历史归档

.claude/skills/
├── full-sop/SKILL.md
├── page-interface-generator/SKILL.md
├── project-agent/SKILL.md
├── requirement-agent/SKILL.md
├── test-design-agent/SKILL.md
├── automation-agent/SKILL.md
├── execution-agent/SKILL.md
├── bug-analysis-agent/SKILL.md
├── report-agent/SKILL.md
├── knowledge-agent/SKILL.md
└── continue/SKILL.md
```
