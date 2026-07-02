# executor.py 解剖报告

> 文件: `aitest/engine/executor.py` | 1401 行
> 日期: 2026-07-01

---

## 职责地图

```
行范围      职责                        归属          行数
──────────────────────────────────────────────────────────
1~29        imports + Windows 编码修复   基础设施       29
31~64       平台模块导入 + 路径配置      Platform       34
67~228      AgentLoop.__init__          混合           162
229~233     HITL 交互 (send_interaction) Core          5
234~264     属性 + 辅助方法             Core           31
266~289     CapabilityRouter 初始化      Platform       24
291~302     ObservationBus 事件发射      Platform       12
304~307     日志                        Runtime        4
309~348     路径工具函数                 Platform       40
350~438     _build_context_vars         Platform       89
440~504     _build_user_input           Core           65
506~543     perceive (感知)             Core           38
545~554     plan (规划委托)             Core           10
556~631     act (执行)                  混合           76
633~669     产出保存 + 一致性检查        Platform       37
671~759     _persist_skill_artifact     Platform       89
761~901     observe (观察)              混合           141
903~910     update (状态更新)           Core           8
912~925     缓存统计事件                Platform       14
927~960     continuation (上下文续传)    Runtime        34
962~1019    run() 主循环 (含 continuation) Core         58
1021~1133   _finalize_session           Platform       113
1135~1356   _run_single_session         Core           222
1358~1364   run_interactive             Core           7
1368~1401   兼容旧接口 (run_agent等)    Core           34
```

---

## 按归属汇总

### Core (Engine 核心) — 517 行 (37%)

```
行范围      内容                              行数
────────────────────────────────────────────────
229~233     send_interaction (HITL)           5
234~264     属性 + 辅助方法                   31
440~504     _build_user_input                 65
506~543     perceive (感知)                   38
545~554     plan (规划委托)                   10
903~910     update (状态更新)                 8
962~1019    run() 主循环                      58
1135~1356   _run_single_session               222
1358~1364   run_interactive                   7
1368~1401   兼容旧接口                        34
```

**这是 Agent 执行循环的核心，应该进 SDK。**

### Runtime (运行时) — 130 行 (9%)

```
行范围      内容                              行数
────────────────────────────────────────────────
304~307     日志                              4
927~960     continuation (上下文续传)          34
556~631     act() 中的窗口检查 + token 更新    42
962~1019    run() 中的 continuation 错误处理   50
```

**上下文窗口管理和续传，应该进 SDK Runtime。**

### Platform (平台特有) — 645 行 (46%)

```
行范围      内容                              行数
────────────────────────────────────────────────
31~64       平台模块导入 + 路径配置            34
266~289     CapabilityRouter 初始化            24
291~302     ObservationBus 事件发射            12
309~348     路径工具函数                       40
350~438     _build_context_vars               89
633~669     产出保存 + 一致性检查              37
671~759     _persist_skill_artifact           89
761~901     observe() 中的安全检查 + 失败归因  60
912~925     缓存统计事件                       14
1021~1133   _finalize_session                 113
```

**平台特有功能，留 aitest。**

### 混合 (需要拆分) — 109 行 (8%)

```
行范围      内容                              行数   Core部分    Platform部分
────────────────────────────────────────────────────────────────────────────
67~228      __init__                          162    状态初始化  config/trace/retry
556~631     act()                             76     LLM调用     窗口检查/产出保存
761~901     observe()                         141    产物验证    安全检查/失败归因
```

---

## 依赖分析

### Platform 依赖 (阻碍移入 SDK)

| 依赖 | 出现次数 | 用途 |
|------|---------|------|
| `aitest.config.config` | 4 | provider 解析、model tier |
| `aitest.runtime.paths.*` | 8 | 路径解析 |
| `aitest.infra.logging` | 1 | 结构化日志 |
| `aitest.infra.trace` | 2 | TraceContext |
| `aitest.infra.pause_handler` | 2 | HITL 暂停 |
| `aitest.infra.worktree_manager` | 1 | Worktree 隔离 |
| `aitest.platform.observation_bus` | 4 | 事件发射 |
| `aitest.platform.capability_router` | 1 | Tool calling |
| `aitest.platform.artifact_lineage` | 1 | 产物血缘 |
| `aitest.platform.operational_metrics` | 1 | 运营指标 |
| `aitest.audit_engine.safety_auditor` | 1 | 安全检查 |
| `aitest.audit_engine.failure_attributor` | 1 | 失败归因 |
| `aitest.audit_engine.online_monitor` | 1 | 在线监控 |
| `aitest.agents.output_persistence` | 3 | 产出保存 |
| `aitest.agents.consistency_checks` | 2 | 一致性检查 |
| `aitest.mcp.mcp_client` | 1 | MCP 客户端 |

### Core 依赖 (可以带入 SDK)

| 依赖 | 出现次数 | 用途 |
|------|---------|------|
| `aitest.engine.task.*` | 3 | 数据结构 ✅ 已在 SDK |
| `aitest.engine.skill_executor.*` | 2 | Skill 执行 |
| `aitest.engine.skill_loader` | 1 | Skill 加载 ✅ 已在 SDK |
| `aitest.engine.planner` | 1 | 规划 ✅ 已在 SDK |
| `aitest.engine.state_machine` | 1 | 状态更新 ✅ 已在 SDK |

---

## 解耦策略

### Step 1: 提取 Core 到接口

```python
# SDK 定义
class AgentLoopProtocol(Protocol):
    def run(self) -> AgentState: ...
    def perceive(self, skill_id: str) -> dict: ...
    def plan(self, skill_index: int, perception: dict) -> dict: ...
    def act(self, skill_id: str) -> LLMResponse: ...
    def observe(self, skill_id: str, response: LLMResponse) -> Observation: ...
    def update(self, skill_id: str, observation: Observation) -> None: ...
```

### Step 2: Platform 依赖通过注入解决

```python
# 现在 (硬编码)
from aitest.runtime.paths import get_workstudy
WORKSTUDY = get_workstudy()

# 改后 (注入)
class AgentLoop:
    def __init__(self, ..., paths: PathResolver, logger: Logger, event_bus: EventBus):
        self.paths = paths
        self.logger = logger
        self.event_bus = event_bus
```

### Step 3: observe() 拆分

```python
# 现在: observe() 做了 3 件事
def observe(self, skill_id, response):
    safety_check(response)          # → Platform
    artifact_check(skill_id)        # → Core
    failure_attribution(obs)        # → Platform

# 改后: Core 只做产物验证
def observe(self, skill_id, response):
    artifact_check(skill_id)        # → Core (SDK)

# 安全检查和失败归因通过 Extension 或 Hook 注入
```

---

## 结论

| 归属 | 行数 | 占比 | 状态 |
|------|------|------|------|
| Core (SDK) | 517 | 37% | 接口已定义，实现待迁移 |
| Runtime (SDK) | 130 | 9% | continuation 待迁移 |
| Platform (aitest) | 645 | 46% | 留在平台层 |
| 混合 (需拆分) | 109 | 8% | 需要解耦后分配 |

**下一步: 按 Step 1→2→3 顺序解耦，而不是直接搬代码。**
