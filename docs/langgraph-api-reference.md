# LangGraph 常用 API 学习文档

> 全部示例代码取自本项目（aitest），结合真实使用场景讲解。
> 学习前提：已理解 State / Node / Edge / Compile 四件套。

---

## 一、导入 API —— 三个包各管一摊

LangGraph 的 API 分散在三个包里：

```python
# langgraph.graph —— 图构建核心（最常用）
from langgraph.graph import StateGraph, END

# langgraph.types —— 高级控制流
from langgraph.types import interrupt, Send, Command

# langgraph.checkpoint.sqlite —— 持久化存储
from langgraph.checkpoint.sqlite import SqliteSaver
```

| 包 | 提供的 API | 用途 |
|----|-----------|------|
| `langgraph.graph` | `StateGraph`, `END` | 构建图结构 |
| `langgraph.types` | `interrupt`, `Send`, `Command` | HITL 暂停、并行、恢复 |
| `langgraph.checkpoint.sqlite` | `SqliteSaver` | 状态存盘（SQLite） |

---

## 二、State 定义 API

### 2.1 TypedDict —— 定义 State 字段结构

State 本质是一个带类型提示的字典，使用标准库 `typing.TypedDict`。

> 文件：`graphs/state.py`

```python
from typing import TypedDict, Optional, List, Dict, Any, Annotated

class SOPState(TypedDict):
    """SOP 编排的完整状态，流经所有 LangGraph 节点。"""

    # 【普通字段】—— 后写覆盖（last-write-wins）
    module: str
    pages: List[str]
    mode: SOPMode
    provider: str
    run_id: str
    current_phase: PhaseName
    current_page_index: int
    bug_cycle_count: int
    status: str
    fatal_error: Optional[str]

    # 【Annotated 字段】—— 通过 reducer 函数控制合并方式
    completed_phases: Annotated[List[PhaseName], _unique_list]
    agent_outputs: Annotated[Dict[str, Any], _merge_agent_outputs]
    per_page_results: Annotated[List[Dict[str, Any]], operator.add]
    skill_observations: Annotated[List[Dict[str, Any]], _bounded_skill_obs]
    human_input: Annotated[Optional[str], _pick_last]
```

**要点：**
- 普通字段：节点返回同名键时，直接覆盖旧值
- `Annotated[类型, reducer函数]`：节点返回同名键时，调用 reducer 合并新旧值

### 2.2 operator.add —— 最简单的 Reducer

```python
import operator

# 两个列表直接拼接：[A] + [B] → [A, B]
per_page_results: Annotated[List[Dict[str, Any]], operator.add]
```

当多个节点都返回 `{"per_page_results": [...]}` 时，LangGraph 自动调用 `operator.add` 把列表拼接起来。

### 2.3 自定义 Reducer 函数

> 文件：`graphs/state.py`

```python
# ① 去重追加 —— completed_phases 跨节点累积时不重复
def _unique_list(current: list, update: list) -> list:
    """去重追加：update 中已存在于 current 的元素被跳过。"""
    seen = set(current)
    new_items = []
    for x in update:
        if x not in seen:
            new_items.append(x)
            seen.add(x)
    return current + new_items

# ② 字典深度合并 —— 每个 Agent 的输出合并到一起
def _merge_agent_outputs(current: dict, update: dict) -> dict:
    """深度合并 agent_outputs，update 的键覆盖 current 的同名键。"""
    merged = dict(current)
    merged.update(update)
    return merged

# ③ 限长列表 —— 防止 skill_observations 无限增长
_SKILL_OBS_MAX = 100

def _bounded_skill_obs(current: list, update: list) -> list:
    """保留最近 100 条 skill_observations。"""
    combined = current + update
    return combined[-_SKILL_OBS_MAX:] if len(combined) > _SKILL_OBS_MAX else combined

# ④ 显式取末值 —— 和默认覆盖行为一样，但语义更明确
def _pick_last(current, update):
    """选取最后一次写入的值。"""
    return update
```

