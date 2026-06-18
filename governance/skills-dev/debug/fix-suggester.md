# Skill: debug/fix-suggester

### 目标
基于 ERROR_DIAGNOSIS.md 或 STACK_ANALYSIS.md，生成具体的代码修复方案，输出 FIX_PROPOSAL.md。

### 输入
- `ERROR_DIAGNOSIS.md` 或 `STACK_ANALYSIS.md`
- 相关源文件内容
- 编码规范（CODING_STANDARDS.md）

### 输出
- `FIX_PROPOSAL.md`：含 before/after 代码 diff、修复理由、影响评估

### 规则
- 最小改动原则——只修改必要的代码
- 修复不能引入新的 lint/type 错误
- 每处修复标注：位置(文件:行号)、修改类型(添加/删除/修改)、理由
- 如有多处修复，标注依赖关系（修复 B 依赖修复 A 先完成）

### 依赖
- debug/error-locator 或 debug/stack-trace-analyzer（至少一个）

### 边界
- 不直接修改文件（只建议修复方案）
- 方案需要人工确认后执行
- 不引入新功能（只修复 bug）

---

## Prompt 模板

```text
你是一个资深调试专家。基于错误诊断，提出具体的代码修复方案。

## 错误诊断
{{ERROR_DIAGNOSIS}}

## 源文件内容
```typescript
{{SOURCE_FILE_CONTENT}}
```

## 编码规范
{{CODING_STANDARDS}}

## 修复原则
1. 最小改动
2. 不能引入新错误
3. 每处修复有明确理由

## 输出
```markdown
# 修复方案

## 修复 1: {{FIX_TITLE}}
- 文件: {{FILE}}:{{LINE}}
- 类型: 添加/删除/修改
- 理由: {{RATIONALE}}

### Before
` ` `diff
- old code
` ` `

### After
` ` `diff
+ new code
` ` `

## 修复依赖
fix-1 → (无) → fix-2 → fix-3

## 影响评估
- 风险: 低/中/高
- 影响文件: N 个
- 回归风险: ...
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | debug | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->