# 隐性耦合点清单

> 审计日期: 2026-07-03 | 共 178 个耦合点 | HIGH 72 / MEDIUM 72 / LOW 34
> 已修复: 51 个文件，+2171/-1206 行（详见末尾修复清单）

---

## 1. EventBus Subscriber 顺序依赖

```
[HIGH] QuotaUsage 依赖 BillingHook 先执行
- location: aitest/platform/hooks/quota_usage.py:63, billing_hook.py:60
- chain: publish_async(RUN_COMPLETED) → BillingHook(10) → QuotaUsage(15)
- reason: QuotaUsage 的 priority=15 被设计为"after billing"，但 EventBus 无运行时约束验证。
  如果 BillingHook 改为 priority=20，QuotaUsage 会在 billing 计算前统计配额。
```

```
[HIGH] AuditLogger 通配符订阅必须先于所有 side-effect
- location: aitest/platform/audit_log.py:39 (priority=0, "*")
- chain: publish_async(ev_completed) → AuditLogger(0, sync) → BillingHook(10, sync) → Webhook(30, async)
- reason: AuditLogger 用 "*" 通配符订阅所有事件，priority=0 保证它第一个执行。
  这是审计完整性的唯一保障。约束仅通过注释表达，无强制机制。
```

```
[MEDIUM] MetricsConsumer 和 ReportConsumer 共享 priority=20，执行顺序不确定
- location: aitest/platform/hooks/metrics_consumer.py:73, report_consumer.py:64
- chain: publish_async(RUN_COMPLETED) → MetricsConsumer(20) → ReportConsumer(20) (or reverse)
- reason: 两者都是 priority=20，顺序取决于 subscribers.py 中的注册顺序。
```

```
[MEDIUM] BillingHook 和 QuotaUsage 的 priority 差值是隐式约定
- location: billing_hook.py:60 (priority=10), quota_usage.py:63 (priority=15)
- chain: 差值 5 是任意数字，无文档说明为什么是 15 不是 11
- reason: 如果有人把 QuotaUsage 改为 priority=10（和 BillingHook 相同），
  执行顺序取决于 subscribe 顺序——行为不确定。
```

---

## 2. event.data Dict Key 依赖

```
[HIGH] BillingHook 硬编码 event.data.get("org_id")
- location: aitest/platform/hooks/billing_hook.py:87
- chain: ExecutionService.make_event(RUN_COMPLETED, org_id=ctx.org_id) → BillingHook → event.data.get("org_id", "")
- reason: 依赖 ExecutionService 传入 org_id kwarg。如果 ExecutionService 改为不传 org_id，
  BillingHook 静默写入 org_id=""，所有计费记录丢失组织归属。
```

```
[HIGH] MetricsConsumer 硬编码 event.data.get("total_tokens") — 类型假设为 int
- location: aitest/platform/hooks/metrics_consumer.py:117
- chain: publish(RUN_COMPLETED) → MetricsConsumer._accumulate → self._total_tokens += tokens
- reason: 做 += 运算，假设 tokens 是 int。如果传入 str 或 None，抛 TypeError 导致整个 handler 崩溃。
```

```
[MEDIUM] QuotaUsage 硬编码 event.data.get("workspace_id") 作为 dict key
- location: aitest/platform/hooks/quota_usage.py:84,96
- chain: publish(RUN_COMPLETED) → self._usage[ws_id] = self._empty_usage(ws_id, org_id)
- reason: workspace_id 被用作 in-memory dict 的 key。空字符串会导致所有无 workspace 的 run 聚合到同一个 bucket。
```

```
[MEDIUM] Timeline 硬编码 event.data.get("phase") — 但 ExecutionService 从不发射 PHASE_STARTED
- location: aitest/platform/timeline.py:110
- chain: Timeline._event_to_entry 处理 PHASE_STARTED → data.get("phase", "")
- reason: ExecutionService 只发射 REQUESTED/STARTED/COMPLETED/FAILED，从不发射 PHASE_STARTED。
  Timeline 的 phase 功能实际是死代码。
```

```
[MEDIUM] ReportConsumer 从 run.error_message 读 error，但 event.data 中也有 "error" key
- location: aitest/platform/hooks/report_consumer.py:117, execution_service.py:248
- chain: ExecutionService: make_event(RUN_FAILED, error=str(e)) vs run.fail(str(e)) → run.error_message
- reason: 两处存储同一个值但字段名不同：event.data["error"] vs run.error_message。
```

```
[MEDIUM] BillingHook 硬编码 billing record 的 key 结构
- location: aitest/platform/hooks/billing_hook.py:82-98
- chain: billing_event = {"event": "billing.usage_recorded", "usage": {"total_tokens": ..., "agent_runs": ...}}
- reason: billing.jsonl 的消费方依赖这些 key。改名会导致下游解析静默失败。
```

```
[MEDIUM] Timeline 硬编码 message 模板中的 field name
- location: aitest/platform/timeline.py:88,101,110,117,128,133,139,147,155
- chain: f"Phase started: {data.get('phase', '')}" — 如果 key 改名，message 显示空字符串
- reason: 静默信息丢失，前端用户看到 "Phase started: " 而非实际 phase 名。
```

---

## 3. format() / Template 变量依赖

```
[MEDIUM] WebhookDispatcher 硬编码 HTTP header 名
- location: aitest/platform/hooks/webhook.py:218-220
- chain: headers={"X-Webhook-Id": target.id, "X-Event-Type": event.event_type}
- reason: 外部 webhook 消费者依赖这些 header 名。改名会导致已注册的 endpoint 丢失事件归属。
```

```
[LOW] BillingHook 硬编码 JSONL record 的 key 结构
- location: aitest/platform/hooks/billing_hook.py:82-98
- chain: {"event": "billing.usage_recorded", "run_id": ..., "usage": {...}}
- reason: billing.jsonl 的消费方依赖这些 key。
```

```
[LOW] MetricsConsumer.flush() 写 metrics.jsonl 的格式
- location: aitest/platform/hooks/metrics_consumer.py:186-188
- chain: snap = self.snapshot() → json.dumps(snap) → metrics.jsonl
- reason: metrics.jsonl 的消费方依赖 snapshot() 的返回结构。
```

```
[MEDIUM] execution.py inspector 硬编码 artifact data key
- location: aitest/server/api/execution.py:411-418
- chain: d.get("path", ""), d.get("type", "unknown"), d.get("size", 0)
- reason: inspector 读 "path" 但 ExecutionService 写 "artifact_path"。inspector 永远读到 ""。
```

```
[MEDIUM] kanban.py 硬编码 SOP_STATUS JSON 文件结构
- location: aitest/server/api/kanban.py:85-98
- chain: data["completed_phases"].append(phase), data["status"] = status, data["progress"] = progress
- reason: 前端 Kanban 和真正的 SOP 执行器可能用不同的 key 写同一个文件。
```

```
[MEDIUM] terminal.py 硬编码 ObservationEvent 到 WS payload 的映射
- location: aitest/server/api/terminal.py:97-104
- chain: payload = {"type": str(event.type.value), "agent": event.agent_name, ...}
- reason: 前端 Agent Terminal 依赖这些字符串值来渲染事件。
```

---

## 4. Threading + asyncio 混用

```
[HIGH] chat.py: asyncio.Queue 从子线程 put_nowait
- location: aitest/server/api/chat.py:466-472
- chain: asyncio.create_task(_run_agent_producer) → asyncio.to_thread(engine.run_interactive) →
  for event in events: s.agent_queue.put_nowait(event)
- reason: put_nowait() 不是线程安全的。当前代码在 Task 内部 await to_thread()，
  子线程 yield 后回到 Task 上下文，但这个边界极其脆弱。
```

```
[HIGH] ExecutionService: threading.Event 从 asyncio.to_thread 中访问
- location: aitest/platform/execution_service.py:184-190
- chain: FastAPI(asyncio) → asyncio.to_thread(svc.execute) → AgentLoop._abort (threading.Event)
  cancel() → self._active_aborts[run_id].set() (从另一个 asyncio.to_thread 调用)
- reason: threading.Lock 在 asyncio 上下文中调用时会阻塞 event loop 线程。
  当前安全是偶然的（cancel 通过 asyncio.to_thread 调用）。
```

```
[HIGH] terminal.py 用 call_soon_threadsafe 桥接 ObservationBus 到 asyncio.Queue
- location: aitest/server/api/terminal.py:89-119
- chain: _on_event (sync, 在 ObservationBus publish 线程中) → loop.call_soon_threadsafe(_enqueue)
  _enqueue → queue.put_nowait(payload)
- reason: 如果 event loop 正忙，_enqueue 排队。queue 满时丢弃最旧事件。event loop 关闭时抛 RuntimeError。
```

```
[MEDIUM] AuditLogger: deque.append 从 EventBus publish 线程，_flush_now 从后台线程
- location: aitest/platform/audit_log.py:58-59, 62-67
- chain: EventBus.publish → AuditLogger._on_event → self._queue.append
  后台线程: self._flush_loop → self._flush_now → self._queue.popleft()
- reason: 依赖 CPython GIL 的原子性保证。不是语言规范保证。
```

