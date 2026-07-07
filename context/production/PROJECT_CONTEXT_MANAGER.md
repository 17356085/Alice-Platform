# Module Context: production

## Overview
- **Module Name:** production
- **Base Path:** `./src/modules/production/`
- **Entry Point:** `./src/modules/production/index.tsx`

## Routes (From `./src/modules/production/routes.tsx`)

| Path Pattern           | Component                | Page Name              | Is Default |
|------------------------|--------------------------|------------------------|------------|
| `/production`          | `ProductionOrderList`    | 生产工单列表           | Yes        |
| `/production/:orderId` | `ProductionOrderDetail`  | 生产工单详情           | No         |

## Components

| Component Name           | File Path                                                      | Use Case                      |
|--------------------------|----------------------------------------------------------------|-------------------------------|
| `ProductionLineStatus`   | `./src/modules/production/components/ProductionLineStatus.tsx` | 显示产线实时状态（占用、空闲） |

## API Endpoints (From `./src/modules/production/api/endpoints.ts`)

| HTTP Method | Endpoint                      | Description          |
|-------------|-------------------------------|----------------------|
| `GET`       | `/api/production/orders`      | 获取工单列表         |
| `GET`       | `/api/production/orders/:id`  | 获取指定工单详情     |
| `POST`      | `/api/production/orders`      | 创建新工单           |
| `PUT`       | `/api/production/orders/:id`  | 更新工单状态         |
| `GET`       | `/api/production/lines`       | 获取产线列表与状态   |

## Global State Usage
*(根据代码扫描发现)*

- **Context Used:** `useAuth()` (来自 `auth` 模块)
- **Purpose:** 获取当前用户角色以判断是否有权限创建/编辑工单

---

#### 2. PAGE_CONTEXT.md