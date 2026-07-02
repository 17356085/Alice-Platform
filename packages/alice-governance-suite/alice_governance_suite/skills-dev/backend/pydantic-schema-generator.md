# Skill: backend/pydantic-schema-generator

### 目标
从 API_CONTRACTS.md 的 Schema 定义生成 Pydantic v2 BaseModel 代码。

### 输入
- `API_CONTRACTS.md` — API 契约中的 Schema 定义
- 数据模型引用（如 DATA_MODEL.md）

### 输出
- `schemas/*.py` — Pydantic v2 BaseModel 类，每个资源一个文件

### 规则
- 使用 Pydantic v2 语法：`model_config = ConfigDict(from_attributes=True)` 用于 ORM 模式
- `field_validator` 用于自定义验证逻辑
- 默认 frozen（不可变）
- Request schema 与 Response schema 分离（不重用）
- 可选字段使用 `Field(default=None)`，必填字段使用 `Field(...)` 或类型注解
- String 字段指定 `min_length` / `max_length`
- Email 字段使用 `EmailStr`（需 pydantic-extra-types）

### 依赖
- architecture/api-contract-designer（API_CONTRACTS.md）

### 边界
- 不定义数据库模型
- 不包含业务逻辑
- Schema 是纯数据定义，无副作用

### 检查清单
- [ ] Create / Update / Response schema 分离
- [ ] `model_config = ConfigDict(from_attributes=True)` 在 Response schema 中
- [ ] 必填/可选字段标注正确
- [ ] 枚举类型使用 `Literal` 或 `Enum`
- [ ] Email 验证使用 `EmailStr`
- [ ] UUID 字段类型为 `UUID`
- [ ] datetime 字段类型为 `datetime`

### 产出物
- `schemas/{{resource}}.py`

---

## Prompt 模板

```text
你是一个资深 Pydantic v2 + FastAPI 后端开发专家。请生成 Pydantic v2 Schema 代码。

⚠️ CRITICAL: 输出纯 Python 代码，包裹在 ```python 代码块中。不要输出解释、分析或文档——只输出代码。

## API 契约 Schema 定义（如为空则从领域知识推导）
```json
{{SCHEMA_DEFINITIONS}}
```

如果上面的 Schema 定义为空或不可用，从 {{module}} 模块的领域术语推导实体并生成 Schema。

## 规则（Pydantic v2 mandatory）
1. 每个 Response schema 必须包含: `model_config = ConfigDict(from_attributes=True)`
2. Request (Create) 与 Response 分离——不允许共用
3. 必填字段: `Field(...)`; 可选字段: `Field(None)` 或 `str | None = None`
4. String: `min_length` / `max_length`; Email: `EmailStr`; 枚举: `Literal["a", "b"]`
5. datetime: `from datetime import datetime`; UUID: `from uuid import UUID`

## 代码模板（严格遵守）
```python
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_extra_types.email import EmailStr
from typing import Literal


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, description="Password (min 8 chars)")
    role: Literal["admin", "user"] = Field("user", description="User role")


class UserUpdate(BaseModel):
    """Schema for updating an existing user. All fields optional."""
    username: str | None = Field(None, min_length=3, max_length=50)
    email: EmailStr | None = None
    role: Literal["admin", "user"] | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    """Schema for user API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

## 输出
只输出 ```python 代码块。不要加任何解释、注释或文档。
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | backend | synced 2026-06-18 10:54

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->