"""PositionVerifier — LLM 输出行号校正。

借鉴 OCR 的定位校正理念:
  - LLM 输出的 file:line 引用可能不准确
  - 独立模块验证行号是否在有效范围内
  - 附加警告信息到 issue.message

用法:
    from alice_engine.extensions.review import PositionVerifier

    verifier = PositionVerifier()
    verified = verifier.verify_issues(issues, workspace=Path("/path/to/project"))
"""

from __future__ import annotations

import logging
from pathlib import Path

from alice_engine.extensions.review.models import ReviewIssue

logger = logging.getLogger(__name__)


class PositionVerifier:
    """位置校正: 验证 LLM 的 file:line 引用。"""

    def verify_issues(
        self,
        issues: list[ReviewIssue],
        workspace: Path | str | None = None,
    ) -> list[ReviewIssue]:
        """校正问题列表中的行号。

        对每个 issue:
          1. 检查文件是否存在
          2. 检查行号是否在有效范围内
          3. 附加警告到 message (不修改原始数据)

        Returns:
            校正后的 issue 列表 (可能过滤掉无效的)
        """
        if not workspace:
            return issues

        workspace = Path(workspace)
        verified: list[ReviewIssue] = []

        for issue in issues:
            corrected = self._verify_single(issue, workspace)
            if corrected is not None:
                verified.append(corrected)

        return verified

    def _verify_single(
        self,
        issue: ReviewIssue,
        workspace: Path,
    ) -> ReviewIssue | None:
        """校正单个问题。"""
        if not issue.file:
            issue.message += " [⚠️ no file specified]"
            return issue

        filepath = workspace / issue.file

        # 检查文件存在性
        if not filepath.exists():
            # 尝试模糊匹配
            fuzzy = self._fuzzy_find(workspace, issue.file)
            if fuzzy:
                issue.message += f" [⚠️ file not found, closest: {fuzzy}]"
                issue.file = fuzzy
                filepath = workspace / fuzzy
            else:
                issue.message += f" [⚠️ file not found: {issue.file}]"
                return issue

        # 检查行号范围
        if issue.line <= 0:
            issue.message += " [⚠️ invalid line number]"
            return issue

        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            total_lines = len(lines)

            if issue.line > total_lines:
                issue.message += (
                    f" [⚠️ line {issue.line} exceeds file length {total_lines}]"
                )
                issue.line = min(issue.line, total_lines)

        except OSError as e:
            issue.message += f" [⚠️ cannot read file: {e}]"

        return issue

    def _fuzzy_find(self, workspace: Path, target: str) -> str | None:
        """尝试模糊匹配文件路径。

        LLM 有时输出的路径不完全准确, 例如:
          - 缺少 src/ 前缀
          - 大小写不匹配
          - 路径分隔符不同
        """
        # 规范化路径
        normalized = target.replace("\\", "/").strip("/")

        # 直接子目录匹配
        parts = normalized.split("/")
        if len(parts) > 1:
            # 尝试从末尾匹配
            for i in range(len(parts)):
                suffix = "/".join(parts[i:])
                for candidate in workspace.rglob(f"*{parts[-1]}"):
                    rel = str(candidate.relative_to(workspace)).replace("\\", "/")
                    if rel.endswith(suffix):
                        return rel

        return None