**Reducer 签名统一**：`def fn(当前值, 新增值) -> 合并后的值`

### 2.4 用裸 dict 作为 State（无类型约束）

> 文件：`graphs/review_graph.py`

```python
def build_review_graph() -> StateGraph:
    builder = StateGraph(dict)  # ← 直接用 dict，不定义固定字段

    initial_state = {
        "mode": mode,
        "trigger": trigger,
        "module": module,
        "phases": [],
        "phase_index": 0,
        "review_results": {},
    }
    final_state = graph.invoke(initial_state)
```

适合快速原型或字段不固定的场景，但失去了类型检查和 IDE 提示。

### 2.5 创建初始 State

> 文件：`graphs/state.py`

```python
def create_initial_state(
    module: str,
    pages: List[str],
    mode: SOPMode = "full",
    provider: str = "claude",
    run_id: str = "",
    bug_cycle_max: int = 3,
) -> dict:
    import time
    if not run_id:
        run_id = f"sop-{module}-{int(time.time())}"

    return {
        "module": module,
        "pages": pages,
        "mode": mode,
        "provider": provider,
        "run_id": run_id,
        "current_phase": "Preflight",
        "completed_phases": [],
        "failed_phases": [],
        "skip_phases": [],
        "current_page_index": 0,
        "bug_cycle_count": 0,
        "bug_cycle_max": bug_cycle_max,
        "status": "running",
        # ...更多字段
    }
```

---

## 三、图构建 API —— 最核心部分

### 3.1 StateGraph —— 创建图构建器

> 文件：`graphs/execution_graph.py`

```python
from langgraph.graph import StateGraph, END
from aitest.graphs.state import SOPState

# 标准写法：绑定 TypedDict
def build_report_subgraph() -> StateGraph:
    builder = StateGraph(SOPState)    # ← 以 SOPState 为 State 类型
    # ... 添加节点和边 ...
    return builder
```

`StateGraph(state_type)` 创建一个图构建器，`state_type` 指定了所有节点共享的状态类型。

### 3.2 add_node —— 注册节点

节点可以是**普通函数**，也可以是**编译后的子图**。

> 文件：`graphs/execution_graph.py`（普通函数节点）

```python
# 写法 A：节点是普通函数
def report_entry(state: SOPState) -> dict:
    return {"current_phase": "Report"}

def report_act(state: SOPState) -> dict:
    return _single_skill_act(state, "reporting/report-generator")

def report_exit(state: SOPState) -> dict:
    return {"completed_phases": ["Report"]}

builder = StateGraph(SOPState)
builder.add_node("entry", report_entry)   # 注册节点：名字 + 函数
builder.add_node("act", report_act)
builder.add_node("exit", report_exit)
```

> 文件：`graphs/sop_graph.py`（子图作为节点）

```python
from aitest.graphs.execution_graph import (
    build_execution_subgraph,
    build_report_subgraph,
    build_knowledge_subgraph,
)

# 写法 B：节点是编译后的子图（子图嵌套）
builder.add_node("execution_agent", build_execution_subgraph().compile())
builder.add_node("report_agent",   build_report_subgraph().compile())
builder.add_node("knowledge_agent", build_knowledge_subgraph().compile())
```

**关键约定**：节点函数签名统一为 `def fn(state) -> dict`，接收完整 state，**只返回需要更新的字段**（部分字典）。

### 3.3 set_entry_point —— 指定起点

> 文件：`graphs/execution_graph.py`

```python
builder = StateGraph(SOPState)
builder.add_node("entry", report_entry)
builder.add_node("act", report_act)
builder.add_node("exit", report_exit)
builder.set_entry_point("entry")   # ← 指定 entry 为入口节点
```

每个图必须有且仅有一个入口节点。

### 3.4 add_edge —— 普通边

> 文件：`graphs/execution_graph.py`

```python
# A → B：固定流转
builder.add_edge("entry", "act")
builder.add_edge("act", "exit")

# → END：图到此结束
builder.add_edge("exit", END)
```

`END` 是 `langgraph.graph` 提供的特殊常量，表示"图结束，不再流转"。