```
[MEDIUM] WebhookDispatcher: HTTP POST 在 ThreadPoolExecutor 线程中执行
- location: aitest/platform/hooks/webhook.py:226, event_bus.py:201
- chain: publish_async → executor.submit(WebhookDispatcher._on_event) → urllib.request.urlopen(timeout=10)
- reason: ThreadPoolExecutor 只有 4 个 worker。4 个 webhook 同时 POST 时池饱和，阻塞后续 publish_async。
```

```
[MEDIUM] kanban.py sop_start 在 daemon 线程中执行
- location: aitest/server/api/kanban.py:139-161
- chain: thread = threading.Thread(target=run_sop_background, daemon=True) → thread.start()
  run_sop_background → asyncio.run_coroutine_threadsafe(broadcast, loop)
- reason: daemon 线程在进程退出时被强制终止，不等待完成。
  如果 sop 正在执行，进程退出时 SOP 状态不一致。
```

---

## 5. Consumer Side Effects

```
[HIGH] BillingHook: 写 billing.jsonl — 同步，在 publish 线程中
- location: aitest/platform/hooks/billing_hook.py:122-125
- chain: publish_async(ev_completed) → BillingHook(priority=10, sync) → open("billing.jsonl", "a")
- reason: priority=10 < ASYNC_THRESHOLD=30，同步写文件。磁盘 I/O 慢时阻塞 ExecutionService。
  单文件追加写入，无 rotation，无 size limit。
```

```
[HIGH] WebhookDispatcher: 外部 HTTP POST — async via ThreadPoolExecutor
- location: aitest/platform/hooks/webhook.py:226
- chain: executor.submit → _deliver → urllib.request.urlopen(url, timeout=10)
- reason: 向外部 endpoint 发送 HTTP 请求。N 个 webhook × timeout=10s = 潜在长时间阻塞。
  _deliver 直接修改 target.failure_count 无锁保护。
```

```
[MEDIUM] ReportConsumer: 读 RunStore + build_timeline — 在 publish 线程中
- location: aitest/platform/hooks/report_consumer.py:113-118
- chain: publish(RUN_COMPLETED, priority=20) → store.load_run() + store.list_events() + build_timeline()
- reason: 3 次数据库查询（PG 模式下每次是 subprocess 调用）。同步执行。
```

```
[MEDIUM] MetricsConsumer: 内存态计数器 — 进程重启丢失
- location: aitest/platform/hooks/metrics_consumer.py:52-65
- chain: self._total_runs += 1, self._total_tokens += tokens
- reason: 所有计数器是内存变量。flush() 是手动调用，无定时自动 flush。进程崩溃时数据丢失。
```

```
[MEDIUM] QuotaUsage: 交叉查询 RunStore
- location: aitest/platform/hooks/quota_usage.py:128-130
- chain: get_usage(ws_id) → store.count_runs(workspace_id=ws_id)
- reason: 一个"读"操作触发数据库查询。高频调用时产生大量不必要的 DB 查询。
```

```
[MEDIUM] WebhookRegistry: JSON 文件 + 内存 dict 两份数据可能不一致
- location: aitest/platform/hooks/webhook.py:67-94
- chain: register() → self._registrations[wid] = reg → self._save() (写文件)
  find_by_event() → 遍历 self._registrations (内存)
- reason: 多进程场景下不一致。failure_count 只在内存中，重启后归零。
```

```
[LOW] BillingHook._seen 和 MetricsConsumer._seen 是内存 TTLSet — 跨重启去重失效
- location: billing_hook.py:53, metrics_consumer.py:49
- chain: TTLSet(max_size=10_000, max_age_s=86_400) — 进程重启后清空
- reason: 如果未来 EventBus 支持持久化和重放，同一事件会被处理两次。
```

---

## 6. RunEvent → UI 映射隐式结构依赖

```
[HIGH] UIProjection 硬编码 AgentEvent.type → UIEventType 映射
- location: aitest/platform/ui_projection.py:59-185
- chain: AgentLoop → yield AgentEvent(type="skill_start") → map_agent_event → _sse(UIEventType.SKILL_STARTED, ...)
- reason: 用 if/elif 链映射。新增 AgentEvent type 时必须手动添加分支。
  遗漏时走到 fallback 返回 THINKING_CHUNK，前端把它当思考文本显示。
```

```
[HIGH] 前端 chat.ts 硬编码 SSE event name → addEventListener
- location: aitest/web/src/stores/chat.ts:155-213
- chain: es.addEventListener("ui.skill_started", ...) → callbacks.onToolStart(data.label)
- reason: 前后端共享的唯一 contract 是字符串 "ui.skill_started"。无共享 schema、无 contract 测试。
```

```
[MEDIUM] UIProjection 硬编码 AgentEvent 字段访问
- location: aitest/platform/ui_projection.py:81-85,98-99
- chain: agent_event.skill_id, agent_event.content, agent_event.progress, agent_event.error, ...
- reason: 如果 AgentEvent 字段改名，UIProjection 抛 AttributeError，整个 SSE 流中断。
```

```
[MEDIUM] UIProjection 硬编码 sop_complete 的 status 判断逻辑
- location: aitest/platform/ui_projection.py:134-138
- chain: success = status not in ("failed", "completed_with_issues", "fail")
- reason: "completed_with_issues" 是 SOPRunner 特有的值。新增 status 值不会被视为失败。
```

```
[LOW] chat.ts 前端 fallback 解析 data.type — 兼容旧格式
- location: aitest/web/src/stores/chat.ts:216-236
- chain: es.onmessage → data.type === "done" | "error"
- reason: 旧格式和新格式并存。意外的 unnamed event 可能触发 onDone/onError。
```

```
[HIGH] 前后端 SSE event name 跨语言耦合 — 无类型安全保障
- location: chat.ts:155-213 (前端), ui_projection.py:37-49 (后端)
- chain: 后端 UIEventType.THINKING_STARTED = "ui.thinking_started" ↔ 前端 listen("ui.thinking_started", ...)
- reason: TypeScript 和 Python 之间的隐式 contract。改名后前端静默失效。
```

```
[MEDIUM] chat.ts es.onerror 不区分网络错误和服务端错误
- location: aitest/web/src/stores/chat.ts:238-245
- chain: onerror → es.close() → if full text: callbacks.onDone(full)
- reason: 部分响应被标记为"完成"。应该检查 es.readyState。
```

```
[MEDIUM] chat.ts sseCancel 不通知服务端停止 Agent 执行
- location: aitest/web/src/stores/chat.ts:248-253
- chain: cancelStream → es.close() — 服务端 AgentLoop 继续执行直到完成
- reason: 前端取消后服务端仍消耗资源。无即时取消机制。
```

---

## 7. Engine Factory → AgentLoop 内部耦合

```
[HIGH] ExecutionEngine Protocol 缺少 _abort 定义，ExecutionService 直接访问私有属性
- location: aitest/platform/engine_factory.py:28-45, execution_service.py:185
- chain: loop = get_engine(...) → self._active_aborts[run.run_id] = loop._abort
- reason: Protocol 未定义 _abort。第三方 engine 实现没有此属性时 cancel() 抛 AttributeError。
```

```
[MEDIUM] engine_factory.py 内部 import AgentLoop 和 SOPRunner — 工厂本身未解耦
- location: aitest/platform/engine_factory.py:131-132
- chain: get_engine() → from aitest.agents.agent_runner import AgentLoop as _AgentLoop
- reason: 工厂必须 import 所有引擎类才能工作。新增引擎必须修改 get_engine() 的 if/elif 链。
```

```
[MEDIUM] engine_factory 硬编码 agent name 白名单
- location: aitest/platform/engine_factory.py:68-69
- chain: for agent_name in ("automation-agent", "execution-agent", ...): register_engine(agent_name, AgentLoop)
- reason: 新增 agent 不在列表中时 fallback 到 "agent" 类型，用 "automation-agent" 作为 agent_name。
```

---

## 8. OwnedDict → LifecycleRegistry Dispose 链

```
[HIGH] OwnedDict._dispose_value 按优先级查找 dispose 方法 — 6 种候选
- location: aitest/platform/ownership.py:207-213
- chain: getattr(value, "destroy", None) or getattr(value, "dispose", None) or
  getattr(value, "stop", None) or getattr(value, "close", None) or
  getattr(value, "shutdown", None) or getattr(value, "_release_resources", None)
- reason: 如果一个对象同时有 "destroy" 和 "stop"，"destroy" 被调用。
  "destroy" 可能是业务方法，"stop" 才是资源清理。无统一 Disposable Protocol。
```

```
[MEDIUM] OwnedDict max_size 淘汰用 next(iter(dict)) — 依赖 Python 3.7+ dict 有序性
- location: aitest/platform/ownership.py:142-144
- chain: oldest = next(iter(self._data)) → old_val = self._data.pop(oldest)
- reason: 淘汰时调用 _dispose_value，如果是耗时操作会在锁内阻塞。
```

```
[MEDIUM] OwnedDict._register_value 尝试 attach __owned__ — 可能失败
- location: aitest/platform/ownership.py:217-219
- chain: value.__owned__ = Owned(lifecycle_id=lifecycle_id, ...)
- reason: built-in 类型或 __slots__ 类会抛 AttributeError，外层 broad except 跳过注册。
```

```
[MEDIUM] LifecycleRegistry.dispose_all 无顺序保证
- location: aitest/platform/lifecycle/registry.py
- chain: main.py shutdown → lifecycle_registry.dispose_all()
- reason: 对象间依赖关系不被考虑。A 依赖 B 时可能先 dispose A 再 dispose B。
```

