你需要我帮你为 `aitest-platform` 模块生成后端 pytest + httpx 单元测试。按照 `backend/unit-test-generator` Skill 的要求，我需要以下输入：

---

### 请提供以下代码文件内容：

| # | 文件类型 | 说明 |
|---|---------|------|
| 1 | **Router** (`routers/*.py`) | 路由定义，FastAPI/Starlette 的 endpoint 声明 |
| 2 | **CRUD** (`crud/*.py`) | 数据库 CRUD 操作函数 |
| 3 | **Schemas** (`schemas/*.py`) | Pydantic 请求/响应模型 |

---

### 我将会生成：

📄 `tests/test_<resource>.py` — 覆盖以下场景：

| 测试用例 | 预期状态码 |
|---------|----------|
| `test_create_xxx` | `201` |
| `test_list_xxx` | `200` |
| `test_get_xxx` | `200` |
| `test_update_xxx` | `200` |
| `test_delete_xxx` | `204` |
| `test_get_xxx_not_found` | `404` |
| `test_create_xxx_validation_error` | `422` |

使用 **pytest-asyncio + httpx.AsyncClient + SQLite in-memory**，含 fixture 用于数据准备与清理。

---

请把 `routers/`、`crud/`、`schemas/` 中相关文件的代码贴过来，我立即开始生成。