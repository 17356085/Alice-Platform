# Skill: backend/sqlalchemy-model-generator

### 目标
从 DATA_MODEL.md 或 API Schema 定义生成 SQLAlchemy 2.0 声明式模型代码。

### 输入
- `DATA_MODEL.md` — 实体、字段、关系定义
- `API_CONTRACTS.md` — 了解哪些资源需要持久化

### 输出
- `models/*.py` — SQLAlchemy 2.0 风格模型类

### 规则
- 使用 SQLAlchemy 2.0 风格：`mapped_column()` 而非 `Column()`
- 所有 column 带类型注解（Mapped[...]）
- `relationship()` 使用 `back_populates`
- 基类使用 `DeclarativeBase`
- 时间戳字段用 `server_default=func.now()`
- UUID 主键用 `uuid.UUID` + `server_default=func.gen_random_uuid()`
- 混合属性（`@hybrid_property`）用于计算字段

### 依赖
- backend/pydantic-schema-generator（了解数据结构）
- architecture/api-contract-designer（API_CONTRACTS.md）

### 边界
- 不定义 API 端点
- 不包含业务逻辑
- 模型是纯数据映射，不含 CRUD 函数

### 检查清单
- [ ] 使用 `mapped_column()` 而非 `Column()`
- [ ] 类型注解完整（Mapped[...]）
- [ ] `relationship()` 使用 `back_populates`
- [ ] 主键使用 UUID 或 int
- [ ] 时间戳字段有 server_default
- [ ] 唯一约束使用 UniqueConstraint
- [ ] import 从 sqlalchemy.orm 而非 sqlalchemy

### 产出物
- `models/{{resource}}.py`

---

## Prompt 模板

```text
你是一个资深 SQLAlchemy 2.0 后端开发专家。请从数据模型定义生成 SQLAlchemy 模型代码。

## 数据模型
```yaml
{{DATA_MODEL_YAML}}
```

## 规则
1. SQLAlchemy 2.0 风格：`mapped_column()` 而非 `Column()`
2. 类型注解：`Mapped[str]`、`Mapped[int]`、`Mapped[datetime]`
3. `relationship()` 使用 `back_populates`
4. 基类: `from app.database import Base`（DeclarativeBase）
5. UUID 主键: `Mapped[uuid.UUID]` + `server_default=func.gen_random_uuid()`
6. 时间戳: `Mapped[datetime]` + `server_default=func.now()`
7. 外键: `ForeignKey("table.column")`

## 代码模板
` ` `python
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("email", name="uq_users_email"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid()
    )
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
` ` `

## 输出
只输出完整的 models/{{resource}}.py 内容，包裹在 ```python 代码块中。
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | backend | synced 2026-06-17 16:53

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->