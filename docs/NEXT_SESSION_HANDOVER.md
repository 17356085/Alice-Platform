# 平台资源化收尾交接

> 更新：2026-07-11
> 状态：P7-1、P8-2、Studio 全局资源页和 Workflow Builder MVP 已完成。后续只处理生产治理与高级交互增强。

## 已完成

### P7-1 — API 路由资源化

- 13 个 router 已统一迁移至 `/api/v1/`。
- 前端 HTTP、WebSocket 与服务端返回的 URL 已同步。
- `verify_routes.py` 与 OpenAPI smoke check 均通过。

### P2-6 / P7-3 — Studio IA 重组（MVP 完成）

- 全局导航：Projects、Runs、Evaluations、Registry、Settings。
- 项目导航：Overview、Build、Run、Quality、Assets。
- 新层级路由已接入，旧项目 URL 会重定向到对应资源页。
- `views/global/`、`views/project/` 与 `views/cross-cutting/` 提供新的惰性加载入口；`GlobalRunsView`、`EvaluationsView`、`RegistryView` 已通过真实资源 API 工作，`BuildView` 支持 Workflow Draft 创建、校验与发布。
- `npm run typecheck` 通过。

### P8-2 — HITL 节点化

设计已写入 [HITL_NODE_DESIGN.md](design/HITL_NODE_DESIGN.md)，并已实现持久化 Gate、审核 REST API、状态 WebSocket 流、执行器等待/超时以及 Studio 审核面板：

- `pending → resolved/timeout/cancelled` 状态模型与幂等决议。
- REST、WebSocket 补发和动态表单 Schema。
- 数据表、权限、超时、故障恢复与四阶段实施验收。

## 环境与健康修复

- 根 `pyproject.toml` 已声明本地 workspace SDK，`uv sync` 不会再卸载 `alice-engine` 等依赖。
- SQLite 旧 `runs` 表会在创建资源索引前补齐 `target_type` 等字段。
- RAG、session database 健康探针已修正；旧项目 `test_project.base_url` 也会被 ecosystem 识别。
- FastAPI 可导入，OpenAPI 注册关键 v1 HTTP 路由，`/health` 返回 HTTP 200。

## 后续工作（非本轮遗留）

1. **完整 lifespan 验证**：在 CI 中启动 Uvicorn，验证后台 Consumer、Redis 可选依赖与真实项目配置。

HITL 已有自动化集成测试：`aitest/tests/platform/test_human_gates.py`，覆盖阻塞 resolve、超时 fallback 和 WebSocket 状态流。

## 验证命令

```powershell
cd D:\Desktop\Alice\aitest\web
npm run typecheck

cd D:\Desktop\Alice
$env:UV_CACHE_DIR='D:\Desktop\Alice\.tmp\uv-cache'
$env:AITEST_DB_BACKEND='sqlite'
uv run python -c "from aitest.server.main import app; print(len(app.openapi()['paths']))"
```
