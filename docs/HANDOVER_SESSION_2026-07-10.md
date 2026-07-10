# 阶段2进度交接文档

> **会话结束时间**: 2026-07-10  
> **Token 使用**: 118k/200k (59%)  
> **当前阶段**: 阶段 2 — Run 资源体验（部分完成）

---

## 已完成工作

### ✅ 阶段 0（解除阻塞）— 100% 完成
1. **P0-3**: `PRODUCT_SPEC_V1_ARCHIVED.md` 加 ⚠️ ARCHIVED 标记，指向 PRODUCT.md
2. **P0-1**: `aitest/adapters/llm/interface.py` 补全 5 个 Provider 类 re-export
3. **P0-2**: Studio 23 个 TypeScript 类型错误修复（subagent 完成，tsc 验证通过）

### ✅ 阶段 1（地基统一）— 100% 完成
1. **P1-1**: 更新 `ADR_001_TLO_DIRECTORY.md`，schema 文档与 `context.py::ProjectConfig` 统一
2. **P1-2**: `agent-definitions.yaml` 版本号 2.2 → 2.5（与 main.py 对齐）
3. **P7-2 挪到阶段2**: 属于资源模型重构，不是地基问题

### ✅ 阶段 2（Run 资源体验）— P7-2 Phase 1-2 完成

#### P7-2 Phase 1: 新执行入口
- ✅ 设计文档: `docs/api/POST_api_v1_runs.md`
- ✅ 新端点: `aitest/server/api/runs.py`
  - `POST /api/v1/runs` — 支持 target.type="agent"
  - `GET /api/v1/runs/:id` — 查询 Run 状态
- ✅ 注册到 `main.py`（优先注册）
- ✅ 向后兼容: 内部委托给 ExecutionService

#### P7-2 Phase 2: 数据库扩展
- ✅ **RunModel** (`aitest/infra/models.py`):
  ```python
  target_type = Column(String(32), default="agent", index=True)
  target_id = Column(String(64), default="")
  target_version = Column(String(64), default="latest")
  environment_id = Column(String(64), default="")
  parent_run_id = Column(String(64), default="", index=True)
  ```
- ✅ **Run dataclass** (`aitest/platform/run.py`): 新字段 + 向后兼容注释
- ✅ **RunStore** (`aitest/platform/run_store.py`):
  - `_ensure_runs_resource_fields()` — 自动迁移逻辑
  - `save_run()` SQL 更新（23 个字段）
  - `_row_to_run()` 解析逻辑（fallback: target_id → agent）
- ✅ **SQLite schema** (`create_tables_sqlite.sql`): 新字段 + 3 个索引
- ✅ **Run.to_dict()**: 新字段序列化

**特性**：
- 向后兼容：旧字段保留，新字段有默认值
- 自动迁移：首次启动时自动 ALTER TABLE
- Fallback 逻辑：`target_id` 为空时回退到 `agent`

---

## 待完成工作（下次会话）

### 🔄 阶段 2 剩余任务

#### P7-2 Phase 3: Studio 前端切换（高优先级）
**任务**: 将前端从旧端点 `POST /api/workspaces/:ws_id/executions` 切换到 `POST /api/v1/runs`

**文件列表**（需要审查）:
```
aitest/web/src/
├── api/
│   ├── client.ts           # HTTP 客户端
│   └── endpoints.ts        # 端点常量（需要添加 /api/v1/runs）
├── views/
│   ├── ExecutionView.tsx   # 执行视图（可能调用旧端点）
│   ├── RunInspectorView.tsx
│   └── DashboardView.tsx
└── stores/
    └── chat.ts             # Chat store（可能调用执行 API）
```

**步骤**:
1. 搜索 `POST.*executions` 找到所有调用点
2. 替换为新端点，映射参数到新 schema
3. 更新 TypeScript 类型定义（RunTarget/RunParams/RunExecution）
4. 测试：创建 Run → 查询状态 → 显示结果

#### P7-2 Phase 4: 支持多类型（workflow/skill/evaluation）
**当前状态**: `runs.py` line 28 返回 501 Not Implemented

