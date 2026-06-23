# 自建 Chat Agent — 实施计划

> 版本：v1.0 | 日期：2026-06-14 | 来源：路径 2 延伸
> 背景文档：`PLATFORM_INDEPENDENCE_ROADMAP.md` → 路径 5（自研 FastAPI 平台）
> 前置阅读：`CLAUDE.md` → `governance/README.md`

---

## 一、问题陈述

当前 Claude Code 每轮对话加载 CLAUDE.md (~1,200 tokens) + Memory (~860 tokens) + 系统提示 (~3,000 tokens)，44% token 消耗与测试任务无关。用户使用 DeepSeek API，月费 ~200 元，其中 ~88 元为纯浪费。

**核心需求**：自建聊天 Agent，用 Web UI + SSE 流式替代 Claude Code 的对话壳，保留 aitest 全部测试能力。

---

## 二、架构总览

```
浏览器 (chat.html)
  │  EventSource (SSE)
FastAPI /api/chat
  │  Generator 桥接（asyncio.Queue）
Interactive AgentLoop (run_interactive)
  │  stream_complete()
LLM Provider → DeepSeek API (Anthropic 兼容)
```

四层改动，逐层可测，最终拼成完整聊天体验。

---

## 三、Phase 分解

### Phase 1: LLM 流式支持（Day 1-2）

**文件**: `aitest/llm/provider.py`

| 改动 | 说明 |
|------|------|
| 新增 `StreamEvent` dataclass | 8 种事件类型：content_start/chunk/end、tool_use_start/input_chunk/end、done、error |
| `LLMProvider` 加 `stream_complete()` | `Generator[StreamEvent, None, LLMResponse]` |
| `ClaudeProvider` 实现 | Anthropic SDK `stream=True`，映射 `content_block_start/delta` → StreamEvent |
| `OpenAIProvider` 实现 | OpenAI SDK `stream=True` |

DeepSeek 的 Anthropic 兼容端点（`ANTHROPIC_BASE_URL`）原生支持 `stream=True`，无需额外适配。

**验证**:
```bash
python -c "
from aitest.llm.provider import get_provider
llm = get_provider('claude')
for e in llm.stream_complete('Say hi', 'Hello'):
    print(e.type, e.content[:50])
"
```

---

### Phase 2: Interactive AgentLoop（Day 3-5）

**文件**: `aitest/agent_runner.py`

| 改动 | 说明 |
|------|------|
| 新增 `AgentEvent` dataclass | agent_start、skill_start、skill_chunk、skill_end、observation、interaction_required、agent_message、agent_end |
| `AgentLoop` 加 `_interaction_queue` | `queue.Queue`，接收外部输入 |
| `AgentLoop` 加 `send_interaction(response)` | 供 API 层唤醒暂停的 Agent |
| `AgentLoop` 加 `run_interactive()` | ~250 行，镜像现有 `run()` 但：Skill 执行用 `stream_complete()`、决策点 yield `interaction_required` 并阻塞等输入 |

现有 `run()` 不动，保持向后兼容。CLI 的 `aitest agent run` 不受影响。

**验证**:
```bash
python -c "
from aitest.agent_runner import AgentLoop
a = AgentLoop('test-design-agent', module='tank', page='alarm-config')
for e in a.run_interactive():
    print(e.type)
"
```

---

### Phase 3: Chat API（Day 6-8）

**新文件**: `aitest/server/api/chat.py`

端点：

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | `/api/chat/sessions` | 创建会话 |
| POST | `/api/chat/sessions/{id}/messages` | 发送消息，返回 stream_url |
| GET | `/api/chat/sessions/{id}/stream/{mid}` | SSE 流 |
| POST | `/api/chat/sessions/{id}/interact` | 用户交互响应 |
| GET | `/api/chat/sessions/{id}/history` | 消息历史 |

SSE 事件协议：

```
event: message     → {"role":"assistant","type":"text","content":"正在分析..."}
event: chunk       → {"content":"逐字增量"}
event: skill_start → {"skill_id":"...","label":"技术分析","index":1,"total":5}
event: skill_end   → {"skill_id":"...","status":"pass","summary":"..."}
event: interaction → {"interaction_id":"...","type":"approve_retry","prompt":"...","options":["approve","reject"]}
event: done        → {"success":true,"summary":"已完成5个Skill"}
```

核心机制：Agent 在独立线程执行，通过 `queue.Queue` 桥接到异步 SSE generator。交互暂停时 SSE 发 `interaction` 事件 → 用户 POST `/interact` → `agent.send_interaction()` 唤醒线程。

**文件改动**: `aitest/server/main.py` — 注册 chat_router、加 CORS 中间件

