"""Output Persistence — Skill 输出持久化。

解耦: 路径通过参数传入。

用法:
    from alice_engine.core.output_persistence import save_skill_output

    saved = save_skill_output(
        skill_id="automation/page-object-generator",
        content=llm_output,
        module="equipment",
        page="alarm-config",
        governance_path="./governance",
    )
"""

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


def save_skill_output(
    skill_id: str,
    content: str,
    module: str,
    page: str,
    agent_name: str = "",
    governance_path: str | Path = None,
    context_modules: str | Path = None,
    logger_fn=None,
) -> str:
    """保存 Skill 输出到文件。

    Args:
        skill_id: Skill ID
        content: LLM 输出内容
        module: 模块名
        page: 页面名
        agent_name: Agent 名称
        governance_path: 治理目录路径
        context_modules: 模块上下文目录路径
        logger_fn: 日志函数

    Returns:
        保存的文件路径，失败返回空字符串
    """
    if not content or not module:
        return ""

    try:
        # 确定保存目录
        # v3.1: 使用 GOVERNANCE 路径而非 CWD，避免 worktree 操作时路径错误
        if context_modules:
            parent_dir = Path(context_modules) / module
        elif governance_path:
            parent_dir = Path(governance_path) / "context" / "modules" / module
        else:
            # 使用 WORKSTUDY 环境变量或默认路径
            import os
            workstudy = os.environ.get("AITEST_WORKSTUDY", ".")
            parent_dir = Path(workstudy) / "governance" / "context" / "modules" / module

        parent_dir.mkdir(parents=True, exist_ok=True)

        # 确定文件名
        filename = _skill_to_filename(skill_id)
        filepath = parent_dir / filename

        # 提取有意义的内容
        content_md = _extract_content(content, filepath.suffix)

        filepath.write_text(content_md, encoding="utf-8")

        if logger_fn:
            logger_fn(f"  saved: {filepath.name}")

        return str(filepath)

    except Exception as e:
        if logger_fn:
            logger_fn(f"  [warn] save failed: {e}")
        else:
            logger.warning("save_skill_output failed: %s", e)
        return ""


def _skill_to_filename(skill_id: str) -> str:
    """Skill ID 转文件名。"""
    name = skill_id.split("/")[-1] if "/" in skill_id else skill_id
    return name.replace("-", "_") + ".md"


def _extract_content(content: str, ext: str) -> str:
    """从 LLM 响应中提取有意义的内容。"""
    if ext in ('.md', '.yaml', '.yml'):
        match = re.search(r'```(?:markdown|md|yaml|yml)?\s*\n(.*?)```', content, re.DOTALL)
        if match:
            return match.group(1).strip()
    elif ext == '.py':
        match = re.search(r'```(?:python|py)?\s*\n(.*?)```', content, re.DOTALL)
        if match:
            return match.group(1).strip()
    elif ext == '.json':
        match = re.search(r'```(?:json)?\s*\n(.*?)```', content, re.DOTALL)
        if match:
            return match.group(1).strip()
    return content


def extract_code_block(text: str, language: str = "python") -> str:
    """提取代码块。"""
    pattern = rf'```{language}\s*\n(.*?)```'
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_yaml_block(text: str) -> str:
    """提取 YAML 块。"""
    return extract_code_block(text, "yaml") or extract_code_block(text, "yml")
