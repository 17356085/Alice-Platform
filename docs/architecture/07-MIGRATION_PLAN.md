# Migration Plan — AITest v1.0 迁移计划

> 状态: v1.0-draft | 日期: 2026-06-23
> 原则: 渐进式迁移，每个模块独立可交付，不要求大爆炸重写

## 总览

```
Week 1 ─── 可靠性基础 ─── Provider Chain + Prompt Cache + Context Window + Security
            ▸ 4 天编码 + 1 天测试
            ▸ 影响: 所有 LLM 调用 + 所有 bash 执行
            ▸ 风险: 低 (都是增量包装，不改核心逻辑)

Week 2 ─── Agent 能力升级 ─── Capability Router + Tool Calling + Complexity Routing
            ▸ 4 天编码 + 1 天集成测试
            ▸ 影响: Agent Loop + SOP Graph 入口
            ▸ 风险: 中 (Tool Calling 启用改变 Agent 行为)

Week 3 ─── 并行化 + 记忆 ─── Page Parallel + Testing Memory + Observation Bus
            ▸ 4 天编码 + 1 天性能测试
            ▸ 影响: SOP Graph + ChromaDB
            ▸ 风险: 中 (并行化改变执行顺序)

Week 4 ─── 前端补齐 ─── API Client + Router + ChatStore SSE + i18n
            ▸ 4 天编码 + 1 天 E2E 测试
            ▸ 影响: 前端所有 view/store
            ▸ 风险: 低 (纯前端改动)
```

---

## Week 1: 可靠性基础

### Day 1-2: Provider Reliability Chain

**文件变更**:
- NEW: `aitest/llm/reliable_provider.py` — `ReliableProvider`, `UsageTracker`
- MOD: `aitest/llm/provider.py` — `ClaudeProvider.complete()` 加 `cache_control` 参数
- MOD: `aitest/agents/agent_runner.py` — 替换 `get_provider()` 为 `get_reliable_provider()`

**实现清单**:
- [x] `ErrorClass` enum + `classify_error()` 函数
- [x] `ReliableProvider.complete()` — retry + fallback chain
- [x] `ReliableProvider._call_with_retry()` — 指数退避 + jitter
- [x] `ReliableProvider._call_with_timeout()` — ThreadPoolExecutor timeout
- [x] `UsageTracker` — token 计数 + 成本估算
- [x] `ClaudeProvider` 支持 `cache_control: {"type": "ephemeral"}`
- [x] 环境变量配置: `AI_FALLBACK_CHAIN`, `AI_MAX_RETRIES`

**测试验证**:
```python
# 测试: 模拟 429 → retry → 成功
def test_retry_on_rate_limit():
    provider = ReliableProvider()
    with mock.patch.object(ClaudeProvider, 'complete',
                           side_effect=[RateLimitError, RateLimitError, mock_response]):
        response = provider.complete("sys", "usr")
        assert response.content == "mock"

# 测试: Claude 失败 → 回退到 DeepSeek
def test_fallback_to_deepseek():
    provider = ReliableProvider()
    with mock.patch.object(ClaudeProvider, 'complete', side_effect=FatalError):
        with mock.patch.object(DeepSeekProvider, 'complete', return_value=mock_response):
            response = provider.complete("sys", "usr")
            assert response.content == "mock"
```

### Day 3: Context Window Management

**文件变更**:
- NEW: `aitest/llm/context_window.py` — `ContextWindowMonitor`, `SessionCompactor`
- MOD: `aitest/agents/agent_runner.py` — 集成窗口监控 + continuation

**实现清单**:
- [x] `MODEL_CONTEXT_LIMITS` 字典
- [x] `ContextWindowMonitor` — estimate + check + threshold
- [x] `SessionCompactor.compact()` — DeepSeek 摘要 + raw truncation fallback
- [x] `build_continuation_prompt()` — continuation message 构建
- [x] AgentLoop 集成: `_check_window()`, `_do_continuation()`
- [x] MAX_CONTINUATIONS = 5

**测试验证**:
```python
def test_context_window_warning():
    monitor = ContextWindowMonitor(model_limit=100000)
    monitor.add_usage(85000, 5000)  # 90K/100K = 90%
    assert monitor.check() == WindowStatus.HARD
    assert monitor.should_continue() == True
```

### Day 4: Security Layer

**文件变更**:
- NEW: `aitest/infra/security.py` — `BashValidator`, `SecurityHook`, `PromptInjectionGuard`
- NEW: `aitest/infra/secure_subprocess.py` — `secure_run()`
- MOD: `aitest/graphs/sop_graph.py` — 替换 `subprocess.run()` 为 `secure_run()`
- MOD: `aitest/agents/agent_runner.py` — 替换 HTML 注释式输入为 `PromptInjectionGuard`

**实现清单**:
- [x] `BLOCKED_COMMANDS` + `CONTEXT_BLOCKED_COMMANDS`
- [x] Per-command `VALIDATORS` (rm, git, python, pytest, pip, curl)
- [x] `BashValidator.validate()` — 三层验证
- [x] `SecurityHook.before_bash()` / `before_write()` / `before_subprocess()`
- [x] `PromptInjectionGuard.scan()` + `sanitize()` + `safe_user_input()`
- [x] `secure_run()` — 包装 `subprocess.run()`

