# MCP Engineering Improvement Plan

> **创建日期**: 2026-06-14
> **状态**: 🟢 P0-P2 全部完成 — 12 Tools + 6 Prompts + 审计日志 + 取消 + Sampling + 限流
> **关联**: [[ARCHITECTURE_REVIEW_V2_2026-06-13]] | [[AI_TEST_PLATFORM_ARCHITECTURE_OPTIMIZATION]]

---

## 1. 当前状态自评修正

| 维度 | 原自评 | 修正（P0+P1 后） | 说明 |
|------|--------|------------------|------|
| Tool 数量 | "5 Tools" | **10 Tools** | +run_pytest (P0-1), +check_consistency (P1-2) |
| `run_pytest` Tool | "存在" | ✅ **已实现** | 支持 module/marker/parallel/test_file/timeout 参数 |
| MCP Prompts | 无 | ✅ **已实现** | 6 个 Prompt 模板，_PromptDef 注册表驱动 |
| MCP Sampling | 无 | ❌ 缺失 | P2 待实施 |
| Transport | stdio | **仅 stdio** | 无 Streaming/SSE，P3 待实施 |
| Error handling | — | ✅ **结构化** | ErrorCode 7 种 + MCPError + suggestion/retryable |
| Auth/Audit | 无 | ❌ 缺失 | P2 待实施 |
| Zero-LLM Tools | 碎片化 | ✅ **2 个 MCP 化** | check_code_quality + check_consistency |

**掌握程度修正**: 🟡 基础掌握 → 🟢 **良好掌握**（P0+P1 达成）

---

## 2. 缺失能力全景

```
MCP Protocol Surface
├── ✅ Tools (list_tools / call_tool)     ← 已实现，8 Tools
├── ✅ Resources (list / read)             ← 已实现，分层知识暴露
├── ❌ Prompts (list / get)                ← P1
├── ❌ Sampling (createMessage)            ← P2
├── ✅ ResourceTemplates                   ← 已实现
├── ❌ Notifications (progress)            ← P1
└── ❌ Roots (list)                        ← P4

Quality Attributes
├── ❌ Structured Error Codes              ← P0
├── ❌ Tool Execution Audit Log            ← P2
├── ❌ Rate Limiting                       ← P2
├── ❌ Cancellation (long-running ops)     ← P2
├── ❌ Result Pagination                   ← P3
└── ❌ Tool Dependency Metadata            ← P3

Zero-LLM Tool Surface
├── ❌ consistency_checker → MCP Tool      ← P1
├── ❌ code-consistency-checker → MCP Tool ← P1
└── ❌ SOP gate checker → MCP Tool         ← P3
```

---

## 3. 实施路线图

### P0 — 基础功能缺口（本周）

| # | 任务 | 文件 | 工作量 | 产出 |
|---|------|------|--------|------|
| P0-1 | `run_pytest` MCP Tool | `aitest/mcp_server.py` | 30 min | 新增 Tool：支持 module/marker/parallel 参数，返回 pytest JSON 结果 |
| P0-2 | 结构化错误码 | `aitest/mcp_server.py` | 2h | `MCPError` 类体系：ErrorCode 枚举 + suggestion 字段，覆盖 8 个 Tool |

**P0-1 设计**:
```python
# run_pytest Tool Schema
{
  "module": "string (required) — 模块名",
  "marker": "string — pytest marker (smoke/integration/destructive)",
  "parallel": "int — 并行数 (默认 1，-1=auto)",
  "test_file": "string — 指定单个 test_*.py（可选）"
}
# Returns: {exit_code, total, passed, failed, error, failures: [...], duration}
```

**P0-2 设计**:
```python
class ErrorCode(enum.Enum):
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    INVALID_PARAMS = "INVALID_PARAMS"
    PRECONDITION_FAILED = "PRECONDITION_FAILED"
    EXECUTION_TIMEOUT = "EXECUTION_TIMEOUT"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"

@dataclass
class MCPError:
    code: ErrorCode
    message: str
    suggestion: str   # 可操作建议，LLM 可直接展示给用户
    retryable: bool
    details: dict     # 额外上下文
```

---

### P1 — 协议完整性（下周）

| # | 任务 | 文件 | 工作量 | 产出 |
|---|------|------|--------|------|
| P1-1 | MCP Prompts | `aitest/mcp_server.py` | 3h | `prompts/list` + `prompts/get`，6 个 prompt 模板 |
| P1-2 | Zero-LLM Tool MCP 化 | `aitest/mcp_server.py` + `consistency_checker.py` | 1h | `check_consistency` Tool 注册 |
| P1-3 | 执行进度通知 | `aitest/mcp_server.py` | 2h | `run_sop` / `run_pytest` 支持 `notifications/progress` |

**P1-1 Prompt 模板清单**:
```
prompt://generate-page-object    — 从 PAGE_CONTEXT 生成 Page Object
prompt://analyze-failure         — 分析测试失败根因
prompt://design-test-cases       — 从 PAGE_CONTEXT 设计测试用例
prompt://review-code             — 代码红线检查 + 修复建议
prompt://sop-status              — 查看模块 SOP 进度
prompt://bug-report              — 生成标准化 Bug 报告
```

