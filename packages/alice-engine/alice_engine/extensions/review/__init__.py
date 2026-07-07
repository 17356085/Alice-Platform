"""Review Extension — 确定性工程驱动的代码审查。

借鉴 OCR (Open Code Review) 的三大能力:
  - RuleConfig: glob → prompt 映射 + 4 层优先级链
  - FileBundler: 关联文件分组为审查单元
  - PositionVerifier: LLM 输出行号校正

用法:
    from alice_engine.extensions.review import RuleConfig, FileBundler, PositionVerifier

    rules = RuleConfig(project_root)
    matched = rules.match_for_files(changed_files)

    bundler = FileBundler()
    bundles = bundler.bundle(changed_files)

    verifier = PositionVerifier()
    verified = verifier.verify_issues(issues, workspace)
"""

from alice_engine.extensions.review.models import (
    ReviewRule,
    ReviewBundle,
    ReviewIssue,
    ReviewResult,
)
from alice_engine.extensions.review.rule_config import RuleConfig
from alice_engine.extensions.review.file_bundler import FileBundler
from alice_engine.extensions.review.position_verifier import PositionVerifier

__all__ = [
    "ReviewRule",
    "ReviewBundle",
    "ReviewIssue",
    "ReviewResult",
    "RuleConfig",
    "FileBundler",
    "PositionVerifier",
]
