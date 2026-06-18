# Skill: backend/fastapi-router-generator

### 目标
从 API_CONTRACTS.md + Pydantic Schema 生成 FastAPI APIRouter 代码，包含完整的端点函数、依赖注入、错误处理。

### 输入
- `API_CONTRACTS.md` — API 端点契约
- `schemas/*.py` — Pydantic 请求/响应 Schema
- `crud/*.py` — 数据访问层函数签名

### 输出
- `routers/*.py` — FastAPI APIRouter，每个资源一个文件

### 规则
- 所有端点使用 `async def`
- 使用依赖注入获取 DB session（`Depends(get_db)`）
- 使用 HTTPException 处理错误
- 每个端点必须有 docstring（含英文描述 + 参数说明）
- 认证使用 `Depends(get_current_user)` 依赖注入
- 分页/排序/搜索从 Query 参数获取
- 状态码 201 用于 POST 创建

### 依赖
- backend/pydantic-schema-generator（schemas/*.py）
- architecture/api-contract-designer（API_CONTRACTS.md）

### 边界
- 不包含业务逻辑（应在 service 层或 CRUD 中）
- 不定义数据库模型
- Router 函数应简洁：验证输入 → 调用 CRUD → 返回响应

### 检查清单
- [ ] 所有端点 `async def`
- [ ] 每个端点有 docstring
- [ ] 认证依赖注入正确
- [ ] HTTPException 用于错误处理
- [ ] 分页参数使用 Query
- [ ] 类型注解完整
- [ ] import 语句完整（无缺失导入）

### 产出物
- `routers/{{resource}}.py`

---

## Prompt 模板

```text
你是一个资深 FastAPI 后端开发专家。请从 API 契约生成 Router 代码。

## API 契约
```yaml
{{API_CONTRACTS_YAML}}
```

## Pydantic Schemas
```python
{{SCHEMAS_CODE}}
```

## CRUD 函数签名
```python
{{CRUD_SIGNATURES}}
```

## 规则
1. 所有端点 `async def`
2. DB session: `Depends(get_db)`
3. 认证: `Depends(get_current_user)`（标注在需要 auth 的端点）
4. 错误: `HTTPException(status_code=..., detail="...")`
5. 201 状态码用于 POST 创建
6. 每个端点必须有中英文 docstring
7. 类型注解完整，无 any

## 代码模板
` ` `python
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import get_current_user
from app.schemas.{{resource}} import {{Resource}}Create, {{Resource}}Update, {{Resource}}Response
from app.crud.{{resource}} import {{resource}}_crud

router = APIRouter(prefix="/{{resource}}", tags=["{{Resource}}"])


@router.get("/", response_model=PaginatedResponse[{{Resource}}Response])
async def list_{{resource}}(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    q: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """List {{resources}} with pagination, sorting, and search."""
    result = await {{resource}}_crud.paginate(
        db, page=page, page_size=page_size,
        sort_by=sort_by, sort_order=sort_order, q=q,
    )
    return result
` ` `

## 输出
只输出完整的 routers/{{resource}}.py 内容，包裹在 ```python 代码块中。
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | backend | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->