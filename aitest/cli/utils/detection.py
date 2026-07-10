"""
项目结构检测工具。

自动检测:
- 前端框架（Vue/React/Angular）
- UI 库（Element Plus/Ant Design/Material UI）
- 测试框架（pytest/playwright/cypress）
- 模块结构
"""

import json
from pathlib import Path
from typing import Optional


def detect_tech_stack(project_path: Path) -> dict:
    """
    自动检测项目技术栈。

    Args:
        project_path: 项目根目录

    Returns:
        {
            "framework": str,       # vue3/react/angular/custom
            "ui_library": str,      # Element Plus/Ant Design/...
            "detected": bool,       # 是否成功检测
            "confidence": str,      # high/medium/low
        }
    """
    tech_stack = {
        "framework": None,
        "ui_library": None,
        "detected": False,
        "confidence": "low",
    }

    # 检测 package.json
    package_json = project_path / "package.json"
    if package_json.exists():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

            # 框架检测
            if "vue" in deps:
                version = deps["vue"]
                if version.startswith("^3") or version.startswith("~3"):
                    tech_stack["framework"] = "vue3"
                else:
                    tech_stack["framework"] = "vue2"
                tech_stack["confidence"] = "high"
            elif "react" in deps:
                tech_stack["framework"] = "react"
                tech_stack["confidence"] = "high"
            elif "@angular/core" in deps:
                tech_stack["framework"] = "angular"
                tech_stack["confidence"] = "high"
            elif "next" in deps:
                tech_stack["framework"] = "nextjs"
                tech_stack["confidence"] = "high"
            elif "nuxt" in deps:
                tech_stack["framework"] = "nuxt"
                tech_stack["confidence"] = "high"

            # UI 库检测
            if "element-plus" in deps:
                tech_stack["ui_library"] = "Element Plus"
            elif "ant-design-vue" in deps:
                tech_stack["ui_library"] = "Ant Design Vue"
            elif "antd" in deps:
                tech_stack["ui_library"] = "Ant Design"
            elif "@mui/material" in deps:
                tech_stack["ui_library"] = "Material UI"
            elif "@angular/material" in deps:
                tech_stack["ui_library"] = "Angular Material"
            elif "vuetify" in deps:
                tech_stack["ui_library"] = "Vuetify"
            elif "naive-ui" in deps:
                tech_stack["ui_library"] = "Naive UI"

            tech_stack["detected"] = tech_stack["framework"] is not None

        except (json.JSONDecodeError, OSError):
            pass

    return tech_stack


def detect_modules(project_path: Path) -> list[str]:
    """
    检测项目模块。

    检测策略:
    1. src/views/ 或 src/pages/ 下的一级目录
    2. src/modules/ 下的目录
    3. 已有 .tlo/knowledge/modules/ 下的目录

    Args:
        project_path: 项目根目录

    Returns:
        模块名称列表
    """
    modules = set()

    # 策略 1: 检测 src/views/ 或 src/pages/
    for views_dir_name in ("src/views", "src/pages", "pages", "views"):
        views_dir = project_path / views_dir_name
        if views_dir.exists() and views_dir.is_dir():
            for item in views_dir.iterdir():
                if item.is_dir() and not item.name.startswith((".", "_")):
                    modules.add(item.name)

    # 策略 2: 检测 src/modules/
    modules_dir = project_path / "src" / "modules"
    if modules_dir.exists() and modules_dir.is_dir():
        for item in modules_dir.iterdir():
            if item.is_dir() and not item.name.startswith((".", "_")):
                modules.add(item.name)

    # 策略 3: 检测已有 .tlo/knowledge/modules/
    tlo_modules = project_path / ".tlo" / "knowledge" / "modules"
    if tlo_modules.exists() and tlo_modules.is_dir():
        for item in tlo_modules.iterdir():
            if item.is_dir():
                modules.add(item.name)

    return sorted(list(modules))


def detect_test_framework(project_path: Path) -> Optional[str]:
    """
    检测测试框架。

    Args:
        project_path: 项目根目录

    Returns:
        pytest-selenium/playwright/cypress/None
    """
    # 检测 package.json
    package_json = project_path / "package.json"
    if package_json.exists():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

            if "playwright" in deps or "@playwright/test" in deps:
                return "playwright"
            elif "cypress" in deps:
                return "cypress"
            elif "puppeteer" in deps:
                return "puppeteer"
        except (json.JSONDecodeError, OSError):
            pass

    # 检测 Python requirements.txt 或 pyproject.toml
    requirements = project_path / "requirements.txt"
    if requirements.exists():
        try:
            content = requirements.read_text(encoding="utf-8").lower()
            if "playwright" in content:
                return "playwright"
            elif "selenium" in content or "pytest-selenium" in content:
                return "pytest-selenium"
        except OSError:
            pass

    pyproject = project_path / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text(encoding="utf-8").lower()
            if "playwright" in content:
                return "playwright"
            elif "selenium" in content or "pytest-selenium" in content:
                return "pytest-selenium"
        except OSError:
            pass

    # 默认返回 pytest-selenium
    return "pytest-selenium"


def detect_base_url(project_path: Path) -> Optional[str]:
    """
    检测项目 base URL。

    检测策略:
    1. package.json 中的 scripts.dev 或 scripts.start
    2. .env 文件中的 VITE_BASE_URL / REACT_APP_URL
    3. vite.config.js / vue.config.js 中的 server.port

    Args:
        project_path: 项目根目录

    Returns:
        base_url 或 None
    """
    # 策略 1: 从 package.json 推断
    package_json = project_path / "package.json"
    if package_json.exists():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
            scripts = data.get("scripts", {})

            # 查找 dev/start 脚本中的端口
            for script_name in ("dev", "start", "serve"):
                script = scripts.get(script_name, "")
                if "--port" in script:
                    # 例如: vite --port 3000
                    parts = script.split("--port")
                    if len(parts) > 1:
                        port = parts[1].strip().split()[0]
                        if port.isdigit():
                            return f"http://localhost:{port}"
        except (json.JSONDecodeError, OSError):
            pass

    # 策略 2: 从 .env 文件读取
    for env_file_name in (".env", ".env.local", ".env.development"):
        env_file = project_path / env_file_name
        if env_file.exists():
            try:
                content = env_file.read_text(encoding="utf-8")
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key in ("VITE_BASE_URL", "REACT_APP_URL", "VUE_APP_BASE_URL", "BASE_URL"):
                            if value.startswith("http"):
                                return value
            except OSError:
                pass

    # 默认返回 localhost:3000（前端项目常用端口）
    return "http://localhost:3000"


def get_project_name_from_path(project_path: Path) -> str:
    """
    从路径推断项目名称。

    Args:
        project_path: 项目根目录

    Returns:
        项目名称
    """
    # 1. 从 package.json 读取 name 字段
    package_json = project_path / "package.json"
    if package_json.exists():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
            name = data.get("name", "")
            if name:
                return name
        except (json.JSONDecodeError, OSError):
            pass

    # 2. 使用目录名
    return project_path.name