### Day 5: 集成测试 + 回归验证

- 全量 SOP Run (equipment 4 页面) — 验证 retry/fallback 不破坏现有流程
- 手动触发 Claude → DeepSeek fallback (改 API key 模拟)
- 手动触发 context window continuation (设低 limit 模拟)
- 安全校验: 尝试执行 `rm -rf /` 确认被阻止

---

## Week 2: Agent 能力升级

### Day 1-2: Capability Router

**文件变更**:
- NEW: `aitest/platform/capabilities/` — 完整模块
  - `router.py` — `CapabilityRouter`, `ToolDef`, `ToolCall`, `ToolResult`
  - `agent_capabilities.py` — `AGENT_CAPABILITIES` 映射
  - `providers/` — `BrowserNavigate`, `BrowserScreenshot`, `RAGSearch`, `Pytest`, `PageObjectGen`, `TestScriptGen`

**实现清单**:
- [x] `CapabilityProvider` ABC — 统一接口
- [x] `CapabilityRouter.register()` / `resolve()` / `execute()`
- [x] `CapabilityRouter.tool_defs_for_agent()` — 返回 LLM 可用的 tool definitions
- [x] 6 个核心 Provider 实现 (browser, rag, execute, codegen)
- [x] `AGENT_CAPABILITIES` — Agent → Capability 映射
- [x] `create_router()` 工厂函数

### Day 3: 启用 Native Tool Calling

**文件变更**:
- MOD: `aitest/agents/skill_executor.py` — `run_skill()` 传 tools + 处理 tool calls

**关键改造**:
```python
# 当前: tools=None
response = llm.complete(system_prompt, user_prompt)

# 改造后: tools 从 CapabilityRouter 获取
router = CapabilityRouter.get_instance()
tools = router.tool_defs_for_agent(agent_name)
response = llm.complete(system_prompt, user_prompt, tools=tools)

# 处理 LLM 返回的 tool calls
while response.tool_calls:
    for tc in response.tool_calls:
        result = router.execute(tc)
        tool_results.append(result)
    # 将 tool results 注入为新消息，继续循环
    response = llm.complete(system_prompt, build_tool_result_message(tool_results), tools=tools)
```

### Day 4: Complexity Routing

**文件变更**:
- NEW: `aitest/platform/complexity/` — `classifier.py`, `factors.py`, `pipelines.py`
- MOD: `aitest/graphs/sop_graph.py` — 加 `complexity_assess_node` + 三档路由

**实现清单**:
- [x] `PageComplexityProfile` dataclass + 评分因子
- [x] `ComplexityClassifier.classify()` — 启发式 + LLM 辅助
- [x] `SIMPLE_PIPELINE` / `STANDARD_PIPELINE` / `COMPLEX_PIPELINE`
- [x] `complexity_assess_node()` — 从 discovery data 评估
- [x] `route_by_complexity()` — 条件路由
- [x] 快速路径: `IMMEDIATE_SIMPLE_PATTERNS` / `IMMEDIATE_COMPLEX_PATTERNS`

### Day 5: 集成测试

- 选 3 个页面 (SIMPLE/STANDARD/COMPLEX 各一个) 跑完整流程
- 验证 tool calling 正确执行 (browser navigate → screenshot → rag search)
- 验证复杂度路由正确分流

---

## Week 3: 并行化 + 记忆

### Day 1-2: 多页面并行执行

**文件变更**:
- MOD: `aitest/graphs/sop_graph.py` — 加 `Send()` 并行扇出

**关键改造**:
```python
from langgraph.types import Send

def fanout_pages(state: SOPState):
    """将 pages 列表展开为并行节点。"""
    return [
        Send("process_single_page", {
            "module": state["module"],
            "current_page": page,
            "pages": [page],  # 单页面
        })
        for page in state["pages"]
    ]

graph.add_conditional_edges("preflight", fanout_pages, ["process_single_page"])
graph.add_node("process_single_page", build_single_page_subgraph())
```

### Day 3-4: Testing Memory

**文件变更**:
- NEW: `aitest/platform/knowledge/testing_memory.py` — Schema + lifecycle
- NEW: `aitest/platform/knowledge/testing_memory_store.py` — ChromaDB CRUD
- NEW: `aitest/platform/knowledge/signal_observer.py` — `SignalObserver`
- MOD: `aitest/platform/knowledge.py` — 集成新的 Memory 类型

**实现清单**:
- [x] 8 种 `TestingMemory` 子类型 dataclass
- [x] `TestingMemoryStore` — 类型化 CRUD
- [x] 4 层注入 (system/skill/tool_result/prepareStep)
- [x] `SignalObserver` — 6 行为信号
- [x] `MemoryLifecycle` — 衰减/提升/删除
- [x] ChromaDB 8 个 collection 创建/迁移

### Day 5: 性能测试

