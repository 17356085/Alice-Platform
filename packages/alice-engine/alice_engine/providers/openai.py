"""OpenAI Provider — OpenAI API。

用法:
    from alice_engine.providers.openai import OpenAIProvider

    provider = OpenAIProvider(api_key="sk-...")
    response = provider.complete("system", "user")
"""

import os
import logging
from alice_engine.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI API Provider。"""

    def __init__(self, model: str = "gpt-4o-mini", api_key: str = ""):
        api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 未设置")

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("请安装: pip install alice-engine[llm-openai]")

        self.client = OpenAI(api_key=api_key)
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
                token_usage={
                    "input": response.usage.prompt_tokens,
                    "output": response.usage.completion_tokens,
                },
            )
        except Exception as e:
            logger.error("OpenAI API error: %s", e)
            return LLMResponse(content=str(e), model=self.model, finish_reason="error")