**扩展点**:
```python
if req.target.type == "workflow":
    # 委托给 WorkflowRunner
elif req.target.type == "skill":
    # 委托给 SkillExecutor
elif req.target.type == "evaluation":
    # 委托给 EvaluationRunner
```

**依赖**: P8-1（Workflow 资源化）、P5-1（Evaluation 资源化）

#### P7-2 Phase 5: 旧端点标记 deprecated
在 `execution_router` 添加 deprecation 警告：
```python
@execution_router.post("/workspaces/{ws_id}/executions", deprecated=True)
async def start_execution(...):
    """⚠️ Deprecated: Use POST /api/v1/runs instead."""
```

#### P7-1: API 路由资源化（中优先级）
**任务**: 14 个 router 按资源模型重组，添加 `/api/v1/` 版本前缀

**当前结构** (`aitest/server/api/`):
```
execution_router      → /api/v1/runs (已迁移)
workspace_router      → /api/v1/workspaces (待迁移)
agents_router         → /api/v1/agents (待迁移)
workflows_router      → /api/v1/workflows (待迁移)
bugs_router           → /api/v1/bugs (待迁移)
audit_router          → /api/v1/audit (待迁移)
kpi_router            → /api/v1/kpi (待迁移)
... (其余 7 个)
```

**策略**: 逐个迁移，旧端点保留 6 个月

#### P2-6/P7-3: Studio IA 重组（低优先级，前端重构）
**任务**: 19 个平铺 Views 按 5-resource 模型合并

**目标结构**:
```
全局导航:
  - Projects（项目列表）
  - Runs（全局运行历史）
  - Evaluations（质量评估）
  - Registry（Agent/Workflow/Skill 注册表）
  - Settings（设置）

Project 内导航（选中项目后）:
  - Overview（项目概览）
  - Build（构建：Agent/Workflow 编辑）
  - Run（执行：创建 Run）
  - Quality（质量：Dataset/Evaluation/Experiment）
  - Assets（资产：Artifact/Knowledge）
```

**工作量**: 需要重新设计 `SidebarNav.tsx` + 合并多个 View 组件

#### P3-2: Multi-Run 对比（独立功能）
**端点**: `GET /api/v1/runs/compare?run_ids=run1,run2,run3`

**返回**:
```json
{
  "runs": [
    {"run_id": "run1", "status": "completed", "total_tokens": 1000, ...},
    {"run_id": "run2", "status": "failed", "total_tokens": 500, ...}
  ],
  "diff": {
    "tokens_delta": [1000, 500],
    "cost_delta": [0.01, 0.005],
    "artifacts_diff": [...]
  }
}
```

#### P3-3: Artifact blob API（独立功能）
**端点**:
- `GET /api/v1/artifacts/:artifact_id/download` — 直接下载
- `GET /api/v1/artifacts/:artifact_id/url` — 返回 Signed URL（未来扩展）

**实现**: 利用 `ArtifactStore.path()` 解析文件路径，`FileResponse` 返回

---

## 关键文件清单

### 后端（已修改）
```
aitest/
├── infra/models.py                    # RunModel 扩展 ★
├── platform/
│   ├── run.py                         # Run dataclass 扩展 ★
│   └── run_store.py                   # 迁移逻辑 + save_run() ★
├── server/
│   ├── main.py                        # runs_router 注册 ★
│   └── api/runs.py                    # 新端点实现 ★ (NEW)
└── adapters/llm/interface.py          # Provider re-exports ★

docs/
├── api/POST_api_v1_runs.md           # 新端点设计文档 ★ (NEW)
├── adr/ADR_001_TLO_DIRECTORY.md      # Schema 统一 ★
└── archive/PRODUCT_SPEC_V1_ARCHIVED.md # 废弃标记 ★

packages/alice-governance/alice_governance/agents/
└── agent-definitions.yaml             # 版本号 2.5 ★

create_tables_sqlite.sql               # SQLite schema 扩展 ★
```

### 前端（已修复 TS 错误，未迁移端点）
```
aitest/web/src/
├── api/
│   ├── client.ts          # 需要添加新端点调用
│   └── endpoints.ts       # 需要添加 /api/v1/runs 常量
├── views/
│   ├── ExecutionView.tsx  # 需要切换到新端点
│   ├── RunInspectorView.tsx
│   ├── DashboardView.tsx
│   └── ... (19 个 Views，P2-6 需要重组)
└── vite-env.d.ts          # TS 类型定义（已修复）
```

