"""
DiffFirstReviewAdapter — Review Skill 接收 Diff 而不是整文件。

集成点:
  1. review_graph.py:run_review_phase() 改用 DiffFirstReviewAdapter
  2. Skill prompt 注入 Diff + 条件降级到全文
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from aitest.governance.diff_extractor import (
    extract_diff_json,
    render_diff_for_llm,
    should_read_full_file,
    DiffFile,
)

WORKSTUDY = Path(__file__).resolve().parent.parent.parent


class DiffFirstReviewAdapter:
    """Diff-first review 适配器。"""

    def __init__(self, context_lines: int = 3, full_file_threshold: int = 100):
        """
        Args:
            context_lines: diff hunk 前后上下文行数
            full_file_threshold: 何时降级到全文 (改动行 > N)
        """
        self.context_lines = context_lines
        self.full_file_threshold = full_file_threshold

    def prepare_review_input(
        self,
        ref1: str = "HEAD~1",
        ref2: str = "HEAD",
        fallback_to_full: bool = True,
    ) -> dict:
        """
        为 Review Skill 准备输入数据。

        Returns:
            {
                "strategy": "diff" | "full",
                "diff_text": "...",  # 如果 strategy=diff
                "file_list": [{"file": ..., "hunks": ...}],  # 元数据
                "fallback_files": {...},  # 如果部分文件降级
                "summary": "..."
            }
        """
        diffs = extract_diff_json(
            ref1=ref1,
            ref2=ref2,
            context_lines=self.context_lines,
            workstudy_path=WORKSTUDY,
        )

        if not diffs:
            return {"strategy": "none", "summary": "No changes detected"}

        # 按文件决策: diff 还是 full
        diff_files = []
        full_files = []

        for diff in diffs:
            if should_read_full_file(diff, threshold_lines=self.full_file_threshold):
                full_files.append(diff.file)
            else:
                diff_files.append(diff)

        # 如果有需要读全文的文件，读它们
        full_file_contents = {}
        if full_files and fallback_to_full:
            for filepath in full_files:
                try:
                    full_path = WORKSTUDY / filepath
                    if full_path.exists():
                        content = full_path.read_text(encoding="utf-8")
                        full_file_contents[filepath] = content
                except Exception:
                    pass

        # 生成 diff 文本
        diff_text = render_diff_for_llm(diff_files, max_context=self.context_lines)

        # 生成摘要
        summary_parts = []
        if diff_files:
            total_added = sum(d.total_added for d in diff_files)
            total_removed = sum(d.total_removed for d in diff_files)
            summary_parts.append(
                f"Diff-based review: {len(diff_files)} files, "
                f"+{total_added} -{total_removed} lines (showing hunks + context)"
            )
        if full_files:
            summary_parts.append(
                f"Full-file review: {len(full_files)} files "
                f"(large changes or new files)"
            )

        return {
            "strategy": "hybrid" if full_files else "diff",
            "diff_text": diff_text,
            "full_files": full_file_contents,
            "diff_files": diff_files,
            "file_list": [
                {
                    "file": d.file,
                    "status": d.status,
                    "hunks": len(d.hunks),
                    "added": d.total_added,
                    "removed": d.total_removed,
                }
                for d in diff_files
            ],
            "summary": " | ".join(summary_parts) if summary_parts else "No changes",
        }

    def build_review_prompt(
        self,
        skill_name: str,
        review_input: dict,
        context_text: str = "",
        trigger: str = "manual",
    ) -> str:
        """
        为 Skill 构建 Prompt。

        集成点: review_graph.py:run_review_phase() 改用此函数
        """
        parts = []

        # 头
        parts.append(f"# Code Review: {skill_name}")
        parts.append(f"Strategy: {review_input['strategy']}")
        parts.append(f"Trigger: {trigger}\n")

        # 摘要
        if review_input.get("summary"):
            parts.append(f"## Summary\n{review_input['summary']}\n")

        # Diff 内容 (优先)
        if review_input.get("diff_text"):
            parts.append("## Code Changes (Diff)\n")
            parts.append(review_input["diff_text"])
            parts.append("")

        # 完整文件 (降级)
        if review_input.get("full_files"):
            parts.append("\n## Full Files (Large Changes)\n")
            for filepath, content in review_input["full_files"].items():
                parts.append(f"### {filepath}\n")
                parts.append("```")
                parts.append(content[:5000])  # Cap at 5k chars per file
                if len(content) > 5000:
                    parts.append(f"\n... ({len(content) - 5000} chars omitted)")
                parts.append("```\n")

        # 审计上下文
        if context_text:
            parts.append("\n## Review Context\n")
            parts.append(context_text)

        # 标准任务
        parts.append("\n## Review Instructions\n")
        parts.append(
            f"""
Review the changes above for:
1. **Correctness** — logic errors, edge cases, null handling
2. **Security** — injection risks, data exposure, auth checks
3. **Performance** — N+1 queries, unnecessary loops, memory leaks
4. **Standards** — alignment with coding conventions

Format output as:
```markdown
# Code Review

## Critical (must fix)
| File:Line | Issue | Fix |
|-----------|-------|-----|

## Major (should fix)
...

## Minor (nice to have)
...

## Summary
[Overall assessment]
```
"""
        )

        return "\n".join(parts)


def adapt_review_graph_node(
    original_run_review_phase_func,
):
    """
    装饰器: 改造 review_graph.py:run_review_phase()
    使其使用 DiffFirstReviewAdapter。

    使用:
      run_review_phase = adapt_review_graph_node(run_review_phase)
    """

    def wrapped(state: dict) -> dict:
        # 原逻辑的前半部分
        idx = state.get("phase_index", 0)
        phases = state.get("phases", [])
        if idx >= len(phases):
            return {**state, "status": "all_phases_done"}

        phase_key = phases[idx]
        skill_id = state.get("PHASE_TO_SKILL", {}).get(phase_key)
        if not skill_id:
            return {**state, "phase_index": idx + 1}

        # NEW: 使用 DiffFirstReviewAdapter
        adapter = DiffFirstReviewAdapter(
            context_lines=3,
            full_file_threshold=100,
        )
        review_input = adapter.prepare_review_input(
            ref1="HEAD~1",
            ref2="HEAD",
            fallback_to_full=True,
        )

        # 构建 Prompt
        user_input = adapter.build_review_prompt(
            skill_name=skill_id,
            review_input=review_input,
            context_text=state.get("context_text", ""),
            trigger=state.get("trigger", "manual"),
        )

        # 运行 Skill (原逻辑)
        from aitest.agents.agent_runner import run_skill

        try:
            resp = run_skill(skill_id, user_input, provider="claude", max_tokens=8192)
            result = resp.content
        except Exception as e:
            result = f"[SKILL ERROR] {skill_id}: {str(e)}"

        # 返回结果 (原逻辑)
        results = dict(state.get("review_results", {}))
        results[phase_key] = result

        return {
            **state,
            "review_results": results,
            "phase_index": idx + 1,
            "last_review_strategy": review_input.get("strategy"),
        }

    return wrapped