**验证**:
```bash
aitest server start
curl -N http://localhost:8000/api/chat/sessions/{id}/stream/{mid}
```

---

### Phase 4: Web UI（Day 9）

**新文件**: `aitest/server/static/chat.html`

- 单文件 HTML，零框架零构建
- EventSource 消费 SSE 流
- 聊天气泡 + 逐字输出
- Skill 进度条
- 交互按钮（approve/reject/skip）
- 暗色主题

**文件改动**: `aitest/server/main.py` — `app.mount("/chat", ...)` 返回 chat.html

---

### Phase 5: 意图解析（Day 10）

**新文件**: `aitest/chat/intent_parser.py`

双层策略：

1. **规则匹配**（零 token 成本）：
   - "给X写测试" / "自动化X" → `{type:"run_agent", agent:"automation-agent"}`
   - "分析X页面" → `{type:"run_skill", skill_id:"test-design/page-analysis"}`
   - "状态" / "进度" → `{type:"status"}`
   - 正则提取 module/page：`(equipment|tank|production|...)/([a-z-]+)`

2. **LLM 兜底**（复杂/模糊意图）：
   - 小 prompt（~200 tokens）→ JSON `{type, agent, module, page, confidence}`
   - 低 temperature（0.3），max_tokens=200

**验证**:
```bash
python -c "
from aitest.chat.intent_parser import parse_intent
print(parse_intent('给equipment/alarm-config写自动化测试'))
# → {type:'run_agent', agent:'automation-agent', module:'equipment', page:'alarm-config'}
"
```

---

## 实施进度（2026-06-14）

| Phase | 内容 | 状态 |
|-------|------|:--:|
| 1 | LLM 流式支持 (StreamEvent + stream_complete) | ✅ 完成 |
| 2 | Interactive AgentLoop (AgentEvent + run_interactive) | ✅ 完成 |
| 3 | Chat API (6 端点 + SSE 桥接) | ✅ 完成 |
| 4 | Web UI (chat.html) | ✅ 完成 |
| 5 | 意图解析 (中英文规则匹配 + LLM 兜底) | ✅ 完成 |

**关键修复**:
- Python 3.12: `asyncio.get_event_loop()` → `get_running_loop()` 预先捕获
- DeepSeek: 空 tool parameters 默认 `{"type":"object"}`
- .env: uvicorn 子进程需显式 `load_dotenv()`

**启动**: `aitest server start` → `http://localhost:8000/chat`

**内存文件**: `~/.claude/projects/d--Desktop-WorkStudy/memory/self-hosted-chat-agent-status.md`

---

## 四、省钱计算

```
                   Claude Code      自建 Agent
                  ────────────      ──────────
系统提示词/轮        ~5,000            0
Skill prompt        ~1,100            ~1,100（按需加载）
上下文注入           ~2,500            ~2,500（RAG 片段）
对话历史累积         ~2,000/轮         0（仅保留关键摘要）
─────────────────────────────────────────────
每模块自动化          104,000 tokens     58,500 tokens
浪费比例              44%               0%
月费（DeepSeek）      ~200 元            ~110 元
```

流式架构无额外 token 开销——StreamEvent 是协议元数据，不计入 LLM token。交互暂停是用户主动触发的，非架构固有成本。

---

## 五、执行顺序与依赖

```
Phase 1 (provider.py)           ← 无依赖，先做
  └→ Phase 2 (agent_runner.py)  ← 依赖 Phase 1 的 StreamEvent
       └→ Phase 3 (chat.py)     ← 依赖 Phase 2 的 run_interactive()
            ├→ Phase 4 (chat.html) ← 依赖 Phase 3 的 SSE 协议
            └→ Phase 5 (intent_parser.py) ← 依赖 Phase 3 的 API 路由
```

Day 1-2: Phase 1 → Day 3-5: Phase 2 → Day 6-8: Phase 3 → Day 9: Phase 4 → Day 10: Phase 5

---

## 六、关键文件清单

| 文件 | 类型 | 说明 |
|------|:--:|------|
| `aitest/llm/provider.py` | 改 | StreamEvent + stream_complete() |
| `aitest/agent_runner.py` | 改 | AgentEvent + run_interactive() |
| `aitest/server/api/chat.py` | **新建** | Chat API 路由（~500 行） |
| `aitest/server/main.py` | 改 | 注册 chat_router、CORS、静态文件 |
| `aitest/server/static/chat.html` | **新建** | Web 聊天界面（~300 行） |
| `aitest/chat/__init__.py` | **新建** | 包标记 |
| `aitest/chat/intent_parser.py` | **新建** | 意图解析（~200 行） |

> 总计新增 ~1,000 行代码，改动 ~200 行（provider.py + agent_runner.py + main.py）。无新外部依赖。
