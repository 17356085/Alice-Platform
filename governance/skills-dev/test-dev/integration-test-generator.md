# Skill: test-dev/integration-test-generator

### 目标
为 API 端点生成集成测试（pytest + httpx + test DB），验证请求→路由→业务逻辑→响应完整链路。

### 输入
- FastAPI router 代码
- Pydantic Schema 定义
- 数据库模型

### 输出
- `tests/integration/test_<resource>.py`

### 规则
- 使用 httpx.AsyncClient + ASGITransport
- 使用测试数据库（SQLite in-memory 或 test PostgreSQL）
- Fixture: 创建测试数据 → 执行请求 → 断言响应 → 清理
- 覆盖: 201 created / 200 list / 200 detail / 404 not found / 422 validation error

### 依赖
- backend/fastapi-router-generator (路由已生成)

---

## Prompt 模板

```text
为以下 API 端点生成集成测试。

## Router 代码
```python
{{ROUTER_CODE}}
```

## Schemas
```python
{{SCHEMA_CODE}}
```

## 输出
完整的 pytest + httpx 集成测试文件。
```
