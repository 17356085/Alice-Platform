# 文档状态校验报告

> 校验日期：2026-07-11  
> 校验范围：2026-07-09、2026-07-10、2026-07-11 期间生成或更新的文档，以及对应当前代码  
> 目的：区分设计、实现、接线、测试和生产可用状态，不覆盖历史文档

## 状态定义

| 状态 | 含义 |
|---|---|
| 设计完成 | 方案和接口已经写出，但不代表代码存在 |
| 代码存在 | 至少有对应实现文件或数据结构 |
| 接线完成 | 已被 API、CLI、Studio 或 Runtime 主链路调用 |
| 测试通过 | 有可执行测试证据；仅有测试文件不算通过 |
| MVP 可用 | 主要用户路径可完成，仍可能缺少企业能力 |
| 生产可用 | 有安全、故障、迁移、部署和运维证据 |

## 校验结果

| 能力 | 文档原口径 | 当前校验口径 | 结论 |
|---|---|---|---|
| Workflow 执行器 | 实现完成 | Executor、HITL、Parallel 代码存在 | 基础执行能力已实现 |
| Parallel Node | 部分文档仍写占位 | 当前代码已有线程池和 LangGraph `Send()` 路径 | 旧设计文档已过期 |
| HITL | 已完成 | Gate 持久化、REST、WebSocket、Studio Panel 存在 | 代码接线完成；受影响回归测试通过 |
| Environment | 设计完成/资源化完成 | Store、Model、REST、迁移文件存在；默认环境已按组织隔离 | 实现与测试已补齐；定向测试通过 |
| Secret Manager | 设计完成/资源化完成 | Store、加密、REST、迁移文件存在 | 本地实现存在，云端 Provider 仍是占位 |
| MCP | 资源化完成 | Store、Manager、`/api/v1/mcp-servers` CRUD/生命周期路由存在 | 本地资源 API 完成；17 项 Store/Manager 测试通过 |
| Plugin | 完整机制完成 | Skill/CLI/API 初版注册与加载；权限白名单、路径防护、Ed25519 签名、独立 Runner、Provider RPC 和资源策略已加入 | Provider RPC/资源策略回归通过；真正 OS 沙箱仍需部署 wrapper（严格模式 fail-closed） |
| Worker Lease / Billing | 待实现 | 租约、心跳、HMAC Token、按组织原子领取、中央 dispatch、断线恢复、mTLS 配置校验、Billing 价格/账期/发票/支付凭证/对账已实现 | 本地与 SQLite 回归通过；真实 mTLS 握手、生产多副本调度和支付厂商接入仍需部署条件 |
| CLI v2 | 核心 CLI 完成 | `mcp/plugin/env/secret` 命令组已覆盖发现、创建、安装、删除、轮换等本地操作 | Secret/Environment/Plugin 扩展命令已补齐；远程安装与企业权限未完成 |
| Studio IA | 路由和导航已实施 | 新目录、Sidebar、真实全局资源页面已建立 | 全局 Runs、Evaluations、Registry MVP 已完成 |
| Global Runs | 使用 GlobalRunsView | `/runs` 使用真实列表、筛选与详情跳转页 | 已完成 |
| Evaluations | 使用 EvaluationsView | `/evaluations` 使用 Evaluation / Dataset API | 已完成 |
| Registry | 使用 RegistryView | `/registry` 使用聚合 Registry API | 已完成 |
| Build / Workflow Builder | BuildView/WorkflowBuilder | `BuildView` 支持 Draft 创建、校验、发布、节点增删、拖拽布局、任意连线/条件和 debug 一步；后端支持分支、并行和断点运行态 | Workflow 高级 MVP 已接线；生产级可视化连线渲染、HITL 调试控制台仍可增强 |
| 生产就绪 | Milestone 5 100% | 生产 Compose、Prometheus、PG/Redis 备份恢复脚本和 Preflight 已提供 | 仍需真实环境执行部署、监控告警和恢复演练，不应标为生产就绪 |

## 已确认的文档矛盾

### Plugin 状态矛盾

`docs/MASTER_ROADMAP.md` 一处写 Plugin Skill/CLI/API 已完成，后文仍写三个集成点“代码待实现”。统一口径应为：

> Plugin Skill/CLI/API 初版集成、权限白名单、路径防护、受信任根签名校验、Sandbox Runner 和 Provider RPC 已实现；OS 级强制隔离需配置并验收部署 wrapper，严格模式会在缺失时拒绝启动。

### Studio 路由矛盾

`docs/STUDIO_IA_REDESIGN.md` 描述的目标路由已完成 MVP 接线：

