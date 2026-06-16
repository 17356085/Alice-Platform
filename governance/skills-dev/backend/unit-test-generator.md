# Skill: backend/unit-test-generator

### 目标
为后端 router + crud 生成 pytest + httpx 测试，覆盖 CRUD 操作。

### 输入
- `routers/*.py`
- `crud/*.py`
- `schemas/*.py`

### 输出
- `tests/test_<resource>.py`

### 规则
- pytest + pytest-asyncio + httpx.AsyncClient
- 测试 DB (SQLite in-memory)
- fixture: 创建测试数据 → 请求 → 断言 → 清理

---

## Prompt 模板

```text
生成后端 API 测试。

## Router
```python
{{ROUTER_CODE}}
```

## 输出
pytest + httpx 测试文件，覆盖: create(201), list(200), get(200), update, delete(204), not_found(404), validation_error(422)。
```
