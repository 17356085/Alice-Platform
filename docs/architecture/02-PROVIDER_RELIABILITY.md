# Provider Reliability Chain — LLM 调用可靠性层

> 参考: Aperant `providers/factory.ts` (12-provider factory + OAuth detection + per-provider quirks)
>       + `session/runner.ts` (auth refresh loop, account switching on 429/401)
>       + Anthropic Prompt Caching docs
> 适配: AITest 4-provider (Claude/OpenAI/DeepSeek/Ollama) + Python 技术栈
> 状态: v1.0-draft | 优先级: P0

## 1. 问题

### 1.1 当前状态

```python
# aitest/llm/provider.py:969 — 当前工厂函数
def get_provider(name: str = "claude", **kwargs) -> LLMProvider:
    instance = PROVIDER_REGISTRY[name](**kwargs)
    # 仅包装了 tracer，无 retry/fallback/cache
    instance.complete = _trace_llm_call(instance.complete)
    return instance

# aitest/agents/skill_executor.py — 调用方
llm = get_provider("claude")
response = llm.complete(system_prompt, user_prompt)  # 失败即抛异常
```

问题：
1. **无重试** — 429 (rate limit) 直接失败，不重试
2. **无回退** — Claude 挂了不会自动切 DeepSeek
3. **无缓存** — 固定 Skill 提示每次都全量发送，浪费 token
4. **无超时** — LLM 调用卡 5 分钟，AgentLoop 卡 5 分钟
5. **无窗口感知** — 不知道已消耗多少 token，是否接近 limit

### 1.2 为什么不能直接用 Aperant 的 factory.ts

Aperant 使用 Vercel AI SDK 的 `generateText()`/`streamText()` 自带 retry。AITest 用的是原生 Python SDK (anthropic/openai packages)，需要自己实现可靠性层。

## 2. 设计

### 2.1 架构

```
ReliableProvider
    │
    ├── RetryManager (指数退避 + jitter)
    │     ├── classify_error() → retryable | fatal
    │     ├── backoff(attempt) → seconds
    │     └── max_retries: 3
    │
    ├── FallbackChain (按优先级回退)
    │     chain: [claude, deepseek, openai]
    │     每个 provider 独立 retry
    │     一个 provider 的 fatal error → 尝试下一个
    │
    ├── PromptCacheManager (Anthropic 专用)
    │     ├── detect_cacheable_blocks()
    │     ├── mark_cache_control()
    │     └── track_cache_hits()
    │
    ├── TimeoutGuard (超时保护)
    │     ├── per-call timeout (default 120s)
    │     └── total-chain timeout (default 600s)
    │
    └── ContextWindowMonitor (窗口感知)
          ├── estimate_tokens()
          ├── warn at 85%
          └── hard_stop at 95%
```

### 2.2 核心类