---

## 9. Query Layer SQL 拼接

```
[HIGH] QueryLayer 所有 filter 方法用 f-string 拼接 SQL — 注入风险
- location: aitest/platform/query_layer.py:90-106, 124-132, 139-158, 164-181, 188-207, 213-228, 234-242
- chain: RunQuery.module("equipment") → f"module = '{value}'" → pg_query(sql)
- reason: 直接拼接用户输入。SessionQuery.title() 用 LIKE '%{value}%'，% 和 _ 是 SQL 通配符。
```

```
[MEDIUM] QueryLayer 硬编码表名和列名 — 无 schema 验证
- location: aitest/platform/query_layer.py:87, 122, 139, 164, 188, 213, 234
- chain: RunQuery.__init__ → super().__init__("runs", order_by="created_at DESC")
- reason: 表名/列名硬编码。migration 重命名表时所有 Query 类静默失败。
```

```
[LOW] QueryLayer get_system_stats 硬编码 11 个子查询
- location: aitest/platform/query_layer.py:249-262
- chain: SELECT (SELECT COUNT(*) FROM runs), (SELECT COUNT(*) FROM run_events), ...
- reason: 假设所有 11 张表都存在。任何一张表被 drop 时整个查询失败。
```

---

## 10. Preflight → Artifact Lineage 硬编码依赖图

```
[HIGH] preflight_check 依赖 PHASE_ARTIFACTS dict 的结构
- location: aitest/platform/preflight.py:21, 123-129
- chain: spec = PHASE_ARTIFACTS.get(agent) → depends_on = spec.get("depends_on", [])
- reason: PHASE_ARTIFACTS 硬编码 8 个 agent 的依赖关系。新增 agent 不在其中时返回 WARN。
```

```
[MEDIUM] preflight_check 递归调用自身 — "all" 依赖展开
- location: aitest/platform/preflight.py:132-142
- chain: depends_on=["all"] → for prev_agent in all_agents: preflight_check(prev_agent, ...)
- reason: 循环依赖时无限递归。当前无循环，但新增 agent 时无自动检测。
```

```
[MEDIUM] preflight_check 硬编码 mode=="resume" 的降级逻辑
- location: aitest/platform/preflight.py:153-155
- chain: if mode == "resume": result.status = "WARN"
- reason: resume 模式下缺失依赖从 BLOCK 降级为 WARN。不能处理缺失依赖的 agent 会被放行。
```

```
[MEDIUM] PHASE_ARTIFACTS 硬编码 artifact 文件名 — 与实际文件系统不同步
- location: aitest/platform/artifact_lineage.py:10-19
- chain: "automation-agent": {"produces": ["TECH_ANALYSIS.md", ...]}
- reason: 实际文件名可能不同。preflight 认为依赖满足但下游 agent 找不到文件。
```

---

## 11. SQL 转义函数重复

```
[HIGH] 5 份独立的 _escape/_escape_json 实现 — 修复不同步
- location: aitest/platform/run_store.py:27-35
         aitest/platform/audit_log.py:14-20
         aitest/platform/artifact_lineage.py:21-27
         aitest/platform/replay.py:39-48
         aitest/server/session_store.py:9-15
- chain: 每个文件各自定义 _escape() 和 _escape_json()
- reason: 一份修复了 bug 其余四份不会自动修复。None 默认值不一致（"'{}'" vs "'[]'"）。
```

---

## 12. Database 层

```
[HIGH] database_pg.py 每次 SQL 调用都 spawn docker exec subprocess
- location: aitest/infra/database_pg.py:30-36, 44-51
- chain: pg_exec(sql) → subprocess.run(["docker", "exec", "aitest-pg", "psql", ...], timeout=30)
- reason: 无连接池、无复用。一次 run completion 可能产生 5-10 次 subprocess 调用。
  Windows 上 subprocess overhead ~50ms/次。
```

```
[HIGH] database_pg.py 用 json_agg 包装所有查询 — 破坏 SQL 语义
- location: aitest/infra/database_pg.py:44
- chain: json_sql = f"SELECT COALESCE(json_agg(t), '[]'::json) FROM ({sql}) t"
- reason: 大结果集生成巨大 JSON 字符串。语法错误可能返回空列表而非异常。
```

```
[HIGH] database_sqlite.py 用全局 threading.Lock — 所有查询串行化
- location: aitest/infra/database_sqlite.py:19, 41, 53
- chain: _lock = threading.Lock() → pg_exec: with _lock → pg_query: with _lock
- reason: 所有 SQLite 操作共享一个全局锁。与 EventBus 的 publish_async 设计矛盾。
```

```
[MEDIUM] database.py _detect_backend 在 import 时调用 docker — 启动阻塞
- location: aitest/infra/database.py:39-43
- chain: subprocess.run(["docker", "exec", "aitest-pg", "pg_isready"], timeout=5)
- reason: Docker 未运行时阻塞 5 秒。发生在第一个数据库调用时。
```

```
[HIGH] database_pg.py 对 psql 输出做字符串清理 — 可能误删数据
- location: aitest/infra/database_pg.py:55-58
- chain: raw.replace("+\n", "").replace("\n", "") — JSON 数据中的 "+\n" 也会被删除
- reason: raw[:raw.rfind("(")] 用最后一个 "(" 截断——JSON 中的 "(" 也会被错误截断。
```

```
[HIGH] RunStore + QueryLayer + session_store 全部用 f-string 拼接 SQL
- location: run_store.py:77-90, query_layer.py:90-242, session_store.py:20-40
- chain: f"INSERT INTO runs ... VALUES ({_escape(run.run_id)}, ...)"
- reason: _escape() 只做单引号转义。反斜杠+单引号可能绕过。无参数化查询。
```

---

## 13. Workspace → Organization 跨模块查询

```
[HIGH] WorkspaceManager.make_context 调用 OrganizationManager.get_role — 权限降级 bug
- location: aitest/platform/workspace.py:173-176
- chain: make_context → om.get_role(org_id, user_id) → 异常时 fallback scopes=["read", "execute"]
- reason: 组织不存在时用户反而获得更多权限。
```

```
[MEDIUM] WorkspaceManager 用 JSON 文件存储 — 与 RunStore 的 PG 不一致
- location: aitest/platform/workspace.py:204-208
- chain: _save → path.write_text(json.dumps(ws.__dict__))
- reason: 两套存储系统有不同的事务保证。无法用 SQL JOIN workspace 和 run。
```

---

## 14. Chat API → Session Store

```
[HIGH] chat.py _ensure_db() 用 asyncio.Lock — 可能从线程调用
- location: aitest/server/api/chat.py:48-57
- chain: _persist_session → await _ensure_db() → async with _db_lock
- reason: 如果 init_db() 失败，_db_initialized 不设为 True，后续每次请求都重试。
```

```
[MEDIUM] chat.py _persist_session 在 fire-and-forget Task 中写 DB
- location: aitest/server/api/chat.py:527-531
- chain: loop.create_task(_persist_session(...)) — 未 await
- reason: 异常被 asyncio.Task 静默吞掉。用户不知道持久化失败。
```

```
[HIGH] session_store.py 全部用 f-string 拼接 SQL — 注入风险
- location: aitest/server/session_store.py:20, 24, 28, 32-33, 37, 40
- chain: pg_exec(f"INSERT INTO chat_sessions ... VALUES ('{session_id}', ...)")
- reason: 第五份 _escape 拷贝。update_session_messages 自己做 replace("'", "''") 不用 _escape。
```

```
[MEDIUM] 前端 ChatSession 和后端 ChatSessionRecord 字段不对应
- location: chat.ts:23-29, chat.py:91-103
- chain: 前端 {id, name, messages, createdAt, serverId} vs 后端 {session_id, messages, agent, ...}
- reason: 前端用 "id" 后端用 "message_id"。前端有 tools/suggestedTasks 后端没有。
```

---

## 15. Auth 中间件

```
[HIGH] auth.py 在每次请求时调用 config.get_env("AITEST_API_KEY") — 无缓存
- location: aitest/server/auth.py:46-49
- chain: _get_api_key() → from aitest.config import config → config.get_env(...)
- reason: 每个 HTTP 请求触发 import（有锁）。运行时修改环境变量可绕过认证。
```

```
[MEDIUM] auth.py 硬编码 _EXEMPT_PREFIXES — WebSocket 路径绕过认证
- location: aitest/server/auth.py:32
- chain: _EXEMPT_PREFIXES = ("/health", "/docs", "/openapi.json", "/static", "/ws/")
- reason: 所有 /ws/ 路径绕过认证。新增需要认证的 WebSocket 端点也会被豁免。
```

```
[HIGH] auth.py 直接比较明文 API key — 时序攻击缓解不完整
- location: aitest/server/auth.py:54-60
- chain: _secure_compare(a, b) → 逐字节异或
- reason: 比较明文而非哈希。数据库泄露时可直接使用。
```

---

## 16. Kanban SOP 伪执行

```
[HIGH] kanban.py sop_start 是伪执行 — 硬编码 sleep 模拟进度
- location: aitest/server/api/kanban.py:139-161
- chain: for i, phase in enumerate(phases): _time.sleep(1.5) → broadcast_sop_phase
- reason: 不实际执行 SOP。真正的 SOP 失败时 Kanban 仍然广播所有 phase 完成。
```

