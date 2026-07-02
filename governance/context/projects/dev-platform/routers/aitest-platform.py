# FastAPI Router Generator — 无法生成

## 问题诊断

两个关键依赖均不可用：

| 依赖 | 状态 | 说明 |
|-------|--------|------|
| `rag.search` | ❌ No available provider | 无法查询 knowledge base 获取历史契约/schema |
| `rag.business_rules` | ❌ No available provider | 无法获取 Module 的业务规则 |
| `API_CONTRACTS.md` | ❌ 文件不存在 | 项目上下文无 API 端点契约 |
| `schemas/*.py` | ❌ 未提供 | 无 Pydantic Schema 输入 |
| `crud/*.py` | ❌ 未提供 | 无 CRUD 函数签名输入 |

## 阻塞原因

此 Skill 的 Prompt 模板明确规定：

> 如果上面输入为空或不可用，从 {{module}} 模块和已有 schemas/models 推导端点。

但当前会话中：
- **未指定** `module` 参数（无法确定是 `equipment`、`personnel`、`warehouse` 还是 `tank` 等 Module）
- **无** schemas/models 文件可读取
- RAG 检索通道全部不可用

## 需要提供的信息

要生成 `routers/{resource}.py`，请补充以下任一组合：

**方案 A（最小输入）：**
```
请为 module = "equipment" 生成 router
```
（我将从领域知识推导典型的 CRUD 端点和 Pydantic schema）

**方案 B（完整输入）：**
1. `API_CONTRACTS.md` 或 API 端点列表（HTTP 方法 + 路径 + 请求/响应结构）
2. Pydantic Schema 定义（`schemas/{resource}.py`）
3. CRUD 函数签名（`crud/{resource}.py`）

**方案 C（已有代码扫描）：**
如果项目中已有 `models/*.py` 和部分 `schemas/*.py`，请告知路径，我可以读取后推导 router。

---

请补充必要输入，我将立即生成完整的 `async def` Router 代码。