```python
# aitest/llm/reliable_provider.py

import time
import random
import logging
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum

from aitest.llm.provider import (
    LLMProvider, LLMResponse, StreamEvent, get_provider, list_providers
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════
#  Error Classification
# ══════════════════════════════════════════════════════════════════════════

class ErrorClass(Enum):
    RETRYABLE = "retryable"        # 429, 503, timeout — retry same provider
    FALLBACK = "fallback"          # 401, 403, 500 — try next provider
    FATAL = "fatal"                # 400 (bad request), invalid API key — stop

def classify_error(error: Exception, status_code: int = 0) -> ErrorClass:
    """分类 LLM 调用错误。

    参考 Aperant session/error-classifier.ts 的分类逻辑。
    """
    # Rate limiting — retry with backoff
    if status_code == 429 or "rate_limit" in str(error).lower():
        return ErrorClass.RETRYABLE
    if status_code in (503, 502) or "overloaded" in str(error).lower():
        return ErrorClass.RETRYABLE
    if "timeout" in str(error).lower() or "timed out" in str(error).lower():
        return ErrorClass.RETRYABLE

    # Auth / permission — try fallback provider
    if status_code in (401, 403):
        return ErrorClass.FALLBACK
    if "invalid_api_key" in str(error).lower() or "unauthorized" in str(error).lower():
        return ErrorClass.FALLBACK

    # Server errors — try fallback
    if status_code >= 500:
        return ErrorClass.FALLBACK

    # Bad request / other — fatal
    if status_code == 400:
        return ErrorClass.FATAL
    if "context_length" in str(error).lower() or "too many tokens" in str(error).lower():
        return ErrorClass.FATAL  # context window exceeded → needs continuation, not retry

    return ErrorClass.FATAL


# ══════════════════════════════════════════════════════════════════════════
#  Retry Configuration
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0        # 基础等待秒数
    max_delay: float = 60.0        # 最大等待秒数
    backoff_multiplier: float = 2.0  # 指数退避系数
    jitter: bool = True            # 是否加随机抖动


def compute_backoff(attempt: int, config: RetryConfig) -> float:
    """计算退避时间。exponential backoff + optional jitter。

    参考 Aperant 的无退避问题：Aperant 当前 429 只切换账号，不做退避。
    AITest 单账号场景更需要退避。
    """
    delay = min(config.base_delay * (config.backoff_multiplier ** attempt), config.max_delay)
    if config.jitter:
        delay = delay * (0.5 + random.random())  # 50%-150% jitter
    return delay


# ══════════════════════════════════════════════════════════════════════════
#  Fallback Chain Configuration
# ══════════════════════════════════════════════════════════════════════════

# 默认回退链：按质量/成本排序
DEFAULT_FALLBACK_CHAIN = [
    {"provider": "claude",   "model": "claude-sonnet-4-6-20250514"},
    {"provider": "deepseek", "model": "deepseek-chat"},
    {"provider": "openai",   "model": "gpt-4o-mini"},
]


@dataclass
class FallbackConfig:
    chain: list[dict] = field(default_factory=lambda: DEFAULT_FALLBACK_CHAIN.copy())
    per_provider_retry: RetryConfig = field(default_factory=RetryConfig)
    total_timeout: float = 600.0       # 整个 chain 的总超时
    per_call_timeout: float = 120.0    # 单次 LLM 调用超时


# ══════════════════════════════════════════════════════════════════════════
#  Prompt Cache Configuration (Anthropic 专用)
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class CacheConfig:
    enabled: bool = True
    min_block_tokens: int = 1024   # Anthropic 最少 1024 tokens 才能标记 cache
    cacheable_system_prompts: bool = True  # Skill system prompts 全部可缓存


# ══════════════════════════════════════════════════════════════════════════
#  ReliableProvider — 可靠性包装器
# ══════════════════════════════════════════════════════════════════════════

class ReliableProvider:
    """LLM 调用可靠性层。

    包装原始的 LLMProvider，增加:
      - 自动重试 (指数退避 + jitter)
      - 多 Provider 回退链
      - Prompt Caching (Anthropic 专用)
      - 超时保护
      - Token 使用追踪

    用法:
        rp = ReliableProvider(fallback_chain=[...])
        response = rp.complete(system_prompt, user_prompt)
    """

    def __init__(
        self,
        fallback_config: FallbackConfig = None,
        cache_config: CacheConfig = None,
    ):
        self.fallback_config = fallback_config or FallbackConfig()
        self.cache_config = cache_config or CacheConfig()
        self._usage_tracker = UsageTracker()

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        agent_name: str = "",
    ) -> LLMResponse:
        """执行 LLM 调用，带完整的可靠性保障。"""
        chain_start = time.time()
        last_error = None

        for i, provider_config in enumerate(self.fallback_config.chain):
            provider_name = provider_config["provider"]
            model = provider_config.get("model")

            try:
                # 单 provider 带 retry
                return self._call_with_retry(
                    provider_name=provider_name,
                    model_override=model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    tools=tools,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    agent_name=agent_name,
                )
            except FatalError:
                raise  # 不重试，直接抛
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Provider '{provider_name}' failed ({type(e).__name__}: {e}). "
                    f"Trying next in chain (position {i+1}/{len(self.fallback_config.chain)})..."
                )
                # 检查总超时
                if time.time() - chain_start > self.fallback_config.total_timeout:
                    raise TimeoutError(
                        f"Fallback chain timed out after {self.fallback_config.total_timeout}s"
                    ) from last_error
                continue

        # 所有 provider 都失败
        raise RuntimeError(
            f"All providers in fallback chain failed. "
            f"Chain: {[c['provider'] for c in self.fallback_config.chain]}. "
            f"Last error: {last_error}"
        ) from last_error

    def _call_with_retry(
        self,
        provider_name: str,
        model_override: Optional[str],
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[dict]],
        temperature: float,
        max_tokens: int,
        agent_name: str,
    ) -> LLMResponse:
        """单个 Provider 的带重试调用。"""
        retry_config = self.fallback_config.per_provider_retry
        last_error = None

        for attempt in range(retry_config.max_retries + 1):
            try:
                llm = get_provider(provider_name, model=model_override) if model_override \
                      else get_provider(provider_name)

                # Inject prompt caching markers (Anthropic only)
                if provider_name == "claude" and self.cache_config.enabled:
                    system_prompt = self._apply_cache_markers(system_prompt)

                # 带超时的调用
                response = self._call_with_timeout(
                    llm, system_prompt, user_prompt, tools, temperature, max_tokens
                )

                # 追踪 token 使用
                self._usage_tracker.record(
                    provider=provider_name,
                    agent=agent_name,
                    input_tokens=response.token_usage.get("input", 0),
                    output_tokens=response.token_usage.get("output", 0),
                    cache_read=response.token_usage.get("cache_read_input_tokens", 0),
                )

                return response

            except Exception as e:
                last_error = e
                error_class = classify_error(e)

                if error_class == ErrorClass.FATAL:
                    raise FatalError(str(e)) from e

                if error_class == ErrorClass.FALLBACK:
                    raise  # 让上层的 chain 循环处理

                # RETRYABLE: 退避后重试
                if attempt < retry_config.max_retries:
                    delay = compute_backoff(attempt, retry_config)
                    logger.info(
                        f"Retry {attempt+1}/{retry_config.max_retries} for "
                        f"'{provider_name}' after {delay:.1f}s ({e})"
                    )
                    time.sleep(delay)
                else:
                    raise  # 重试耗尽，让 chain 循环处理

        raise RuntimeError(f"Retry exhausted for '{provider_name}'") from last_error

    def _call_with_timeout(self, llm, *args, **kwargs) -> LLMResponse:
        """带超时的 LLM 调用。"""
        # Python 的同步调用无法直接 interrupt
        # 生产环境建议用 asyncio + asyncio.wait_for()
        # 这里用 signal.alarm 做简易实现 (Unix only)
        # 或用 concurrent.futures.ThreadPoolExecutor + Future.result(timeout)
        import concurrent.futures

        timeout = self.fallback_config.per_call_timeout
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(llm.complete, *args, **kwargs)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                raise TimeoutError(f"LLM call timed out after {timeout}s")

    def _apply_cache_markers(self, system_prompt: str) -> str:
        """为 Anthropic system prompt 标记 cache_control 断点。

        Anthropic Prompt Caching:
        - 至少 1024 tokens 的 content block 才能被标记为 cacheable
        - 最多标记 4 个 cache breakpoints
        - cache 有 5 分钟 TTL

        策略:
        1. AITest 的 Skill system prompt 通常 2000-5000 tokens → 标记整个 system block
        2. 缓存命中时，输入 token 成本降低 90%

        参考:
        - https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
        - Aperant transforms.ts: prompt caching thresholds (1024/2048/4096 tokens)
        """
        # ClaudeProvider 需要支持 cache_control 参数
        # 当前 provider.py 的 complete() 不支持此参数，需要扩展
        return system_prompt  # 实际 cache 标记在 ClaudeProvider 层处理

    def stream_complete(self, *args, **kwargs):
        """流式调用 (同样带可靠性保障)。"""
        # P1 实现，当前直接委托
        ...


class FatalError(Exception):
    """不可恢复的错误，不应重试或回退。"""
    pass


# ══════════════════════════════════════════════════════════════════════════
#  Usage Tracker — Token 使用追踪
# ══════════════════════════════════════════════════════════════════════════

class UsageTracker:
    """追踪每个 Provider/Agent 的 Token 使用量。

    用于:
      - 上下文窗口监控 (当前 session 已消耗 token)
      - 成本估算 (按 provider 的定价)
      - Prompt cache 命中率统计
    """

    def __init__(self):
        self._records: list[dict] = []
        self._session_input = 0
        self._session_output = 0
        self._cache_read = 0

    def record(self, provider: str, agent: str, input_tokens: int,
               output_tokens: int, cache_read: int = 0):
        self._records.append({
            "provider": provider,
            "agent": agent,
            "input": input_tokens,
            "output": output_tokens,
            "cache_read": cache_read,
            "timestamp": time.time(),
        })
        self._session_input += input_tokens
        self._session_output += output_tokens
        self._cache_read += cache_read

    def session_total(self) -> int:
        return self._session_input + self._session_output

    def cache_hit_rate(self) -> float:
        if self._session_input == 0:
            return 0.0
        return self._cache_read / self._session_input

    def estimated_cost(self) -> float:
        """粗估成本 (USD)。仅作参考。"""
        # Claude Sonnet: $3/M input, $15/M output
        # 实际按 provider 精确计算
        return (self._session_input / 1_000_000 * 3.0 +
                self._session_output / 1_000_000 * 15.0)
```