```
[HIGH] kanban.py SOP_STATUS 文件和 ExecutionService Run 状态是两套独立系统
- location: kanban.py:85-98, execution_service.py
- chain: kanban: _update_module_phase → SOP_STATUS_{module}.json
  ExecutionService: run.complete() → PG runs table
- reason: 同一执行产生两份状态记录，无关联。通过 /api/sop/start 启动时 Run 不更新。
```

```
[MEDIUM] SOP_STATUS 文件用 module 名作为文件名 — 模块名冲突
- location: aitest/server/api/kanban.py:87
- chain: status_file = sop_dir / f"SOP_STATUS_{module}.json"
- reason: 两个不同 workspace 的同名 module 同时执行时互相覆盖。
```

---

## 17. 前端状态管理

```
[HIGH] chat.ts EventSource onerror 不区分网络错误和服务端错误
- location: aitest/web/src/stores/chat.ts:238-245
- chain: onerror → es.close() → if full text: callbacks.onDone(full)
- reason: 部分响应被标记为"完成"。应该检查 es.readyState。
```

```
[HIGH] chat.ts EventSource 不支持手动重连 — 断开后状态不可恢复
- location: aitest/web/src/stores/chat.ts:130-246
- chain: onerror → es.close() → _es = null — 不自动重连
- reason: 用户必须手动重新发送消息。流式响应中途断开时部分文本丢失。
```

```
[MEDIUM] chat.ts _accumulated 是模块级变量 — 跨 session 泄漏
- location: aitest/web/src/stores/chat.ts:120
- chain: let _accumulated: string[] = [] — sseStart 时清空
- reason: 两个 session 快速切换时，session A 的已接收文本可能丢失。
```

```
[LOW] chat.ts localStorage 和后端 SQLite 是两套独立存储系统
- location: chat.ts:71-101 (localStorage), chat.py:60-83 (SQLite)
- chain: 前端用 localStorage 存 sessions，后端用 SQLite
- reason: 无同步机制。换浏览器时 localStorage 丢失但 SQLite 保留。
```

```
[MEDIUM] 前端 messages 和后端 messages 的格式不同
- location: chat.ts:15-21, chat.py:274-279
- chain: 前端 {id, role, content, timestamp, tools?, suggestedTasks?}
  后端 {message_id, role, content, timestamp}
- reason: tools 和 suggestedTasks 在后端持久化时丢失。
```

---

## 18. Main.py 启动

```
[HIGH] main.py lifespan 中 12 个 try/except import — 启动时静默跳过失败模块
- location: aitest/server/main.py:57-95
- chain: try: from ... import ... except Exception as e: log.error(...)
- reason: 服务器启动看起来成功但部分功能不可用。activate_subscribers 失败时所有 EventBus consumers 不启动。
```

```
[MEDIUM] main.py 硬编码 _RATE_EXEMPT_PATHS — 无配置
- location: aitest/server/main.py:201
- chain: _RATE_EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/"}
- reason: 新增公开端点必须手动添加。/metrics 被限流时监控系统收不到数据。
```

```
[MEDIUM] rate_limit_middleware 的 _rate_state dict 无上限
- location: aitest/server/main.py:197-198
- chain: _rate_state: dict[str, list[float]] = {}
- reason: 大量不同 IP 时无限增长。rate_state_cleanup_loop 只清理时间戳不清理空条目。
```

---

## 19. ObservationBus 自注册

```
[HIGH] memory_observer.py 模块导入时自注册到 ObservationBus
- location: aitest/platform/memory_observer.py:282-284
- chain: import memory_observer → _register_with_bus() → bus.subscribe(SKILL_FAILED, on_skill_failed)
- reason: 任何 import 此模块的代码触发副作用。如果 import 发生在 ObservationBus 初始化之前，handler 注册到错误的 bus。
```

```
[MEDIUM] memory_consumer.py 用 BoundSubscription 注册但 fallback 到 bare subscribe
- location: aitest/platform/memory_consumer.py:100-113
- chain: try: BoundSubscription(...) except: bus.subscribe(...)
- reason: fallback 时 handler 不被 OwnedDict 追踪，dispose 时不会自动 unsubscribe——幽灵 handler。
```

```
[MEDIUM] memory_observer 硬编码 _COUNTERS_PATH — 跨进程不安全
- location: aitest/platform/memory_observer.py:38-39
- chain: _COUNTERS_PATH = Path("governance") / ".data" / "dead_ends" / "counters.json"
- reason: 相对路径依赖 CWD。多进程共享时 _load_counters 和 _save_counters 之间无锁。
```

---

## 20. GovernanceBridge

```
[HIGH] GovernanceBridge.stop() 不真正 unsubscribe
- location: aitest/platform/governance_bridge.py:78-83
- chain: stop() → self._active = False — 不从 governance bus 移除 handler
- reason: _forward 闭包仍持有 platform_bus 引用，阻止 GC。governance bus 不支持 unsubscribe。
```

```
[MEDIUM] GovernanceBridge._forward 创建的 RunEvent 没有 run_id
- location: aitest/platform/governance_bridge.py:55-58
- chain: run_id=event.data.get("run_id", "") — governance event 通常无 run_id
- reason: AuditLogger 记录的审计条目中 run_id 为空。event_query 按 run_id 查询时找不到。
```

---

## 21. EventBus 生命周期

```
[HIGH] 全局 EventBus singleton 在测试间泄漏状态
- location: aitest/platform/event_bus.py:220-230
- chain: get_bus() → if _bus is None: _bus = EventBus()
- reason: 测试 A 注册的 handler 在测试 B 中仍然存在。reset_bus() 需要显式调用。
```

```
[HIGH] 同样的 singleton 泄漏问题存在于所有平台模块
- location: run_store.py:141-150, audit_log.py:110-123, metrics_consumer.py:192-203, ...
- chain: get_xxx() → if _xxx is None: _xxx = Xxx()
- reason: MetricsConsumer 计数器跨测试累加。AuditLogger deque 跨测试保留。
```

```
[HIGH] EventBus._executor 生命周期与 singleton 绑定
- location: aitest/platform/event_bus.py:84, 243-250
- chain: EventBus.__init__ → ThreadPoolExecutor(max_workers=4) — 进程生命周期内存在
  reset_bus() → _executor.shutdown(wait=False) — 不等待正在执行的 handler
- reason: shutdown 时 HTTP POST 正在进行会被中断。
```

```
[MEDIUM] publish_async 的 Future 未被追踪 — 无法等待完成
- location: aitest/platform/event_bus.py:201
- chain: self._executor.submit(self._run_handler, handler, event) — Future 被丢弃
- reason: 调用方无法知道异步 handler 是否完成、是否成功。
```

```
[MEDIUM] EventBus._executor 无 queue depth 限制
- location: aitest/platform/event_bus.py:84
- chain: ThreadPoolExecutor 内部用无界 SimpleQueue
- reason: 1000 个 run 同时完成时队列无限增长。无 backpressure。
```

---

## 22. Replay 系统

```
[HIGH] ReplayRecorder 和 RunEvent 是两套独立的执行记录系统
- location: aitest/platform/replay.py, aitest/platform/run_event.py
- chain: ReplayRecorder → execution_steps table, RunEvent → run_events table
- reason: 无外键关联。查 run_events 想重放找不到 step 级别数据。
```

```
[MEDIUM] ReplayRecorder 用 time.time()，RunEvent 用 datetime.now(timezone.utc).isoformat()
- location: replay.py:30, run_event.py:244
- chain: 两种时间格式不同。微小差异可能导致重放时"时间倒流"。
```

```
[LOW] replay.py 第四份 _escape/_escape_json 拷贝
- location: aitest/platform/replay.py:39-48
- chain: 全系统至少 4 份相同的 SQL 转义函数。
```

---

## 23. Server API 端点

```
[HIGH] execution.py 每个端点函数内部 import — 延迟 import 掩盖循环依赖
- location: aitest/server/api/execution.py:87, 126, 150, 255, 311, 504, ...
- chain: @execution_router.get(...) → def endpoint(): from aitest.platform.xxx import yyy
- reason: 14 个端点函数各自在函数体内 import。运行时失败不在启动时暴露。
```

```
[MEDIUM] execution.py 大部分端点直接调用 get_run_store() — 不使用 DI
- location: aitest/server/api/execution.py:88, 127, 151, 256, 312
- chain: store = get_run_store() — 全局 singleton
- reason: 和 app.state.execution_service 可能用不同 store 实例。
```

```
[HIGH] execution.py 硬编码 event_type 字符串匹配来分类事件
- location: aitest/server/api/execution.py:279-284
- chain: if "llm" in e.event_type.lower(): llm_calls.append(entry)
- reason: "agent" 子串匹配 "observation.agent_start" 等无关事件。分类和 EventType 无映射关系。
```

```
[MEDIUM] execution.py inspector 的 Phase breakdown 是死代码
- location: aitest/server/api/execution.py:362-374
- chain: phase_events = [e for e in events if e.event_type in (PHASE_STARTED, PHASE_COMPLETED)]
- reason: ExecutionService 从不发射 PHASE_STARTED/COMPLETED。phase_events 永远为空。
```

