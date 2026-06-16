# Governance Layer

## 目标
在不推倒现有项目结构的前提下，增加一层 AI 协作治理骨架。

## 核心原则
1. 协作层先行，代码层后移
2. 先建治理索引，再逐步映射旧资产
3. context/ 先按测试项目划分，再按模块划分
4. 项目级放稳定共性，模块级承载业务与测试细节
5. workflows/skills/templates/ 服务于模块上下文树
6. artifacts/ 只存过程产物，不替代事实源

## 当前状态（2026-06-11 — 架构优化 v1.0 第2个月完成）

```
Prompt工程 ✅ → Workflow工程 ✅ → Skill工程 ✅ (24 active + 6 deprecated) → Agent工程 ✅ (8 Agent v2.0)
→ MCP工程 ✅ (2 MCP Server) → RAG工程 ✅ (5 collections, 235 docs) → Workflow Engine ✅ → Agent Scheduler ✅
→ Event Bus ✅ → Memory ✅ → Platform工程 ⏳
```

- **Skill**: 24 active + 6 deprecated，7 分类体系
  - `skills/knowledge/`：knowledge-manager（合并 extract+precipitate）+ completeness-check
  - `skills/reporting/`：report-generator（合并 test-summary+progress-report, 三模式）
  - `skills/_deprecated/`：6 个废弃归档
- **Agent**: 8 Agent v2.0 + Skill Primary Owner 已明确
- **RAG 向量检索**：ChromaDB 5 集合 235 文档
  - known_issues (16) + project_context (12) + tech_analysis (72) + page_context (102) + page_objects (33)
  - bug-analysis Skill 已集成 L0 RAG 自动匹配
  - MCP Tool: `rag_search_known_issues`
- **Workflow Engine**：YAML DAG 引擎（`aitest/workflow_engine.py`）
  - module-onboarding.yaml 定义（7 步骤 → 6 DAG 层级）
  - 支持 checkpoint/resume, 拓扑排序, 并行层级检测
- **Agent Scheduler**：前置条件检测 + Agent 推荐（`aitest/agent_scheduler.py`）
  - 模块 SOP 状态机：自动检测当前 Phase → 推荐下一步 Agent
- **Event Bus**：文件持久化事件系统（`aitest/event_bus.py`）
  - 事件类型：AgentCompleted / BugClosed / CycleEnd / ContextUpdated
  - Knowledge Agent 事件驱动基础就绪
- **MCP Server**: 2 个（aitest-tools 5 tools + aitest-knowledge 分层资源）
- **CURRENT_TASK**: 标准化模板 + context-sync 适配
- **Context 版本号**: PROJECT_CONTEXT + MODULE_INDEX
- **Memory**: 3 条关键决策（tank UI 框架 / RAG 可用性 / Skill 合并记录）
- **架构优化方案**: `governance/docs/architecture/AI_TEST_PLATFORM_ARCHITECTURE_OPTIMIZATION.md`

## 入口
- 项目索引：`context/project-index.yaml`
- 事实源规则：`context/source-of-truth.md`
- 工作流注册表：`workflows/workflow-registry.yaml`
- Skill 注册表：`skills/skill-registry.yaml`
- 口语化入口：`CLAUDE.md` § 口语化入口
- 迁移计划：`docs/operations/PHASE_PLAN.md`

## 当前纳管范围
- Web 自动化项目（ZJSN_Test-master526）
- 小程序自动化项目（mp-weixin-automator）
- 6 个模块: equipment / system-user / system-role / system-management / tank / personnel
