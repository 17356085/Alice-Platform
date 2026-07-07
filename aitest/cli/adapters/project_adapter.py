"""Project adapter — 项目管理 CRUD。

项目发现策略:
  1. ~/.alice/config.yaml 中已注册的项目
  2. governance/context/projects/ 下的项目
  3. 工作目录下 .tlo/project.yaml 的项目
"""

import yaml
from pathlib import Path
from typing import Optional

from aitest.cli.config import CLIConfig


class ProjectAdapter:
    """项目管理 adapter。"""

    def __init__(self, config: CLIConfig):
        self.config = config

    def list_projects(self, workspace: str = None) -> list[dict]:
        """列出所有项目。

        Returns:
            [{"id": str, "name": str, "path": str, "source": str, "active": bool}]
        """
        projects = []
        active_id = self.config.active_project

        # 方式 1: 从 config 中读取已注册项目
        for project_id, info in self.config.get("projects", {}).items():
            if isinstance(info, dict):
                projects.append({
                    "id": project_id,
                    "name": info.get("name", ""),
                    "path": info.get("path", ""),
                    "source": "config",
                    "active": project_id == active_id,
                })

        # 方式 2: 扫描 governance/context/projects/
        workspace_dir = self._resolve_workspace(workspace)
        if workspace_dir:
            governance_projects = workspace_dir / "governance" / "context" / "projects"
            if governance_projects.exists():
                for d in governance_projects.iterdir():
                    if d.is_dir() and (d / "project.yaml").exists():
                        project_id = d.name
                        if not any(p["id"] == project_id for p in projects):
                            data = self._load_yaml(d / "project.yaml")
                            projects.append({
                                "id": project_id,
                                "name": data.get("project", {}).get("name", ""),
                                "path": str(d),
                                "source": "governance",
                                "active": project_id == active_id,
                            })

            # 方式 3: 扫描工作目录下的 .tlo/project.yaml
            for d in workspace_dir.iterdir():
                if d.is_dir():
                    tlo = d / ".tlo"
                    if tlo.exists() and (tlo / "project.yaml").exists():
                        data = self._load_yaml(tlo / "project.yaml")
                        project_id = data.get("project", {}).get("id", d.name)
                        if not any(p["id"] == project_id for p in projects):
                            projects.append({
                                "id": project_id,
                                "name": data.get("project", {}).get("name", ""),
                                "path": str(d),
                                "source": "tlo",
                                "active": project_id == active_id,
                            })

        return projects

    def show_project(self, project_id: str = None) -> dict:
        """显示项目详情。

        Returns:
            {"id": str, "name": str, "config": dict, "path": str, "tlo_exists": bool}
        """
        project_id = project_id or self.config.active_project
        if not project_id:
            raise ValueError("未指定项目 ID，也未设置活跃项目。请使用 'alice project set --id=<id>'")

        # 查找项目路径
        project_path = self._find_project_path(project_id)
        if not project_path:
            raise ValueError(f"项目 {project_id} 不存在")

        tlo_dir = project_path / ".tlo"
        project_yaml = tlo_dir / "project.yaml"

        # 兼容旧路径
        if not project_yaml.exists():
            project_yaml = project_path / "project.yaml"

        config = self._load_yaml(project_yaml) if project_yaml.exists() else {}

        # 统计模块
        modules_dir = tlo_dir / "knowledge" / "modules"
        modules = []
        if modules_dir.exists():
            modules = [d.name for d in modules_dir.iterdir() if d.is_dir()]

        return {
            "id": project_id,
            "name": config.get("project", {}).get("name", ""),
            "config": config,
            "path": str(project_path),
            "tlo_exists": tlo_dir.exists(),
            "modules": modules,
            "module_count": len(modules),
        }

    def set_active_project(self, project_id: str):
        """设置活跃项目。"""
        # 验证项目存在
        projects = self.list_projects()
        project = next((p for p in projects if p["id"] == project_id), None)
        if not project:
            available = [p["id"] for p in projects]
            raise ValueError(f"项目 {project_id} 不存在。可用项目: {', '.join(available) if available else '无'}")

        self.config.active_project = project_id
        # 确保项目已注册
        self.config.register_project(project_id, project["path"], project.get("name", ""))

    def register_project(self, path: str) -> dict:
        """注册新项目。

        Returns:
            {"id": str, "name": str, "path": str}
        """
        project_dir = Path(path).resolve()
        if not project_dir.exists():
            raise ValueError(f"路径不存在: {path}")

        tlo_dir = project_dir / ".tlo"
        project_yaml = tlo_dir / "project.yaml"

        if not project_yaml.exists():
            raise ValueError(
                f"项目路径 {path} 下不存在 .tlo/project.yaml\n"
                "请先运行 'alice project init' 创建项目配置"
            )

        data = self._load_yaml(project_yaml)
        project_id = data.get("project", {}).get("id", project_dir.name)
        project_name = data.get("project", {}).get("name", "")

        self.config.register_project(project_id, str(project_dir), project_name)

        return {
            "id": project_id,
            "name": project_name,
            "path": str(project_dir),
        }

    def unregister_project(self, project_id: str):
        """取消注册项目。"""
        self.config.unregister_project(project_id)

    def validate_project(self, project_id: str = None) -> dict:
        """检查项目配置是否合法。

        Returns:
            {"ok": bool, "checks": [{"name": str, "status": str, "detail": str}]}
        """
        project_id = project_id or self.config.active_project
        if not project_id:
            return {"ok": False, "checks": [{"name": "项目", "status": "[FAIL]", "detail": "未指定项目"}]}

        project_path = self._find_project_path(project_id)
        if not project_path:
            return {"ok": False, "checks": [{"name": "项目", "status": "[FAIL]", "detail": f"项目 {project_id} 不存在"}]}

        checks = []

        # 1. 项目目录
        checks.append({"name": "项目目录", "status": "ok", "detail": str(project_path)})

        # 2. .tlo 目录
        tlo_dir = project_path / ".tlo"
        if tlo_dir.exists():
            checks.append({"name": ".tlo 目录", "status": "ok", "detail": "存在"})
        else:
            checks.append({"name": ".tlo 目录", "status": "warn", "detail": "不存在"})

        # 3. project.yaml
        project_yaml = tlo_dir / "project.yaml"
        if project_yaml.exists():
            data = self._load_yaml(project_yaml)
            checks.append({"name": "project.yaml", "status": "ok", "detail": "存在"})

            # 检查必填字段
            if data.get("project", {}).get("id"):
                checks.append({"name": "项目 ID", "status": "ok", "detail": data["project"]["id"]})
            else:
                checks.append({"name": "项目 ID", "status": "error", "detail": "缺失"})

            if data.get("connection", {}).get("base_url"):
                checks.append({"name": "目标 URL", "status": "ok", "detail": data["connection"]["base_url"]})
            else:
                checks.append({"name": "目标 URL", "status": "warn", "detail": "未配置"})
        else:
            checks.append({"name": "project.yaml", "status": "error", "detail": "不存在"})

        # 4. test_accounts.yaml
        accounts_yaml = tlo_dir / "context" / "test_accounts.yaml"
        if accounts_yaml.exists():
            checks.append({"name": "test_accounts.yaml", "status": "ok", "detail": "存在"})
        else:
            checks.append({"name": "test_accounts.yaml", "status": "warn", "detail": "不存在 (可选)"})

        # 5. 模块目录
        modules_dir = tlo_dir / "knowledge" / "modules"
        if modules_dir.exists():
            modules = [d.name for d in modules_dir.iterdir() if d.is_dir()]
            checks.append({"name": "模块目录", "status": "ok", "detail": f"{len(modules)} 个模块"})
        else:
            checks.append({"name": "模块目录", "status": "warn", "detail": "不存在"})

        ok = all(c["status"] != "error" for c in checks)
        return {"ok": ok, "checks": checks}

    def _find_project_path(self, project_id: str) -> Optional[Path]:
        """查找项目路径。"""
        # 1. 从 config 获取
        path = self.config.get(f"projects.{project_id}.path")
        if path:
            p = Path(path)
            if p.exists():
                return p

        # 2. 扫描 governance/context/projects/
        workspace = self._resolve_workspace()
        if workspace:
            governance_path = workspace / "governance" / "context" / "projects" / project_id
            if governance_path.exists() and (governance_path / "project.yaml").exists():
                return governance_path

        return None

    def _resolve_workspace(self, workspace: str = None) -> Optional[Path]:
        """解析工作目录。"""
        if workspace:
            return Path(workspace)

        # 从活跃项目路径推断
        active_path = self.config.active_project_path
        if active_path:
            return Path(active_path).parent

        # 尝试从当前目录推断
        cwd = Path.cwd()
        if (cwd / "governance").exists():
            return cwd
        if (cwd / ".." / "governance").exists():
            return cwd.parent

        return None

    @staticmethod
    def _load_yaml(path: Path) -> dict:
        """安全加载 YAML 文件。"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except (yaml.YAMLError, OSError):
            return {}
