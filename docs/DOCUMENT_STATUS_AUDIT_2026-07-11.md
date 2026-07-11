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
| Plugin | 完整机制完成 | Skill/CLI/API 初版注册与加载；权限白名单、路径防护、受信任根 Ed25519 签名校验、独立 Sandbox Runner 已加入 | 基础进程隔离 Runner 与 6 项新增回归通过；OS 级资源隔离和 Provider RPC 仍待完善 |
| Worker Lease / Billing | 待实现 | 租约、心跳、Worker REST、远程注册/心跳、HMAC Token、任务领取/完成归属与 Billing REST 已实现 | 全量 SQLite 回归通过；生产调度、多租户任务隔离和计费治理未完成 |
| CLI v2 | 核心 CLI 完成 | `mcp/plugin/env/secret` 命令组已覆盖发现、创建、安装、删除、轮换等本地操作 | Secret/Environment/Plugin 扩展命令已补齐；远程安装与企业权限未完成 |
| Studio IA | 路由和导航已实施 | 新目录、Sidebar、真实全局资源页面已建立 | 全局 Runs、Evaluations、Registry MVP 已完成 |
| Global Runs | 使用 GlobalRunsView | `/runs` 使用真实列表、筛选与详情跳转页 | 已完成 |
| Evaluations | 使用 EvaluationsView | `/evaluations` 使用 Evaluation / Dataset API | 已完成 |
| Registry | 使用 RegistryView | `/registry` 使用聚合 Registry API | 已完成 |
| Build / Workflow Builder | BuildView/WorkflowBuilder | `BuildView` 支持 Draft 创建、校验、发布、节点添加/移除、线性连线保存 | 可用节点编辑 MVP 已完成；自由拖拽图形画布仍可后续增强 |
| 生产就绪 | Milestone 5 100% | Worker、Billing、远程 Worker、企业权限仍未完成 | 不应标为生产就绪 |

## 已确认的文档矛盾

### Plugin 状态矛盾

`docs/MASTER_ROADMAP.md` 一处写 Plugin Skill/CLI/API 已完成，后文仍写三个集成点“代码待实现”。统一口径应为：

> Plugin Skill/CLI/API 初版集成、权限白名单、路径防护、受信任根签名校验和 Sandbox Runner 已实现；OS 级强制隔离及 Provider RPC 仍未完成。

### Studio 路由矛盾

`docs/STUDIO_IA_REDESIGN.md` 描述的目标路由已完成 MVP 接线：

```text
/runs -> GlobalRunsView
/evaluations -> EvaluationsView
/registry -> RegistryView
/projects/:id/build -> BuildView
```

因此 Studio 当前状态为：

> IA 导航、三张全局资源页与可保存节点编辑器已完成；自由拖拽图形画布仍是后续增强项。

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
- 完整 `aitest/tests` SQLite 回归：`1470 passed, 4 skipped, 1 warning`
- 修复数据库 auto 模式仅探测 5432 端口的问题：PostgreSQL 认证失败时现在自动回退 SQLite
- 启动排查发现 PATH 中的 `aitest` 指向 `C:\Users\17356\AppData\Roaming\Python\Python312\Scripts\aitest.exe`；项目应使用 `D:\Desktop\Alice\.venv\Scripts\aitest.exe server start`
- 本轮最终合并 pytest 受本机执行额度限制未能再次运行；以上分项测试均在修改后执行并通过
- 当前工作区仍有未提交的 View 删除、新目录 View、后端 API 和执行器改动

## 当前唯一推荐状态口径

```text
Engine：核心执行能力可用
Platform：核心资源和 API 大量已实现
CLI：核心资源命令与外部资源发现/只读管理已实现
Studio：导航重组、三张全局资源页与 Builder MVP 已完成
Workflow：后端执行器与可保存节点编辑 MVP 完成，自由图形画布待增强
Plugin：初版集成与 Sandbox Runner 完成，OS 级强制隔离和 Provider RPC 待完善
MVP：接近完成，但不能称生产就绪
Enterprise：尚未完成
```

## 后续文档治理规则

1. 历史会话总结保留，不作为当前架构真相。
2. 当前状态只在本报告和后续单一 Roadmap 中维护。
3. “完成”必须同时给出代码路径、接线路径和测试证据。
4. 没有可运行测试证据时，最多标记为“代码存在”或“待验证”。
5. 生产就绪必须单独满足安全、迁移、部署、故障恢复和运维验收。