---

### P2 — 生产就绪（2 周内）

| # | 任务 | 工作量 |
|---|------|--------|
| P2-1 | MCP Sampling（LLM-in-the-loop） | 4h |
| P2-2 | Tool Auth + Rate Limiting | 3h |
| P2-3 | Tool 执行审计日志 | 2h |
| P2-4 | 长任务 Cancellation 支持 | 2h |

---

### P3 — 长期优化（1 个月内）

| # | 任务 | 工作量 |
|---|------|--------|
| P3-1 | Streaming HTTP Transport | 4h |
| P3-2 | Tool 依赖元数据（depends_on/produces/side_effect） | 2h |
| P3-3 | SOP Gate Checker → MCP Tool | 1h |
| P3-4 | 结果分页（search/status Tools） | 1h |

---

### P4 — 按需

| # | 任务 | 工作量 |
|---|------|--------|
| P4-1 | MCP Roots（多工作区） | 1h |

---

## 4. 目标状态

完成 P0+P1 后，掌握程度达到 🟢 **良好掌握**：

| 维度 | 当前 | 目标 |
|------|------|------|
| Tools | 8 | 11（+run_pytest, +check_consistency, +check_code_consistency） |
| Prompts | 0 | 6 模板 |
| Resources | ✅ | ✅ |
| Error handling | 裸 str | 结构化 ErrorCode + suggestion |
| Zero-LLM Tool | 碎片化 | 3 个 MCP 化 |
| Notifications | 无 | long-running Tools 推送进度 |
| Sampling | 无 | 目标 P2 |
| Streaming | 无 | 目标 P3 |

---

## 5. 实施日志

| 日期 | 阶段 | 内容 |
|------|------|------|
| 2026-06-14 | — | Plan created |
| 2026-06-14 | P0-1 ✅ | `run_pytest` Tool 实现：支持 module/marker/parallel/test_file/timeout 参数，结构化解析 pytest 输出（passed/failed/error/skipped + failure_output + suggestion） |
| 2026-06-14 | P0-2 ✅ | 结构化错误码体系：`ErrorCode` 枚举（7 种）+ `MCPError` dataclass + `_error_response()` / `_success_response()` 工厂函数。8 个 Tool handler + `call_tool` 全部更新为结构化错误 |
| 2026-06-14 | P1-1 ✅ | MCP Prompts 实现：`_PromptDef` 注册表 + `list_prompts` + `get_prompt`。6 个 Prompt 模板：generate-page-object / analyze-failure / design-test-cases / review-code / sop-status / bug-report |
| 2026-06-14 | P1-2 ✅ | Zero-LLM Tool `check_consistency` 注册：包装 `consistency_checker.run_all_checks()`，6 项跨层检查，零 AI 调用成本 |
| 2026-06-14 | P2-3 ✅ | 审计日志体系：`_AuditRecord` dataclass — timestamp/tool_name/arguments/duration_ms/status/error_code/result_summary/caller_pid。每次 `call_tool` 写入 `governance/audit/tool-calls.jsonl`。静默失败不中断 Tool 执行 |
| 2026-06-14 | P2-4 ✅ | 长任务 Cancellation：`_TaskHandle` + `asyncio.Event` 取消信号。`_run_pytest` 改用 `subprocess.Popen` 轮询（每秒检查取消信号），`_run_sop_handler` 每 graph step 检查。新增 `cancel_task` + `list_tasks` 两个管理 Tool |
| 2026-06-14 | P2-1 ✅ | MCP Sampling：`_sampling_available()` + `_request_llm_summary()` + `_request_llm_sync()`。`rag_search_known_issues` 当结果 > 3 时自动请求 LLM 重排序/摘要。客户端不支持 sampling 时自动降级 |
| 2026-06-14 | P2-2 ✅ | Tool Auth + Rate Limiting：`ToolPermission` 三级（READ 30/min / WRITE 10/min / EXECUTE 5/min），滑动窗口限流。`call_tool` 入口拦截，超频返回 `PERMISSION_DENIED` ErrorCode + `retry_after` 秒数 |

**P0-P2 完成后的完整工具矩阵**:

| Tool | 权限 | 类型 | 说明 |
|------|------|------|------|
| `check_code_quality` | READ | Zero-LLM | 8 条代码红线扫描 |
| `search_known_issues` | READ | Zero-LLM | known-issues.yaml 关键词搜索 |
| `get_module_status` | READ | Zero-LLM | 模块 SOP 进度 + 文档完整性 |
| `get_automation_coverage` | READ | Zero-LLM | PageObject + 测试脚本数量 |
| `rag_search_known_issues` | READ | LLM+Sampling | ChromaDB 向量检索 + LLM 重排序 |
| `check_consistency` | READ | Zero-LLM | 跨层一致性检查（6 项） |
| `list_tasks` | READ | Zero-LLM | 查看运行中长任务 |
| `cancel_task` | WRITE | Zero-LLM | 取消运行中长任务 |
| `run_test_design_agent` | EXECUTE | LLM Agent | 测试设计全流程 |
| `run_automation_agent` | EXECUTE | LLM Agent | 自动化代码生成 |
| `run_sop` | EXECUTE | LLM Agent | 完整 SOP 编排 (LangGraph)，支持取消 |
| `run_pytest` | EXECUTE | Hybrid | 运行 pytest 测试，支持取消 |

