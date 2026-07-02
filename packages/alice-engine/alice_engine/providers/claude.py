"""Claude Provider — Anthropic Claude API。

用法:
    from alice_engine.providers.claude import ClaudeProvider

    provider = ClaudeProvider(api_key="sk-...")
    response = provider.complete("system", "user")
"""

import os
import logging
from alice_engine.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class ClaudeProvider(LLMProvider):
    """Anthropic Claude API Provider。"""

    def __init__(self, model: str = "claude-sonnet-4-6", api_key: str = ""):
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY 未设置")

        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("请安装: pip install alice-engine[llm-anthropic]")

        self.client = Anthropic(api_key=api_key)
        self.model = model

    def supports_tools(self) -> bool:
        return True

    def complete(self, system_prompt: str, user_prompt: str,
                 tools: list = None, **kwargs) -> LLMResponse:
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 8192),
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return LLMResponse(
                content=response.content[0].text if response.content else "",
                model=self.model,
                finish_reason=response.stop_reason or "stop",
                token_usage={
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                },
            )
        except Exception as e:
            logger.error("Claude API error: %s", e)
            return LLMResponse(content=str(e), model=self.model, finish_reason="error")