---

## 下次会话启动步骤

1. **验证当前修改**:
   ```bash
   cd D:\Desktop\Alice
   # 检查数据库迁移是否自动执行
   python -c "from aitest.platform.run_store import get_run_store; get_run_store()"
   
   # 启动服务器
   aitest server start
   # 访问 http://localhost:8000/docs 查看 /api/v1/runs 端点
   ```

2. **测试新端点**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/runs \
     -H "Content-Type: application/json" \
     -d '{
       "target": {"type": "agent", "id": "page-observer", "version": "latest"},
       "params": {"module": "user_manage", "pages": ["user_list"]},
       "execution": {"async": true}
     }'
   ```

3. **开始 P7-2 Phase 3**:
   - 读取 `aitest/web/src/api/client.ts`
   - 搜索 `executions` 找到所有旧端点调用
   - 逐个替换为新端点

4. **如果优先级变化**:
   - 可以跳过 Phase 3，直接实现 P3-2/P3-3（独立小功能）
   - 或者跳到阶段 3（质量闭环：Dataset/Evaluation/Experiment）

---

## 注意事项

### 向后兼容保证
- 所有新字段都有默认值
- 旧字段（agent/module/pages）完全保留
- 旧端点 `POST /api/workspaces/:ws_id/executions` 仍然可用
- `_row_to_run()` 的 fallback 逻辑：`target_id` 为空时用 `agent`

### 数据库迁移
- 自动迁移在 `RunStore.__init__()` 时执行
- 使用 `ALTER TABLE` 添加新列（SQLite 兼容）
- 如果迁移失败，日志会记录 warning，不会阻塞启动
- PostgreSQL 用户需要手动运行相同的 ALTER TABLE（或用 Alembic）

### TypeScript 类型
- P0-2 修复了 23 个错误，但没有添加新端点的类型定义
- 下次会话需要在 `src/api/` 添加 `CreateRunRequest`/`CreateRunResponse` 接口

---

## 累积问题清单（原始 28 项）

- ✅ P0-1/2/3: 已完成
- ✅ P1-1/2: 已完成
- 🔄 P7-2: Phase 1-2 完成，Phase 3-5 待完成
- ⏸️ P7-1: 待开始（API 路由资源化）
- ⏸️ P2-6/P7-3: 待开始（Studio IA 重组）
- ⏸️ P3-2/3: 待开始（Multi-Run 对比 + Artifact blob API）
- ⏸️ P4-1: 待开始（Skill 版本绑定）
- ⏸️ P5-1: 待开始（Dataset/Evaluation/Experiment）
- ⏸️ P6-1~5: 待开始（ModelProvider/MCP/Plugin/Environment/Secret）
- ⏸️ P8-1~3: 待开始（Workflow 图模型资源化）

---

## 技术债务提醒

1. **Alembic 缺失**: 当前用手动 ALTER TABLE，生产环境应该用 Alembic 管理迁移
2. **PostgreSQL 支持**: RunStore 的迁移逻辑只测试了 SQLite，PG 需要单独验证
3. **Signed URL**: P3-3 设计文档提到 Signed URL，但未实现（需要 S3/云存储集成）
4. **前端 API 类型**: 新端点缺少 TypeScript 类型定义
5. **测试覆盖**: 新端点和数据库迁移逻辑没有单元测试

---

## 会话总结

**时长**: ~2 小时  
**Token**: 118k/200k (59%)  
**修改文件**: 13 个  
**新增文件**: 2 个  
**完成进度**: 阶段 0（100%）+ 阶段 1（100%）+ 阶段 2（40%）

**核心成果**:
1. 解除所有阻塞（P0-1/2/3）
2. 统一版本号和 schema（P1-1/2）
3. 新执行端点完整后端支持（P7-2 Phase 1-2）
4. 数据库自动迁移机制

**建议下次优先级**: P7-2 Phase 3（前端切换）→ P3-2/3（独立小功能）→ P7-1（router 重组）
