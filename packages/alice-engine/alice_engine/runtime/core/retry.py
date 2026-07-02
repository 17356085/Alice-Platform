"""ReliableProvider — LLM 调用可靠性层。

重试 + 降级 + 超时 + 用量追踪。

解耦: LLM provider 通过接口注入，不依赖平台模块。

用法:
    from alice_engine.runtime.retry import ReliableProvider

    provider = MockProvider()
    reliable = ReliableProvider(primary=provider, max_retries=3)
    response = reliable.complete(system_prompt, user_prompt)
"""

import time
import random
import logging
import concurrent.futures
from dataclasses import dataclass, field
from typing import Callable
from enum import Enum

from alice_engine.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class ErrorClass(Enum):
    RETRYABLE = "retryable"    # 429, 503, timeout
    FALLBACK = "fallback"      # 401, 403, 500
    FATAL = "fatal"            # 400, context_length


def classify_error(error: Exception) -> ErrorClass:
    """分类错误类型。"""
    msg = str(error).lower()
    if any(kw in msg for kw in ["429", "503", "timeout", "rate limit"]):
        return ErrorClass.RETRYABLE
    if any(kw in msg for kw in ["401", "403", "500", "auth"]):
        return ErrorClass.FALLBACK
    if any(kw in msg for kw in ["400", "context_length", "too long"]):
        return ErrorClass.FATAL
    return ErrorClass.RETRYABLE


@dataclass
class UsageTracker:
    """用量追踪。"""

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_requests: int = 0
    total_errors: int = 0
    total_retries: int = 0

    def record(self, response: LLMResponse):
        self.total_input_tokens += response.usage.get("input", 0)
        self.total_output_tokens += response.usage.get("output", 0)
        self.total_requests += 1

    def record_error(self):
        self.total_errors += 1

    def record_retry(self):
        self.total_retries += 1

    def summary(self) -> dict:
        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "requests": self.total_requests,
            "errors": self.total_errors,
            "retries": self.total_retries,
        }


class ReliableProvider(LLMProvider):
    """可靠性 Provider — 重试 + 降级 + 超时。

    用法:
        provider = MockProvider()
        reliable = ReliableProvider(primary=provider, max_retries=3)
        response = reliable.complete(system_prompt, user_prompt)
    """

    def __init__(
        self,
        primary: LLMProvider,
        fallback_chain: list[LLMProvider] | None = None,
        max_retries: int = 3,
        timeout: float = 120.0,
        backoff_base: float = 1.0,
        backoff_max: float = 30.0,
    ):
        self.primary = primary
        self.fallback_chain = fallback_chain or []
        self.max_retries = max_retries
        self.timeout = timeout
        self.backoff_base = backoff_base
        self.backoff_max = backoff_max
        self.usage = UsageTracker()

    def supports_tools(self) -> bool:
        return self.primary.supports_tools()

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[dict] | None = None,
        **kwargs,
    ) -> LLMResponse:
        """带重试和降级的 completion。"""
        providers = [self.primary] + self.fallback_chain
        last_error = None

        for provider in providers:
            for attempt in range(self.max_retries):
                try:
                    response = provider.complete(
                        system_prompt, user_prompt, tools=tools, **kwargs
                    )
                    self.usage.record(response)
                    return response

                except Exception as e:
                    last_error = e
                    error_class = classify_error(e)

                    if error_class == ErrorClass.FATAL:
                        self.usage.record_error()
                        raise

                    if error_class == ErrorClass.FALLBACK:
                        logger.warning("Provider %s failed: %s, trying next",
                                       type(provider).__name__, e)
                        break  # 跳到下一个 provider

                    # RETRYABLE: 指数退避重试
                    self.usage.record_retry()
                    wait = min(
                        self.backoff_base * (2 ** attempt) + random.uniform(0, 1),
                        self.backoff_max,
                    )
                    logger.info("Retry %d/%d after %.1fs: %s",
                                attempt + 1, self.max_retries, wait, e)
                    time.sleep(wait)

        raise last_error or Exception("All providers failed")


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
