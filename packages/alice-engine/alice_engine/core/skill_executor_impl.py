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

import logging
import time
from pathlib import Path

from alice_engine.providers.base import LLMProvider, LLMResponse

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

    def execute(
        self,
        skill_id: str,
        user_input: str,
        context_vars: dict = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        variant: str = None,
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

        # 4. 调用 LLM
        try:
            response = self.provider.complete(
                system_prompt=system_prompt,
                user_prompt=user_input,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            return LLMResponse(
                content=f"[LLM 调用失败] {e}",
                model="none", finish_reason="error",
            )

        elapsed = time.time() - start_time
        if response.token_usage:
            response.token_usage["elapsed_seconds"] = round(elapsed, 1)

        return response
