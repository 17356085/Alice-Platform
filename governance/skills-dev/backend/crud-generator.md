# Skill: backend/crud-generator

### 目标
基于 SQLAlchemy model + Pydantic schema，生成异步 CRUD 数据访问层。

### 输入
- `models/*.py`
- `schemas/*.py`

### 输出
- `crud/*.py`

### 规则
- 所有函数 `async def`
- paginate: page, page_size, sort_by, sort_order, filters
- create/update 接收 Pydantic schema 并 flush 到 DB

---

## Prompt 模板

```text
生成异步 CRUD 层。

## Model
```python
{{MODEL_CODE}}
```

## Schema
```python
{{SCHEMA_CODE}}
```

## 输出
完整的 crud/*.py，含 paginate, create, get, update, delete。
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | backend | synced 2026-06-17 16:53

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->