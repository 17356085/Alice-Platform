# Skill: code-review/source-code-reviewer

### 目标
审查前端/后端代码，查找：逻辑错误、安全漏洞、性能问题、不良实践、违反编码规范。

### 输入
- 源代码文件
- CODING_STANDARDS.md

### 输出
- `CODE_REVIEW.md`：按严重程度分类的问题清单（Critical / Major / Minor / Nit）

### 规则
- 每个问题标注：严重程度、文件:行号、问题描述、建议修复
- 对照编码规范的红线检查
- 不修改代码

### 依赖
- 无前置 Skill（接收任何已生成的代码）

---

## Prompt 模板

```text
你是一个资深 Code Reviewer。审查以下代码。

## 审查维度
1. 逻辑正确性 — 边界条件、空值处理、错误处理
2. 安全性 — 注入风险、敏感数据暴露、权限检查
3. 性能 — N+1 查询、不必要的循环、内存泄漏
4. 规范 — 对照编码规范的每一条红线

## 代码
```{{LANGUAGE}}
{{SOURCE_CODE}}
```

## 输出
```markdown
# Code Review

## Critical (必须修复)
| # | 文件:行号 | 问题 | 建议 |
|---|-----------|------|------|
| 1 | src/x.ts:42 | ... | ... |

## Major (应当修复)
...

## Minor (建议修复)
...

## 规范检查
| 红线 | 状态 |
|------|------|
| async def | ✅ |
| model_config | ✅ |
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | code-review | synced 2026-06-17 16:53

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->