"""
Diff 提取器 — 从 git 拉结构化 diff，省 token。

用途: Review 流程只看改动行 + 上下文，不读整文件。

结构:
  - DiffFile: file path, hunks (start, end, added, removed, context)
  - extract_diff_json(): git diff → JSON
  - render_diff_for_llm(): 可读格式给 LLM
  - should_read_full_file(): 决策函数 — 何时降级
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List


@dataclass
class DiffHunk:
    """单个 hunk: 改动块。"""
    file: str
    line_start: int  # 改动块在文件中的起始行
    line_end: int    # 改动块的结束行
    added_lines: List[str]     # 新增行
    removed_lines: List[str]   # 删除行
    context_before: List[str]  # 前 3 行上下文
    context_after: List[str]   # 后 3 行上下文
    old_start: int   # 原文件行号
    new_start: int   # 新文件行号


@dataclass
class DiffFile:
    """单个文件的 diff。"""
    file: str
    status: str  # added / modified / deleted / renamed
    hunks: List[DiffHunk]
    total_added: int
    total_removed: int
    is_new: bool = False


def extract_diff_json(
    ref1: str = "HEAD~1",
    ref2: str = "HEAD",
    context_lines: int = 3,
    workstudy_path: Optional[str] = None,
) -> List[DiffFile]:
    """
    从 git diff 提取结构化数据。

    Args:
        ref1: 基线 (e.g., "HEAD~1", "main")
        ref2: 新版本 (e.g., "HEAD")
        context_lines: 上下文行数 (default 3)
        workstudy_path: 工作区根目录 (auto-detect if None)

    Returns:
        DiffFile 列表
    """
    if workstudy_path is None:
        workstudy_path = Path(__file__).resolve().parent.parent.parent

    try:
        # 获取 diff 输出（--unified=N format）
        cmd = [
            "git",
            "diff",
            f"--unified={context_lines}",
            f"{ref1}..{ref2}",
        ]
        result = subprocess.run(
            cmd,
            cwd=str(workstudy_path),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )

        if result.returncode != 0:
            return []

        diff_text = result.stdout
        return _parse_unified_diff(diff_text, context_lines)

    except Exception as e:
        print(f"[DiffExtractor] Error: {e}")
        return []


def _parse_unified_diff(diff_text: str, context_lines: int) -> List[DiffFile]:
    """解析 unified diff 格式为结构化数据。"""
    files: dict[str, DiffFile] = {}
    current_file: Optional[str] = None
    current_hunks: List[DiffHunk] = []

    lines = diff_text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # 文件头
        if line.startswith("diff --git"):
            # 保存前一个文件
            if current_file and current_hunks:
                total_added = sum(len(h.added_lines) for h in current_hunks)
                total_removed = sum(len(h.removed_lines) for h in current_hunks)
                files[current_file] = DiffFile(
                    file=current_file,
                    status="modified",
                    hunks=current_hunks,
                    total_added=total_added,
                    total_removed=total_removed,
                )

            # 解析新文件
            parts = line.split()
            if len(parts) >= 4:
                current_file = parts[3][2:] if parts[3].startswith("b/") else parts[3]
                current_hunks = []
            i += 1
            continue

        # Hunk 头
        if line.startswith("@@"):
            # @@ -old_start,old_count +new_start,new_count @@ [function]
            hunk_header = line
            i += 1

            # 解析 hunk 坐标
            try:
                import re

                match = re.search(r"-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?", hunk_header)
                if match:
                    old_start = int(match.group(1))
                    new_start = int(match.group(3))
                else:
                    old_start = new_start = 0

            except Exception:
                old_start = new_start = 0

            # 收集 hunk 内容
            added = []
            removed = []
            context_before = []
            context_after = []
            line_start = new_start

            while i < len(lines):
                hunk_line = lines[i]

                # Hunk 结束
                if hunk_line.startswith("@@"):
                    break
                if hunk_line.startswith("diff --git"):
                    break

                # 行前缀
                prefix = hunk_line[0] if hunk_line else " "
                content = hunk_line[1:] if len(hunk_line) > 0 else ""

                if prefix == "+":
                    added.append(content)
                elif prefix == "-":
                    removed.append(content)
                elif prefix == " ":
                    context_after.append(content)
                    # Shift context_before → context_after (sliding window)
                    if len(context_before) >= context_lines:
                        context_before.pop(0)
                    context_before.append(content)

                i += 1

            # 创建 hunk 对象
            line_end = line_start + len(added) - 1 if added else line_start
            hunk = DiffHunk(
                file=current_file or "unknown",
                line_start=line_start,
                line_end=line_end,
                added_lines=added,
                removed_lines=removed,
                context_before=context_before[-context_lines:] if context_before else [],
                context_after=context_after[:context_lines],
                old_start=old_start,
                new_start=new_start,
            )

            if current_file:
                current_hunks.append(hunk)
            continue

        i += 1

    # 保存最后一个文件
    if current_file and current_hunks:
        total_added = sum(len(h.added_lines) for h in current_hunks)
        total_removed = sum(len(h.removed_lines) for h in current_hunks)
        files[current_file] = DiffFile(
            file=current_file,
            status="modified",
            hunks=current_hunks,
            total_added=total_added,
            total_removed=total_removed,
        )

    return list(files.values())


def render_diff_for_llm(diffs: List[DiffFile], max_context: int = 5) -> str:
    """
    将 diff 渲染为 LLM 友好的格式。

    格式:
    ```
    ## file.py
    - Lines 42-58: 2 added, 1 removed

    Context (line 38-40):
    38 | def old_func():
    39 |     pass
    40 |

    Hunk 1:
    41 | +def new_func():
    42 | +    x = 1
    43 | -def old_func():

    Context (line 44-46):
    44 |     pass
    ```
    """
    if not diffs:
        return "No changes."

    parts = ["# Code Changes\n"]

    for diff_file in diffs:
        parts.append(f"\n## {diff_file.file}")
        parts.append(
            f"- Status: {diff_file.status} | "
            f"+{diff_file.total_added} -{diff_file.total_removed}"
        )

        for i, hunk in enumerate(diff_file.hunks):
            parts.append(f"\n### Hunk {i + 1}")
            parts.append(f"Lines {hunk.line_start}–{hunk.line_end}\n")

            # Context before
            if hunk.context_before:
                parts.append("**Context (before):**")
                for j, ctx_line in enumerate(hunk.context_before[-max_context:]):
                    line_num = hunk.line_start - len(hunk.context_before) + j
                    parts.append(f"  {line_num} | {ctx_line}")
                parts.append("")

            # Changes
            parts.append("**Changes:**")
            for removed in hunk.removed_lines:
                parts.append(f"  - {removed}")
            for added in hunk.added_lines:
                parts.append(f"  + {added}")
            parts.append("")

            # Context after
            if hunk.context_after:
                parts.append("**Context (after):**")
                for j, ctx_line in enumerate(hunk.context_after[:max_context]):
                    line_num = hunk.line_end + j + 1
                    parts.append(f"  {line_num} | {ctx_line}")
                parts.append("")

    return "\n".join(parts)


def should_read_full_file(diff: DiffFile, threshold_lines: int = 100) -> bool:
    """
    决策函数: 是否需要读整个文件?

    降级条件:
    - 新增文件 (is_new)
    - 改动行数 > threshold_lines
    - 文件大小写不清楚 (context 不足)
    """
    if diff.is_new:
        return True
    if diff.total_added + diff.total_removed > threshold_lines:
        return True
    # Hunk 无上下文 → 可能是文件边界, 需要全文
    for hunk in diff.hunks:
        if not hunk.context_before or not hunk.context_after:
            return True
    return False


def diff_to_dict(diffs: List[DiffFile]) -> dict:
    """序列化为 JSON。"""
    return {
        "files": [
            {
                **asdict(f),
                "hunks": [asdict(h) for h in f.hunks],
            }
            for f in diffs
        ]
    }
