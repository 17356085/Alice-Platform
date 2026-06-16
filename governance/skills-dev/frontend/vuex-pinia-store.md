# Skill: frontend/vuex-pinia-store

### 目标
生成 Pinia store 代码：state、getters、async actions，类型安全。

### 输入
- `DATA_FLOW.md`
- `API_CONTRACTS.md`

### 输出
- `src/stores/*.ts`

### 规则
- `defineStore` + Composition API style
- Actions 必须 `async`
- Getters 用于计算状态
- 类型注解完整

---

## Prompt 模板

```text
生成 Pinia store。

## API 端点
{{API_ENDPOINTS}}

## 数据流
{{DATA_FLOW}}

## 输出
```typescript
import { defineStore } from 'pinia'
export const useXxxStore = defineStore('xxx', () => {
  const items = ref<Item[]>([])
  const loading = ref(false)
  async function fetchItems() { ... }
  return { items, loading, fetchItems }
})
```
```
