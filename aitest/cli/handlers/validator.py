"""
合法性检查 — 验证生成的文件是否符合要求。
"""

from pathlib import Path
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """合法性检查结果。"""
    ok: bool
    errors: list[str] = None


def validate_file(file_path: Path, phase: str) -> ValidationResult:
    """验证文件是否合法。"""
    if not file_path.exists():
        return ValidationResult(ok=False, errors=["文件不存在"])

    content = file_path.read_text(encoding="utf-8")

    # 基本检查: 文件非空
    if not content.strip():
        return ValidationResult(ok=False, errors=["文件为空"])

    # 根据文件类型检查
    if file_path.suffix == ".md":
        return _validate_markdown(content, phase)
    elif file_path.suffix == ".py":
        return _validate_python(content)
    elif file_path.suffix in (".yaml", ".yml"):
        return _validate_yaml(content)

    return ValidationResult(ok=True)


def _validate_markdown(content: str, phase: str) -> ValidationResult:
    """验证 Markdown 文件。"""
    errors = []

    # 检查标题
    if "#" not in content:
        errors.append("缺少 # 标题")

    # 根据 Phase 检查特定内容
    if phase == "Test Design":
        if "BS-" not in content and "TC-" not in content:
            errors.append("缺少 BS-XXX 或 TC-XXX 编号")
    elif phase == "Requirement":
        if "页面" not in content and "page" not in content.lower():
            errors.append("缺少页面列表")

    if errors:
        return ValidationResult(ok=False, errors=errors)

    return ValidationResult(ok=True)


def _validate_python(content: str) -> ValidationResult:
    """验证 Python 文件。"""
    import ast

    try:
        ast.parse(content)
    except SyntaxError as e:
        return ValidationResult(ok=False, errors=[f"语法错误: {e}"])

    return ValidationResult(ok=True)


def _validate_yaml(content: str) -> ValidationResult:
    """验证 YAML 文件。"""
    import yaml

    try:
        yaml.safe_load(content)
    except yaml.YAMLError as e:
        return ValidationResult(ok=False, errors=[f"YAML 格式错误: {e}"])

    return ValidationResult(ok=True)
