# Skill: requirements-dev/data-model-spec

### 目标
从功能需求推导数据模型：实体、字段、类型、关系、索引，生成 DATA_MODEL.md。

### 输入
- `FEATURE_SPEC.md`
- `API_CONTRACTS.md`（如有）

### 输出
- `DATA_MODEL.md`：含 ERD 图（mermaid）、实体定义表

### 规则
- 每个字段标注: 名、类型、必填?、默认值、外键引用
- 关系标注: 1:1 / 1:N / N:N
- 索引建议: 唯一索引、查询索引

---

## Prompt 模板

```text
你是数据库架构师。从以下需求推导数据模型。

## 需求
{{REQUIREMENTS}}

## 输出
```markdown
# 数据模型

## ERD
` ` `mermaid
erDiagram
  User ||--o{ Order : places
` ` `

## 实体定义
### User
| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| id | UUID | ✅ | gen | PK |
| username | str(50) | ✅ | - | unique |
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | requirements-dev | synced 2026-06-17 16:53

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->