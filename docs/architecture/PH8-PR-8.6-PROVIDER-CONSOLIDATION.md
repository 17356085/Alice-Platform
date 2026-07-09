# PH8-PR-8.6: Provider 单一事实源与兼容层退场计划

> 版本: v1.0  
> 日期: 2026-07-08  
> 状态: Draft  
> Tracking: PH8-PR-8.6

## 一句话目标

避免 `aitest.llm.providers.*` 与 `alice_engine.providers.*` 双实现继续漂移，收敛到 SDK 单一事实源，平台层仅保留 adapter 逻辑（密钥注入、trace、billing）。

---

## 当前问题

### 双实现现状对比

| Provider | `aitest/llm/providers/` (旧) | `alice_engine/providers/` (新, SDK) | 差距 |
|----------|------------------------------|-------------------------------------|------|
| **claude** | 253 行，complete + stream_complete + tool calling + Prompt Caching | 60 行，仅 complete | 缺 stream、tool、caching |
| **openai** | 234 行，complete + stream_complete + tool calling + reasoning_content 支持 | 63 行，仅 complete | 缺 stream、tool、reasoning |
| **deepseek** | 242 行，complete + stream_complete + tool calling + reasoning_content | 63 行，仅 complete | 缺 stream、tool、reasoning |
| **ollama** | ~200 行（未读全），complete + stream | ~60 行（推测）| 缺 stream |
| **mimo** | ~200 行（未读全），complete + stream | ~60 行（推测）| 缺 stream |
| **mock** | 简单实现 | 简单实现 | 基本对等 |

### 调用方现状

**`aitest.llm.provider.get_provider()` 的调用点**（6 处平台代码 + 若干测试）：
1. `aitest/platform/complexity/classifier.py:143` — 复杂度分类器（LLM 辅助）
2. `aitest/chat/intent_parser.py:176` — 意图解析
3. `aitest/testing/evaluator_judge.py:93, 439` — 评估器（需要 LLM）
4. `aitest/server/api/chat.py:371` — **Chat API（需要 streaming）**
5. `aitest/__init__.py:20` / `aitest/llm/__init__.py:13` — 包级别 re-export（向后兼容）
6. 测试文件若干（`test_provider_base.py`, `test_complexity.py`, `conftest.py` fixtures）

**`alice_engine.providers.get_provider()` 的调用点**（3 处 SDK 内部）：
1. `packages/alice-engine/alice_engine/core/executor_impl.py:364, 369`
2. `packages/alice-engine/alice_engine/core/executor.py:34, 116, 122, 124`
3. `packages/alice-engine/alice_engine/core/skill_executor.py:20, 132`

### 关键风险

如果现在就让 `aitest.llm.provider.get_provider()` 委托给 SDK 层：

1. **Chat API 会挂**（`chat.py:371` 需要 streaming，SDK 层没有）
2. **Prompt Caching 丢失**（成本会大幅上升，skill 执行每次都全额付费 system prompt）
3. **Tool calling 丢失**（evaluator/classifier 如果用 tool calling 会挂，虽然目前调用点看起来未必用了 tool）
4. **Reasoning model 支持丢失**（DeepSeek-v4 / o1 的 `reasoning_content` 字段处理会丢）

---

## 目标架构

### 职责分层

```
┌─────────────────────────────────────────────────────────────┐
│ Platform Layer (aitest/llm/, aitest/adapters/llm/)         │
│ ─ 兼容 facade: aitest.llm.provider.get_provider()          │
│ ─ Platform adapter:                                         │
│   • API key injection (aitest.runtime.config)              │
│   • Trace decorator (_trace_llm_call)                      │
│   • Billing/metering hooks (future)                        │
│   • Platform-specific error handling                        │
└────────────────────┬────────────────────────────────────────┘
                     │ delegates to
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ SDK Layer (alice_engine.providers.*)                        │
│ ─ 唯一执行实现 (single source of truth)                    │
│ ─ 功能完整:                                                 │
│   • complete() — 同步调用                                   │
│   • stream() — 流式调用                                     │
│   • Tool calling 支持 (Claude/OpenAI/DeepSeek)             │
│   • Provider 特定优化:                                      │
│     - Claude: Prompt Caching                                │
│     - DeepSeek/OpenAI: reasoning_content 支持              │
│ ─ 零平台依赖（只依赖 os.environ 读 API key fallback）      │
└─────────────────────────────────────────────────────────────┘
```

