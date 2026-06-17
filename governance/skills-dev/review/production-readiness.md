# Skill: review/production-readiness

### 目标
评估系统或模块的生产就绪度：错误处理完整性、可观测性覆盖、回滚能力、SLA 合规性、安全态势。输出就绪度评分和阻断项清单。

### 输入
- 目标模块/系统的最新代码
- 最近的执行日志 (trace_log.jsonl)
- 最近的错误日志
- SOP_STATUS 文件
- 最近的审计报告 (State + SOP + Cost)
- `governance/context/environments.yaml` — 环境配置
- 部署配置（如有）

### 输出
- `PROD_READY.md`：就绪度评分（按维度）、阻断项清单（必须修才能上线）、警告项清单（应该修）、Go/No-Go 建议

### 规则
- 评估维度：
  1. **错误处理** — 异常捕获覆盖率、错误信息质量、降级策略
  2. **可观测性** — 日志完整性、指标暴露、追踪链路、告警配置
  3. **回滚能力** — 数据库迁移可逆性、配置回滚、版本回退路径
  4. **SLA 合规** — 可用性目标、响应时间、错误率阈值
  5. **安全态势** — 密钥管理、认证授权、数据保护、依赖漏洞
  6. **配置管理** — 环境隔离、敏感配置保护、配置变更追踪
  7. **依赖健康** — 外部依赖可用性、API 限流、超时配置
- 阻断项 = 上线前必须修复的问题
- 警告项 = 上线后尽快修复的问题
- Go/No-Go = 基于阻断项数量的上线决策建议

### 依赖
- 依赖最近的审计报告和执行日志
- 建议先运行 State Auditor + SOP Auditor 确保没有已知问题

### 边界
- 不修改代码或配置
- 不执行部署
- 不进行实际的安全渗透测试
- 不修改环境配置

### 检查清单
- [ ] 错误处理评估完成
- [ ] 可观测性评估完成
- [ ] 回滚能力评估完成
- [ ] SLA 合规检查完成
- [ ] 安全态势评估完成
- [ ] 配置管理评估完成
- [ ] 依赖健康检查完成
- [ ] 阻断项清单明确
- [ ] Go/No-Go 建议给出

### 产出物
- 文件路径: `governance/artifacts/reviews/{{module}}/PROD_READY-{{date}}.md`
- 格式: 遵循 `governance/templates/review-report.template.md` 标准结构

---

## Prompt 模板

```text
你是一个 SRE (Site Reliability Engineer) 和安全生产专家，负责评估系统/模块的生产就绪度。

## 评审上下文

### 目标模块/系统
{{MODULE_NAME}}

### 代码路径
{{CODE_PATHS}}

### 最近执行日志（最近 N 条异常）
```
{{RECENT_ERROR_LOGS}}
```

### 最近审计摘要
- State Audit: {{STATE_AUDIT_SUMMARY}}
- SOP Audit: {{SOP_AUDIT_SUMMARY}}
- Cost Audit: {{COST_AUDIT_SUMMARY}}

### 环境配置
```
{{ENVIRONMENT_CONFIG}}
```

### 已知问题
{{KNOWN_ISSUES}}

## 评审任务

### 1. 错误处理 (Error Handling)
- 是否有全局异常捕获？未捕获的异常会导致什么？
- 错误信息是否包含足够上下文（堆栈、输入参数、时间）？
- 是否有优雅降级策略（关键功能失败时系统如何表现）？
- 错误分类是否合理（可恢复 vs 不可恢复）？

### 2. 可观测性 (Observability)
- 日志是否结构化（JSON 格式、统一字段）？
- 是否有关键指标暴露（成功率、延迟、Token 消耗）？
- 追踪链路是否完整（一个请求从入口到出口）？
- 是否有告警规则？告警阈值是否合理？
- 是否存在"监控盲区"（某段代码完全没有日志）？

### 3. 回滚能力 (Rollback)
- 数据库 schema 变更是否可逆？
- 配置文件变更是否有版本控制？
- 代码回滚路径是否清晰（git revert → 重新部署）？
- Prompt 版本变更是否有回滚机制（Regression Gate 的 promote_skill_version）？

### 4. SLA 合规 (SLA Compliance)
- 系统的可用性目标是什么？当前是否达标？
- 关键路径的响应时间是否在 SLA 内？
- Token 消耗是否在预算内？
- 错误率是否在可接受范围内？

### 5. 安全态势 (Security Posture)
- API Key 是否安全存储（.env 文件，不进 git）？
- 是否有输入验证和安全过滤？
- 依赖库是否有已知漏洞？（检查 requirements.txt / package.json 引用的版本）
- 是否有最小权限原则（Agent 是否只能访问必要的资源）？

### 6. 配置管理 (Configuration Management)
- 环境配置是否隔离（dev / staging / prod）？
- 敏感配置是否加密或使用环境变量？
- 配置变更是否有审计追踪？
- 是否有配置漂移检测？

### 7. 依赖健康 (Dependency Health)
- 外部 API (Anthropic / 被测系统) 是否有超时和重试配置？
- 文件系统依赖是否可靠（磁盘空间检查）？
- 数据库 (SQLite) 是否有备份策略？

## 输出格式

```markdown
# Production Readiness Review — {{MODULE}}

---
report_id: REVIEW-{{DATE}}-{{UUID8}}
review_type: production
module: {{MODULE}}
trigger: pre-release
depth: standard
reviewer: review/production-readiness v1.0
created: {{ISO8601}}
---

## Executive Summary

**Overall Readiness Score:** {{SCORE}}/100 ({{GRADE}})
**Go/No-Go:** 🟢 GO / 🟡 CONDITIONAL GO / 🔴 NO-GO
**Blockers:** {{N}}
**Warnings:** {{N}}

## Dimension Scores

| Dimension | Score | Status | Notes |
|-----------|-------|--------|-------|
| Error Handling | xx/100 | ✅/🟡/🔴 | ... |
| Observability | xx/100 | ✅/🟡/🔴 | ... |
| Rollback | xx/100 | ✅/🟡/🔴 | ... |
| SLA Compliance | xx/100 | ✅/🟡/🔴 | ... |
| Security Posture | xx/100 | ✅/🟡/🔴 | ... |
| Configuration Mgmt | xx/100 | ✅/🟡/🔴 | ... |
| Dependency Health | xx/100 | ✅/🟡/🔴 | ... |

## Blockers (must fix before release)

| ID | Dimension | Finding | Impact | Fix |
|----|-----------|---------|--------|-----|
| B01 | ... | ... | ... | ... |

## Warnings (fix after release)

| ID | Dimension | Finding | Impact | Fix |
|----|-----------|---------|--------|-----|

## Go/No-Go Decision

**Decision:** 🟢 GO / 🟡 CONDITIONAL GO / 🔴 NO-GO

**Rationale:** {{RATIONALE}}

**Conditions for Go:**
1. {{CONDITION_1}}
2. {{CONDITION_2}}

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| ... | H/M/L | H/M/L | ... |

## Action Items

| Priority | Action | Before Release? | Effort |
|----------|--------|----------------|--------|
| P0 | ... | Yes | S/M/L |
| P1 | ... | No | S/M/L |
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | review | synced 2026-06-17 16:53

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->