"""CLI 配置管理 — ~/.alice/config.yaml 持久化。

配置优先级:
    CLI 参数 > 环境变量 > ~/.alice/config.yaml > 项目 .tlo/project.yaml > 默认值
"""

import os
import yaml
from pathlib import Path
from typing import Any, Optional

CONFIG_DIR = Path.home() / ".alice"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULTS = {
    "active_project": None,
    "projects": {},
    "defaults": {
        "llm_provider": "deepseek",
        "mock_llm": False,
        "mode": "full",
        "output_format": "table",
    },
    "server": {
        "host": "0.0.0.0",
        "port": 8000,
    },
}


class CLIConfig:
    """CLI 配置管理。"""

    def __init__(self):
        self._data: dict = {}
        self._load()

    def _load(self):
        """加载配置文件。"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._data = yaml.safe_load(f) or {}
            except (yaml.YAMLError, OSError):
                self._data = {}
        # 合并默认值
        self._data = self._deep_merge(DEFAULTS, self._data)

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        """深度合并两个字典。"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = CLIConfig._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def save(self):
        """保存配置文件。"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.dump(self._data, f, allow_unicode=True, default_flow_style=False)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值。支持点号分隔的嵌套键。"""
        keys = key.split(".")
        value = self._data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def set(self, key: str, value: Any):
        """设置配置值。支持点号分隔的嵌套键。"""
        keys = key.split(".")
        data = self._data
        for k in keys[:-1]:
            if k not in data or not isinstance(data[k], dict):
                data[k] = {}
            data = data[k]
        data[keys[-1]] = value
        self.save()

    def delete(self, key: str):
        """删除配置值。"""
        keys = key.split(".")
        data = self._data
        for k in keys[:-1]:
            if not isinstance(data, dict) or k not in data:
                return
            data = data[k]
        if isinstance(data, dict) and keys[-1] in data:
            del data[keys[-1]]
            self.save()

    @property
    def active_project(self) -> Optional[str]:
        """活跃项目 ID。优先级: 环境变量 > config。"""
        return os.environ.get("AITEST_PROJECT") or self.get("active_project")

    @active_project.setter
    def active_project(self, value: str):
        self.set("active_project", value)

    @property
    def active_project_path(self) -> Optional[str]:
        """活跃项目路径。"""
        project_id = self.active_project
        if project_id:
            return self.get(f"projects.{project_id}.path")
        return None

    def register_project(self, project_id: str, path: str, name: str = ""):
        """注册项目到配置。"""
        self.set(f"projects.{project_id}", {"path": path, "name": name})

    def unregister_project(self, project_id: str):
        """从配置中移除项目。"""
        self.delete(f"projects.{project_id}")
        if self.active_project == project_id:
            self.delete("active_project")

    def resolve_llm_provider(self, cli_override: str = None) -> str:
        """解析 LLM Provider。优先级: CLI > 环境变量 > config > 默认。"""
        if os.environ.get("MOCK_LLM") == "1":
            return "mock"
        return (
            cli_override
            or os.environ.get("LLM_PROVIDER")
            or self.get("defaults.llm_provider", "deepseek")
        )

    def resolve_output_format(self, cli_override: str = None) -> str:
        """解析输出格式。优先级: CLI > 环境变量 > config > 默认。"""
        return (
            cli_override
            or os.environ.get("ALICE_OUTPUT_FORMAT")
            or self.get("defaults.output_format", "table")
        )

    def resolve_mode(self, cli_override: str = None) -> str:
        """解析执行模式。优先级: CLI > config > 默认。"""
        return cli_override or self.get("defaults.mode", "full")

    def get_all(self) -> dict:
        """返回完整配置（用于 show）。"""
        return self._data.copy()
