# 开发平台 — 技术栈参考

> 提供给开发 Agent 的库 API 速查。仅在 Skill 的 context_injector 中注入相关部分。

---

## Vue 3 (Composition API)

```typescript
// defineProps
interface Props { users: User[]; loading: boolean }
const props = defineProps<Props>()

// defineEmits
const emit = defineEmits<{ (e: 'select', id: string): void }>()

// ref / computed
const count = ref(0)
const doubled = computed(() => count.value * 2)
```

## Element Plus 常用组件

```vue
<el-table :data="items" @selection-change="handleSelect">
  <el-table-column prop="name" label="Name" />
</el-table>
<el-form :model="form" :rules="rules" @submit.prevent="handleSubmit">
  <el-form-item label="Username" prop="username">
    <el-input v-model="form.username" />
  </el-form-item>
</el-form>
<el-dialog v-model="visible" title="Edit" width="600px">...</el-dialog>
<el-button type="primary" @click="handleSave">Save</el-button>
<el-skeleton :rows="5" animated />
<el-result icon="error" sub-title="Something went wrong" />
<el-empty description="No data" />
```

## Pinia Store

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getUsers, type User } from '@/api/users'

export const useUserStore = defineStore('user', () => {
  const users = ref<User[]>([])
  const loading = ref(false)

  const activeUsers = computed(() => users.value.filter(u => u.is_active))

  async function fetchUsers() {
    loading.value = true
    try { users.value = await getUsers() }
    finally { loading.value = false }
  }

  return { users, loading, activeUsers, fetchUsers }
})
```

## Vue Router

```typescript
// router/index.ts
const routes = [
  { path: '/', component: () => import('@/pages/HomePage.vue') },
  { path: '/users', component: () => import('@/pages/UserListPage.vue'), meta: { requiresAuth: true } },
]
```

## FastAPI Router

```python
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=PaginatedResponse[UserResponse])
async def list_users(...): ...

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(body: UserCreate, ...): ...
```

## Pydantic v2 Schema

```python
from pydantic import BaseModel, ConfigDict, Field, field_validator

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    username: str
```

## SQLAlchemy 2.0 Model

```python
from sqlalchemy import String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    username: Mapped[str] = mapped_column(String(50))
```

## asyncpg / aiosqlite

```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://..."  # or sqlite+aiosqlite:///...

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

## pytest + httpx

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_list_users(client):
    response = await client.get("/api/v1/users")
    assert response.status_code == 200
```
