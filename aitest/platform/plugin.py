"""
Plugin System — dynamic Capability Provider loading.

Plugins are Python packages that register Capability Providers without
modifying core platform code. Each plugin has an `aitest_plugin.yaml` manifest.

Plugin manifest (aitest_plugin.yaml):
    name: my-browser-plugin
    version: 1.0.0
    description: Custom Playwright browser provider
    providers:
      - name: playwright_browser
        class: my_plugin.providers:PlaywrightBrowserProvider
        replaces: browser_use
    entry_point: my_plugin:register

Discovery:
  1. AITEST_PLUGIN_PATH env var (colon/semicolon-separated directories)
  2. <workstudy>/plugins/  (built-in plugins)
  3. <project>/.tlo/plugins/  (project-specific plugins)

Usage:
    from aitest.platform.plugin import PluginManager

    pm = PluginManager()
    pm.discover()
    pm.load_all()
    providers = pm.get_providers()  # dict[name] = provider_class
"""

import os
import sys
import importlib
import threading
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Callable

import yaml
from aitest.config import config

# ── Default plugin search paths ────────────────────────────────────────

from aitest.platform.paths import get_workstudy
_WORKSTUDY = get_workstudy()


def _default_plugin_paths() -> list[Path]:
    """Default plugin discovery paths."""
    paths = []

    # Built-in plugins
    builtin = _WORKSTUDY / "plugins"
    if builtin.exists():
        paths.append(builtin)

    # Env var override
    env_path = config.get_env("AITEST_PLUGIN_PATH", "")
    if env_path:
        sep = ";" if sys.platform == "win32" else ":"
        for p in env_path.split(sep):
            p = Path(p.strip())
            if p.exists():
                paths.append(p)

    # Project-specific plugins (from active project's .tlo/)
    try:
        from aitest.platform.paths import get_tlo_dir
        tlo = get_tlo_dir()
        if tlo:
            project_plugins = tlo / "plugins"
            if project_plugins.exists():
                paths.append(project_plugins)
    except Exception:
        pass

    return paths


# ── Plugin descriptor ──────────────────────────────────────────────────

@dataclass
class PluginInfo:
    """Metadata about a discovered plugin (v2.0 — 支持多种扩展类型)."""
    name: str
    version: str = "0.0.0"
    description: str = ""
    author: str = ""
    homepage: str = ""
    path: Path = None

    # 扩展类型
    providers: list[dict] = field(default_factory=list)
    skills: list[dict] = field(default_factory=list)         # P6-3: Skill 扩展
    cli_commands: list[dict] = field(default_factory=list)   # P6-3: CLI 命令扩展
    api_routes: list[dict] = field(default_factory=list)     # P6-3: API 路由扩展

    # 元数据
    entry_point: str = ""
    dependencies: list[str] = field(default_factory=list)

    # 状态
    loaded: bool = False
    error: str = ""


# ── Plugin Manager ─────────────────────────────────────────────────────

