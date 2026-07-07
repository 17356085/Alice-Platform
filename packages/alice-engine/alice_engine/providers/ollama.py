"""Ollama Provider — 本地 Ollama 模型。

用法:
    from alice_engine.providers.ollama import OllamaProvider

    provider = OllamaProvider(model="qwen3:14b")
    response = provider.complete("system", "user")
"""

import logging
from alice_engine.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Ollama 本地模型 Provider。"""

    provider_name = "ollama"
    provider_description = "Local Ollama model provider"
    provider_supports_tools = False

    def __init__(self, model: str = "qwen3:14b", base_url: str = "http://localhost:11434"):
        try:
            import httpx
        except ImportError:
            raise ImportError("请安装: pip install httpx")

        self.model = model
        self.base_url = base_url

    def supports_tools(self) -> bool:
        return False

    def complete(self, system_prompt: str, user_prompt: str,
                 tools: list = None, **kwargs) -> LLMResponse:
        import httpx
        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "stream": False,
                },
                timeout=120.0,
            )
            data = response.json()
            content = data.get("message", {}).get("content", "")
            return LLMResponse(
                content=content,
                model=self.model,
                finish_reason="stop",
                usage={
                    "input": data.get("prompt_eval_count", 0),
                    "output": data.get("eval_count", 0),
                },
            )
        except Exception as e:
            logger.error("Ollama error: %s", e)
            return LLMResponse(content=str(e), model=self.model, finish_reason="error")
