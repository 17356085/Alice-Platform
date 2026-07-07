"""MiMo Provider — MiMo API (OpenAI-compatible)。

用法:
    from alice_engine.providers.mimo import MiMoProvider

    provider = MiMoProvider(api_key="tp-...")
    response = provider.complete("system", "user")
"""

import os
import logging
from alice_engine.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class MiMoProvider(LLMProvider):
    """MiMo API Provider (OpenAI-compatible)。"""

    def __init__(self, model: str = "mimo-v2.5", api_key: str = ""):
        api_key = api_key or os.environ.get("MIMO_API_KEY", "")
        if not api_key:
            raise ValueError("MIMO_API_KEY 未设置")

        base_url = os.environ.get("MIMO_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1")

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("请安装: pip install openai")

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def supports_tools(self) -> bool:
        return True

    def complete(self, system_prompt: str, user_prompt: str,
                 tools: list = None, **kwargs) -> LLMResponse:
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", 8192),
            )
            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=self.model,
                finish_reason=response.choices[0].finish_reason or "stop",
                usage={
                    "input": response.usage.prompt_tokens if response.usage else 0,
                    "output": response.usage.completion_tokens if response.usage else 0,
                },
            )
        except Exception as e:
            logger.error("MiMo API error: %s", e)
            return LLMResponse(content=str(e), model=self.model, finish_reason="error")