class PluginManager:
    """Discovers, validates, and loads plugins (v2.0 — 支持多种扩展类型)."""

    def __init__(self, search_paths: list[Path] = None):
        self._search_paths = search_paths or _default_plugin_paths()
        self._plugins: dict[str, PluginInfo] = {}
        self._providers: dict[str, type] = {}
        self._skills: dict[str, Path] = {}                # P6-3: Skill 注册表
        self._cli_commands: dict[str, type] = {}          # P6-3: CLI 命令注册表
        self._api_routes: list[tuple[str, type]] = []     # P6-3: API 路由注册表
        self._lock = threading.Lock()

    # ── Discovery ────────────────────────────────────────────────────

    def discover(self) -> list[PluginInfo]:
        """Scan all search paths for aitest_plugin.yaml manifests."""
        discovered = []
        for search_path in self._search_paths:
            for plugin_dir in sorted(search_path.iterdir()):
                if not plugin_dir.is_dir():
                    continue
                manifest = plugin_dir / "aitest_plugin.yaml"
                if not manifest.exists():
                    continue

                try:
                    with open(manifest, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)

                    if not data or "name" not in data:
                        continue

                    info = PluginInfo(
                        name=data["name"],
                        version=data.get("version", "0.0.0"),
                        description=data.get("description", ""),
                        author=data.get("author", ""),
                        homepage=data.get("homepage", ""),
                        path=plugin_dir,
                        providers=data.get("providers", []),
                        skills=data.get("skills", []),
                        cli_commands=data.get("cli_commands", []),
                        api_routes=data.get("api_routes", []),
                        entry_point=data.get("entry_point", ""),
                        dependencies=data.get("dependencies", []),
                    )
                    self._plugins[info.name] = info
                    discovered.append(info)
                except Exception as e:
                    from aitest.infra.logging import get_logger
                    get_logger("plugin").warning(
                        "manifest_parse_failed",
                        path=str(manifest),
                        error=str(e),
                    )

        return discovered

    # ── Loading ──────────────────────────────────────────────────────

    def load_all(self) -> dict[str, int]:
        """Load all discovered plugins. Returns {name: provider_count}."""
        results = {}
        for name, info in self._plugins.items():
            try:
                count = self._load_one(info)
                results[name] = count
            except Exception as e:
                info.error = str(e)
                results[name] = 0
                from aitest.infra.logging import get_logger
                get_logger("plugin").error(
                    "plugin_load_failed",
                    plugin=name,
                    error=str(e),
                )
        return results

    def _load_one(self, info: PluginInfo) -> int:
        """Load a single plugin: import module + register providers/skills/cli/api."""
        if info.loaded:
            return len(info.providers) + len(info.skills) + len(info.cli_commands) + len(info.api_routes)

        # Add plugin directory to sys.path
        plugin_root = str(info.path.parent) if info.path.parent else str(info.path)
        if info.path and info.path.parent:
            plugin_root = str(info.path.parent)
            if plugin_root not in sys.path:
                sys.path.insert(0, plugin_root)

        # Call entry point if defined
        if info.entry_point:
            module_name, func_name = info.entry_point.split(":")
            mod = importlib.import_module(module_name)
            register_fn = getattr(mod, func_name, None)
            if register_fn:
                register_fn(self)

        # Register providers
        count = 0
        for provider_def in info.providers:
            pname = provider_def.get("name", "")
            pclass_path = provider_def.get("class", "")
            if pname and pclass_path:
                mod_path, cls_name = pclass_path.split(":")
                mod = importlib.import_module(mod_path)
                cls = getattr(mod, cls_name, None)
                if cls:
                    self._providers[pname] = cls
                    count += 1

        # P6-3: Register skills
        for skill_def in info.skills:
            sname = skill_def.get("name", "")
            sfile = skill_def.get("file", "")
            if sname and sfile and info.path:
                skill_path = info.path / sfile
                if skill_path.exists():
                    self._skills[sname] = skill_path
                    count += 1

        # P6-3: Register CLI commands
        for cli_def in info.cli_commands:
            cname = cli_def.get("name", "")
            cclass_path = cli_def.get("class", "")
            if cname and cclass_path:
                mod_path, cls_name = cclass_path.split(":")
                mod = importlib.import_module(mod_path)
                cls = getattr(mod, cls_name, None)
                if cls:
                    self._cli_commands[cname] = cls
                    count += 1

        # P6-3: Register API routes
        for api_def in info.api_routes:
            prefix = api_def.get("prefix", "")
            rclass_path = api_def.get("class", "")
            if prefix and rclass_path:
                mod_path, cls_name = rclass_path.split(":")
                mod = importlib.import_module(mod_path)
                cls = getattr(mod, cls_name, None)
                if cls:
                    self._api_routes.append((prefix, cls))
                    count += 1

        info.loaded = True
        return count

    # ── Registration (called by plugins) ─────────────────────────────

    def register_provider(self, name: str, provider_class: type):
        """Register a capability provider. Called by plugin entry points."""
        with self._lock:
            self._providers[name] = provider_class

    def register_skill(self, name: str, skill_path: Path):
        """Register a skill. Called by plugin entry points."""
        with self._lock:
            self._skills[name] = skill_path

    def register_cli_command(self, name: str, command_class: type):
        """Register a CLI command. Called by plugin entry points."""
        with self._lock:
            self._cli_commands[name] = command_class

    def register_api_route(self, prefix: str, router_class: type):
        """Register an API route. Called by plugin entry points."""
        with self._lock:
            self._api_routes.append((prefix, router_class))

    # ── Query ────────────────────────────────────────────────────────

    def get_providers(self) -> dict[str, type]:
        """Get all registered providers (built-in + plugins)."""
        return dict(self._providers)

    def get_provider(self, name: str) -> Optional[type]:
        """Get a specific provider by name."""
        return self._providers.get(name)

    def get_skills(self) -> dict[str, Path]:
        """Get all registered skills (name → path)."""
        return dict(self._skills)

    def get_skill(self, name: str) -> Optional[Path]:
        """Get a specific skill by name."""
        return self._skills.get(name)

    def get_cli_commands(self) -> dict[str, type]:
        """Get all registered CLI commands (name → class)."""
        return dict(self._cli_commands)

    def get_cli_command(self, name: str) -> Optional[type]:
        """Get a specific CLI command by name."""
        return self._cli_commands.get(name)

    def get_api_routes(self) -> list[tuple[str, type]]:
        """Get all registered API routes ([(prefix, router_class), ...])."""
        return list(self._api_routes)

    def list_plugins(self) -> list[dict]:
        """List all discovered plugins with status (v2.0 — 包含所有扩展类型)."""
        return [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "author": p.author,
                "homepage": p.homepage,
                "providers": [pr["name"] for pr in p.providers],
                "skills": [sk["name"] for sk in p.skills],
                "cli_commands": [cmd["name"] for cmd in p.cli_commands],
                "api_routes": [route["prefix"] for route in p.api_routes],
                "loaded": p.loaded,
                "error": p.error or None,
            }
            for p in self._plugins.values()
        ]


# ── Singleton ──────────────────────────────────────────────────────────

_plugin_manager: Optional[PluginManager] = None
_pm_lock = threading.Lock()


def get_plugin_manager() -> PluginManager:
    """Get or create the global PluginManager singleton."""
    global _plugin_manager
    with _pm_lock:
        if _plugin_manager is None:
            _plugin_manager = PluginManager()
            _plugin_manager.discover()
        return _plugin_manager