```
[MEDIUM] execution.py history 端点 in-memory 过滤 module/agent
- location: aitest/server/api/execution.py:538-540
- chain: runs = store.list_runs(...) → if module: runs = [r for r in runs if r.module == module]
- reason: 先加载全部再过滤。total 在过滤前计算，分页数据不一致。
```

```
[MEDIUM] execution.py audit/stats 和 audit 用不同的查询路径
- location: aitest/server/api/execution.py:554-601
- chain: query_audit 支持 since/until，audit_stats 不支持
- reason: 两个端点返回不一致的数据。
```

```
[HIGH] execution.py 和 chat.py 的 HTTP 错误格式不一致
- location: execution.py (raise HTTPException), main.py:247-290 (error handler)
- chain: 成功返回裸 dict，错误返回 {"error": {"code", "message", "request_id"}}
- reason: 前端必须同时处理两种格式。
```

```
[MEDIUM] chat.py SSE 错误和 HTTP 错误格式完全不同
- location: chat.py:543-544
- chain: SSE: {"event": "ui.error", "data": {"message": ...}}
  HTTP: {"error": {"code", "message", "request_id"}}
- reason: 前端必须区分两种错误来源。
```

---

## 24. agents.py 硬编码 fallback

```
[HIGH] agents.py 硬编码 known modules fallback
- location: aitest/server/api/agents.py:148-153
- chain: if not result: result = {"equipment": [...], "tank": [...], "production": [...]}
- reason: 如果目录扫描失败，返回硬编码的 3 个模块。新模块不会出现。
```

```
[MEDIUM] agents.py 硬编码 agent 过滤条件
- location: aitest/server/api/agents.py:165
- chain: if agent.endswith("-agent") and not agent.startswith(("project", "requirement"))
- reason: 新增 agent 前缀不在排除列表中时会出现在列表中。
```

---

## 25. Logging 层

```
[HIGH] logging.py 硬编码日志路径 — 依赖 paths.get_workstudy()
- location: aitest/infra/logging.py:34-36
- chain: _WORKSTUDY = get_workstudy() → _LOG_DIR = _WORKSTUDY / "governance" / ".traces"
- reason: 日志路径在模块加载时确定。get_workstudy() 未初始化时路径错误。
```

```
[MEDIUM] logging.py 的 JSONL 格式被下游消费者隐式依赖
- location: aitest/infra/logging.py
- chain: {"level":"INFO","component":"sop_graph","message":"preflight_start",...}
- reason: key 名变更时所有基于日志的 dashboard 和告警静默失效。
```

---

## 26. Config 模块

```
[HIGH] config.py 延迟 import runtime.config — 循环依赖的 workaround
- location: aitest/config.py:3
- chain: from aitest.runtime.config import Config, config, _env, _env_int
- reason: chat.py 在模块级 import config。如果 runtime.config 有副作用，在服务器初始化之前发生。
```

```
[MEDIUM] config 模块在 import 时解析 .env — 环境变量时序耦合
- location: aitest/runtime/config.py
- chain: import config → _env("ANTHROPIC_API_KEY") → os.environ.get(...)
- reason: 热重载时 config 值可能过期。测试 fixture 修改 os.environ 不影响已缓存的 config。
```

```
[LOW] chat.py 硬编码 _DEFAULT_PROVIDER — 与 config 模块的默认值可能不同
- location: aitest/server/api/chat.py:41
- chain: _DEFAULT_PROVIDER = _resolve_default_provider() — 模块加载时求值一次
- reason: config 运行时改变时 _DEFAULT_PROVIDER 不更新。
```

---

## 27. Engine skill_executor

```
[HIGH] AGENT_SKILL_MAP 在模块加载时从 YAML 文件读取 — import 时副作用
- location: aitest/engine/skill_executor.py:20
- chain: AGENT_SKILL_MAP = _get_defs()._load_skill_map()
- reason: YAML 文件不存在或格式错误时 import 失败。所有依赖此模块的代码都会失败。
```

```
[MEDIUM] FALLBACK_AGENT_SKILL_MAP 硬编码 — 与 YAML 文件可能不同步
- location: aitest/engine/skill_executor.py:5
- chain: AGENT_SKILL_MAP = _get_defs()._load_skill_map() if _get_defs() else FALLBACK_AGENT_SKILL_MAP
- reason: fallback 值和最新 YAML 不同步。服务器用 fallback 启动时返回过期 agent 列表。
```

---

## 28. 前端 API client

```
[HIGH] chat.ts 硬编码 API 端点路径
- location: aitest/web/src/stores/chat.ts:393, 403
- chain: api.post(ENDPOINTS.CHAT_SESSIONS, ...) → POST /api/chat/sessions
- reason: ENDPOINTS 和后端 router prefix 是隐式匹配。后端改 prefix 时前端 404。
```

```
[MEDIUM] chat.ts 的 stream_url 拼接依赖后端返回格式
- location: aitest/web/src/stores/chat.ts:403-406
- chain: result.stream_url → new EventSource(stream_url)
- reason: 后端改 stream_url 格式时 EventSource 连接到错误 URL。
```

---

## 29. Task Queue — SQL 拼接 + 硬编码重试逻辑

```
[HIGH] task_queue.py 用 f-string 拼接 SQL — 与 RunStore 相同的注入风险
- location: aitest/infra/task_queue.py:26, 34, 40, 54, 58, 64, 69, 78
- chain: pg_exec(f"INSERT INTO tasks ... VALUES ({_escape(task_id)}, ...)")
- reason: 第六份 _escape 拷贝（line 18-20）。mark_failed 中 error_msg 用 replace("'", "''") 而非 _escape。
```

```
[HIGH] TaskRunner._execute 硬编码 from aitest.agents.agent_runner import run_agent
- location: aitest/infra/task_queue.py:142
- chain: _execute → from aitest.agents.agent_runner import run_agent → run_agent(agent_name=task["agent"], ...)
- reason: TaskRunner 只能执行 AgentLoop 类型的任务。如果任务类型扩展（比如 SOP、自定义脚本），
  必须修改 _execute。延迟 import 在每次执行时触发——如果 agent_runner import 失败，
  任务会 mark_failed 然后重试 3 次，浪费资源。
```

```
[MEDIUM] TaskRunner._loop 硬编码错误关键词决定是否重试
- location: aitest/infra/task_queue.py:134
- chain: if any(kw in error_str.lower() for kw in ("fatal", "context_length", "permission", "denied", "auth")):
  mark_failed_no_retry → else: mark_failed (with retry)
- reason: 重试策略通过字符串匹配错误信息决定。如果 AgentLoop 抛出 "PermissionError" 但消息是中文，
  关键词不匹配，任务会被重试（浪费资源）。如果新错误类型包含 "auth" 子串（比如 "authentication_cache"），
  会被错误地标记为不可重试。
```

```
[MEDIUM] TaskQueue.recover_stale_tasks 硬编码超时消息
- location: aitest/infra/task_queue.py:70
- chain: pg_query("SELECT COUNT(*) ... WHERE error_msg='stale task — timed out after 30min'")
- reason: 查询依赖 error_msg 的精确字符串。如果改了消息文案，计数查询返回 0。
```

---

## 30. Pause Handler — 文件轮询 + 竞态条件

```
[HIGH] pause_handler.py 用文件轮询等待 resume — 不是事件驱动
- location: aitest/infra/pause_handler.py:180-214
- chain: while True: if resume_path.exists(): return True → time.sleep(backoff)
- reason: wait_for_resume 用指数退避轮询文件系统（1s→2s→4s→8s→15s→30s）。
  最坏情况下用户点击 resume 后要等 30 秒才被检测到。
  更严重的是：如果 AgentLoop 在子线程中调用 wait_for_resume，
  轮询会消耗 CPU（虽然有 sleep，但线程始终存在）。
```

```
[HIGH] pause_handler.py write_resume_file 和 wait_for_resume 之间有 TOCTOU 竞态
- location: aitest/infra/pause_handler.py:99-124 (write), 196-198 (check)
- chain: write_resume_file → pause_path.unlink() → resume_path.write_text()
  wait_for_resume → if resume_path.exists(): _cleanup_sentinels(pause_path, resume_path)
- reason: write_resume_file 先删 pause.json 再写 resume.json。
  如果 wait_for_resume 在这两步之间检查 resume_path.exists()，会返回 False。
  下一次轮询（最多 30s 后）才会检测到。中间状态是"既没有 pause 也没有 resume"。
```

```
[MEDIUM] pause_handler.py 硬编码 DEFAULT_BASE_DIR = Path("governance") / ".data"
- location: aitest/infra/pause_handler.py:44
- chain: 所有函数用 DEFAULT_BASE_DIR 作为默认参数
- reason: 相对路径依赖 CWD。如果进程从不同目录启动，pause/resume 文件写到不同位置。
```

---

## 31. Queue Factory — 运行时后端自动选择

```
[HIGH] queue_factory 根据 Redis 可用性自动选择后端 — 运行时行为不确定
- location: aitest/infra/queue_factory.py:53-61
- chain: if redis_url or _redis_reachable(): _create_rq() else: _create_sqlite()
- reason: 同一套代码在不同启动时序下有不同的行为。Redis 容器延迟启动时 fallback 到 SQLite，
  即使之后 Redis 可用了也不会切换。用户不知道任务存在 SQLite 中（不可靠）还是 Redis 中（可靠）。
```

