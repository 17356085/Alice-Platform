"""Review Extension — 数据结构。

借鉴 OCR (Open Code Review) 的确定性工程理念:
  - 规则配置: glob 模式 → 自然语言指令映射
  - 文件打包: 关联文件合并为审查单元
  - 位置校正: 验证 LLM 输出的行号准确性
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ReviewRule:
    """单条审查规则。

    规则不是模式匹配引擎，而是 glob → prompt 的映射。
    实际检测仍由 LLM 完成，规则告诉 LLM "找什么"。
    """

    path_pattern: str        # glob 模式, e.g. "**/*.vue"
    instruction: str         # 自然语言指令
    source: str              # "system" | "global" | "project" | "cli"
    merge_system: bool = False  # 是否与系统规则合并


@dataclass
class ReviewBundle:
    """文件审查单元 (一组关联文件)。

    OCR 的核心理念: 将关联文件合并为一个审查单元,
    上下文隔离，支持并发审查。
    """

    bundle_id: str
    files: list[str] = field(default_factory=list)
    reason: str = ""         # 分组原因, e.g. "vue+ts component pair"


@dataclass
class ReviewIssue:
    """单个审查发现。"""

    severity: str = "minor"  # critical | major | minor | nit
    file: str = ""
    line: int = 0
    column: int | None = None
    message: str = ""
    rule_source: str = ""    # 哪条规则触发
    fix_suggestion: str = ""


@dataclass
class ReviewResult:
    """审查结果。"""

    strategy: str = "diff"   # "diff" | "full" | "hybrid"
    bundles: list[ReviewBundle] = field(default_factory=list)
    issues: list[ReviewIssue] = field(default_factory=list)
    rules_applied: list[str] = field(default_factory=list)
    summary: str = ""