### 功能对齐矩阵

SDK 层必须实现以下功能才能替代平台层：

| 功能 | Claude | OpenAI | DeepSeek | Ollama | MiMo | Mock | 优先级 |
|------|--------|--------|----------|--------|------|------|--------|
| `complete()` | ✅ (已有) | ✅ | ✅ | ✅ | ✅ | ✅ | P0 |
| `stream()` | ❌ 缺失 | ❌ | ❌ | ❌ | ❌ | N/A | **P0** (chat API 阻塞) |
| Tool calling | ❌ 缺失 | ❌ | ❌ | N/A | N/A | N/A | P1 |
| Prompt Caching | ❌ 缺失 | N/A | N/A | N/A | N/A | N/A | **P0** (成本) |
| `reasoning_content` | N/A | ❌ 缺失 | ❌ 缺失 | N/A | N/A | N/A | P1 |
| Error handling (返回 error LLMResponse 而非抛异常) | ❌ 缺失 | ❌ | ❌ | ❌ | ❌ | ✅ | P1 |

**说明：**
- **P0**：必须完成，否则平台现有功能会挂或成本大幅上升
- **P1**：重要但非阻塞，可分阶段补齐

---

## 迁移路径

### Phase 1: SDK Provider 功能补齐（代码变更）

#### 1.1 统一 `LLMProvider` 基类契约

**当前问题：**
- `aitest.adapters.llm.provider_base.LLMProvider` 有 `stream_complete()` 抽象方法
- `alice_engine.providers.base.LLMProvider` **没有** `stream()` 方法（`stream()` 只是个 stub，默认抛 `NotImplementedError`）

**目标：**
- `alice_engine.providers.base.LLMProvider` 添加 `stream()` 抽象方法（或明确可选方法，带默认实现抛 `NotImplementedError`）
- 统一返回类型：`Generator[StreamEvent, None, LLMResponse]`（与平台层一致）

**变更文件：**
- `packages/alice-engine/alice_engine/providers/base.py`
  - 添加 `StreamEvent` dataclass（从 `aitest.adapters.llm.provider_base` 迁移过来）
  - `LLMProvider.stream()` 改为抽象方法或明确带默认实现的可选方法

#### 1.2 补齐 Claude Provider

**文件：** `packages/alice-engine/alice_engine/providers/claude.py`

**变更：**
1. 添加 `stream()` 方法（从 `aitest/llm/providers/claude.py` 迁移逻辑）
2. 添加 Prompt Caching 支持：
   - `complete()` 方法添加 `cache_system: bool = True` 参数
   - 当 `cache_system=True` 且 `len(system_prompt) >= 1024` 时，system block 改为：
     ```python
     [{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}]
     ```
3. 添加 tool calling 支持（`complete()` 和 `stream()` 都需要）
4. 错误处理改为返回 `LLMResponse(finish_reason="error")` 而非抛异常
5. `__init__` 改为容错：API key 缺失时 `self.client = None`，`complete()` 返回 error response

**预计行数：** ~250 行（与平台层对等）

#### 1.3 补齐 OpenAI Provider

**文件：** `packages/alice-engine/alice_engine/providers/openai.py`

**变更：**
1. 添加 `stream()` 方法
2. 添加 tool calling 支持
3. 添加 `reasoning_content` fallback 逻辑（DeepSeek-v4 / o1 兼容）：
   ```python
   content = message.content or ""
   if not content:
       reasoning = getattr(message, "reasoning_content", None)
       if reasoning:
           content = reasoning
   ```
4. 错误处理改为返回 error response
5. `__init__` 改为容错

**预计行数：** ~230 行

#### 1.4 补齐 DeepSeek Provider

**文件：** `packages/alice-engine/alice_engine/providers/deepseek.py`

**变更：**
1. 添加 `stream()` 方法
2. 添加 tool calling 支持（但需 `_detect_tool_support(model)` 判断，`deepseek-reasoner` / `deepseek-r1` 不支持 tool）
3. 添加 `reasoning_content` fallback 逻辑
4. 默认模型改为 `deepseek-v4-flash`（与平台层一致）
5. 错误处理改为返回 error response
6. `__init__` 改为容错

**预计行数：** ~240 行

