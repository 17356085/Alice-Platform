"""
P2-1: MCP Sampling — Tool 反向调用 LLM (LLM-in-the-loop)
客户端不支持 sampling 时自动降级。
"""
import asyncio as _asyncio
from typing import Optional

# 延迟绑定：由 __init__.py 在 Server 创建后设置
_server_ref = None


def set_server(server) -> None:
    """设置全局 Server 引用（由 __init__.py 调用）。"""
    global _server_ref
    _server_ref = server


def _get_server():
    if _server_ref is None:
        raise RuntimeError("MCP Server not initialized. Call aitest.mcp.sampling.set_server() first.")
    return _server_ref


def sampling_available() -> bool:
    """检查当前 MCP 客户端是否支持 sampling 能力。"""
    try:
        server = _get_server()
        ctx = server.request_context
        session = ctx.session
        return session.check_client_capability("sampling")
    except Exception:
        return False


async def request_llm_summary(prompt_text: str, max_tokens: int = 500) -> Optional[str]:
    """请求 LLM 对文本进行摘要。失败时返回 None（不中断主流程）。"""
    if not sampling_available():
        return None
    try:
        from mcp.types import SamplingMessage, TextContent as SamplingText
        server = _get_server()
        ctx = server.request_context
        session = ctx.session
        result = await session.create_message(
            messages=[SamplingMessage(role="user", content=SamplingText(type="text", text=prompt_text))],
            max_tokens=max_tokens,
        )
        if result.content and result.content.type == "text":
            return result.content.text
        return None
    except Exception:
        return None


def request_llm_sync(prompt_text: str, max_tokens: int = 500) -> Optional[str]:
    """同步包装器 — 在 Tool handler 中调用 request_llm_summary。"""
    try:
        loop = _asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            future = _asyncio.run_coroutine_threadsafe(
                request_llm_summary(prompt_text, max_tokens), loop
            )
            return future.result(timeout=15)
        else:
            return _asyncio.run(request_llm_summary(prompt_text, max_tokens))
    except Exception:
        return None
