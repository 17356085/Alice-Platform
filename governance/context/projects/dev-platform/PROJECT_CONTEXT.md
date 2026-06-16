# 开发平台 — 项目上下文

> 最后更新: 2026-06-14
> 目标: Vue 3 + TypeScript 前端 / FastAPI + SQLAlchemy 2.0 后端

## 项目概述

- **名称**: {{PROJECT_NAME}}
- **类型**: fullstack
- **前端**: Vue 3 + Composition API + TypeScript + Vite + Element Plus + Pinia
- **后端**: FastAPI + SQLAlchemy 2.0 + Pydantic v2
- **数据库**: PostgreSQL (prod) / SQLite (dev)
- **包管理器**: npm (前端) / pip (后端)

## 目录结构

```
{{PROJECT_NAME}}/
├── frontend/               # 前端项目
│   ├── src/
│   │   ├── components/     # 可复用组件
│   │   ├── pages/          # 路由页面
│   │   ├── stores/         # Pinia stores
│   │   ├── router/         # Vue Router 配置
│   │   ├── api/            # API 调用封装
│   │   └── types/          # TypeScript 类型定义
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── backend/                # 后端项目
│   ├── app/
│   │   ├── routers/        # FastAPI APIRouter 模块
│   │   ├── schemas/        # Pydantic v2 Schema
│   │   ├── models/         # SQLAlchemy 2.0 Model
│   │   ├── crud/           # 数据访问层
│   │   └── database.py     # DB 连接 + session
│   ├── tests/              # pytest 测试
│   ├── requirements.txt
│   └── pyproject.toml
└── docs/                   # 架构文档
```

## 关键约束

1. 前端禁止 Options API，统一 Composition API (`<script setup lang="ts">`)
2. TypeScript strict mode，禁止 `any`
3. 后端统一 `async def`，禁止同步端点
4. SQLAlchemy 2.0 风格（`mapped_column()`），禁用 1.x `Column()`
5. Pydantic v2（`ConfigDict`），禁用 v1 `class Config`

## 环境变量

### 前端 (.env)
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 后端 (.env)
```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname
SECRET_KEY=your-secret-key
```