> 文件：`graphs/review_graph.py`（更长的普通边链）

```python
builder.add_edge("entry", "run_review_phase")
builder.add_edge("synthesis", "report")
builder.add_edge("report", "emit_events")
builder.add_edge("emit_events", "exit")
builder.add_edge("exit", END)
```

### 3.5 add_conditional_edges —— 条件边

这是最灵活的 API，根据当前 state 动态决定下一步去哪个节点。

#### 用法 ①：路由函数 + 字典映射表

> 文件：`graphs/sop_graph.py`

```python
def route_next_phase(state: SOPState) -> str:
    """根据 completed_phases + skip_phases 决定下一个节点。"""
    # 致命错误 → 直接退出
    if state.get("fatal_error"):
        return "exit"

    # Status 模式 → preflight 后直接退出
    if state.get("mode") == "status":
        return "exit"

    # 质量门禁强制重试
    force_retry = state.get("force_retry_phase")
    if force_retry:
        return PHASE_TO_NODE.get(force_retry)

    completed = set(state.get("completed_phases", []))
    skipped = set(state.get("skip_phases", []))

    # 遍历标准阶段顺序
    for phase in CANONICAL_PHASES:
        if phase in completed or phase in skipped:
            continue
        return PHASE_TO_NODE[phase]

    # 全部完成
    return "exit"

# 使用
all_routable_nodes = list(ALL_AGENT_NODES) + ["page_advance"]
route_map = {name: name for name in all_routable_nodes}
route_map["exit"] = "exit"

builder.add_conditional_edges(
    "preflight",          # 源节点
    route_next_phase,     # 路由函数：def fn(state) -> str
    route_map,            # 映射表：{返回值: 目标节点名}
)
```

#### 用法 ②：lambda 内联路由

> 文件：`graphs/sop_graph.py`

```python
# 审批通过 → 继续；审批拒绝 → 退出
builder.add_conditional_edges(
    "automation_strategy_approval",
    lambda s: "automation_agent_post" if s.get("auto_strategy_approved") else "exit",
    {"automation_agent_post": "automation_agent_post", "exit": "exit"},
)
```

适合简单的一步判断。

#### 用法 ③：循环跳转

> 文件：`graphs/bug_analysis_graph.py`

```python
def loop_router(state: SOPState) -> Literal["loop", "report"]:
    cycle = state.get("bug_cycle_count", 0)
    approved = state.get("fix_approved")
    if approved is False:
        return "report"
    if cycle >= 3:
        return "report"
    if verify_result.get("passed"):
        return "report"
    return "loop"

builder.add_conditional_edges(
    "verify",
    loop_router,
    {"loop": "loop", "report": "report"},
)
```

### 3.6 add_conditional_edges 的三种第三参数形态

| 第三参数 | 路由函数返回值 | 效果 |
|----------|--------------|------|
| `{返回值: 节点名}` 字典 | `str` | 去**一个**节点（最常用） |
| `["节点名"]` 列表 | `list[Send]` | 并行去**N 个**节点（见第六节 Send API） |
| 不传 / `None` | `str` | 返回值本身被当作节点名 |

### 3.7 边覆盖规则

> 文件：`graphs/sop_graph.py`

```python
# 步骤1：给大部分节点添加通用条件边
for node_name in ALL_AGENT_NODES:
    if node_name not in _CUSTOM_EDGE_NODES:
        builder.add_conditional_edges(node_name, route_next_phase, route_map)

# 步骤2：给特殊节点添加定制边（后添加的覆盖先添加的）
builder.add_edge("test_design_agent", "testcase_quality_gate")  # ← 覆盖！
builder.add_edge("automation_agent_post", "page_advance")
```

**规则**：对同一个源节点，后添加的边会覆盖先添加的。这用于给特定节点定制路线。

### 3.8 完整图构建示例

> 文件：`graphs/execution_graph.py` —— 最简单的 3 节点图