#### 1.5 补齐 Ollama / MiMo Provider（低优先级，可延后）

**文件：**
- `packages/alice-engine/alice_engine/providers/ollama.py`
- `packages/alice-engine/alice_engine/providers/mimo.py`

**变更：**
1. 添加 `stream()` 方法
2. 错误处理改为返回 error response
3. `__init__` 改为容错

**优先级：** P1（当前平台调用点未见使用 ollama/mimo，可在 Phase 2 补齐）

---

### Phase 2: Platform Adapter 层改造（委托实现）

#### 2.1 改造 `aitest.adapters.llm.interface.get_provider()`

**当前：**
```python
# aitest/adapters/llm/interface.py
PROVIDER_REGISTRY = {
    "claude": ClaudeProvider,  # 来自 aitest.llm.providers.claude
    "openai": OpenAIProvider,
    # ...
}

def get_provider(name: str = "claude", **kwargs) -> LLMProvider:
    instance = PROVIDER_REGISTRY[name](**kwargs)
    # 包装 tracer
    instance.complete = _trace_llm_call(instance.complete)
    return instance
```

**目标：**
```python
# aitest/adapters/llm/interface.py
def get_provider(name: str = "claude", **kwargs) -> LLMProvider:
    # 委托给 SDK 层
    from alice_engine.providers import get_provider as _sdk_get_provider
    
    # 注入平台密钥（如果 kwargs 未提供 api_key）
    if "api_key" not in kwargs:
        from aitest.runtime.config import config as _cfg
        key_map = {
            "claude": _cfg.get_env("ANTHROPIC_API_KEY", ""),
            "anthropic": _cfg.get_env("ANTHROPIC_API_KEY", ""),
            "openai": _cfg.get_env("OPENAI_API_KEY", ""),
            "deepseek": _cfg.get_env("DEEPSEEK_API_KEY", ""),
            "mimo": _cfg.get_env("MIMO_API_KEY", ""),
        }
        if name in key_map and key_map[name]:
            kwargs["api_key"] = key_map[name]
    
    # 如果是 mimo，还需要注入 base_url
    if name == "mimo" and "base_url" not in kwargs:
        kwargs["base_url"] = _cfg.get_env("MIMO_BASE_URL", "")
    
    # 获取 SDK provider 实例
    instance = _sdk_get_provider(name, **kwargs)
    
    # 包装 tracer（平台层专属逻辑）
    try:
        from aitest.infra.trace import _trace_llm_call
        instance.complete = _trace_llm_call(instance.complete)
        if hasattr(instance, "stream"):
            instance.stream = _trace_llm_call(instance.stream)
    except Exception:
        pass  # tracer 包装失败不影响核心功能
    
    return instance
```

**变更文件：**
- `aitest/adapters/llm/interface.py` — 改造 `get_provider()` 为委托实现
- `aitest/adapters/llm/provider_base.py` — 改为从 SDK 层 re-export `LLMProvider`, `LLMResponse`, `StreamEvent`（向后兼容）

#### 2.2 标记 `aitest/llm/providers/*.py` 为 Deprecated

**变更文件：**
- `aitest/llm/providers/claude.py` → 文件顶部添加 deprecation warning docstring
- `aitest/llm/providers/openai.py` → 同上
- `aitest/llm/providers/deepseek.py` → 同上
- `aitest/llm/providers/ollama.py` → 同上
- `aitest/llm/providers/mimo.py` → 同上

**示例：**
```python
"""
[DEPRECATED] 此文件已废弃，将在 Phase 9 删除。

新代码请直接使用 `alice_engine.providers.claude.ClaudeProvider`。
平台调用方请使用 `aitest.llm.provider.get_provider("claude")`（已委托给 SDK 层）。

迁移时间表：
- Phase 8 (当前): 标记 deprecated，保留文件以防回滚
- Phase 9: 删除 `aitest/llm/providers/` 目录
"""
```

---

### Phase 3: 测试与验证

#### 3.1 SDK 层单元测试

**新增测试文件：**
- `packages/alice-engine/tests/providers/test_claude_provider.py`
- `packages/alice-engine/tests/providers/test_openai_provider.py`
- `packages/alice-engine/tests/providers/test_deepseek_provider.py`