## 3. 与现有 provider.py 的集成

### 3.1 改造 ClaudeProvider.complete()

```python
# aitest/llm/provider.py — ClaudeProvider 加 cache_control 支持

class ClaudeProvider(LLMProvider):
    def complete(self, system_prompt, user_prompt, tools=None,
                 temperature=0.7, max_tokens=8192, cache_system=True):
        # ... existing code ...

        # 构建 system block (带 cache_control)
        system_block = {
            "type": "text",
            "text": system_prompt,
        }
        if cache_system and len(system_prompt) > 1024:
            system_block["cache_control"] = {"type": "ephemeral"}

        # ... rest of API call ...
```

### 3.2 工厂函数升级

```python
# aitest/llm/reliable_provider.py

def get_reliable_provider(
    primary: str = "claude",
    fallback_chain: list[dict] = None,
) -> ReliableProvider:
    """创建带可靠性保障的 Provider。

    用法:
        llm = get_reliable_provider("claude")
        # 自动使用默认回退链: claude → deepseek → openai

        llm = get_reliable_provider(
            "deepseek",
            fallback_chain=[
                {"provider": "deepseek", "model": "deepseek-chat"},
                {"provider": "openai",   "model": "gpt-4o-mini"},
            ]
        )
    """
    chain = fallback_chain or DEFAULT_FALLBACK_CHAIN
    # 确保 primary 在 chain 首位
    if chain[0]["provider"] != primary:
        chain = [{"provider": primary}] + chain

    return ReliableProvider(fallback_config=FallbackConfig(chain=chain))
```

