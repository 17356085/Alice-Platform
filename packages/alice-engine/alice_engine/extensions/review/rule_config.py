"""RuleConfig — 4 层优先级链规则配置系统。

借鉴 OCR 的规则设计理念:
  - 规则 = glob 模式 → 自然语言指令的映射
  - 4 层优先级: CLI > 项目 > 全局 > 系统默认
  - 规则不是模式匹配引擎，而是告诉 LLM "在这些文件中找什么"

用法:
    from alice_engine.extensions.review import RuleConfig

    rules = RuleConfig(project_root)
    matched = rules.match_for_files(["src/views/Home.vue", "src/api/user.py"])
    # → {"src/views/Home.vue": ["检查 v-html XSS防护", ...], ...}
"""

from __future__ import annotations

import json
import logging
from fnmatch import fnmatch
from pathlib import Path
from typing import Optional

from alice_engine.extensions.review.models import ReviewRule

logger = logging.getLogger(__name__)

# 内嵌系统默认规则 (最低优先级)
_SYSTEM_RULES: list[dict] = [
    {
        "path": "**/*.vue",
        "rule": (
            "检查: 1) v-html 是否有 XSS 防护; "
            "2) props 是否有类型校验; "
            "3) 事件处理函数是否有错误边界; "
            "4) 响应式数据是否有初始值"
        ),
    },
    {
        "path": "**/*.{ts,js}",
        "rule": (
            "检查: 1) 类型断言(as/!)是否安全; "
            "2) 异步调用是否有错误处理; "
            "3) 空值检查是否完整; "
            "4) 是否有未处理的 Promise rejection"
        ),
    },
    {
        "path": "**/*.py",
        "rule": (
            "检查: 1) SQL 注入风险(raw SQL, f-string 拼接); "
            "2) async 函数中的同步阻塞调用; "
            "3) 异常处理是否过于宽泛(Exception); "
            "4) 敏感数据是否硬编码"
        ),
    },
    {
        "path": "**/*.{json,yaml,yml}",
        "rule": (
            "检查: 1) 配置项是否有敏感信息(API key, 密码); "
            "2) JSON/YAML 语法是否正确; "
            "3) 必填字段是否缺失"
        ),
    },
    {
        "path": "**/*mapper*.xml",
        "rule": (
            "检查: 1) SQL 注入风险(参数化查询); "
            "2) XML 标签是否闭合; "
            "3) 参数类型是否匹配"
        ),
    },
    {
        "path": "**/requirements*.txt",
        "rule": (
            "检查: 1) 是否有已知漏洞的依赖版本; "
            "2) 版本是否固定(避免 >= 导致不可重复构建); "
            "3) 是否有不必要的依赖"
        ),
    },
]


