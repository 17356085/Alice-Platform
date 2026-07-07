"""SkillExecutor 实现 — Skill 加载、上下文注入、LLM 调用。

解耦: 通过接口注入依赖，不直接依赖平台模块。

用法:
    from alice_engine.core.skill_executor_impl import SkillExecutorImpl

    executor = SkillExecutorImpl(
        skill_loader=loader,
        provider=provider,
        injector=injector,
    )
    response = executor.execute("automation/page-object-generator", user_input)
"""

import asyncio
import json
import logging
import time
from pathlib import Path

from alice_engine.providers.base import LLMProvider, LLMResponse
from alice_engine.runtime.core.security import SecurityError, get_security_hook

logger = logging.getLogger(__name__)


class SkillExecutorImpl:
    """Skill 执行器实现。

    用法:
        executor = SkillExecutorImpl(
            skill_loader=SkillLoader(governance_path),
            provider=MockProvider(),
        )
        response = executor.execute("automation/page-object-generator", "生成 PO")
    """

    def __init__(
        self,
        skill_loader=None,
        provider: LLMProvider = None,
        injector=None,
        adapter=None,
        security_hook=None,
    ):
        """
        Args:
            skill_loader: SkillLoader 实例
            provider: LLMProvider 实例
            injector: ContextInjector 实例 (可选)
            adapter: PromptAdapter 实例 (可选)
        """
        self.skill_loader = skill_loader
        self.provider = provider
        self.injector = injector
        self.adapter = adapter
        self.security_hook = security_hook

    def execute(
        self,
        skill_id: str,
        user_input: str,
        context_vars: dict = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        variant: str = None,
        reliable_provider=None,
        capability_router=None,
        agent_name: str = "",
        mcp_tools: dict | None = None,
        mcp_clients: list | None = None,
        security_hook=None,
    ) -> LLMResponse:
        """执行单个 Skill。

        Args:
            skill_id: Skill ID
            user_input: 用户输入
            context_vars: 上下文变量
            temperature: 温度
            max_tokens: 最大 token 数
            variant: Prompt 变体

        Returns:
            LLMResponse
        """
        context_vars = context_vars or {}
        start_time = time.time()
        security_hook = security_hook or self.security_hook or get_security_hook()

        # 1. 加载 Skill prompt
        try:
            system_prompt = self.skill_loader.load(skill_id, variant=variant)
        except FileNotFoundError as e:
            return LLMResponse(
                content=f"[Skill 加载失败] {e}",
                model="none", finish_reason="error",
            )

        # 2. 注入上下文 — v3.1: 修复签名匹配 ContextInjector.inject(skill_id, context_vars, system_prompt, user_prompt)
        if self.injector:
            try:
                result = self.injector.inject(skill_id, context_vars, system_prompt, user_input)
                if isinstance(result, tuple) and len(result) == 2:
                    system_prompt, user_input = result
                else:
                    system_prompt = result
            except Exception:
                pass  # 注入失败时使用原始 prompt

        # 3. 适配 prompt
        if self.adapter:
            system_prompt = self.adapter.adapt(system_prompt, self.provider)

        try:
            allowed, reason, user_input = security_hook.before_prompt(
                user_input,
                source=f"skill:{skill_id}",
            )
            if not allowed:
                return LLMResponse(
                    content=f"[Security] prompt blocked: {reason}",
                    model="none",
                    finish_reason="error",
                )
        except Exception as e:
            return LLMResponse(
                content=f"[Security] prompt check failed: {e}",
                model="none",
                finish_reason="error",
            )

        # 4. 组装可调用工具
        tools = []
        if capability_router:
            try:
                tools.extend(capability_router.tool_defs_for_agent(agent_name or ""))
            except Exception:
                pass

        mcp_tools = mcp_tools or {}
        if mcp_tools:
            tools.extend(
                td for td in mcp_tools.values()
                if isinstance(td, dict)
            )

        # 5. 调用 LLM
        llm = reliable_provider or self.provider
        provider_name = type(getattr(llm, "primary", llm)).__name__.replace("Provider", "").lower() or "unknown"
        allowed, reason = security_hook.before_provider(
            provider_name,
            system_prompt=system_prompt,
            user_prompt=user_input,
            tools=tools or None,
        )
        if not allowed:
            return LLMResponse(
                content=f"[Security] provider blocked: {reason}",
                model="none",
                finish_reason="error",
            )
        if tools and hasattr(llm, "supports_tools") and not llm.supports_tools():
            return LLMResponse(
                content="[Security] provider does not support tool calling",
                model="none",
                finish_reason="error",
            )
        try:
            response = llm.complete(
                system_prompt=system_prompt,
                user_prompt=user_input,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools or None,
            )
        except Exception as e:
            return LLMResponse(
                content=f"[LLM 调用失败] {e}",
                model="none", finish_reason="error",
            )

        # 6. Tool calling
        tool_results: list[dict] = []
        if getattr(response, "tool_calls", None):
            tool_results = self._execute_tool_calls(
                response.tool_calls,
                capability_router=capability_router,
                context_vars=context_vars,
                agent_name=agent_name,
                mcp_clients=mcp_clients or [],
                security_hook=security_hook,
            )
            response.tool_results = tool_results
            if tool_results:
                rendered = self._render_tool_results(tool_results)
                if rendered:
                    response.content = f"{response.content}\n\n{rendered}".strip()

        elapsed = time.time() - start_time
        usage = getattr(response, "usage", None)
        if usage is None:
            usage = getattr(response, "token_usage", None)
            if usage is not None:
                try:
                    setattr(response, "usage", usage)
                except Exception:
                    pass
        if usage:
            usage["elapsed_seconds"] = round(elapsed, 1)

        return response

    def _execute_tool_calls(
        self,
        tool_calls: list[dict],
        *,
        capability_router,
        context_vars: dict,
        agent_name: str,
        mcp_clients: list,
        security_hook,
    ) -> list[dict]:
        results: list[dict] = []
        mcp_by_prefix = {
            f"mcp__{getattr(client, 'server_id', '')}__": client
            for client in mcp_clients
            if getattr(client, "server_id", "")
        }

        for tc in tool_calls:
            tool_name = tc.get("name", tc.get("function", {}).get("name", ""))
            if not tool_name:
                continue
            arguments = self._normalize_tool_args(
                tc.get("input", tc.get("arguments", tc.get("function", {}).get("arguments", {}))),
            )
            allowed, reason = security_hook.before_tool_call(tool_name, arguments)
            if not allowed:
                results.append({
                    "call_id": tc.get("id", tool_name),
                    "success": False,
                    "content": f"Security blocked tool call: {reason}",
                    "error": "security_blocked",
                })
                continue

            mcp_client = next(
                (client for prefix, client in mcp_by_prefix.items() if tool_name.startswith(prefix)),
                None,
            )
            if mcp_client and hasattr(mcp_client, "call_tool"):
                try:
                    result = asyncio.run(mcp_client.call_tool(tool_name, arguments))
                except RuntimeError:
                    result = {
                        "call_id": tc.get("id", ""),
                        "success": False,
                        "content": "MCP tool execution unavailable in running event loop",
                        "error": "event_loop_running",
                    }
                results.append(result)
                continue

            if capability_router:
                for item in capability_router.execute_tool_calls(
                    [tc],
                    context_vars or {},
                    agent_name=agent_name,
                ):
                    results.append({
                        "call_id": item.call_id,
                        "success": item.success,
                        "content": item.content,
                        "data": item.data,
                        "error": item.error,
                        "duration_ms": item.duration_ms,
                        "truncated": item.truncated,
                    })
        return results

    @staticmethod
    def _normalize_tool_args(arguments):
        if isinstance(arguments, str):
            try:
                return json.loads(arguments)
            except Exception:
                return {}
        return arguments if isinstance(arguments, dict) else {}

    @staticmethod
    def _render_tool_results(tool_results: list[dict]) -> str:
        lines = []
        for idx, result in enumerate(tool_results, start=1):
            prefix = "✅" if result.get("success") else "❌"
            call_id = result.get("call_id", f"tool-{idx}")
            content = str(result.get("content", "")).strip()
            lines.append(f"{prefix} ToolResult[{call_id}]: {content[:2000]}")
        return "\n".join(lines)
