我注意到工具调用返回了错误信息 "No available provider for 'rag.search'"，说明 RAG 搜索功能当前不可用。不过，根据你的需求，你希望我从 **API_CONTRACTS.md + Pydantic Schema** 生成 FastAPI APIRouter 代码。

但是，我注意到你提供的上下文中有几个关键文件标记为 **不存在**：
1. `CODING_STANDARDS.md` — 不存在
2. `TECH_STACK_REFERENCE.md` — 不存在
3. `API_CONTRACTS.md` — 不存在

此外，你也没有提供具体的：
- `API_CONTRACTS.yaml` 内容
- `schemas/*.py` Pydantic Schema 代码
- `crud/*.py` 函数签名

---

## 请问你能提供以下信息吗？

要生成正确的 Router 代码，我需要你提供：

### 1️⃣ API_CONTRACTS.md 或 YAML 内容
例如：
```yaml
resource: equipment
endpoints:
  - method: GET
    path: /equipment
    summary: List equipment
    auth: true
    pagination: true
  - method: POST
    path: /equipment
    summary: Create equipment
    auth: true
    status: 201
```

### 2️⃣ Pydantic Schemas 代码
例如 `schemas/equipment.py` 的内容

### 3️⃣ CRUD 函数签名
例如 `crud/equipment.py` 的内容

---

如果你已经有这些文件在项目中，请告诉我项目路径，我可以尝试直接读取它们。或者你直接把内容贴给我，我来生成 `routers/equipment.py`。