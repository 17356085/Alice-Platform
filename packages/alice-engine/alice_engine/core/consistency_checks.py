"""Consistency Checks — 代码一致性检查。

解耦: 路径通过参数传入。

用法:
    from alice_engine.core.consistency_checks import run_mechanical_check

    issues = run_mechanical_check(
        content=code_content,
        checks=[("继承 BasePage", r"class \\w+\\(BasePage\\):", True)],
    )
"""

import re
from pathlib import Path


def run_mechanical_check(
    content: str,
    checks: list[tuple[str, str, bool]],
) -> list[str]:
    """机械化检查 — grep 规则匹配。

    Args:
        content: 要检查的内容
        checks: 检查规则列表 [(label, pattern, should_find), ...]

    Returns:
        问题列表
    """
    issues = []
    for label, pattern, should_find in checks:
        found = bool(re.search(pattern, content, re.MULTILINE))
        if found != should_find:
            if should_find:
                issues.append(f"FAIL: {label} — 未找到")
            else:
                issues.append(f"FAIL: {label} — 不应存在")
    return issues


def run_redline_check(
    content: str,
    redline_checks: list[tuple[str, str, bool]],
) -> tuple[bool, list[str]]:
    """红线检查。

    Args:
        content: 要检查的内容
        redline_checks: 红线规则 [(label, pattern, should_find), ...]

    Returns:
        (passed, issues)
    """
    issues = run_mechanical_check(content, redline_checks)
    return len(issues) == 0, issues


def run_mechanical_consistency_check(module, page, checks, logger=None):
    """兼容旧接口 — 机械化一致性检查。"""
    return None


def run_llm_consistency_review(module, page, provider, build_context_vars=None, run_skill_fn=None):
    """兼容旧接口 — LLM 一致性审查。"""
    return None
