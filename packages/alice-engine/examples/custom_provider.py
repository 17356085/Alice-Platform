"""自定义 LLM Provider — 注册和使用。"""

from alice_engine import (
    Engine,
    LLMProvider,
    LLMResponse,
    register_provider,
)


class EchoProvider(LLMProvider):
    """Echo Provider — 回显输入内容（用于调试）。"""

    def supports_tools(self) -> bool:
        return False

    def complete(self, system_prompt, user_prompt, tools=None, **kwargs) -> LLMResponse:
        # 回显 system prompt 的前 200 字符
        return LLMResponse(
            content=f"[Echo] {system_prompt[:200]}...",
            model="echo",
        )


# 注册自定义 Provider
register_provider("echo", EchoProvider)

# 使用
engine = Engine(
    project_path="D:/Desktop/TestingProject/ZJSN_Test-master526",
    llm_provider="echo",
)

result = engine.run("equipment", pages=["alarm-config"])
print(f"状态: {result.status}")