```text
/runs -> GlobalRunsView
/evaluations -> EvaluationsView
/registry -> RegistryView
/projects/:id/build -> BuildView
```

因此 Studio 当前状态为：

> IA 导航、三张全局资源页与可保存拖拽画布、任意连线/条件、调试一步入口 MVP 已完成；生产级连线渲染与调试控制台仍是后续增强项。

### CLI 命令矛盾

CLI 设计文档列出 `mcp`、`plugin`、`env`、`secret` 命令；当前已提供命令组。CLI 应标记为：

> 核心资源命令、发现、创建、安装、删除和 Secret 轮换已实现；远程安装、权限治理和企业审计仍未完成。

## 验证证据

- `aitest/web`: `npm run typecheck` 通过
- `git diff --check` 通过
- SQLite 受影响回归：`77 passed, 1 skipped`（HITL、Parallel、Plugin、Worker Lease、Billing、Run Executor）；唯一跳过项为显式标记的外部 Provider 集成测试
- Worker ORM 已修复 Declarative `metadata` 保留名和 PostgreSQL `JSONB` 对 SQLite 的不兼容；共享 ORM 模型也已采用跨方言 JSON 类型
- Studio 全局资源 API：4 项测试通过；MCP Store/Manager：17 项通过、1 项显式跳过；外部资源 CLI：2 项通过
- Environment、Plugin 安全、远程 Worker API、数据库回退、MCP 与全局 API 定向测试：`29 passed, 1 skipped`
- 后端 `.venv` 导入检查通过，`/health` TestClient 返回 HTTP 200（整体状态为 degraded，Redis 未连接属于可选基础设施状态）
- Plugin Sandbox、Worker Token/任务领取新增测试：`6 passed`
- Worker 高级定向回归：`43 passed, 1 warning`；包含原子领取契约、调度、mTLS 校验、断线恢复和远程 API
- Plugin Sandbox/Provider RPC：`6 passed`
- Billing/部署/恢复定向回归：`20 passed, 1 warning`
- Workflow 分支/任意连线/并行/debug 回归：`15 passed`
- 完整 `aitest/tests` SQLite 回归：`1495 passed, 4 skipped, 1 warning`
- Worker 高级回归：`43 passed, 1 warning`；RBAC/控制面审计回归：`42 passed`；配额/Billing/Workspace 回归：`29 passed`；Billing/部署/恢复回归：`20 passed, 1 warning`；Workflow 回归：`15 passed`
- 已修复 MCP Registry 默认 Store 的 SQLite 连接生命周期；未屏蔽 warning 复核后，原 `ResourceWarning` 已消失，剩余为 FastAPI/Starlette TestClient 与依赖弃用提示
- 修复数据库 auto 模式仅探测 5432 端口的问题：PostgreSQL 认证失败时现在自动回退 SQLite
- 启动排查发现 PATH 中的 `aitest` 指向 `C:\Users\17356\AppData\Roaming\Python\Python312\Scripts\aitest.exe`；项目应使用 `D:\Desktop\Alice\.venv\Scripts\aitest.exe server start`
- 最终合并 pytest 已在项目 `.venv`、SQLite 模式下运行并通过：`1495 passed, 4 skipped, 1 warning`
- 当前工作区仍有未提交的前端 Builder、后端 API、执行器、部署和治理改动

## 当前唯一推荐状态口径

```text
Engine：核心执行能力可用
Platform：核心资源和 API 大量已实现
CLI：核心资源命令与外部资源发现/只读管理已实现
Studio：导航重组、三张全局资源页与 Builder MVP 已完成
Workflow：后端分支/并行/任意连线/debug runtime 与 Builder MVP 完成，生产级调试控制台待增强
Plugin：初版集成、Sandbox Runner、Provider RPC 和严格隔离入口完成，真实 OS wrapper 部署验收待完成
Governance：全局 strict RBAC 基线、组织/Workspace scope、哈希链审计/归档、Preflight、PG/Redis 生产基线、备份恢复脚本和配额阻断基础完成，真实环境演练待完成
MVP：接近完成，但不能称生产就绪
Enterprise：尚未完成
```

## 后续文档治理规则

1. 历史会话总结保留，不作为当前架构真相。
2. 当前状态只在本报告和后续单一 Roadmap 中维护。
3. “完成”必须同时给出代码路径、接线路径和测试证据。
4. 没有可运行测试证据时，最多标记为“代码存在”或“待验证”。
5. 生产就绪必须单独满足安全、迁移、部署、故障恢复和运维验收。
