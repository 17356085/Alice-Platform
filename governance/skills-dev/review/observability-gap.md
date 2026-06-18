# Skill: review/observability-gap

### 目标
评估系统可观测性覆盖：日志完整性、指标暴露、追踪链路、告警配置。输出观测盲区清单和补全建议。

### 输入
- Trace log (`governance/.traces/trace_log.jsonl`)
- 错误日志 (如有)
- `aitest/error_logger.py` — 错误记录机制
- `aitest/trace.py` — TraceContext 实现
- `aitest/governance_kpi.py` — KPI 采集机制
- 系统架构文档

### 输出
- `OBSERVABILITY_REVIEW.md`：观测覆盖矩阵、盲区清单、补全建议

### 规则
- 评估维度：
  1. **日志覆盖** — 是否所有关键路径有日志？日志是否结构化？
  2. **指标暴露** — 是否有关键指标（延迟、成功率、Token消耗）？是否有时序数据？
  3. **追踪链路** — 一个请求能否从入口追踪到出口？span 是否完整？
  4. **告警配置** — 是否有关键指标告警？告警阈值是否合理？
  5. **错误追踪** — 错误是否有统一收集？是否能追溯到根因？
- 盲区 = 该有但完全没有观测能力的路径
- 薄弱区 = 有观测但不够（如只有 log 没有 metric）

### 依赖
- 需要 trace_log.jsonl 和错误日志
- 建议先运行 production-readiness（可观测性是其中一个维度）

### 边界
- 不实现观测能力
- 不配置告警
- 只评估当前状态和差距

### 产出物
- 文件路径: `governance/artifacts/reviews/{{module}}/OBSERVABILITY_REVIEW-{{date}}.md`

---

## Prompt 模板

```text
你是一个 SRE 和可观测性专家。

## 系统信息

### 日志机制
{{LOGGING_MECHANISM}}

### Trace 实现
{{TRACE_IMPLEMENTATION}}

### KPI 采集
{{KPI_COLLECTION}}

### 错误处理
{{ERROR_HANDLING}}

## 任务

### 1. 日志覆盖评估
- 关键路径: AgentLoop.run() → run_skill() → LLM call → observe → update
- 每个路径点是否有日志？日志是否包含足够上下文？
- 日志格式是否结构化（JSON）？

### 2. 指标完整性
- 四大黄金信号: Latency / Traffic / Errors / Saturation
- 是否每个都有对应的指标？
- 指标是否有时序存储？

### 3. 追踪链路
- 一个 SOP run 从 entry 到 exit 是否可追踪？
- trace_id 是否贯穿始终？
- 是否有 span 断裂（trace 中间断掉）？

### 4. 告警覆盖
- 是否有关键指标告警？
- 告警阈值是否有依据（baseline）？
- 是否有误报/漏报风险？

### 5. 观测盲区
- 系统中有哪些路径完全无观测？
- 哪些 Agent/Skill 的调用未被追踪？

## 输出格式

```markdown
# Observability Gap Assessment — {{MODULE_OR_SYSTEM}}

## Executive Summary
**Observability Coverage Score:** {{SCORE}}/100
**Blind Spots:** {{N}} | **Weak Spots:** {{N}} | **Well-Covered:** {{N}}

## Coverage Matrix

| Path/Component | Logs | Metrics | Traces | Alerts | Coverage |
|---------------|------|---------|--------|--------|----------|
| AgentLoop.run() | ✅/🟡/❌ | ✅/🟡/❌ | ✅/🟡/❌ | ✅/🟡/❌ | xx% |
| run_skill() | ... | ... | ... | ... | xx% |
| LLM call | ... | ... | ... | ... | xx% |
| observe() | ... | ... | ... | ... | xx% |
| Event emit | ... | ... | ... | ... | xx% |

## Golden Signals Assessment

| Signal | Current | Target | Gap |
|--------|---------|--------|-----|
| Latency | ... | <xx ms | ... |
| Traffic | ... | calls/hour tracked | ... |
| Errors | ... | error rate <x% | ... |
| Saturation | ... | token budget tracked | ... |

## Blind Spots

| Path | Missing | Impact | Priority |
|------|---------|--------|----------|
| ... | no logs at all | can't debug failures | P0 |

## Recommendations

| Priority | Action | Effort |
|----------|--------|--------|
| P0 | Add structured JSON logging to `run_skill()` | S |
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | review | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->