- 4 页面并行 vs 顺序执行: 对比耗时
- Token 消耗对比: 并行前 vs 并行后
- Memory 注入延迟测试: 每层注入 < 阈值

---

## Week 4: 前端补齐

### Day 1: API Client 抽象层

**文件变更**:
- NEW: `aitest/web/src/api/client.ts` — 统一 HTTP/WS 客户端
- NEW: `aitest/web/src/api/endpoints.ts` — API 端点定义

```typescript
// api/client.ts
class ApiClient {
  private baseUrl: string;
  private wsUrl: string;

  async get<T>(path: string): Promise<T> { ... }
  async post<T>(path: string, body: unknown): Promise<T> { ... }
  streamSSE(path: string, body: unknown): EventSource { ... }
  connectWS(path: string): WebSocket { ... }
}

export const api = new ApiClient('/api/v1');
```

### Day 2: Router 独立化

**文件变更**:
- NEW: `aitest/web/src/router/index.ts` — Vue Router 配置
- MOD: `aitest/web/src/App.vue` — `<RouterView>` 替换内联路由
- MOD: `aitest/web/src/main.ts` — `app.use(router)`

```typescript
// router/index.ts
const routes = [
  { path: '/', redirect: '/chat' },
  { path: '/chat', component: () => import('@/views/IntelligenceChatView.vue') },
  { path: '/kanban', component: () => import('@/views/KanbanView.vue') },
  { path: '/onboarding', component: () => import('@/views/OnboardingWizardView.vue') },
  // ... 懒加载所有 view
];
```

### Day 3: ChatStore 连接真实 SSE 后端

**文件变更**:
- MOD: `aitest/web/src/stores/chat.ts` — 移除 `simulateTools()` / `generateResponse()`
- MOD: `aitest/web/src/composables/useChatSSE.ts` — 真实 SSE 连接

```typescript
// 替换模拟数据
async sendMessage(content: string) {
  const eventSource = api.streamSSE('/chat/stream', { message: content });
  eventSource.onmessage = (event) => {
    const chunk = JSON.parse(event.data);
    this.messages.push(chunk);
  };
}
```

### Day 4: i18n 全覆盖

**文件变更**:
- MOD: `aitest/web/src/locales/zh.json` — 补充所有硬编码字符串
- MOD: `aitest/web/src/locales/en.json` — 补充所有硬编码字符串

**范围**:
- 系统输出/错误消息
- 聊天界面
- SOP 进度显示
- Onboarding 向导
- 设置面板

### Day 5: E2E 测试 + 文档

- Playwright 冒烟测试: chat → kanban → onboarding → settings
- 更新 `CLAUDE.md` 为 v1.0 架构
- 更新 `governance/context/shared-language.md` 术语

---

## 兼容性与风险

### 向后兼容

所有改造都是**增量**的，不破坏现有功能：

| 模块 | 兼容策略 |
|------|----------|
| Provider Chain | `get_provider()` 保持不变，新增 `get_reliable_provider()` |
| Capability Router | 无 Router 时 `tools=None`，行为与当前一致 |
| Complexity Routing | SIMPLE/STANDARD 路由是新增的，COMPLEX 走原有全流程 |
| Context Window | 不超限时不触发 continuation |
| Security | `secure_run()` 可选使用，直接 `subprocess.run()` 仍可用（不推荐） |

### 已知风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Tool calling 改变 Agent 行为模式 | 中 | Agent 可能过度使用 tool 而非生成文本 | 先只给 execution-agent 开 tools，逐步扩展 |
| 并行执行导致 ChromaDB 写入冲突 | 低 | 数据损坏 | ChromaDB 默认线程安全；加写入锁 |
| Continuation 摘要丢失关键上下文 | 中 | Agent 重复已完成工作 | 摘要 prompt 经过 Aperant 验证；加 checkpoint |
| Prompt Cache 不命中 | 低 | 成本未节省但不增加 | 监控 `cache_hit_rate`，低于 50% 时调整策略 |

---

## 成功指标

| 指标 | 当前基线 | v1.0 目标 | 测量方式 |
|------|----------|-----------|----------|
| SOP Run 成功率 | ~62% (828 tests baseline) | >85% | `SOP_STATUS` JSON |
| LLM 调用可用性 | ~95% (无 retry) | >99.5% | `UsageTracker` |
| Token 成本/SOP Run | ~130K/页 | ~80K/页 (38%↓) | `UsageTracker.session_total()` |
| Prompt Cache 命中率 | 0% | >60% | `UsageTracker.cache_hit_rate()` |
| 多页面执行时间 | 顺序 ~40min/4页 | 并行 ~12min/4页 | SOP Run duration |
| 简单页面 Token | ~130K | ~15K (88%↓) | Complexity routing + UsageTracker |
| 安全事件 | 无检测能力 | 100% 检测 + 阻止 | `SecurityHook` 日志 |

## 非目标 (v1.0 不做)

- 分布式执行 (Celery/Redis)
- OAuth 多账户自动切换
- Electron 桌面壳
- GitHub/GitLab PR Review
- 12-provider 全支持 (保持 4 provider)
- Memory 图数据库 (只用 ChromaDB)
