# Backlog 调研报告 — 四项对比

> **日期**: 2026-07-11  
> **目的**: 评估剩余 4 个 backlog 项的现状、缺失和工作量

---

## 1. P8 Parallel 节点（Workflow 并行执行）

### 现状
- **位置**: `aitest/platform/workflow_executor.py:230-242`
- **当前实现**: 占位函数，打印警告后顺序执行
```python
def execute_parallel_node(...):
    logger.warning("Parallel execution not implemented, executing sequentially")
    # TODO: 使用 LangGraph Send() API 实现真正的并行
    return {"success": True, "note": "Parallel execution not implemented"}
```

### 缺失
1. LangGraph `Send()` API 集成（参考 `aitest/graphs/parallel_sop.py` 现有实现）
2. 并行状态聚合（等待所有子节点完成）
3. 错误处理（部分子节点失败的策略）
4. 并发控制（max_concurrency 限制）

### 工作量
- **规模**: 小
- **代码量**: ~100-150 行（主要在 workflow_executor.py）
- **风险**: 低（已有 parallel_sop.py 可参考）
- **依赖**: 无新依赖，仅需 LangGraph API 调用

---

## 2. P6-3 Skill/CLI/API 自动集成（Plugin 系统）

### 现状
- **位置**: `aitest/platform/plugin.py:220-252`
- **当前实现**: Plugin 系统已注册 Skill/CLI/API 到内存字典
```python
self._skills: dict[str, Path] = {}           # 已实现注册
self._cli_commands: dict[str, type] = {}     # 已实现注册
self._api_routes: list[tuple[str, type]] = []  # 已实现注册
```

### 缺失（三个集成点）
1. **Skill 集成**: 
   - Skill Executor 需要从 PluginManager 加载 Plugin Skill
   - 位置: `packages/alice-engine/alice_engine/core/skill_loader.py`
   
2. **CLI 集成**: 
   - CLI 主文件需要动态注册 Plugin 命令
   - 位置: `aitest/cli/main.py` 或 `main_v2.py`
   
3. **API 集成**: 
   - FastAPI 主文件需要动态 include Plugin 路由
   - 位置: `aitest/server/main.py`

### 工作量
- **规模**: 中
- **代码量**: ~200-300 行（3 个集成点，每个 ~70-100 行）
- **风险**: 中（需要协调 3 个不同系统）
- **依赖**: 设计文档已完成（`docs/plugin_system_design.md`）

---

## 3. Worker Lease/Heartbeat API（企业特性）

### 现状
- **位置**: `aitest/platform/execution_worker.py`
- **当前实现**: ExecutionWorker 已实现基础工作池逻辑
```python
class ExecutionWorker:
    def start(self): ...  # 启动 worker
    def stop(self): ...   # 停止 worker
    def stats(self): ...  # 获取统计信息
```

### 缺失
1. **Lease 机制**: Worker 租约（防止重复执行）
   - 数据库表: `worker_leases` (worker_id, lease_id, expires_at)
   - API: `POST /api/v1/workers/:id/lease`, `DELETE /api/v1/workers/:id/lease`
   
2. **Heartbeat 机制**: Worker 心跳（健康检查）
   - 数据库表: `worker_heartbeats` (worker_id, last_heartbeat_at, status)
   - API: `POST /api/v1/workers/:id/heartbeat`

3. **REST API**: Worker 管理端点
   - `GET /api/v1/workers` — 列出 Workers
   - `GET /api/v1/workers/:id` — 获取 Worker 状态
   - `POST /api/v1/workers/:id/stop` — 停止 Worker

### 工作量
- **规模**: 中-大
- **代码量**: ~400-500 行（数据模型 + API + 租约逻辑 + 心跳）
- **风险**: 中-高（分布式系统，租约过期、竞态条件）
- **依赖**: 需要数据库迁移（2 张新表）

---

## 4. Billing REST API（企业特性）

### 现状
- **位置**: `aitest/platform/hooks/billing_hook.py`
- **当前实现**: BillingHookConsumer 已实现事件监听 + JSONL 持久化
```python
class BillingHookConsumer:
    def _on_run_completed(self, event): ...  # 监听 run.completed
    def _on_cost_recorded(self, event): ...  # 监听 cost.recorded
    def query(self, org_id, limit): ...      # 查询 billing 记录（内部方法）
```

### 缺失
1. **REST API**: 计费查询端点
   - `GET /api/v1/billing/usage` — 查询使用量
   - `GET /api/v1/billing/costs` — 查询成本
   - `GET /api/v1/billing/invoices` — 查询账单

2. **数据模型**: 计费资源模型
   - `billing_usage` 表（从 JSONL 迁移到数据库）
   - `billing_invoices` 表（月度账单）

3. **聚合逻辑**: 计费统计
   - 按时间范围聚合（日/周/月）
   - 按 org_id/workspace_id 分组
   - 成本计算（token 使用 × 单价）

### 工作量
- **规模**: 中
- **代码量**: ~300-400 行（API + 数据模型 + 聚合查询）
- **风险**: 低-中（主要是查询逻辑，无复杂状态）
- **依赖**: 需要数据库迁移（2 张新表）

---

## 对比总结

| 项目 | 规模 | 代码量 | 风险 | 依赖 | 推荐优先级 |
|------|------|--------|------|------|----------|
| **P8 Parallel 节点** | 小 | ~100-150 行 | 低 | 无 | ⭐⭐⭐ 最高 |
| **P6-3 Plugin 集成** | 中 | ~200-300 行 | 中 | 设计已完成 | ⭐⭐ 中 |
| **Worker Lease/Heartbeat** | 中-大 | ~400-500 行 | 中-高 | 2 张新表 | ⭐ 低 |
| **Billing REST API** | 中 | ~300-400 行 | 低-中 | 2 张新表 | ⭐ 低 |

---

## 推荐顺序

### 🥇 第一推荐: P8 Parallel 节点
**理由**:
- 风险最小（已有参考实现 `parallel_sop.py`）
- 工作量最小（~100-150 行）
- 无新依赖（仅 LangGraph API）
- 完成 Workflow 执行引擎的最后一块拼图
- **快速胜利**（1-2 天完成）

**关键文件**:
- `aitest/platform/workflow_executor.py` — 主要修改
- `aitest/graphs/parallel_sop.py` — 参考实现

---

### 🥈 第二推荐: P6-3 Plugin 自动集成
**理由**:
- 设计文档已完成（`docs/plugin_system_design.md`）
- Plugin 系统已部分实现（注册逻辑完整）
- 仅需 3 个集成点（Skill/CLI/API）
- 完成 Plugin 系统的完整闭环
- **中等工作量**（2-3 天完成）

**关键文件**:
- `alice_engine/core/skill_loader.py` — Skill 集成
- `aitest/cli/main.py` — CLI 集成
- `aitest/server/main.py` — API 集成

---

### 🥉 第三推荐: Billing REST API
**理由**:
- 风险较低（主要是查询逻辑）
- BillingHookConsumer 已实现数据收集
- 企业特性（可延后）

**不推荐立即实现**: Worker Lease/Heartbeat（风险最高，分布式系统复杂度）

---

## 最终建议

**建议顺序**: P8 → P6-3 → Billing → Worker

**理由**: 先完成低风险、高价值的项目（Parallel 节点），再完成中等复杂度的系统集成（Plugin），最后处理企业特性。

**预计总时间**: 5-7 天（P8 1-2 天 + P6-3 2-3 天 + Billing 2 天）