**测试覆盖：**
1. `complete()` — mock Anthropic/OpenAI SDK，验证：
   - 正常响应解析
   - Tool calling 响应解析
   - Prompt Caching (`cache_control` 字段正确构建)
   - Reasoning content fallback
   - Error response（API key 缺失、SDK 抛异常）
2. `stream()` — mock SDK stream，验证：
   - StreamEvent 序列正确（`content_start` → `content_chunk*` → `content_end` → `done`）
   - Tool calling stream 正确（`tool_use_start` → `tool_input_chunk*` → `tool_use_end`）
   - 最终 `LLMResponse` 聚合正确（accumulated text, tool_calls, usage）
3. `supports_tools()` 返回值正确
4. 容错行为（API key 缺失时不抛异常）

**预计新增测试：** ~300 行 / provider

#### 3.2 Platform 层集成测试

**已有测试调整：**
- `aitest/tests/test_provider_base.py` — 无需改动（继续测 `aitest.llm.provider.get_provider()`，底层已委托给 SDK）
- `aitest/tests/platform/test_complexity.py` — 已有 mock，无需改动
- `aitest/tests/llm/test_context_window.py` — 已有 mock，无需改动

**新增集成测试：**
- `aitest/tests/platform/test_provider_adapter.py` — 验证：
  1. `aitest.llm.provider.get_provider()` 返回的实例确实是 SDK 层的类
  2. Trace decorator 正确包装了 `complete()` 和 `stream()`
  3. API key 注入正确（从 `aitest.runtime.config` 读取）

#### 3.3 回归验证

**验证点：**
1. Chat API streaming 正常工作（`aitest/server/api/chat.py`）
2. Complexity classifier LLM 调用正常（`aitest/platform/complexity/classifier.py`）
3. Evaluator LLM 调用正常（`aitest/testing/evaluator_judge.py`）
4. SDK 层 skill execution 正常（`alice_engine.core.skill_executor.py`）

**验证方式：**
- 本地启动 `aitest server start`，手动测 Chat API streaming
- 跑一次完整 `pytest aitest/tests/platform/test_complexity.py -v`
- 跑一次 `pytest packages/alice-engine/tests -v`

---

### Phase 4: 弃用计划与文档

#### 4.1 弃用周期

| 阶段 | 时间点 | 操作 |
|------|--------|------|
| **Phase 8 (当前)** | 2026-07-08 ~ 2026-07-15 | SDK Provider 补齐 + Platform 委托实现 + 标记 deprecated |
| **Phase 9** | 2026-07-15 ~ 2026-07-22 | 删除 `aitest/llm/providers/` 目录（保留 `aitest.llm.provider` facade） |
| **Phase 10** | 2026-07-22+ | （可选）进一步清理 `aitest.adapters.llm` 为纯 re-export 层 |

#### 4.2 迁移文档

**新增文档：**
- `docs/architecture/PROVIDER-MIGRATION-GUIDE.md` — 供平台开发者参考，说明：
  1. 为何做这个迁移
  2. 旧代码 (`aitest.llm.providers.*`) 如何迁移到新代码 (`alice_engine.providers.*`)
  3. 如何自定义 provider（直接在 SDK 层注册，或通过 Platform adapter 注入特定逻辑）
  4. 向后兼容承诺（`aitest.llm.provider.get_provider()` 入口至少保留到 Phase 10）

---

## 风险与缓解

### 风险 1: SDK Provider 补齐工作量大

**风险等级：** 高

**影响：** 预计 3 个主要 provider (claude/openai/deepseek) 每个补齐 ~200 行 + 测试 ~300 行 = **共 1500 行代码变更**

**缓解措施：**
1. 优先补齐 P0 功能（streaming + Prompt Caching），P1 功能（tool calling, reasoning_content）可分阶段
2. 复用平台层已有实现（直接迁移，不重写）
3. 自动化测试先行（先写测试 mock，再补实现，TDD 方式）

### 风险 2: 破坏现有调用方

**风险等级：** 中

**影响：** 如果 SDK Provider 行为与平台层不一致（如错误处理、返回值格式），会导致现有调用方挂掉

**缓解措施：**
1. Phase 2 委托实现时，保持 `aitest.llm.provider.get_provider()` 入口签名不变
2. 完整回归测试（覆盖 chat API、complexity、evaluator）
3. 分阶段上线：先在 dev 环境验证，再合并主线

