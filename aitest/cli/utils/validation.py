"""
配置验证工具。

验证:
- URL 格式
- 测试账号格式
- 项目路径
- 配置完整性
"""

from pathlib import Path
from typing import Optional
import re


def validate_url(url: str) -> dict:
    """
    验证 URL 格式。

    Args:
        url: URL 字符串

    Returns:
        {"ok": bool, "error": str}
    """
    if not url:
        return {"ok": False, "error": "URL 不能为空"}

    if not url.startswith(("http://", "https://")):
        return {"ok": False, "error": "URL 必须以 http:// 或 https:// 开头"}

    # 简单的 URL 格式检查
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    if not url_pattern.match(url):
        return {"ok": False, "error": "URL 格式不正确"}

    return {"ok": True, "error": None}


def validate_accounts(accounts: list) -> dict:
    """
    验证测试账号格式。

    Args:
        accounts: [{"role": str, "username": str, "password": str}]

    Returns:
        {"ok": bool, "errors": list}
    """
    errors = []

    for i, account in enumerate(accounts):
        if not isinstance(account, dict):
            errors.append(f"账号 {i+1}: 格式错误，应为字典")
            continue

        # 检查必需字段
        required_fields = ("role", "username", "password")
        missing = [f for f in required_fields if f not in account or not account[f]]
        if missing:
            errors.append(f"账号 {i+1}: 缺少字段 {', '.join(missing)}")

        # 检查字段类型
        for field in required_fields:
            if field in account and not isinstance(account[field], str):
                errors.append(f"账号 {i+1}: {field} 必须是字符串")

    return {"ok": len(errors) == 0, "errors": errors}


def validate_project_path(project_path: Path, config) -> dict:
    """
    验证项目路径。

    Args:
        project_path: 项目路径
        config: CLIConfig 实例

    Returns:
        {
            "ok": bool,
            "errors": list,
            "warnings": list,
            "existing_config": bool,
            "duplicate_registration": str or None,
        }
    """
    result = {
        "ok": True,
        "errors": [],
        "warnings": [],
        "existing_config": False,
        "duplicate_registration": None,
    }

    # 1. 路径存在性
    if not project_path.exists():
        result["errors"].append(f"路径不存在: {project_path}")
        result["ok"] = False
        return result

    if not project_path.is_dir():
        result["errors"].append(f"路径不是目录: {project_path}")
        result["ok"] = False
        return result

    # 2. 重复注册检测
    registered_projects = config.get("projects", {})
    for project_id, info in registered_projects.items():
        if isinstance(info, dict):
            registered_path = Path(info.get("path", "")).resolve()
            if registered_path == project_path.resolve():
                result["duplicate_registration"] = project_id
                result["warnings"].append(f"路径已注册为项目: {project_id}")

    # 3. 已有配置检测
    project_yaml = project_path / ".tlo" / "project.yaml"
    if project_yaml.exists():
        result["existing_config"] = True
        result["warnings"].append(".tlo/project.yaml 已存在，初始化将覆盖现有配置")

    return result


def validate_config(config: dict, strict: bool = False) -> dict:
    """
    验证完整配置。

    Args:
        config: 配置字典
        strict: 严格模式（将警告视为错误）

    Returns:
        {"ok": bool, "errors": list, "warnings": list}
    """
    errors = []
    warnings = []

    # 1. 项目名称
    project_name = config.get("project_name", "")
    if not project_name:
        errors.append("项目名称不能为空")
    elif len(project_name) < 2:
        errors.append("项目名称至少 2 个字符")
    elif len(project_name) > 50:
        errors.append("项目名称最多 50 个字符")

    # 2. URL 验证
    base_url = config.get("base_url", "")
    if base_url:
        url_result = validate_url(base_url)
        if not url_result["ok"]:
            errors.append(f"目标 URL: {url_result['error']}")
    else:
        warnings.append("未配置目标 URL")

    # 3. 测试账号验证
    test_accounts = config.get("test_accounts", [])
    if config.get("login_required") and not test_accounts:
        warnings.append("需要登录但未配置测试账号")
    if test_accounts:
        accounts_result = validate_accounts(test_accounts)
        if not accounts_result["ok"]:
            errors.extend(accounts_result["errors"])

    # 4. 模块列表
    modules = config.get("modules", [])
    if not modules:
        warnings.append("未配置模块，后续可能需要手动添加")

    # 5. 技术栈
    tech_stack = config.get("tech_stack", {})
    if not tech_stack.get("framework"):
        warnings.append("未配置前端框架")

    # 严格模式：将警告视为错误
    if strict and warnings:
        errors.extend(warnings)
        warnings = []

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def validate_module_name(module_name: str) -> dict:
    """
    验证模块名称。

    Args:
        module_name: 模块名称

    Returns:
        {"ok": bool, "error": str}
    """
    if not module_name:
        return {"ok": False, "error": "模块名称不能为空"}

    # 模块名称规则：只允许字母、数字、下划线、中划线
    pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
    if not pattern.match(module_name):
        return {"ok": False, "error": "模块名称只能包含字母、数字、下划线、中划线"}

    if len(module_name) > 50:
        return {"ok": False, "error": "模块名称最多 50 个字符"}

    return {"ok": True, "error": None}