### 3.3 AgentLoop 集成

```python
# aitest/agents/agent_runner.py — 修改 AgentLoop.__init__

class AgentLoop:
    def __init__(self, agent_name, provider="claude", ...):
        # 原来: self.provider = provider
        # 改为:
        self.reliable_provider = get_reliable_provider(
            primary=provider,
            # 可选: 从环境变量读取自定义回退链
            fallback_chain=self._parse_fallback_env(),
        )
```

## 4. 配置

### 4.1 环境变量

```bash
# .env
AI_PRIMARY_PROVIDER=claude
AI_FALLBACK_CHAIN=claude,deepseek,openai    # 逗号分隔
AI_MAX_RETRIES=3
AI_PER_CALL_TIMEOUT=120
AI_TOTAL_CHAIN_TIMEOUT=600
AI_CACHE_ENABLED=true
```

### 4.2 项目配置 (project.yaml)

```yaml
# governance/context/projects/<project>/project.yaml
ai:
  primary_provider: claude
  fallback_chain:
    - provider: claude
      model: claude-sonnet-4-6-20250514
    - provider: deepseek
      model: deepseek-chat
  retry:
    max_retries: 3
    base_delay: 1.0
  cache:
    enabled: true
```

## 5. 监控指标

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| `fallback_rate` | 触发回退的比例 | > 10% |
| `cache_hit_rate` | Prompt cache 命中率 | < 50% |
| `avg_retry_count` | 平均重试次数 | > 1.0 |
| `chain_exhaustion_rate` | 所有 provider 都失败的比例 | > 1% |
| `p95_latency` | P95 延迟 | > 30s |
| `session_token_total` | 当前 session token 消耗 | > 180K (90% of 200K limit) |

## 6. 参考来源

| 特性 | 参考 |
|------|------|
| 多 Provider 注册 + 回退 | Aperant `providers/factory.ts` — 12 providers + availability check |
| Auth refresh + 429 处理 | Aperant `session/runner.ts` — auth refresh loop, account switching |
| Prompt caching 阈值 | Anthropic docs + Aperant `transforms.ts` — 1024/2048/4096 thresholds |
| 错误分类 | Aperant `session/error-classifier.ts` — auth vs rate-limit vs generic |
| 指数退避 + jitter | AWS SDK retry mode — standard exponential backoff with full jitter |
| 超时控制 | Aperant `session/runner.ts` — 60s stream inactivity timeout |