### 风险 3: Prompt Caching 丢失导致成本上升

**风险等级：** 高（成本影响）

**影响：** 如果忘记在 SDK Claude Provider 中补 Prompt Caching，每次 skill 调用会全额付费 system prompt（2K-5K tokens），成本上升 10x

**缓解措施：**
1. Prompt Caching 列为 P0 功能，必须在 Phase 1 补齐
2. 测试用例中明确验证 `cache_control` 字段存在
3. 上线后监控 Anthropic API 费用（对比上线前后）

---

## 验收标准

Phase 8 PR 8.6 完成标准（来自 `phase-8-pr-backlog.md`）：

1. ✅ SDK Provider Runtime 成为唯一执行实现
   - `alice_engine.providers.claude/openai/deepseek` 功能完整（complete + stream + tool calling + 特殊功能）
   - 平台层 `aitest.llm.providers.*` 标记 deprecated
2. ✅ `aitest.llm` 仅保留兼容 facade 和平台密钥/计费 Adapter
   - `aitest.adapters.llm.interface.get_provider()` 委托给 SDK 层
   - API key 注入、trace decorator 在 adapter 层实现
3. ✅ Provider 名称、配置、streaming、错误响应合同统一
   - `LLMProvider.stream()` 抽象方法统一
   - `StreamEvent` 类型统一
   - 错误处理统一（返回 error response，不抛异常）
4. ✅ 写清弃用周期和迁移路径
   - `aitest/llm/providers/*.py` 顶部 deprecation docstring
   - `docs/architecture/PROVIDER-MIGRATION-GUIDE.md`

---

## 正式 Gate 命令

```bash
# SDK 层单元测试
python -m pytest -q -p no:cacheprovider \
  packages/alice-engine/tests/providers/test_claude_provider.py \
  packages/alice-engine/tests/providers/test_openai_provider.py \
  packages/alice-engine/tests/providers/test_deepseek_provider.py

# Platform 层集成测试
python -m pytest -q -p no:cacheprovider \
  aitest/tests/test_provider_base.py \
  aitest/tests/platform/test_provider_adapter.py \
  aitest/tests/platform/test_complexity.py

# 全量回归
python -m pytest -q -p no:cacheprovider \
  -m "not slow and not llm" \
  packages/alice-engine/tests \
  aitest/tests
```

预期：
- SDK Provider 单元测试全部通过（streaming、tool calling、caching、error handling）
- Platform adapter 集成测试通过（委托正确、trace 装饰器正确、API key 注入正确）
- 现有平台调用方回归通过（chat API、complexity、evaluator）

---

## 下一步行动

1. **[本会话]** 补齐 `alice_engine.providers.claude.ClaudeProvider`：
   - 添加 `stream()` 方法
   - 添加 Prompt Caching 支持
   - 添加 tool calling 支持
   - 改为容错错误处理
2. **[本会话]** 补齐 `alice_engine.providers.openai.OpenAIProvider` 和 `deepseek.DeepSeekProvider`
3. **[本会话]** 添加 `alice_engine.providers.base.StreamEvent` dataclass
4. **[本会话]** 改造 `aitest.adapters.llm.interface.get_provider()` 为委托实现
5. **[本会话或下一会话]** 编写 SDK 层单元测试
6. **[下一会话]** 编写 Platform 层集成测试 + 回归验证
7. **[下一会话]** 标记 `aitest/llm/providers/*.py` deprecated + 编写迁移文档

---

## 附录：代码量预估

| 模块 | 新增 | 修改 | 删除（Phase 9） | 合计 |
|------|------|------|-----------------|------|
| SDK Provider 实现 | ~600 行 | ~100 行 | 0 | ~700 行 |
| SDK Provider 测试 | ~900 行 | 0 | 0 | ~900 行 |
| Platform adapter | 0 | ~80 行 | 0 | ~80 行 |
| Platform 测试 | ~150 行 | ~20 行 | 0 | ~170 行 |
| 文档 + deprecation | ~200 行 | ~50 行 | 0 | ~250 行 |
| **Phase 8 总计** | ~1850 行 | ~250 行 | 0 | ~2100 行 |
| **Phase 9 删除** | 0 | 0 | ~1200 行 | -1200 行 |

**净变更（Phase 8+9）：** +900 行（主要是 SDK 测试）
