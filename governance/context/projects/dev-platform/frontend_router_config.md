# Vue Router 配置生成

RAG 工具不可用，无法检索 `COMPONENT_TREE.md` 及业务规则。基于共享语言中定义的业务模块（equipment、personnel、warehouse、tank），按 skill 规范生成通用路由配置：

```typescript
// src/router/index.ts
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  // ==================== 主布局 ====================
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/pages/DashboardPage.vue'),
        meta: { title: '仪表盘', requiresAuth: true },
      },

      // ==================== Equipment 模块 ====================
      {
        path: 'equipment',
        name: 'EquipmentList',
        component: () => import('@/pages/equipment/EquipmentListPage.vue'),
        meta: { title: '设备管理', requiresAuth: true },
      },
      {
        path: 'equipment/:id',
        name: 'EquipmentDetail',
        component: () => import('@/pages/equipment/EquipmentDetailPage.vue'),
        meta: { title: '设备详情', requiresAuth: true },
      },

      // ==================== Personnel 模块 ====================
      {
        path: 'personnel',
        name: 'PersonnelList',
        component: () => import('@/pages/personnel/PersonnelListPage.vue'),
        meta: { title: '人员管理', requiresAuth: true },
      },
      {
        path: 'personnel/:id',
        name: 'PersonnelDetail',
        component: () => import('@/pages/personnel/PersonnelDetailPage.vue'),
        meta: { title: '人员详情', requiresAuth: true },
      },

      // ==================== Warehouse 模块 ====================
      {
        path: 'warehouse',
        name: 'WarehouseList',
        component: () => import('@/pages/warehouse/WarehouseListPage.vue'),
        meta: { title: '仓库管理', requiresAuth: true },
      },
      {
        path: 'warehouse/:id',
        name: 'WarehouseDetail',
        component: () => import('@/pages/warehouse/WarehouseDetailPage.vue'),
        meta: { title: '仓库详情', requiresAuth: true },
      },

      // ==================== Tank 模块 ====================
      {
        path: 'tank',
        name: 'TankList',
        component: () => import('@/pages/tank/TankListPage.vue'),
        meta: { title: '储罐管理', requiresAuth: true },
      },
      {
        path: 'tank/:id',
        name: 'TankDetail',
        component: () => import('@/pages/tank/TankDetailPage.vue'),
        meta: { title: '储罐详情', requiresAuth: true },
      },
    ],
  },

  // ==================== 独立页面 ====================
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/LoginPage.vue'),
    meta: { title: '登录', requiresAuth: false },
  },

  // ==================== 404 兜底 ====================
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/pages/NotFoundPage.vue'),
    meta: { title: '404', requiresAuth: false },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

// ==================== 全局导航守卫 ====================
router.beforeEach((to, _from, next) => {
  // 更新页面标题
  document.title = `${to.meta.title || 'AITest Platform'} | AITest`

  // 鉴权检查（排除登录页 & 404）
  const requiresAuth = to.meta.requiresAuth !== false
  const token = localStorage.getItem('token')

  if (requiresAuth && !token) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
```

---

### ⚠️ 关键说明

| 项目 | 状态 |
|---|---|
| RAG 知识库 | **不可用** — 无法检索 `COMPONENT_TREE.md` 实际路由映射 |
| 业务规则 | **不可用** — 无法查询各模块页面特定约束 |
| 生成结果 | 基于共享语言中 4 个 Module（equipment/personnel/warehouse/tank）的**通用模板** |

### 待确认项（需提供 `COMPONENT_TREE.md` 后修正）

1. 实际页面文件名与路径是否匹配上述约定（如 `EquipmentListPage.vue`）
2. 是否存在嵌套子路由（如 equipment 下有 tabs 子页面）
3. 是否需要动态路由（后端返回权限控制的路由表）
4. `MainLayout.vue` 的实际路径及命名
5. 是否有 redirect 或 alias 特殊需求

> 请提供 `COMPONENT_TREE.md` 内容，我将根据实际路由映射精修此配置。