```python
def build_report_subgraph() -> StateGraph:
    builder = StateGraph(SOPState)
    builder.add_node("entry", report_entry)
    builder.add_node("act",   report_act)
    builder.add_node("exit",  report_exit)
    builder.set_entry_point("entry")
    builder.add_edge("entry", "act")
    builder.add_edge("act", "exit")
    builder.add_edge("exit", END)
    return builder
```

> 文件：`graphs/execution_graph.py` —— 4 节点图（多一个质量门禁）

```python
def build_execution_subgraph() -> StateGraph:
    builder = StateGraph(SOPState)
    builder.add_node("entry", exec_entry)
    builder.add_node("act",   exec_act)
    builder.add_node("gate",  exec_gate)   # ← 质量门禁
    builder.add_node("exit",  exec_exit)
    builder.set_entry_point("entry")
    builder.add_edge("entry", "act")
    builder.add_edge("act", "gate")
    builder.add_edge("gate", "exit")
    builder.add_edge("exit", END)
    return builder
```

---

## 四、编译与执行 API

### 4.1 compile —— 编译图

> 文件：`graphs/sop_graph.py`

```python
from aitest.graphs.checkpoint import get_checkpointer

# 不带 checkpointer（不能 HITL、不能断点续跑）
compiled = builder.compile()

# 带 checkpointer（支持 HITL + 断点续跑）
compiled = builder.compile(checkpointer=get_checkpointer())
```

**分水岭**：传了 `checkpointer` 才能用 `interrupt()`、`get_state()`、断点续跑。

### 4.2 invoke —— 一次性执行完

> 文件：`graphs/review_graph.py`

```python
# 最简调用（无 checkpointer）
graph = build_review_graph().compile()
final_state = graph.invoke(initial_state)
```

> 文件：`graphs/__init__.py`

```python
# 带 thread_id（用于 checkpointer 标识）
result = compiled.invoke(
    initial_state,
    {"configurable": {"thread_id": "my-run"}}
)
```

`invoke()` 会阻塞直到图跑完全部节点，返回最终 State。适合不需要中途交互的场景。

### 4.3 stream —— 流式执行

> 文件：`graphs/sop_runner.py`

```python
# stream_mode="updates"：每个节点完成后 yield 一次
stream = compiled.stream(
    initial_state,
    thread,                    # {"configurable": {"thread_id": "..."}}
    stream_mode="updates"
)

for event in stream:
    # event 结构: {节点名: 该节点返回的更新字典}
    for node_name, update in event.items():
        print(f"[{node_name}] completed")
        if update.get("fatal_error"):
            print(f"  Fatal error: {update['fatal_error']}")
```

**stream_mode 取值：**

| 值 | 每次 yield 的内容 | 项目用法 |
|----|------------------|---------|
| `"updates"` | `{节点名: 更新字典}` | 最常用，按节点粒度追踪进度 |
| `"values"` | 完整 State 快照 | 项目未用 |
| `"debug"` | 含执行元数据 | 项目未用 |

### 4.4 stream + Command(resume) —— 恢复执行

> 文件：`graphs/sop_runner.py`

```python
from langgraph.types import Command

# 正常流式执行
stream = compiled.stream(initial_state, thread, stream_mode="updates")

for event in stream:
    # ① 检测 interrupt 事件
    if "__interrupt__" in event:
        interrupt_items = event["__interrupt__"]

        # ② 将审批信息发给用户，阻塞等待回复
        response = user_await_response(interrupt_items)

        # ③ 用 Command(resume=...) 恢复执行
        stream = compiled.stream(
            Command(resume=response),   # 人类的回复
            thread,                     # 同一个 thread_id
            stream_mode="updates",
        )
        continue

    # ④ 正常节点更新
    for node_name, update in event.items():
        handle_node_update(node_name, update)
```

### 4.5 stream(None) —— 断点续跑

> 文件：`infra/cli/graph_cmds.py`

```python
# 不传新输入，从 checkpointer 存档处继续执行
for event in compiled.stream(None, thread, stream_mode="updates"):
    ...
```

