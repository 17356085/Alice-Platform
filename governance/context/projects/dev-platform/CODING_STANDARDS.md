# 开发平台 — 编码规范

> 适用于: Vue 3 + TypeScript 前端 / FastAPI + Python 后端
> 开发 Agent 必读，代码生成后自检

---

## 前端规范（Vue 3 + TypeScript）

### 组件结构

```vue
<script setup lang="ts">
// 1. imports
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

// 2. props & emits
interface Props { /* ... */ }
const props = defineProps<Props>()
const emit = defineEmits<{ (e: 'submit', data: FormData): void }>()

// 3. state
const loading = ref(true)
const error = ref('')
const data = ref<Item[]>([])

// 4. methods
async function fetchData() { /* ... */ }

// 5. lifecycle
onMounted(() => fetchData())
</script>

<template>
  <div class="component-name">
    <el-skeleton v-if="loading" />
    <el-result v-else-if="error" icon="error" />
    <el-empty v-else-if="!data.length" />
    <template v-else>
      <!-- 正常渲染 -->
    </template>
  </div>
</template>

<style scoped>
.component-name { /* 局部样式 */ }
</style>
```

### 8 条红线

| # | ❌ 禁止 | ✅ 必须 |
|---|---------|--------|
| 1 | Options API (`defineComponent`) | `<script setup lang="ts">` |
| 2 | `any` 类型 | 完整类型注解 |
| 3 | 无 scoped 样式 | `<style scoped>` |
| 4 | `console.log()` | `useLogger()` 或移除 |
| 5 | 内联 interface | `types/` 目录导入 |
| 6 | 硬编码 API URL | 环境变量 `import.meta.env.VITE_API_BASE_URL` |
| 7 | sync 数据处理 | `async/await` |
| 8 | Props 直接修改 | `emit` 事件通知父组件 |

---

## 后端规范（FastAPI + SQLAlchemy 2.0）

### Router 结构

```python
from fastapi import APIRouter, Depends, HTTPException, Query

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """List users with pagination."""
    ...
```

### 8 条红线

| # | ❌ 禁止 | ✅ 必须 |
|---|---------|--------|
| 1 | `def` 同步端点 | `async def` |
| 2 | Pydantic v1 `class Config` | `model_config = ConfigDict(from_attributes=True)` |
| 3 | `print()` | `logger.info()` / `logger.warning()` |
| 4 | `Column()` (SQLAlchemy 1.x) | `mapped_column()` (2.0) |
| 5 | 无 docstring | 每个端点有 docstring |
| 6 | `Any` 类型 | 具体类型注解 |
| 7 | 吞异常 (`except: pass`) | `HTTPException` 显式抛出 |
| 8 | 硬编码配置 | `settings.DATABASE_URL` 等 |

### 自检命令

```bash
# 后端
grep -rn "def " app/routers/ | grep -v "async def"  # 检查同步端点
grep -rn "class Config:" app/schemas/                  # 检查 Pydantic v1
grep -rn "print(" app/                                  # 检查 print 调试
grep -rn "Column(" app/models/                           # 检查 SQLAlchemy 1.x

# 前端
grep -rn "defineComponent" src/                          # 检查 Options API
grep -rn ": any" src/                                    # 检查 any 类型
grep -rn "console\.\(log\|warn\)" src/                   # 检查 console
```