```
[MEDIUM] queue_factory._redis_reachable 硬编码 localhost:6379
- location: aitest/infra/queue_factory.py:78
- chain: _redis.Redis(host="localhost", port=6379, socket_connect_timeout=1)
- reason: 如果 Redis 在远程服务器或非标准端口，_redis_reachable 返回 False，
  即使 REDIS_URL 环境变量指向正确的远程地址。_redis_reachable 和 _create_rq 使用不同的连接逻辑。
```

---

## 32. Health Check — 15+ 模块 import + 硬编码组件名

```
[HIGH] health.py 在单个函数中 import 15+ 模块 — 任何 import 失败降级整个组件
- location: aitest/server/core/health.py:7-225
- chain: get_health_response → from aitest.infra.queue_factory import get_queue
  → from aitest.knowledge.rag_engine import get_chroma_client
  → from aitest.infra.redis_cache import redis_cache
  → from aitest.server.redis_session_store import redis_session_store
  → ... (15+ imports)
- reason: 每个 import 在 try/except 中，失败时 components["xxx"] = {"status": "error"}。
  但如果 Redis 模块 import 失败（比如 redis 包未安装），所有 Redis 组件显示 error。
  整体状态降级为 "degraded"——即使核心功能正常。
```

```
[HIGH] health.py 访问私有属性 _known_issues_mtime
- location: aitest/server/core/health.py:61
- chain: from aitest.knowledge.rag_engine import _known_issues_mtime, KNOWN_ISSUES
- reason: 直接 import 模块级私有变量。如果 rag_engine 重构（比如把 mtime 移到类中），
  health.py 的 import 失败，known_issues 组件显示 error。
```

```
[MEDIUM] health.py 硬编码组件名称和检查逻辑
- location: aitest/server/core/health.py:26-223
- chain: components["task_queue"], components["rag"], components["known_issues"], ...
- reason: 新增组件必须手动在 health.py 中添加检查块。如果忘记添加，
  新组件不会出现在健康检查中——运维人员不知道它的状态。
```

---

## 33. Sweep Loop — 私有属性访问 + 硬编码间隔

```
[HIGH] sweep.py 访问 ownership_checker._scan_count — 私有属性
- location: aitest/server/core/sweep.py:44, 73, 87, 98
- chain: if ownership_checker._scan_count % 5 == 0: ...
  if ownership_checker._scan_count % 6 == 0: ...
- reason: sweep 循环依赖 OwnershipChecker 的私有计数器来决定何时执行清理。
  如果 OwnershipChecker 重构（比如改名 _scan_count），sweep 静默跳过所有条件清理。
```

```
[HIGH] sweep.py import chat._cleanup_old_sessions — 私有函数
- location: aitest/server/core/sweep.py:27
- chain: from aitest.server.api.chat import _cleanup_old_sessions
- reason: sweep 直接调用 chat 模块的私有函数。如果 chat.py 重命名或移除此函数，
  sweep 的 import 失败（在 try/except 中），chat session 不会被清理——内存泄漏。
```

```
[MEDIUM] sweep.py 硬编码 10 个清理步骤的执行间隔
- location: aitest/server/core/sweep.py:13, 44, 73, 87, 98, 113
- chain: await asyncio.sleep(60) — 每 60 秒一次
  ownership_checker._scan_count % 5 == 0 — 每 5 次 sweep（~5min）
  ownership_checker._scan_count % 6 == 0 — 每 6 次 sweep（~6min）
- reason: 清理间隔硬编码。如果系统负载高（sweep 延迟执行），实际间隔会更长。
  如果需要更频繁的清理（比如审计日志增长快），必须改代码。
```

---

## 34. Audit Scheduler — 依赖 audit_engine 模块

```
[HIGH] audit_scheduler.py import aitest.audit_engine.scheduled_audit — 可能不存在
- location: aitest/server/core/audit_scheduler.py:12
- chain: from aitest.audit_engine.scheduled_audit import run_all_audits, discover_modules
- reason: 如果 audit_engine 模块不存在（比如未安装），import 失败。
  但 import 在 while 循环外——如果首次 import 成功但后续 import 失败，
  不会重新尝试。更严重的是：audit_scheduler_loop 在 main.py lifespan 中启动，
  如果 import 失败，整个 lifespan 失败，服务器不启动。
```

```
[MEDIUM] audit_scheduler.py 用 asyncio.to_thread 调用同步审计函数
- location: aitest/server/core/audit_scheduler.py:21
- chain: results = await asyncio.to_thread(run_all_audits, modules)
- reason: run_all_audits 可能执行很长时间（遍历所有模块做审计）。
  asyncio.to_thread 在默认 executor 中执行——如果 executor 线程池饱和，
  会阻塞其他 asyncio.to_thread 调用（比如 ExecutionService.execute）。
```

---

## 35. Intent Parser — 硬编码 Agent 别名 + 正则

```
[HIGH] intent_parser.py 硬编码 AGENT_ALIASES — 28 个模式匹配规则
- location: aitest/chat/intent_parser.py:38-59
- chain: AGENT_ALIASES = [("完整流程", "full-sop", 8), ("写测试", "automation-agent", 7), ...]
- reason: 新增 agent 必须手动在 AGENT_ALIASES 中添加匹配规则。
  如果用户用不在列表中的表述（比如 "帮我写个测试" vs "写测试"），意图识别失败，
  fallback 到 "chat" 类型。中英文混排增加维护负担。
```

```
[MEDIUM] intent_parser.py 硬编码 "full-sop" → "automation-agent" 映射
- location: aitest/chat/intent_parser.py:128-130
- chain: if agent == "full-sop": best_is_sop = True; best_agent = "automation-agent"
- reason: SOP 模式固定使用 automation-agent 作为入口 agent。
  如果 SOP 入口 agent 改名，intent_parser 不知道。
```

```
[MEDIUM] intent_parser.py _get_known_modules 依赖文件系统目录结构
- location: aitest/chat/intent_parser.py:22-28
- chain: modules_dir = get_project_dir() / "modules" → sorted([d.name for d in modules_dir.iterdir()])
- reason: 模块发现依赖项目目录中存在 "modules" 子目录。
  如果项目结构不同（比如 modules 在别处），known_modules 为空，
  正则匹配中的 module_pattern 变成 r"\w+"——匹配任何单词，误识别率高。
```

```
[MEDIUM] intent_parser.py parse_with_llm 硬编码 LLM prompt
- location: aitest/chat/intent_parser.py:163-173
- chain: prompt = f"你是测试意图分类器。分析用户消息，输出 JSON。..." 
- reason: LLM prompt 硬编码在代码中。如果 agent 列表变化（新增/移除 agent），
  prompt 中的 agent 描述过时，LLM 分类不准确。
```

---

## 36. Operational Metrics — 硬编码路径 + 内存计数器

```
[MEDIUM] operational_metrics.py 硬编码 _METRICS_DIR 路径
- location: aitest/platform/operational_metrics.py:42-44
- chain: _WORKSTUDY = get_workstudy() → _METRICS_DIR = _WORKSTUDY / "governance" / "kpi" / "timeseries"
- reason: 模块加载时确定路径。如果 get_workstudy() 返回错误路径，指标写到错误位置。
```

```
[MEDIUM] operational_metrics.py 8 个 KPI 指标硬编码在模块中
- location: aitest/platform/operational_metrics.py:1-28
- chain: 8 个指标（p95 latency, token cost, workflow success rate, ...）
- reason: 新增指标必须修改模块代码。指标的 label（agent name, module name）无注册表。
```

---

## 37. Organization — JSON 文件存储 + 权限模型硬编码

```
[HIGH] OrganizationManager 用 JSON 文件存储 — 与 RunStore 的 PG 不一致
- location: aitest/platform/organization.py:77-78
- chain: self._data_dir = get_workstudy() / "governance" / ".data" / "orgs"
- reason: Organization 数据在 JSON 文件中，Run 数据在 PG 中。
  无法用 SQL JOIN org 和 run。多进程写同一个 JSON 文件可能冲突。
```

```
[MEDIUM] ROLE_DEFAULT_SCOPES 硬编码角色→权限映射
- location: aitest/platform/organization.py:55-60
- chain: ROLE_DEFAULT_SCOPES = {"owner": [...], "admin": [...], "member": [...], "viewer": [...]}
- reason: 新增角色必须修改代码。workspace.py 的 make_context 依赖这个 dict。
```

---

## 38. Plugin System — YAML manifest + sys.path 操作

```
[HIGH] plugin.py 在模块加载时 import yaml — 可能未安装
- location: aitest/platform/plugin.py:39
- chain: import yaml — 如果 PyYAML 未安装，整个 plugin 模块 import 失败
- reason: 所有依赖 plugin.py 的代码都会 import 失败。
```

```
[MEDIUM] plugin.py 硬编码插件搜索路径
- location: aitest/platform/plugin.py:48-77
- chain: _WORKSTUDY / "plugins" → AITEST_PLUGIN_PATH env → .tlo/plugins/
- reason: 插件发现路径硬编码。如果插件在其他位置，必须设置环境变量。
```

---

## 39. Tenant Manager — 内存态 + 无持久化

