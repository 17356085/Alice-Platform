"""Code consistency checks — mechanical grep + LLM adversarial review.

Extracted from agent_runner.py (W01 refactor, 2026-06-17).
~164 lines extracted: _act_mechanical_consistency_check, _act_llm_consistency_review,
_persist_consistency_report, _persist_review_report.
"""

import re
from pathlib import Path

from aitest.llm.provider import LLMResponse
from aitest.agents.output_persistence import (
    _slug_to_page_name, _page_slug_to_underscore,
    persist_consistency_report, persist_review_report,
)

from aitest.platform.paths import get_workstudy, get_test_project_root
WORKSTUDY = get_workstudy()


def run_mechanical_consistency_check(module: str, page: str,
                                     code_redline_checks: list,
                                     logger=None) -> LLMResponse:
    """Mechanical code compliance check (no LLM — grep patterns).

    Args:
        module: module name
        page: page slug
        code_redline_checks: list of (label, pattern, should_find) tuples
        logger: optional callable

    Returns:
        LLMResponse with model='mechanical'
    """
    page_name = _slug_to_page_name(page)
    zjsn = get_test_project_root()
    po_file = zjsn / "page" / f"{module}_page" / f"{page_name}Page.py" if zjsn else Path(f"page/{module}_page/{page_name}Page.py")
    test_file = zjsn / "script" / module / f"test_{_page_slug_to_underscore(page)}.py" if zjsn else Path(f"script/{module}/test_{_page_slug_to_underscore(page)}.py")

    issues = []
    for fpath in [po_file, test_file]:
        if not fpath.exists():
            continue
        content = fpath.read_text(encoding="utf-8")
        is_po_file = "Page.py" in fpath.name

        for label, pattern, should_find in code_redline_checks:
            if "BasePage" in label and not is_po_file:
                continue

            found = bool(re.search(pattern, content, re.MULTILINE))
            if found != should_find:
                if should_find:
                    issues.append(f"{fpath.name}: 缺少 {label}（应包含 {pattern}）")
                else:
                    for match in re.finditer(pattern, content, re.MULTILINE):
                        line_no = content[:match.start()].count("\n") + 1
                        matched_text = match.group().strip()[:60]
                        if "print" in label and "def " in matched_text:
                            continue
                        issues.append(f"{fpath.name}:{line_no}: {label}（禁止模式: {matched_text}）")

    lines = []
    if issues:
        lines.append(f"FAIL: 代码合规检查发现 {len(issues)} 个问题:")
        for issue in issues:
            lines.append(f"  - {issue}")
    else:
        lines.append("PASS: 代码合规检查通过，无违规项。")

    persist_consistency_report(module, page, lines, issues)

    return LLMResponse(
        content="\n".join(lines),
        model="mechanical",
        finish_reason="stop",
        token_usage={"input": 0, "output": 0},
    )


def run_llm_consistency_review(module: str, page: str, provider: str,
                                build_context_vars, run_skill_fn) -> LLMResponse:
    """LLM adversarial code review for locator stability, wait strategy, assertions.

    Args:
        module: module name
        page: page slug
        provider: LLM provider string
        build_context_vars: callable() → dict of context vars
        run_skill_fn: callable(skill_id, user_input, provider, context_vars) → LLMResponse

    Returns:
        LLMResponse with review results.
    """
    page_name = _slug_to_page_name(page)
    zjsn = get_test_project_root()
    po_file = zjsn / "page" / f"{module}_page" / f"{page_name}Page.py" if zjsn else Path(f"page/{module}_page/{page_name}Page.py")
    test_file = zjsn / "script" / module / f"test_{_page_slug_to_underscore(page)}.py" if zjsn else Path(f"script/{module}/test_{_page_slug_to_underscore(page)}.py")

    code_snippets = []
    for fpath in [po_file, test_file]:
        if fpath.exists():
            content = fpath.read_text(encoding="utf-8")
            code_snippets.append(f"### {fpath.name}\n```python\n{content[:3000]}\n```")

    if not code_snippets:
        return LLMResponse(
            content="PASS: 无代码文件可审查（文件不存在）",
            model="mechanical",
            finish_reason="stop",
            token_usage={"input": 0, "output": 0},
        )

    review_prompt = f"""你是自动化测试代码规范审查专家。对以下代码进行**对抗性深度审查**。

## 审查维度（grep 无法检测的问题）

1. **定位器稳定性**: CSS Selector 是否过于依赖动态类名？是否优先使用测试 id/data-testid？定位器是否可能在 Vue 重渲染后失效？
2. **等待策略**: 是否正确使用 wait_vue_stable？是否存在隐式等待依赖？弹窗/下拉框是否有显式等待？
3. **断言充分性**: 断言是否只检查表面文本而忽略数据正确性？分页/搜索后是否验证结果变化？
4. **Element Plus 坑位**: el-dialog 是否处理了 Teleport？el-select 选项是否在 body 下？el-cascader 是否有联动加载等待？
5. **异常处理**: 清理/重置操作是否有 try/finally？弹窗关闭失败是否有 fallback？

## 待审查代码

{chr(10).join(code_snippets)}

## 输出格式

```
### 深度审查报告

| # | 维度 | 严重度 | 位置 | 问题 | 建议修复 |
|---|------|--------|------|------|---------|

**总体评分**: X/10
**关键风险**: ...
```
"""
    try:
        response = run_skill_fn(
            skill_id="automation/code-consistency-checker",
            user_input=review_prompt,
            provider=provider,
            context_vars=build_context_vars(),
        )
        if response and response.content:
            persist_review_report(module, page, response.content)
        return response or LLMResponse(
            content="REVIEW_FAILED: LLM 调用返回空",
            model="unknown",
            finish_reason="error",
            token_usage={"input": 0, "output": 0},
        )
    except Exception as e:
        return LLMResponse(
            content=f"REVIEW_FAILED: {e}",
            model="unknown",
            finish_reason="error",
            token_usage={"input": 0, "output": 0},
        )
