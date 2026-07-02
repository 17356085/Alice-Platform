"""Project — 项目配置和资源发现。

职责:
  - 读取 project.yaml
  - 发现模块和页面
  - 管理项目路径
  - 验证项目配置

不属于 Project:
  - 测试执行 (Engine)
  - LLM 调用 (Provider)
  - 用户交互 (CLI/Web)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from alice_engine.behavior import BehaviorPack, load_behavior_pack
from alice_engine.exceptions import ProjectNotFoundError

logger = logging.getLogger(__name__)


@dataclass
class ProjectConfig:
    """project.yaml 的原始数据。"""

    name: str = ""
    url: str = ""
    tech_stack: dict = field(default_factory=dict)
    test_framework: str = "pytest"
    accounts: list[dict] = field(default_factory=list)
    modules: list[str] = field(default_factory=list)
    api_docs: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict, repr=False)


class Project:
    """项目实例 — 管理配置和资源发现。

    用法:
        project = Project("./my-project")
        print(project.name)           # "my-project"
        print(project.modules)        # ["equipment", "tank"]
        print(project.config.url)     # "https://example.com"
    """

    def __init__(self, path: str | Path):
        """初始化 Project。

        Args:
            path: 项目根目录路径

        Raises:
            ProjectNotFoundError: 项目路径不存在或缺少 project.yaml
        """
        self._path = Path(path).resolve()

        if not self._path.exists():
            raise ProjectNotFoundError(f"项目路径不存在: {self._path}")

        self._config = self._load_config()
        logger.info("Project loaded: %s (%s)", self.name, self._path)

    @property
    def path(self) -> Path:
        """项目根目录。"""
        return self._path

    @property
    def name(self) -> str:
        """项目名称。"""
        return self._config.name or self._path.name

    @property
    def config(self) -> ProjectConfig:
        """项目配置。"""
        return self._config

    @property
    def modules(self) -> list[str]:
        """可用模块列表。"""
        modules = []

        # 从 .tlo/knowledge/modules/ 读取
        modules_dir = self._path / ".tlo" / "knowledge" / "modules"
        if modules_dir.exists():
            for item in modules_dir.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    modules.append(item.name)

        # 从 project.yaml 读取
        for m in self._config.modules:
            if m not in modules:
                modules.append(m)

        return sorted(modules)

    @property
    def governance_path(self) -> Path:
        """Governance 目录路径（向后兼容）。"""
        return self._path / "governance"

    @property
    def has_governance(self) -> bool:
        """是否有 governance 目录。"""
        return self.governance_path.exists()

    @property
    def behavior_pack(self) -> BehaviorPack:
        """行为包 — SDK 的行为定义抽象层。

        优先从项目目录下的 governance/ 加载，
        不存在则返回空 pack（不崩溃）。
        """
        return load_behavior_pack(self.governance_path)

    def module_path(self, module: str) -> Path:
        """获取模块目录路径。"""
        return self._path / ".tlo" / "knowledge" / "modules" / module

    def has_module(self, module: str) -> bool:
        """检查模块是否存在。"""
        return module in self.modules

    def validate(self) -> ValidationResult:
        """验证项目配置。

        Returns:
            ValidationResult
        """
        result = ValidationResult(project=self)

        # 检查 project.yaml
        if not self._config.name:
            result.add_warning("project.yaml 缺少 name 字段")

        if not self._config.url:
            result.add_warning("project.yaml 缺少 url 字段")

        # 检查模块
        if not self.modules:
            result.add_warning("没有发现任何模块")

        # 检查 governance
        if not self.has_governance:
            result.add_warning("behavior pack (governance/) 不存在，将使用空 fallback")

        return result

    def _load_config(self) -> ProjectConfig:
        """从 project.yaml 加载配置。"""
        candidates = [
            self._path / ".tlo" / "project.yaml",
            self._path / "project.yaml",
        ]

        for config_file in candidates:
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}

                return ProjectConfig(
                    name=data.get("name", ""),
                    url=data.get("url", ""),
                    tech_stack=data.get("tech_stack", {}),
                    test_framework=data.get("test_framework", "pytest"),
                    accounts=data.get("accounts", []),
                    modules=data.get("modules", []),
                    api_docs=data.get("api_docs", {}),
                    raw=data,
                )

        # 没有 project.yaml，返回空配置
        logger.warning("project.yaml not found in %s, using empty config", self._path)
        return ProjectConfig()

    @classmethod
    def exists(cls, path: str | Path) -> bool:
        """检查项目配置是否存在。"""
        path = Path(path)
        return any(
            (path / p).exists()
            for p in [".tlo/project.yaml", "project.yaml"]
        )

    def __repr__(self) -> str:
        return f"Project(name={self.name!r}, path={self._path!r})"


@dataclass
class ValidationResult:
    """项目验证结果。"""

    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    project: Project | None = None

    def add_error(self, msg: str):
        self.errors.append(msg)
        self.valid = False

    def add_warning(self, msg: str):
        self.warnings.append(msg)