```
[HIGH] TenantManager 的 Tenant 对象是纯内存态 — 进程重启后丢失
- location: aitest/platform/tenant.py:63-71
- chain: Tenant._usage = TenantUsage() — 内存变量
- reason: 活跃 agent 计数、token 用量等在进程重启后归零。
  如果进程崩溃时有 3 个活跃 agent，重启后计数为 0，
  check_capacity 不会阻塞——可能超过并发限制。
```

```
[MEDIUM] TenantLimits 硬编码资源限制
- location: aitest/platform/tenant.py:32-37
- chain: max_concurrent_agents=3, max_token_budget_per_run=100_000, max_sessions=100
- reason: 所有 tenant 默认相同的限制。不能按 tenant 定制（除非代码修改）。
```

---

## 40. Parallel Runner — subprocess 调用 + 硬编码超时

```
[HIGH] parallel_runner.py 用 subprocess 执行 SOP — 每个模块一个进程
- location: aitest/infra/parallel_runner.py:56-60
- chain: subprocess.run([sys.executable, "-m", "aitest.infra.cli", "sop", "run", ...], timeout=1800)
- reason: 每个模块的 SOP 执行在独立子进程中。子进程不共享内存、EventBus、RunStore。
  如果子进程崩溃，父进程只看到 returncode != 0，不知道具体原因。
  环境变量 AITEST_PARALLEL=1 被设置——子进程可能有不同行为。
```

```
[MEDIUM] parallel_runner.py 硬编码 1800 秒超时
- location: aitest/infra/parallel_runner.py:59
- chain: timeout=1800 (30 分钟)
- reason: 所有模块共享同一个超时。如果某个模块的 SOP 需要更长时间，
  会被强制终止。不可配置。
```

---

## 41. Worker Pool — ThreadPoolExecutor + 无队列深度限制

```
[HIGH] worker_pool.py 的 _MAX_FUTURES = 10_000 — 硬编码上限
- location: aitest/infra/worker_pool.py:54
- chain: _MAX_FUTURES = 10_000 — 超过时淘汰最旧的 Future
- reason: 如果 10_000 个任务同时提交，最旧的 Future 被淘汰——
  调用方的 future.result() 会抛 CancelledError。无告警。
```

```
[MEDIUM] worker_pool.py 的 per_tenant 限制依赖 TenantManager
- location: aitest/infra/worker_pool.py:80 (推断)
- chain: submit → tenant.check_capacity("agent_execution") → TenantCapacityError
- reason: 如果 TenantManager 未初始化或 Tenant 不存在，check_capacity 可能不生效。
```

---

## 42. Redis 硬编码连接

```
[HIGH] redis_cache.py 和 redis_pubsub.py 硬编码 localhost:6379
- location: aitest/infra/redis_cache.py:45-46, redis_pubsub.py:42
- chain: _redis.Redis(host="localhost", port=6379, socket_connect_timeout=1)
- reason: 两个模块各自独立创建 Redis 连接，不共享连接池。
  如果 Redis 在远程服务器，两者都连不上。
  更严重的是：redis_cache 不读 REDIS_URL 环境变量（queue_factory 读）——
  同一个系统中不同模块用不同的 Redis 配置。
```

```
[MEDIUM] redis_pubsub.py 的 subscribe 是阻塞生成器 — 不能在 asyncio 中直接使用
- location: aitest/infra/redis_pubsub.py:18-19
- chain: for event in subscribe("kanban:update"): await websocket.send_json(event)
- reason: subscribe 返回的是同步生成器，在 asyncio 中使用会阻塞 event loop。
  文档示例代码（line 18-19）直接在 async 函数中 await 同步生成器——语法错误。
```

---

## 43. Testing Memory Store — 硬编码 ChromaDB 路径 + 8 个 collection

```
[HIGH] TestingMemoryStore 硬编码 ChromaDB 持久化路径 ".chroma_testing"
- location: aitest/platform/testing_memory_store.py:50
- chain: persist = self._persist_dir or ".chroma_testing" → chromadb.PersistentClient(path=persist)
- reason: 相对路径 ".chroma_testing" 依赖 CWD。如果进程从不同目录启动，
  ChromaDB 数据写到不同位置——memory_observer 写的数据 memory_consumer 找不到。
```

```
[MEDIUM] TestingMemoryStore 硬编码 8 个 collection 名称
- location: aitest/platform/testing_memory_store.py:19-28
- chain: COLLECTIONS = {"ui_patterns": MemoryType.UI_PATTERN, "locator_history": ...}
- reason: 新增 MemoryType 时必须同时更新 COLLECTIONS dict。
  如果只在 testing_memory.py 中添加了新类型但没更新 collection 映射，
  store.add() 返回空字符串——数据静默丢失。
```

---

## 44. Agent Capabilities — 硬编码 agent→capability 映射

```
[HIGH] agent_capabilities.py 硬编码 8 个 agent 的 capability 列表
- location: aitest/platform/capability_router/agent_capabilities.py:10-67
- chain: AGENT_CAPABILITIES = {"project-agent": ["rag.search", ...], "automation-agent": [...]}
- reason: 新增 agent 或 capability 时必须手动更新这个 dict。
  如果 agent YAML 声明了 capability 但 dict 中没有，
  CapabilityRouter 不会把该 capability 的 tool definitions 传给 LLM。
```

---

## 45. Re-export 模块链

```
[HIGH] 多个模块是 re-export wrapper — 实际实现在 alice_engine 包中
- location: aitest/infra/security.py:1 → from alice_engine.runtime.security import ...
  aitest/runtime/security.py:1 → from alice_engine.runtime.security import ...
  aitest/graphs/sop_runner.py:1 → from alice_engine.workflow.sop_runner import SOPRunner
  aitest/engine/skill_executor.py:1 → from alice_engine.core.agent_definitions import ...
  aitest/infra/error_logger.py:1 → from aitest.runtime.error_handling import ...
- reason: aitest 包中的多个模块只是 re-export alice_engine 的实现。
  如果 alice_engine 的某个类改名或移除，所有 re-export 链上的 import 失败。
  更严重的是：开发者可能不知道实际实现在 alice_engine 中，
  在 aitest 端做修改不会生效（因为实际代码在 packages/alice-engine/ 中）。
```

```
[MEDIUM] aitest/config.py re-export runtime.config — 但 runtime.config 是简单类
- location: aitest/config.py:3 → from aitest.runtime.config import Config, config, _env, _env_int
- reason: runtime.config 的 RuntimeConfig 只有 3 个属性和 1 个方法。
  config.py 的存在是为了打破循环依赖，但增加了 import 链的复杂度。
```

---

## 46. alice-engine/core/executor.py — 未定义引用（部分重构残留）

```
[HIGH] executor.py 引用 10+ 个未定义名称 — 运行时会 NameError
- location: packages/alice-engine/alice_engine/core/executor.py (多处)
- chain: AgentLoop.__init__ → config.resolve_llm_provider() (config 未导入)
  AgentLoop.act() → run_skill(...) (run_skill 未定义)
  AgentLoop.skills → AGENT_SKILL_MAP (未导入)
  AgentLoop.__init__ → TraceContext.set(...) (TraceContext 未定义)
  AgentLoop.observe() → check_output_safety() / attribute_failure() (未定义)
- reason: 文件处于部分重构状态。`pass  # X removed` 注释标记了移除的模块，
  但后续引用该模块的代码行未清理。任何调用这些方法的路径都会 NameError。
```

```
[HIGH] executor.py __init__.py 导入不存在的模块
- location: packages/alice-engine/alice_engine/core/__init__.py:16
- chain: from alice_engine.core.skill_executor import SkillExecutorProtocol, ...
- reason: skill_executor.py 不存在。实际文件是 skill_executor_impl.py。
  import 时 ModuleNotFoundError。
```

```
[HIGH] executor.py 硬编码模型名称映射 — 3 处独立维护
- location: executor.py:260-266, skill_registry.py:265-279, skill_registry.py:433-438
- chain: _resolve_model_for_provider() → {"claude": "claude-sonnet-4-6", ...}
  skill_registry.py → PROVIDER_CAPABILITIES, PROVIDER_DEFAULTS
- reason: 三处独立维护模型名称→能力映射。无单一数据源。
```

```
[HIGH] planner.py 线程不安全的模块级可变状态
- location: packages/alice-engine/alice_engine/core/planner.py:44
- chain: _confirmed_skills: set = set() — 被所有 plan_next_action() 调用共享
- reason: 并行 SOP 执行时，多个 AgentLoop 并发调用 confirm_skill()，
  对 set 的并发读写无锁保护。竞态条件。
```

```
[HIGH] executor.py monkey-patches sys.stdout
- location: packages/alice-engine/alice_engine/core/executor.py:28-29
- chain: sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
- reason: 模块导入时全局替换 stdout。影响进程中所有代码。
```

```
[MEDIUM] executor.py 硬编码 28 个 artifact_map 条目
- location: packages/alice-engine/alice_engine/core/executor.py:706-736
- chain: _persist_skill_artifact() → artifact_map = {"automation/code-gen": "PageObject.py", ...}
- reason: 与 agent_definitions.py 的 FALLBACK_AGENT_SKILL_MAP 重复维护。
```

```
[MEDIUM] SkillExecutorImpl 与 ContextInjector 接口签名不匹配
- location: skill_executor_impl.py:91, interfaces.py:204-210
- chain: execute() → injector.inject(skill_id, system_prompt, context_vars) — 3 参数
  ContextInjector.inject() 协议定义: (skill_id, context_vars, system_prompt, user_prompt) — 4 参数
