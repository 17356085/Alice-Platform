"""Provider Reliability Chain — LLM 调用可靠性层。

Week 1 Day 1-2: retry + fallback + cache + timeout + usage tracking.

参考:
  - Aperant providers/factory.ts (12-provider factory + per-provider quirks)
  - Aperant session/runner.ts (auth refresh, 429/401 handling)
  - Aperant transforms.ts (prompt caching thresholds)
  - Anthropic Prompt Caching docs

用法:
    from aitest.llm.reliable_provider import get_reliable_provider
    llm = get_reliable_provider("claude")
    response = llm.complete(system_prompt, user_prompt)
"""
import time
import random
import logging
import concurrent.futures
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum

from aitest.llm.provider import (
    LLMProvider, LLMResponse, StreamEvent,
    get_provider, list_providers,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════
#  Error Classification
# ══════════════════════════════════════════════════════════════════════════

class ErrorClass(Enum):
    RETRYABLE = "retryable"    # 429, 503, timeout — retry same provider
    FALLBACK = "fallback"      # 401, 403, 500 — try next provider
    FATAL = "fatal"            # 400, context_length — stop immediately


def classify_error(error: Exception, status_code: int = 0) -> ErrorClass:
    """分类 LLM 调用错误。参考 Aperant session/error-classifier.ts。"""
    msg = str(error).lower()

    # Rate limiting — retry with backoff
    if status_code == 429 or "rate_limit" in msg or "rate limit" in msg:
        return ErrorClass.RETRYABLE
    if status_code in (503, 502) or "overloaded" in msg:
        return ErrorClass.RETRYABLE
    if "timeout" in msg or "timed out" in msg or "connection" in msg:
        return ErrorClass.RETRYABLE
    if "server error" in msg or "internal server error" in msg:
        return ErrorClass.RETRYABLE

    # Auth / permission — try fallback provider
    if status_code in (401, 403):
        return ErrorClass.FALLBACK
    if "invalid_api_key" in msg or "unauthorized" in msg or "authentication" in msg:
        return ErrorClass.FALLBACK
    if status_code >= 500:
        return ErrorClass.FALLBACK

    # Context window exceeded — fatal (needs continuation, not retry)
    if status_code == 400 and ("context_length" in msg or "too many tokens" in msg):
        return ErrorClass.FATAL

    # Bad request — fatal
    if status_code == 400:
        return ErrorClass.FATAL

    return ErrorClass.FATAL


# ══════════════════════════════════════════════════════════════════════════
#  Retry Configuration
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True


def compute_backoff(attempt: int, config: RetryConfig) -> float:
    """指数退避 + jitter。"""
    delay = min(config.base_delay * (config.backoff_multiplier ** attempt), config.max_delay)
    if config.jitter:
        delay = delay * (0.5 + random.random())
    return delay


# ══════════════════════════════════════════════════════════════════════════
#  Fallback Chain Configuration
# ══════════════════════════════════════════════════════════════════════════

DEFAULT_FALLBACK_CHAIN = [
    {"provider": "claude",   "model": None},   # None = use default model
    {"provider": "deepseek", "model": "deepseek-chat"},
    {"provider": "openai",   "model": "gpt-4o-mini"},
]


@dataclass
class FallbackConfig:
    chain: list[dict] = field(default_factory=lambda: DEFAULT_FALLBACK_CHAIN.copy())
    per_provider_retry: RetryConfig = field(default_factory=RetryConfig)
    total_timeout: float = 600.0
    per_call_timeout: float = 120.0


# ══════════════════════════════════════════════════════════════════════════
#  Usage Tracker
# ══════════════════════════════════════════════════════════════════════════

class UsageTracker:
    """Token 使用追踪。每个 session 一个实例。"""

    def __init__(self):
        self._records: list[dict] = []
        self._session_input: int = 0
        self._session_output: int = 0
        self._cache_read: int = 0
        self._fallback_count: int = 0
        self._retry_count: int = 0

    def record(self, provider: str, agent: str, input_tokens: int,
               output_tokens: int, cache_read: int = 0, thinking_tokens: int = 0):
        self._records.append({
            "provider": provider, "agent": agent,
            "input": input_tokens, "output": output_tokens,
            "cache_read": cache_read, "thinking": thinking_tokens,
            "timestamp": time.time(),
        })
        self._session_input += input_tokens
        self._session_output += output_tokens
        self._cache_read += cache_read

    def record_fallback(self): self._fallback_count += 1
    def record_retry(self): self._retry_count += 1

    def session_total(self) -> int:
        return self._session_input + self._session_output

    def cache_hit_rate(self) -> float:
        if self._session_input == 0:
            return 0.0
        return self._cache_read / self._session_input

    def estimated_cost(self) -> float:
        """粗估 USD 成本。Claude Sonnet: $3/M input, $15/M output."""
        return (self._session_input / 1_000_000 * 3.0 +
                self._session_output / 1_000_000 * 15.0)

    def summary(self) -> str:
        return (
            f"Tokens: {self.session_total():,} (in:{self._session_input:,} out:{self._session_output:,}) "
            f"Cache: {self.cache_hit_rate():.0%} "
            f"Fallback: {self._fallback_count} Retry: {self._retry_count} "
            f"Est. cost: ${self.estimated_cost():.4f}"
        )

    def reset_session(self):
        self._session_input = 0
        self._session_output = 0
        self._cache_read = 0


# 全局追踪器（跨 Agent）
_global_usage_tracker = UsageTracker()


def get_usage_tracker() -> UsageTracker:
    return _global_usage_tracker


# ══════════════════════════════════════════════════════════════════════════
#  ReliableProvider — 可靠性包装器
# ══════════════════════════════════════════════════════════════════════════

class ReliableProvider:
    """LLM 调用可靠性层。

    包装原始 LLMProvider，增加:
      - 自动重试 (指数退避 + jitter)
      - 多 Provider 回退链
      - 超时保护
      - Token 使用追踪

    用法:
        rp = ReliableProvider()
        response = rp.complete(system_prompt, user_prompt)
    """

    def __init__(self, fallback_config: FallbackConfig = None):
        self.fallback_config = fallback_config or FallbackConfig()
        self.tracker = UsageTracker()
        self._usage_tracker = _global_usage_tracker  # 全局共享

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        agent_name: str = "",
    ) -> LLMResponse:
        """执行 LLM 调用，带完整的可靠性保障。

        1. Circuit Breaker 检查 (快速失败)
        2. Retry (指数退避 + jitter, 3x)
        3. Fallback Chain (claude → deepseek → openai)
        """
        from aitest.llm.circuit_breaker import get_circuit_breaker, CircuitOpenError

        chain_start = time.time()
        last_error = None

        for i, provider_config in enumerate(self.fallback_config.chain):
            provider_name = provider_config["provider"]
            model_override = provider_config.get("model")

            # ── Circuit Breaker: fast-fail if provider is unhealthy ──
            cb = get_circuit_breaker(f"llm:{provider_name}")
            if cb.state.value == "open":
                logger.warning(
                    f"Circuit OPEN for '{provider_name}'. "
                    f"Skipping to next in chain ({i+1}/{len(self.fallback_config.chain)})..."
                )
                continue

            try:
                return self._call_with_retry(
                    provider_name=provider_name,
                    model_override=model_override,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    tools=tools,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    agent_name=agent_name,
                )
            except _FatalError:
                raise
            except CircuitOpenError:
                # Circuit opened mid-call — skip to next
                self.tracker.record_fallback()
                continue
            except Exception as e:
                last_error = e
                self.tracker.record_fallback()
                self._usage_tracker.record_fallback()
                logger.warning(
                    f"Provider '{provider_name}' failed ({type(e).__name__}). "
                    f"Trying next in chain ({i+1}/{len(self.fallback_config.chain)})..."
                )
                if time.time() - chain_start > self.fallback_config.total_timeout:
                    raise TimeoutError(
                        f"Fallback chain timed out after {self.fallback_config.total_timeout}s"
                    ) from last_error
                continue

        raise RuntimeError(
            f"All providers in fallback chain failed. "
            f"Chain: {[c['provider'] for c in self.fallback_config.chain]}. "
            f"Last error: {last_error}"
        ) from last_error

    def _call_with_retry(
        self, provider_name: str, model_override: Optional[str],
        system_prompt: str, user_prompt: str,
        tools: Optional[list[dict]], temperature: float, max_tokens: int,
        agent_name: str,
    ) -> LLMResponse:
        """单 Provider 带重试调用。"""
        retry_config = self.fallback_config.per_provider_retry
        last_error = None

        for attempt in range(retry_config.max_retries + 1):
            try:
                llm = (get_provider(provider_name, model=model_override)
                       if model_override else get_provider(provider_name))

                response = self._call_with_timeout(
                    llm, system_prompt, user_prompt, tools, temperature, max_tokens
                )

                # 追踪
                usage = response.token_usage or {}
                self.tracker.record(
                    provider=provider_name, agent=agent_name,
                    input_tokens=usage.get("input", 0),
                    output_tokens=usage.get("output", 0),
                    cache_read=usage.get("cache_read_input_tokens", 0),
                )
                self._usage_tracker.record(
                    provider=provider_name, agent=agent_name,
                    input_tokens=usage.get("input", 0),
                    output_tokens=usage.get("output", 0),
                    cache_read=usage.get("cache_read_input_tokens", 0),
                )

                if response.finish_reason == "error":
                    raise _ProviderError(f"[{provider_name}] LLM returned error: {response.content[:200]}")

                return response

            except _FatalError:
                raise
            except Exception as e:
                last_error = e
                error_class = classify_error(e)

                if error_class == ErrorClass.FATAL:
                    raise _FatalError(str(e)) from e

                if error_class == ErrorClass.FALLBACK:
                    raise  # 让上层 chain 循环处理

                # RETRYABLE
                if attempt < retry_config.max_retries:
                    delay = compute_backoff(attempt, retry_config)
                    self.tracker.record_retry()
                    self._usage_tracker.record_retry()
                    logger.info(
                        f"Retry {attempt+1}/{retry_config.max_retries} "
                        f"for '{provider_name}' after {delay:.1f}s ({e})"
                    )
                    time.sleep(delay)
                else:
                    raise

        raise RuntimeError(f"Retry exhausted for '{provider_name}'") from last_error

    def _call_with_timeout(self, llm: LLMProvider, *args, **kwargs) -> LLMResponse:
        """带超时的 LLM 调用。使用线程池实现跨平台超时。"""
        timeout = self.fallback_config.per_call_timeout
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(llm.complete, *args, **kwargs)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                raise TimeoutError(f"LLM call timed out after {timeout}s")

    def stream_complete(self, *args, **kwargs):
        """流式调用（暂不实现可靠性层，直接委托）。"""
        llm = get_provider(self.fallback_config.chain[0]["provider"])
        return llm.stream_complete(*args, **kwargs)


class _FatalError(Exception):
    """不可恢复的错误。"""
    pass


class _ProviderError(Exception):
    """Provider 返回了 error finish_reason。"""
    pass


# ══════════════════════════════════════════════════════════════════════════
#  工厂函数
# ══════════════════════════════════════════════════════════════════════════

def get_reliable_provider(
    primary: str = "claude",
    fallback_chain: list[dict] = None,
) -> ReliableProvider:
    """创建带可靠性保障的 Provider。

    用法:
        llm = get_reliable_provider("claude")
        llm = get_reliable_provider("deepseek", fallback_chain=[
            {"provider": "deepseek", "model": "deepseek-chat"},
            {"provider": "openai", "model": "gpt-4o-mini"},
        ])
    """
    if fallback_chain:
        chain = fallback_chain
    else:
        chain = DEFAULT_FALLBACK_CHAIN.copy()
        # 确保 primary 在链首位
        if chain[0]["provider"] != primary:
            chain.insert(0, {"provider": primary, "model": None})

    return ReliableProvider(fallback_config=FallbackConfig(chain=chain))
