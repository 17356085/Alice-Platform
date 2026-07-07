"""ReliableProvider — LLM reliability helpers with compatibility shims."""

import concurrent.futures
from enum import Enum
from dataclasses import dataclass, field
import logging
import random
import time

from alice_engine.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class ErrorClass(Enum):
    RETRYABLE = "retryable"    # 429, 503, timeout
    FALLBACK = "fallback"      # 401, 403, 500
    FATAL = "fatal"            # 400, context_length


def classify_error(error: Exception, status_code: int | None = None) -> ErrorClass:
    """分类错误类型。"""
    msg = str(error).lower()
    if status_code in (429, 503):
        return ErrorClass.RETRYABLE
    if status_code in (401, 403, 500):
        return ErrorClass.FALLBACK
    if status_code == 400:
        if "context_length" in msg or "too many tokens" in msg:
            return ErrorClass.FATAL
        return ErrorClass.FATAL
    if any(kw in msg for kw in ["429", "503", "timeout", "timed out", "rate limit", "server error"]):
        return ErrorClass.RETRYABLE
    if any(kw in msg for kw in ["401", "403", "500", "auth", "unauthorized", "forbidden", "invalid_api_key"]):
        return ErrorClass.FALLBACK
    if any(kw in msg for kw in ["400", "context_length", "too long", "too many tokens", "bad request"]):
        return ErrorClass.FATAL
    return ErrorClass.FATAL


@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True


def compute_backoff(attempt: int, config: RetryConfig) -> float:
    delay = min(config.base_delay * (config.backoff_multiplier ** attempt), config.max_delay)
    if config.jitter:
        delay = delay * (0.5 + random.random())
    return delay


DEFAULT_FALLBACK_CHAIN = [
    {"provider": "mimo", "model": "mimo-default"},
    {"provider": "deepseek", "model": "deepseek-chat"},
    {"provider": "openai", "model": "gpt-4o-mini"},
    {"provider": "claude", "model": "claude-sonnet"},
]


@dataclass
class FallbackConfig:
    chain: list[dict] = field(default_factory=lambda: DEFAULT_FALLBACK_CHAIN.copy())
    per_provider_retry: RetryConfig = field(default_factory=RetryConfig)
    total_timeout: float = 600.0
    per_call_timeout: float = 120.0


class _FatalError(Exception):
    """不可恢复错误。"""


class UsageTracker:
    """用量追踪。"""

    def __init__(self):
        self._records: list[dict] = []
        self._session_input = 0
        self._session_output = 0
        self._cache_read = 0
        self._fallback_count = 0
        self._retry_count = 0

    def record(
        self,
        provider: str,
        agent: str,
        input_tokens: int,
        output_tokens: int,
        cache_read: int = 0,
    ) -> None:
        self._records.append(
            {
                "provider": provider,
                "agent": agent,
                "input": input_tokens,
                "output": output_tokens,
                "cache_read": cache_read,
                "timestamp": time.time(),
            }
        )
        self._session_input += input_tokens
        self._session_output += output_tokens
        self._cache_read += cache_read

    def session_total(self) -> int:
        return self._session_input + self._session_output

    def record_fallback(self) -> None:
        self._fallback_count += 1

    def record_retry(self) -> None:
        self._retry_count += 1

    def cache_hit_rate(self) -> float:
        if self._session_input == 0:
            return 0.0
        return self._cache_read / self._session_input

    def estimated_cost(self) -> float:
        return (self._session_input / 1_000_000 * 3.0 +
                self._session_output / 1_000_000 * 15.0)

    def reset_session(self) -> None:
        self._session_input = 0
        self._session_output = 0
        self._cache_read = 0
        self._fallback_count = 0
        self._retry_count = 0

    def summary(self) -> str:
        total = self.session_total()
        return (
            f"Tokens: {total:,} | "
            f"Fallback: {self._fallback_count} | "
            f"Retry: {self._retry_count} | "
            f"Cache hit: {self.cache_hit_rate():.0%}"
        )


