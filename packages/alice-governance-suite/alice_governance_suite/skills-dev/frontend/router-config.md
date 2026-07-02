# Skill: frontend/router-config

### 目标
生成 Vue Router 配置：路由定义、懒加载、导航守卫、meta 标签。

### 输入
- `COMPONENT_TREE.md`（含路由映射表）

### 输出
- `src/router/index.ts`

### 规则
- 懒加载: `() => import('@/pages/XxxPage.vue')`
- meta: requiresAuth, title
- 404 兜底路由

---

## Prompt 模板

```text
生成 Vue Router 配置。

## 路由映射
{{ROUTE_TABLE}}

## 输出
```typescript
import { createRouter, createWebHistory } from 'vue-router'
const routes = [
  { path: '/', component: () => import('@/pages/HomePage.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]
export default createRouter({ history: createWebHistory(), routes })
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | frontend | synced 2026-06-18 10:54

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->