传 `None` 表示"不从新输入开始，从上次 `interrupt()` 暂停的位置继续"。这实现了断点续跑。

### 4.6 get_state —— 读取当前状态

> 文件：`graphs/checkpoint.py`

```python
thread = {"configurable": {"thread_id": run_id}}
state = compiled.get_state(thread)

if state and state.values:
    print(state.values.get("completed_phases"))
    print(state.values.get("current_phase"))
    print(state.values.get("status"))
```

`get_state()` 返回 `StateSnapshot` 对象，`.values` 是当前 State 字典。常用于：
- 断点续跑前查看"上次跑到哪了"
- CLI `status` 命令
- 调试

---

## 五、人机协作（HITL）API

### 5.1 interrupt —— 在节点内按下暂停键

> 文件：`graphs/bug_analysis_graph.py`

```python
from langgraph.types import interrupt

def request_approval_node(state: SOPState) -> dict:
    """请求人工审批修复方案。使用 interrupt() 挂起执行。"""
    cycle = state.get("bug_cycle_count", 0)
    bug_cycle_max = state.get("bug_cycle_max", 3)
    fix_info = state.get("agent_outputs", {}).get("bug_fix", {})

    # ★ 暂停！payload 发给人类，图在这里冻结
    approval = interrupt({
        "type": "bug_fix_approval",
        "cycle": f"{cycle + 1}/{bug_cycle_max}",
        "module": state["module"],
        "fix_summary": fix_info.get("fix_summary", "No fix generated"),
        "options": ["approve", "reject", "skip"],
    })

    # ★ 恢复后，approval 就是人类传回的值（通过 Command(resume)）
    approved = approval == "approve"
    return {
        "fix_approved": approved,
        "human_input": str(approval),
    }
```

**关键理解：**
- `interrupt(payload)` 的参数 `payload` 发给人类看（审批信息）
- `interrupt()` 的返回值 = 人类通过 `Command(resume=xxx)` 传回的值
- 从节点函数视角，这就是一个"等待人类输入的 `input()`"

### 5.2 Command(resume=) —— 恢复执行

```python
from langgraph.types import Command

# 在 stream 中检测到 __interrupt__ 后
stream = compiled.stream(
    Command(resume="approve"),   # "approve" 将成为 interrupt() 的返回值
    thread,                      # 必须是同一个 thread_id
    stream_mode="updates",
)
```

`Command` 还可以控制流转方向（`Command(goto="node_name")`），项目里只用到了 `resume`。

### 5.3 __interrupt__ 事件检测

```python
for event in compiled.stream(initial_state, thread, stream_mode="updates"):
    # 当图被 interrupt() 暂停时，stream 会 yield __interrupt__ 事件
    if "__interrupt__" in event:
        interrupt_items = event["__interrupt__"]
        for item in interrupt_items:
            # item.value 就是 interrupt() 传入的 payload
            payload = getattr(item, 'value', None) or item
            yield interaction_event(payload)
```

**流程图：**

```
节点 A → request_approval_node → interrupt("awaiting")
                                      ↓
                                  stream yield {"__interrupt__": ...}
                                      ↓
                              Runner 检测到，转发给前端
                                      ↓
                              用户点击 "approve"
                                      ↓
                              stream(Command(resume="approve"), ...)
                                      ↓
                              interrupt() 返回 "approve"
                                      ↓
                              节点继续执行 → 返回 {fix_approved: True}
```

### 5.4 HITL 完整流转示例

> 文件：`graphs/bug_analysis_graph.py` —— 循环修复 + 人工审批

```
entry → analyze_fail → auto_fix → request_approval → verify
            ↑                                             │
            │                   (loop: 修复未通过)         │
            └─────────────────────────────────────────────┘
                                                          │
                                                     (report)
                                                          ↓
                                                       report → exit → END
```

每次循环都会经过 `request_approval` 节点 → `interrupt()` 暂停等审批。最多暂停 3 次。

---

## 六、并行 API —— Send

### 6.1 Send —— 创建并行任务

> 文件：`graphs/parallel_sop.py`