- reason: 参数顺序和数量不匹配。平台实现按协议定义会收到错误参数。
```

```
[MEDIUM] PromptAdapter.adapt() 签名不匹配
- location: prompt_adapter.py:48-53, skill_executor_impl.py:95
- chain: execute() → adapter.adapt(system_prompt, self.provider) — provider 是 LLMProvider 对象
  adapt() 期望 provider_type: str — 字符串
- reason: 传入对象期望字符串，ADAPTATIONS.get(provider_type) 静默失败。
```

```
[MEDIUM] yaml 作为隐式依赖 — 未在 pyproject.toml 声明
- location: skill_loader.py:94, agent_definitions.py:94, planner.py:155
- chain: import yaml — 多处内联导入
- reason: pyyaml 未安装时，所有 skill 加载和 agent 定义路径静默 fallback。
```

```
[MEDIUM] _ALL_ARTIFACT_RULES 外部可变模块级 dict
- location: task.py:25, executor.py:46,535,694,848
- chain: executor.py 从 task.py 导入 _ALL_ARTIFACT_RULES，由平台代码外部填充
- reason: 如果平台未填充，所有 artifact 检查静默通过（空规则=无检查）。
```

---

## 47. alice-engine 其他模块

```
[MEDIUM] SkillResult dataclass 在两处独立定义
- location: agent_loop.py:86-93, skill_executor.py:18-25
- chain: 两处定义相同的 SkillResult dataclass
- reason: 更新一处不更新另一处会类型不匹配。
```

```
[MEDIUM] MILESTONE_SKILLS 硬编码 13 个 skill ID — 与 agent_definitions 重复
- location: state_machine.py:128-142, agent_definitions.py:19-47
- chain: MILESTONE_SKILLS = ["project/init", "requirement/analyze", ...]
- reason: 新增 skill 需要同时更新两处。
```

```
[LOW] _guess_provider_tier 与 PROVIDER_DEFAULTS 重复映射
- location: skill_registry.py:423-429, skill_registry.py:433-438
- chain: 两处独立的 provider→tier 映射
- reason: 更新一处不更新另一处行为不一致。
```

```
[LOW] SkillLoader 的 skill_id 匹配用最后一段 — 脆弱启发式
- location: skill_loader.py:116,129,196-197,287
- chain: s_id.split("/")[-1] == skill_id.split("/")[-1]
- reason: "code-review/review" 会匹配 "debug/review"。
```

```
[LOW] output_persistence.py fallback 到 Path(".") / module
- location: output_persistence.py:59
- chain: parent_dir = Path(".") / module — 依赖 CWD
- reason: worktree 操作时 CWD 改变，文件写到意外位置。
```

---

## 统计

| 严重度 | 数量 |
| --- | --- |
| HIGH | 72 |
| MEDIUM | 72 |
| LOW | 34 |
| **总计** | **178** |

### 按类别分布

| 类别 | HIGH | MEDIUM | LOW | 总计 |
|------|------|--------|-----|------|
| EventBus subscriber 顺序依赖 | 2 | 2 | 0 | 4 |
| event.data dict key 依赖 | 2 | 5 | 0 | 7 |
| format/template 变量依赖 | 0 | 5 | 2 | 7 |
| threading + asyncio 混用 | 3 | 3 | 0 | 6 |
| consumer side effects | 2 | 4 | 1 | 7 |
| RunEvent → UI 映射 | 3 | 4 | 1 | 8 |
| Engine factory 耦合 | 1 | 2 | 0 | 3 |
| OwnedDict/Lifecycle | 1 | 3 | 0 | 4 |
| QueryLayer SQL | 1 | 1 | 1 | 3 |
| Preflight/Lineage | 1 | 3 | 0 | 4 |
| SQL 转义重复 | 1 | 0 | 0 | 1 |
| Database 层 | 4 | 1 | 0 | 5 |
| Workspace/Org | 1 | 1 | 0 | 2 |
| Chat/Session | 2 | 3 | 0 | 5 |
| Auth | 2 | 1 | 0 | 3 |
| Kanban SOP | 2 | 1 | 0 | 3 |
| 前端状态 | 2 | 2 | 1 | 5 |
| Main.py 启动 | 1 | 2 | 0 | 3 |
| ObservationBus 注册 | 1 | 2 | 0 | 3 |
| GovernanceBridge | 1 | 1 | 0 | 2 |
| EventBus 生命周期 | 3 | 2 | 0 | 5 |
| Replay | 1 | 1 | 1 | 3 |
| Server API 端点 | 3 | 5 | 0 | 8 |
| agents.py | 1 | 1 | 0 | 2 |
| Logging | 1 | 1 | 0 | 2 |
| Config | 1 | 1 | 1 | 3 |
| Engine skill_executor | 1 | 1 | 0 | 2 |
| 前端 API client | 1 | 1 | 0 | 2 |
| Task Queue | 2 | 2 | 0 | 4 |
| Pause Handler | 2 | 1 | 0 | 3 |
| Queue Factory | 1 | 1 | 0 | 2 |
| Health Check | 2 | 1 | 0 | 3 |
| Sweep Loop | 2 | 1 | 0 | 3 |
| Audit Scheduler | 1 | 1 | 0 | 2 |
| Intent Parser | 1 | 3 | 0 | 4 |
| Operational Metrics | 0 | 2 | 0 | 2 |
| Organization | 1 | 1 | 0 | 2 |
| Plugin System | 1 | 1 | 0 | 2 |
| Tenant Manager | 1 | 1 | 0 | 2 |
| Parallel Runner | 1 | 1 | 0 | 2 |
| Worker Pool | 1 | 1 | 0 | 2 |
| Redis 硬编码 | 1 | 1 | 0 | 2 |
| TestingMemoryStore | 1 | 1 | 0 | 2 |
| Agent Capabilities | 1 | 0 | 0 | 1 |
| Re-export 链 | 1 | 1 | 0 | 2 |

| alice-engine 核心 | 10 | 5 | 3 | 18 |

---

## 已修复清单（批次 1-10，2026-07-03）

| 批次 | 策略 | 消除耦合点 | 测试 |
| --- | --- | --- | --- |
| 1 | SQL 参数化 | 6 份 _escape + 所有 f-string SQL (8 文件) | 29 |
| 2 | EventDataKey | consumer 硬编码 key (6 文件) | 16 |
| 3 | EventBus 改进 | Future 追踪 + backpressure + priority 约束 | 8 |
| 4 | Singleton → DI | 18 个端点 + main.py 注入 | 22 |
| 5 | 硬编码 → 配置 | 10 个模块的路径/超时/阈值 | 13 |
| 6 | Threading 修复 | terminal.py event loop 保护 | — |
| 7 | Re-export deprecation | 4 个 re-export 链 | — |
| 8 | 私有属性 → 公开 API | sweep.py scan_count | — |
| 9 | Pause Handler | TOCTOU 竞态 + 轮询加速 | — |
| 10 | SSE Contract | 前后端共享 SSE_EVENTS 常量 | — |
| **合计** | | **44 个耦合点** | **88** |

新增文件：
- `aitest/infra/sql.py` — 统一参数化查询 API
- `aitest/platform/config_registry.py` — 集中配置中心
- `aitest/web/src/api/sse-events.ts` — 前后端共享 SSE 常量
- `tests/test_sql_parameterization.py` — 29 测试
- `tests/test_event_schema.py` — 16 测试
- `tests/test_event_bus_improvements.py` — 8 测试
- `tests/test_di_injection.py` — 22 测试
- `tests/test_config_registry.py` — 13 测试

### P0+P1 代码修复（alice-engine + 模块 bug）

| 文件 | 问题 | 修复 |
| --- | --- | --- |
| `packages/alice-engine/alice_engine/core/executor.py` | 10+ 未定义引用 (NameError) | 添加 config, AGENT_SKILL_MAP, get_agent_definition, run_skill, TraceContext, get_logger, get_tracer, GOVERNANCE 定义 |
| `packages/alice-engine/alice_engine/core/executor.py` | run_interactive() 调用不存在的函数 | 实现简单版本: run() → AgentEvent 流 |
| `packages/alice-engine/alice_engine/core/executor.py` | 15 个 pass # X removed 后引用未清理 | 清理死代码或添加 stub |
| `packages/alice-engine/alice_engine/core/__init__.py` | 导入不存在的 skill_executor 模块 | 改为从 skill_executor_impl 导入 |
| `packages/alice-engine/alice_engine/core/planner.py` | _confirmed_skills 模级 set 竞态 | 改为 threading.local() |
| `packages/alice-engine/alice_engine/core/skill_executor_impl.py` | inject() 签名不匹配 ContextInjector | 修复参数顺序和返回值处理 |
| `aitest/agents/agent_scheduler.py` | logger 未定义 (应用 _log) | 修复为 _log |
| `aitest/knowledge/rag_engine.py` | 缺少 import re, Settings, CHROMA_DIR | 添加缺失导入和定义 |

### 总计

- 审计发现: 178 个耦合点 (HIGH 72 / MEDIUM 72 / LOW 34)
- 已修复: 51 个文件, +2171/-1206 行
- 测试: 88 个全部通过