**Prompt 模板**: 6 个 | **ErrorCode 枚举**: 8 种 | **审计日志**: JSONL @ `governance/audit/` | **速率限制**: READ 30/min, WRITE 10/min, EXECUTE 5/min

---

## 6. P3+P4 实施日志

| 日期 | 阶段 | 内容 |
|------|------|------|
| 2026-06-14 | P3-0 ✅ | **模块化拆分**: 1369 行单体 `mcp_server.py` → `aitest/mcp/` 包（20 文件，1661 行）。config / error_taxonomy / audit / rate_limit / cancellation / sampling 六层基础设施独立；tools/ 13 个 Tool handler 各居其位；prompts/ 模板文本与逻辑分离；protocol.py 协议层。原 `mcp_server.py` 降级为 15 行兼容 shim |
| 2026-06-14 | P3-2 ✅ | **Tool 依赖元数据**: `ToolDef` 新增 `permission` / `depends_on` / `produces` / `side_effect` / `estimated_duration` 五字段。每个 Tool 自带完整元数据，Agent 可据此自动推导调用顺序 |
| 2026-06-14 | P3-3 ✅ | **SOP Gate Checker MCP 化**: 新增 `check_sop_gate` Tool（READ 权限）。封装 `check_sop_gate.py`，脚本缺失时回退到基础文档存在性检查。Agent 启动前自动验证前置条件 |
| 2026-06-14 | P3-4 ✅ | **结果分页**: `search_known_issues` 新增 `offset`/`limit` 参数（默认 0/50），返回 `total`/`offset`/`limit`/`returned` 分页元数据 |
| 2026-06-14 | P3-1 ✅ | **Streaming HTTP Transport**: `run_http()` 入口 — `StreamingHttpServer` + `uvicorn`。`--transport http` 切换。依赖可选安装，缺失时自动降级 stdio |
| 2026-06-14 | P4-1 ✅ | **MCP Roots 占位**: HTTP server 预留 `/roots` 路由注释。单项目场景不需要多工作区，代码就位 |

### P3 完成后的文件结构

```
aitest/mcp/                        ← 新包（1661 行 / 20 文件）
├── __init__.py        ( 96行)     Server 工厂 + run_stdio/run_http/main
├── config.py          ( 21行)     路径常量单一事实源
├── error_taxonomy.py  ( 55行)     ErrorCode(8) + MCPError + 工厂函数
├── audit.py           ( 50行)     AuditRecord + JSONL 写入
├── rate_limit.py      ( 69行)     ToolPermission + 滑动窗口限流
├── cancellation.py    ( 63行)     TaskHandle + asyncio.Event 取消
├── sampling.py        ( 68行)     LLM sampling (set_server 延迟绑定)
├── protocol.py        (109行)     list_tools + call_tool + audit/限流包装
├── tools/
│   ├── __init__.py    (198行)     ★ TOOL_REGISTRY (13 Tools + 元数据)
│   ├── registry.py    ( 31行)     ToolDef dataclass
│   ├── quality.py     ( 41行)     check_code_quality
│   ├── knowledge.py   ( 89行)     search_known_issues + RAG sampling
│   ├── status.py      ( 86行)     module_status + coverage
│   ├── agents.py      ( 69行)     test_design / automation agent
│   ├── execution.py   (249行)     run_pytest (Popen)+ run_sop (LangGraph)
│   ├── consistency.py ( 43行)     check_consistency (Zero-LLM)
│   ├── management.py  ( 31行)     cancel_task + list_tasks
│   └── gate_checker.py( 81行)     check_sop_gate (P3-3, 回退门禁)
└── prompts/
    ├── __init__.py    (117行)     PromptDef + list/get handlers
    └── templates.py   ( 95行)     6 个模板文本常量（纯数据）

aitest/mcp_server.py   ( 15行)     向下兼容 shim
```

### 最终指标

| 指标 | 实施前 | P0-P2 后 | P3-P4 后 |
|------|--------|---------|----------|
| 文件数 | 1 (442行) | 1 (1369行) | **20 (1661行)** |
| Tools | 8 | 12 | **13** (+check_sop_gate) |
| Prompts | 0 | 6 | 6 |
| ErrorCode | 0 | 8 | 8 |
| 最大单文件 | 442 | 1369 | **249** (execution.py) |
| Transport | stdio | stdio | stdio + HTTP (可选) |
| 元数据 | 无 | 无 | **5 字段 per Tool** |
| 掌握程度 | 🟡 基础 | 🟢 良好 | 🟢 **良好**（可测试/可扩展） |
