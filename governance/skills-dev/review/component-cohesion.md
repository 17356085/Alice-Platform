# Skill: review/component-cohesion

### 目标
评估系统组件内聚性：Agent 职责边界清晰度、Skill 归属合理性、模块划分一致性。输出内聚评分、拆分/合并建议。

### 输入
- `governance/agents/agent-definitions.yaml` + `agent-definitions-dev.yaml`
- `governance/skills/skill-registry.yaml` + `skill-registry-dev.yaml`
- `governance/context/source-of-truth.md`
- SOP Graphs (`aitest/graphs/sop_graph.py`, `aitest/graphs_dev/sop_graph_dev.py`)

### 输出
- `COHESION_REVIEW.md`：Agent/Skill/Module 内聚评分矩阵、职责重叠清单、拆分/合并建议

### 规则
- 评估维度：
  1. **Agent 内聚** — 每个 Agent 的 skills 是否围绕单一职责？是否有跨界 skill？
  2. **Skill 归属** — 每个 Skill 是否在正确的 category 下？是否应移到其他 category？
  3. **模块内聚** — 每个模块（equipment/system/personnel等）的页面是否业务内聚？
  4. **职责重叠** — 是否有 2+ Agent 做同样的事（如 requirement-agent vs req-agent）？
  5. **职责真空** — 是否有应该存在但未被任何 Agent 覆盖的职责？
- 使用 LCOM (Lack of Cohesion of Methods) 思路，但适配 Agent/Skill 体系
- 内聚评分: 0-100，高内聚 = 好

### 依赖
- 无前置 Skill（但建议先运行 architecture-assessment 了解整体架构）

### 边界
- 不修改 Agent/Skill 定义
- 只评估结构，不评估执行质量

### 产出物
- 文件路径: `governance/artifacts/reviews/{{module}}/COHESION_REVIEW-{{date}}.md`

---

## Prompt 模板

```text
你是一个软件架构师，专精于组件内聚性分析和模块化设计。

## 系统定义

### Agent 体系
{{AGENT_DEFINITIONS}}

### Skill 体系
{{SKILL_REGISTRIES}}

### 模块划分
{{MODULE_LIST}}

## 任务

### 1. Agent 内聚性分析
对每个 Agent，评估其 skills 的内聚程度：
- 所有 skills 是否围绕一个清晰的职责？
- 是否存在"万能 Agent"（skills 跨越多个不相关领域）？
- 是否存在"侏儒 Agent"（只有 1-2 个 skills，可合并）？

### 2. Skill 归属合理性
- 每个 Skill 的 category 是否合理？
- 是否有跨 category 放置的 Skill？
- 不同 category 的 Skill 是否有重复功能？

### 3. 模块内聚性
- 每个业务模块（tank/equipment/warehouse等）的页面是否业务相关？
- 是否有跨模块的页面应该拆分？
- 是否有孤立的页面应该合并？

### 4. 职责重叠检测
- 哪些 Agent 对共享相同的触发关键词？
- 哪些 Skill 的输入/输出高度重叠？
- Test SOP Agent 与 Dev SOP Agent 的重叠度？

### 5. 职责真空检测  
- 哪些 phase 没有专职 Agent？
- 哪些治理维度没有被任何 Skill 覆盖？
- 是否有 common utility 应该在多个 Agent 间共享但没有？

## 输出格式

```markdown
# Component Cohesion Review — {{MODULE_OR_SYSTEM}}

## Executive Summary
**Overall Cohesion Score:** {{SCORE}}/100
**Overlaps Detected:** {{N}} | **Vacuums:** {{N}} | **Split Suggestions:** {{N}} | **Merge Suggestions:** {{N}}

## Agent Cohesion Scores

| Agent | Skill Count | Cohesion Score | Issue |
|-------|-------------|----------------|-------|
| ... | N | xx/100 | too broad / too narrow / well-scoped |

## Skill Attribution Assessment

| Skill | Current Category | Suggested Category | Rationale |
|-------|-----------------|-------------------|-----------|
| ... | ... | ... | ... |

## Responsibility Overlap Matrix

| Agent A | Agent B | Overlap Type | Shared Skills/Keywords |
|---------|---------|-------------|----------------------|
| requirement-agent | req-agent | functional | requirements, 需求分析 |

## Split/Merge Recommendations

### Split
| Agent | Issue | Suggested Split |
|-------|-------|----------------|
| ... | too many unrelated skills | Agent-A (skills X,Y) + Agent-B (skills Z,W) |

### Merge
| Agents | Issue | Suggested Merge |
|--------|-------|----------------|
| ... | too few skills, overlap | Merged-Agent (all skills) |
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | review | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->