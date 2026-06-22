# Skill: review/security-posture

### 目标
评估系统安全态势：认证授权、密钥管理、数据保护、依赖漏洞。输出风险评分和漏洞清单。

### 输入
- `.env` 文件存在性检查（不读取内容）
- `.gitignore` 检查
- `requirements.txt` / `package.json` — 依赖版本
- 代码库中的认证/授权实现
- Agent 权限边界定义

### 输出
- `SECURITY_REVIEW.md`：安全评分、漏洞清单（按 CVSS 思路分级）、修复建议

### 规则
- 评估维度：
  1. **密钥管理** — API Key 是否在 .env、是否进 git、是否有轮换机制
  2. **依赖安全** — 是否有已知 CVE 的依赖版本
  3. **最小权限** — Agent 是否能访问不必要的数据/API
  4. **输入验证** — 用户输入是否经过验证和清理
  5. **数据保护** — 敏感数据（trace log 中的 API 响应）是否有脱敏
- 漏洞分级: Critical / High / Medium / Low (参考 CVSS)

### 依赖
- 需要访问项目配置文件
- 建议先运行 production-readiness（安全是其子维度）

### 边界
- 不执行渗透测试
- 不修改安全配置
- 不读取 .env 文件内容（只检查是否存在）

### 产出物
- 文件路径: `governance/artifacts/reviews/{{module}}/SECURITY_REVIEW-{{date}}.md`

---

## Prompt 模板

```text
你是一个应用安全专家。

## 系统信息

### 密钥管理方式
{{KEY_MANAGEMENT}}

### 依赖清单
```
{{DEPENDENCIES}}
```

### Agent 权限边界
{{AGENT_BOUNDARIES}}

### 数据处理流程
{{DATA_FLOW_DESCRIPTION}}

## 任务

### 1. 密钥管理审计
- API Key 存储位置和访问控制
- 是否在 .gitignore 中
- 是否有硬编码密钥

### 2. 依赖漏洞扫描
- 检查已知的 CVE
- 评估依赖版本是否过时

### 3. 最小权限评估
- 每个 Agent 是否只能访问必需的资源
- 是否有 Agent 有过度权限

### 4. 输入验证
- 用户输入（chat.html / CLI / API）是否有验证
- 是否存在注入风险

### 5. 数据保护
- trace log 中的 API 响应是否可能包含敏感数据
- 事件数据是否可能泄露信息

## 输出格式

```markdown
# Security Posture Review — {{MODULE_OR_SYSTEM}}

## Executive Summary
**Security Score:** {{SCORE}}/100
**Critical Vulnerabilities:** {{N}} | **High:** {{N}} | **Medium:** {{N}} | **Low:** {{N}}

## Vulnerability Inventory

### Critical

| ID | Category | Description | Affected Component | Fix |
|----|----------|-------------|-------------------|-----|
| S01 | ... | ... | ... | ... |

### High / Medium / Low
...

## Security Dimension Scores

| Dimension | Score | Assessment |
|-----------|-------|------------|
| Key Management | xx/100 | ... |
| Dependency Security | xx/100 | ... |
| Least Privilege | xx/100 | ... |
| Input Validation | xx/100 | ... |
| Data Protection | xx/100 | ... |

## Recommendations

| Priority | Action | Effort |
|----------|--------|--------|
| P0 | ... | S/M/L |
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | review | synced 2026-06-18 10:54

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->