```python
from langgraph.types import Send

def fanout_pages(state: SOPState) -> list[Send]:
    """将 pages 列表展开为 N 个并行节点。"""
    pages = state.get("pages", [])
    module = state.get("module", "")
    provider = state.get("provider", "claude")

    if not pages:
        return []

    sends = []
    for i, page in enumerate(pages):
        # 每个页面构造独立的局部状态
        page_state = {
            "module": module,
            "pages": [page],                           # 只包含自己的页面
            "current_page_index": 0,
            "provider": provider,
            "mode": state.get("mode", "full"),
            "run_id": f"{state.get('run_id', '')}-p{i}",
        }
        # Send(目标节点名, 该任务的独立状态)
        sends.append(Send("process_single_page", page_state))

    return sends   # 返回 [Send, Send, Send] → 3 个并行任务
```

**Send(node_name, state) 的两个参数：**
1. `node_name`：这个任务要去的目标节点
2. `state`：这个任务的**独立状态**（不是共享的完整 State）

### 6.2 add_conditional_edges + Send 配合

> 文件：`graphs/parallel_sop.py`

```python
def build_parallel_sop_graph() -> StateGraph:
    builder = StateGraph(SOPState)

    builder.add_node("preflight", preflight_node)
    builder.add_node("process_single_page", process_single_page)
    builder.add_node("merge_pages", merge_pages)

    builder.set_entry_point("preflight")

    # ★ 条件边 + Send API：第三参数是列表（不是字典）
    builder.add_conditional_edges(
        "preflight",                # 源节点
        fanout_pages,               # 路由函数，返回 list[Send]
        ["process_single_page"],    # 可能的目标节点列表
    )

    # Fan-in：所有并行任务完成后汇聚到 merge_pages
    builder.add_edge("process_single_page", "merge_pages")
    builder.add_edge("merge_pages", END)

    return builder
```

**关键区别**：
- 普通条件边第三参数是 `{返回值: 节点名}` 字典
- Send 条件边第三参数是 `["节点名"]` 列表

### 6.3 Fan-in 靠 Reducer 自动合并

N 个 `process_single_page` 并行完成后，都流向 `merge_pages`。每个任务返回的 `completed_phases`（带 `operator.add` reducer）自动汇聚到列表中——这就是第二节 Reducer 的用武之地。

**Fan-out / Fan-in 流程：**

```
preflight
    │
    ├──→ Send(process_single_page, {pages:["page-A"]})  并行执行
    ├──→ Send(process_single_page, {pages:["page-B"]})  并行执行
    └──→ Send(process_single_page, {pages:["page-C"]})  并行执行
                                              │
                                    (全部完成后)
                                              ↓
                                       merge_pages
                                              ↓
                                            END
```

### 6.4 单页面处理节点示例

> 文件：`graphs/parallel_sop.py`

```python
def process_single_page(state: SOPState) -> dict:
    """处理单个页面的完整 SOP 流水线。"""
    module = state.get("module", "")
    pages = state.get("pages", [])
    page = pages[0] if pages else ""

    # 在此完成该页面的全部测试流程...

    return {
        "per_page_results": [{"page": page, "status": "completed"}],
        "completed_phases": ["Report"],
    }
```

---

## 七、Checkpoint API —— 状态持久化

### 7.1 SqliteSaver —— SQLite 存储

> 文件：`graphs/checkpoint.py`

```python
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

def get_checkpointer() -> SqliteSaver:
    """返回 SqliteSaver 实例。数据库路径：governance/.graph_state/checkpoints.sqlite"""
    db_path = CHECKPOINT_DIR / "checkpoints.sqlite"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    return SqliteSaver(conn)
```

### 7.2 编译时传入 checkpointer

```python
checkpointer = get_checkpointer()
compiled = builder.compile(checkpointer=checkpointer)
```

### 7.3 完整的 checkpoint 工具函数

> 文件：`graphs/checkpoint.py`

