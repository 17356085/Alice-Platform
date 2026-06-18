# Skill: frontend/page-implementer

### 目标
组装多个组件生成完整页面，包含数据获取（API 调用）、状态管理（Pinia store 连接）、路由参数处理。

### 输入
- `COMPONENT_TREE.md` — 页面在组件树中的位置
- `API_CONTRACTS.md` — 页面需要调用的 API 端点
- 子组件的 `PROPS_INTERFACE.yaml` — 传递给子组件的数据接口
- Pinia store 定义

### 输出
- `*.vue` 文件（完整页面），包含数据获取逻辑、子组件拼装、路由感知

### 规则
- 数据获取在 `onMounted` 或路由守卫中进行
- 页面级 loading / error 状态必须在页面上管理
- 使用 Pinia store 的 `storeToRefs()` 获取响应式状态
- API 调用封装在 `api/` 模块中，不直接在页面中 fetch
- 路由参数通过 `useRoute()` 获取
- 页面跳转通过 `useRouter()` 进行

### 依赖
- frontend/vue-component-generator（子组件已生成）
- architecture/api-contract-designer（API_CONTRACTS.md）

### 边界
- 不创建新的可复用组件（已由 vue-component-generator 负责）
- 不修改 Pinia store 定义（已由 vuex-pinia-store 负责）
- 页面逻辑应简洁：获取数据 → 传给子组件 → 处理子组件事件

### 检查清单
- [ ] loading / error / empty 状态完整
- [ ] API 调用有 try-catch 错误处理
- [ ] 子组件 Props 传递正确
- [ ] 子组件 Events 处理正确
- [ ] useRoute / useRouter 使用正确
- [ ] `<script setup lang="ts">`
- [ ] ESLint + TypeScript 编译通过

### 产出物
- 文件路径: `src/pages/{{PageName}}.vue`

---

## Prompt 模板

```text
你是一个资深 Vue 3 + TypeScript 前端开发专家。请组装子组件生成完整页面。

## 页面信息
- 页面名称: {{PageName}}
- 路由路径: {{RoutePath}}
- 页面职责: {{PageDescription}}

## 子组件
{{CHILD_COMPONENTS_LIST}}

## API 端点
```yaml
{{PAGE_API_ENDPOINTS}}
```

## Pinia Store
```typescript
{{STORE_DEFINITION}}
```

## 任务
1. 在 `onMounted` 中调用 API 获取数据
2. 将数据通过 Props 传给子组件
3. 处理子组件的 Events（如 select、submit、delete）
4. 实现页面级 loading / error / empty 状态
5. 处理路由参数（如 /users/:id）

## 输出格式
只输出完整的 .vue 文件内容，包裹在 ```vue 代码块中。

## 代码结构
` ` `vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/stores/user'
import { getUsers, deleteUser } from '@/api/users'
// ...子组件 imports

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const { users } = storeToRefs(store)

const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    await store.fetchUsers()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})

// 事件处理
function handleSelect(userId: string) {
  router.push(`/users/${userId}`)
}
</script>

<template>
  <div class="page-container">
    <el-skeleton v-if="loading" :rows="5" animated />
    <el-result v-else-if="error" icon="error" :sub-title="error" />
    <template v-else>
      <!-- 子组件拼装 -->
    </template>
  </div>
</template>

<style scoped>
.page-container { padding: 20px; }
</style>
` ` `
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | frontend | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->