class ReliableProvider(LLMProvider):
    """可靠性 Provider — 重试 + 降级 + 超时。"""

    def __init__(
        self,
        primary: LLMProvider | None = None,
        fallback_chain: list[LLMProvider] | None = None,
        max_retries: int = 3,
        timeout: float = 120.0,
        backoff_base: float = 1.0,
        backoff_max: float = 30.0,
        fallback_config: FallbackConfig | None = None,
    ):
        self.primary = primary
        self.fallback_chain = list(fallback_chain or [])
        if fallback_config is None:
            chain = DEFAULT_FALLBACK_CHAIN.copy()
            if self.fallback_chain:
                chain = [{"provider": getattr(primary, "provider_id", lambda: "primary")()}] if primary else []
            fallback_config = FallbackConfig(
                chain=chain,
                per_provider_retry=RetryConfig(
                    max_retries=max_retries,
                    base_delay=backoff_base,
                    max_delay=backoff_max,
                ),
                per_call_timeout=timeout,
            )
        self.fallback_config = fallback_config
        self.tracker = UsageTracker()

    def supports_tools(self) -> bool:
        if self.primary is None:
            return True
        return self.primary.supports_tools()

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[dict] | None = None,
        **kwargs,
    ) -> LLMResponse:
        """带重试和降级的 completion。"""
        providers = self._resolve_chain()
        last_error = None
        chain_start = time.time()
        retry_config = self.fallback_config.per_provider_retry

        for provider_name, provider in providers:
            for attempt in range(retry_config.max_retries + 1):
                try:
                    response = self._call_with_timeout(
                        provider.complete,
                        system_prompt,
                        user_prompt,
                        tools=tools,
                        **kwargs,
                    )
                    usage = getattr(response, "usage", {}) or getattr(response, "token_usage", {}) or {}
                    self.tracker.record(
                        provider_name,
                        str(kwargs.get("agent_name", "")),
                        int(usage.get("input", usage.get("prompt_tokens", 0)) or 0),
                        int(usage.get("output", usage.get("completion_tokens", 0)) or 0),
                        int(usage.get("cache_read_input_tokens", 0) or 0),
                    )
                    return response if isinstance(response, LLMResponse) else LLMResponse(content=str(response))

                except Exception as e:
                    last_error = e
                    error_class = classify_error(e)

                    if error_class == ErrorClass.FATAL:
                        raise _FatalError(str(e)) from e

                    if error_class == ErrorClass.FALLBACK:
                        self.tracker.record_fallback()
                        logger.warning("Provider %s failed: %s, trying next", provider_name, e)
                        break

                    if attempt < retry_config.max_retries:
                        self.tracker.record_retry()
                        wait = compute_backoff(attempt, retry_config)
                        logger.info("Retry %d/%d after %.1fs: %s", attempt + 1, retry_config.max_retries, wait, e)
                        time.sleep(wait)
                    else:
                        self.tracker.record_fallback()
                        break

            if time.time() - chain_start > self.fallback_config.total_timeout:
                raise TimeoutError(
                    f"Fallback chain timed out after {self.fallback_config.total_timeout}s"
                ) from last_error

        raise last_error or Exception("All providers failed")

    def _resolve_chain(self) -> list[tuple[str, LLMProvider]]:
        chain: list[tuple[str, LLMProvider]] = []
        if self.primary is not None:
            chain.append((self.primary.provider_id(), self.primary))
        for item in self.fallback_chain:
            chain.append((item.provider_id(), item))
        if chain:
            return chain

        from alice_engine.providers import get_provider

        for item in self.fallback_config.chain:
            provider_name = item.get("provider", "mock")
            chain.append((provider_name, get_provider(provider_name)))
        return chain

    def _call_with_timeout(self, fn, *args, **kwargs):
        timeout = self.fallback_config.per_call_timeout
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(fn, *args, **kwargs)
            return future.result(timeout=timeout)


def get_reliable_provider(
    primary: str | LLMProvider,
    fallback_chain: list | None = None,
    **kwargs,
) -> ReliableProvider:
    """获取 ReliableProvider 实例。

    Args:
        primary: Provider 名称或实例
        fallback_chain: 降级链 (provider 名称列表或实例列表)
        **kwargs: 传递给 ReliableProvider

    Returns:
        ReliableProvider 实例
    """
    from alice_engine.providers import get_provider

    if isinstance(primary, str):
        primary = get_provider(primary)

    fallback_providers = []
    if fallback_chain:
        for fb in fallback_chain:
            if isinstance(fb, dict):
                fallback_providers.append(get_provider(fb.get("provider", "mock")))
            elif isinstance(fb, str):
                fallback_providers.append(get_provider(fb))
            else:
                fallback_providers.append(fb)

    return ReliableProvider(
        primary=primary,
        fallback_chain=fallback_providers,
        **kwargs,
    )