```python
def get_latest_state(run_id: str) -> Optional[dict]:
    """获取最近一次 checkpoint 的完整状态。"""
    graph = build_sop_graph()
    checkpointer = get_checkpointer()
    compiled = graph.compile(checkpointer=checkpointer)

    thread = {"configurable": {"thread_id": run_id}}
    state = compiled.get_state(thread)
    if state and state.values:
        return state.values
    return None

def list_runs(limit: int = 20) -> list[dict]:
    """列出所有最近的 checkpoint 运行。"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.execute(
        """SELECT DISTINCT thread_id, MAX(created_at) as updated_at
           FROM checkpoints GROUP BY thread_id
           ORDER BY updated_at DESC LIMIT ?""",
        (limit,)
    )
    return [{"run_id": row[0], "updated_at": row[1]} for row in cursor.fetchall()]

def cleanup_run(run_id: str) -> bool:
    """删除一个 run 的所有 checkpoint。"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (run_id,))
    conn.commit()
    return True
```

---

## 八、API 速查表

| API | 包 | 签名 | 一句话说明 |
|-----|---|------|-----------|
| `StateGraph` | langgraph.graph | `StateGraph(state_type)` | 创建图构建器 |
| `END` | langgraph.graph | 常量 | 图结束标记 |
| `add_node` | builder 方法 | `add_node(name, fn_or_subgraph)` | 注册节点（函数或编译后子图） |
| `add_edge` | builder 方法 | `add_edge(a, b)` | 固定流转 a→b |
| `add_conditional_edges` | builder 方法 | `add_conditional_edges(src, fn, map)` | 条件分支，根据 state 动态路由 |
| `set_entry_point` | builder 方法 | `set_entry_point(name)` | 指定入口节点 |
| `compile` | builder 方法 | `compile(checkpointer=...)` | 编译成可执行图 |
| `invoke` | compiled 方法 | `invoke(state, config)` | 一次性执行完，返回最终 State |
| `stream` | compiled 方法 | `stream(input, config, stream_mode)` | 流式执行，每个节点 yield 一次 |
| `get_state` | compiled 方法 | `get_state(thread_config)` | 读取某次运行的状态快照 |
| `interrupt` | langgraph.types | `interrupt(payload)` | 在节点内暂停图执行 |
| `Command` | langgraph.types | `Command(resume=value)` | 恢复执行，value 成为 interrupt() 返回值 |
| `Send` | langgraph.types | `Send(node, state)` | 创建并行子任务 |
| `SqliteSaver` | langgraph.checkpoint.sqlite | `SqliteSaver(conn)` | 基于 SQLite 的状态持久化 |
| `TypedDict` | typing（标准库） | 定义 dict 字段结构 | 定义 State 结构 |
| `Annotated` | typing（标准库） | `Annotated[T, reducer]` | 给字段附加 Reducer 合并逻辑 |
| `operator.add` | operator（标准库） | 列表拼接 | 内置 Reducer，直接 `+` 合并列表 |

---

## 九、项目文件索引

想深入看项目代码，从这些文件入手：

| 文件 | 内容 | 适合学什么 |
|------|------|-----------|
| `graphs/execution_graph.py` | 3 个子图（execution/report/knowledge） | **State/Node/Edge/Compile 四件套入门** |
| `graphs/state.py` | SOPState 定义 + 全部 Reducer | **TypedDict/Annotated/Reducer 机制** |
| `graphs/sop_graph.py` | 父图编排 + route_next_phase | **条件路由 + 子图嵌套** |
| `graphs/bug_analysis_graph.py` | Bug 分析 + HITL 审批 | **interrupt/Command + 循环修复** |
| `graphs/parallel_sop.py` | 多页面并行执行 | **Send API fan-out/fan-in** |
| `graphs/sop_runner.py` | 流式执行 + HITL 交互 | **stream + Command(resume) 完整流程** |
| `graphs/checkpoint.py` | SqliteSaver 配置 + 工具函数 | **checkpointer + get_state** |
| `graphs/review_graph.py` | 代码审查图（dict State） | **裸 dict 作为 State 的用法** |