class RuleConfig:
    """4 层优先级链规则配置。

    优先级 (首次匹配生效):
      1. cli_rules (最高, 通过参数传入)
      2. 项目规则 (<project>/governance/review-rules/rule.json)
      3. 全局规则 (~/.alice/review-rules/rule.json)
      4. 系统默认 (内嵌 _SYSTEM_RULES)
    """

    def __init__(self, project_root: Path | str | None = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self._rules: list[ReviewRule] = []
        self._include: list[str] = []
        self._exclude: list[str] = []
        self._load_all()

    def _load_all(self) -> None:
        """按优先级从低到高加载。"""
        self._rules = []
        self._include = []
        self._exclude = []

        # Layer 4 (最低): 系统默认
        self._load_system_rules()

        # Layer 3: 全局
        global_path = Path.home() / ".alice" / "review-rules" / "rule.json"
        self._load_from_file(global_path, source="global")

        # Layer 2: 项目
        project_path = self.project_root / "governance" / "review-rules" / "rule.json"
        self._load_from_file(project_path, source="project")

    def _load_system_rules(self) -> None:
        """加载内嵌系统规则。"""
        for entry in _SYSTEM_RULES:
            self._rules.append(ReviewRule(
                path_pattern=entry["path"],
                instruction=entry["rule"],
                source="system",
                merge_system=False,
            ))

    def _load_from_file(self, filepath: Path, source: str) -> None:
        """从 JSON 文件加载规则。"""
        if not filepath.exists():
            return

        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load rules from %s: %s", filepath, e)
            return

        # 加载 include/exclude
        if "include" in data:
            self._include.extend(data["include"])
        if "exclude" in data:
            self._exclude.extend(data["exclude"])

        # 加载规则
        for entry in data.get("rules", []):
            path_pattern = entry.get("path", "")
            rule_text = entry.get("rule", "")
            merge = entry.get("merge_system_rule", False)

            if not path_pattern or not rule_text:
                continue

            # 判断 rule 是内联内容还是文件路径
            instruction = self._resolve_rule_content(rule_text, filepath.parent)

            self._rules.append(ReviewRule(
                path_pattern=path_pattern,
                instruction=instruction,
                source=source,
                merge_system=merge,
            ))

    def _resolve_rule_content(self, rule_text: str, base_dir: Path) -> str:
        """判断 rule 是内联内容还是文件路径。

        OCR 的逻辑:
          - 包含换行 → 内联内容
          - 单行、无空格、以 .md/.txt/.markdown 结尾 → 文件路径
          - 否则 → 内联内容
        """
        # 多行一定是内联
        if "\n" in rule_text:
            return rule_text

        stripped = rule_text.strip()

        # 检查是否像文件路径
        if stripped and " " not in stripped and any(
            stripped.endswith(ext) for ext in (".md", ".txt", ".markdown")
        ):
            # 解析路径
            path = Path(stripped)
            if not path.is_absolute():
                path = base_dir / path

            # 安全检查: 不允许路径逃逸
            try:
                resolved = path.resolve()
                if resolved.exists() and resolved.stat().st_size <= 512 * 1024:
                    return resolved.read_text(encoding="utf-8")
            except (OSError, ValueError):
                pass

            logger.warning("Rule file not found or invalid: %s", stripped)
            return f"[Rule file not found: {stripped}]"

        # 默认: 内联内容
        return stripped

    def match_for_files(
        self,
        files: list[str],
        cli_rules: list[ReviewRule] | None = None,
    ) -> dict[str, list[str]]:
        """为文件列表匹配规则。

        返回 {file: [instruction1, instruction2, ...]}。
        每个文件可能匹配多条规则。
        """
        result: dict[str, list[str]] = {}

        for filepath in files:
            # include/exclude 过滤
            if not self._should_include(filepath):
                continue

            matched_instructions: list[str] = []

            # Layer 1 (最高): CLI 规则
            if cli_rules:
                for rule in cli_rules:
                    if self._match_glob(rule.path_pattern, filepath):
                        matched_instructions.append(rule.instruction)

            # Layer 2-4: 已加载的规则 (项目 > 全局 > 系统)
            # 由于加载顺序是从低到高，遍历时高优先级在后面
            # 但这里需要首次匹配生效，所以反向遍历
            seen_sources: dict[str, bool] = {}
            for rule in reversed(self._rules):
                if self._match_glob(rule.path_pattern, filepath):
                    # 同一 source 层级只取第一个匹配
                    if rule.source in seen_sources:
                        continue
                    seen_sources[rule.source] = True

                    if rule.merge_system:
                        # 合并: 高优先级规则 + 系统规则
                        system_instr = self._get_system_instruction(filepath)
                        if system_instr:
                            matched_instructions.append(
                                f"{rule.instruction}\n\n[系统规则补充] {system_instr}"
                            )
                        else:
                            matched_instructions.append(rule.instruction)
                    else:
                        matched_instructions.append(rule.instruction)

            if matched_instructions:
                result[filepath] = matched_instructions

        return result

    def _should_include(self, filepath: str) -> bool:
        """检查文件是否在 include/exclude 范围内。"""
        # exclude 优先
        for pattern in self._exclude:
            if self._match_glob(pattern, filepath):
                return False

        # 如果有 include, 文件必须匹配至少一个
        if self._include:
            return any(self._match_glob(p, filepath) for p in self._include)

        return True

    def _get_system_instruction(self, filepath: str) -> str | None:
        """获取系统默认规则中匹配的指令。"""
        for rule in self._rules:
            if rule.source == "system" and self._match_glob(rule.path_pattern, filepath):
                return rule.instruction
        return None

    @staticmethod
    def _match_glob(pattern: str, filepath: str) -> bool:
        """glob 匹配, 支持 ** 和 {a,b}。

        使用 Python 标准库 fnmatch，对 ** 做特殊处理。
        """
        # 处理 {a,b} 大括号展开
        if "{" in pattern and "}" in pattern:
            import re
            brace_match = re.search(r"\{([^}]+)\}", pattern)
            if brace_match:
                alternatives = brace_match.group(1).split(",")
                prefix = pattern[:brace_match.start()]
                suffix = pattern[brace_match.end():]
                return any(
                    RuleConfig._match_glob(prefix + alt + suffix, filepath)
                    for alt in alternatives
                )

        # 处理 ** 递归匹配
        if "**" in pattern:
            # ** 匹配任意目录深度
            parts = pattern.split("**")
            if len(parts) == 2:
                prefix, suffix = parts
                # 去掉前导 /
                suffix = suffix.lstrip("/")

                if not prefix:
                    # **/*.py → 匹配任意深度
                    if not suffix:
                        return True  # ** alone matches everything
                    return fnmatch(filepath, suffix) or fnmatch(
                        filepath.split("/")[-1], suffix
                    )

                # src/**/*.py → src/ 下任意深度
                if filepath.startswith(prefix):
                    remaining = filepath[len(prefix):].lstrip("/")
                    if not suffix:
                        return True  # src/** matches everything under src/
                    return fnmatch(remaining, suffix) or fnmatch(
                        remaining.split("/")[-1], suffix
                    )

        # 普通 glob
        return fnmatch(filepath, pattern) or fnmatch(
            filepath.split("/")[-1], pattern
        )

    def get_all_rules(self) -> list[ReviewRule]:
        """返回所有已加载的规则 (调试用)。"""
        return list(self._rules)
