---

### 建模结果

#### 1. 页面列表 (pages 列表)

| Slug (唯一标识) | Path (路由路径) | Component (组件名) | 描述 |
| :--- | :--- | :--- | :--- |
| `tank-home` | `/tank` | `TankDashboard` | 模块主页（可能是布局组件，通常重定向） |
| `tank-overview` | `/tank/` | `TankOverview` | Tank概览仪表盘 |
| `tank-list` | `/tank/list` | `TankList` | Tank列表页 |
| `tank-create` | `/tank/new` | `TankCreate` | 创建Tank页 |
| `tank-detail` | `/tank/:id` | `TankDetail` | Tank详情页 (动态参数) |
| `tank-edit` | `/tank/:id/edit` | `TankEdit` | 编辑Tank页 (动态参数) |
| `tank-history` | `/tank/:id/history` | `TankHistory` | Tank告警/历史记录页 (动态参数) |

#### 2. 路由映射表

| 路由路径 | 对应组件 | 页面层级 |
| :--- | :--- | :--- |
| `/tank` | `TankDashboard` | L0 (模块根节点) |
| `/tank/` | `TankOverview` | L1 (默认首页) |
| `/tank/list` | `TankList` | L1 (列表页) |
| `/tank/new` | `TankCreate` | L1 (新建页) |
| `/tank/:id` | `TankDetail` | L1 (详情页) |
| `/tank/:id/edit` | `TankEdit` | L2 (详情页的子操作) |
| `/tank/:id/history` | `TankHistory` | L2 (详情页的子操作) |

#### 3. 页面层级（页面树）