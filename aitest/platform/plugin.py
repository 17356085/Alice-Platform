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

# ── Default plugin search paths ────────────────────────────────────────

_WORKSTUDY = Path(__file__).resolve().parent.parent.parent


def _default_plugin_paths() -> list[Path]:
    """Default plugin discovery paths."""
    paths = []

    # Built-in plugins
    builtin = _WORKSTUDY / "plugins"
    if builtin.exists():
        paths.append(builtin)

    # Env var override
    env_path = os.environ.get("AITEST_PLUGIN_PATH", "")
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
    """Metadata about a discovered plugin."""
    name: str
    version: str = "0.0.0"
    description: str = ""
    path: Path = None
    providers: list[dict] = field(default_factory=list)
    entry_point: str = ""
    loaded: bool = False
    error: str = ""


# ── Plugin Manager ─────────────────────────────────────────────────────

class PluginManager:
    """Discovers, validates, and loads plugins."""

    def __init__(self, search_paths: list[Path] = None):
        self._search_paths = search_paths or _default_plugin_paths()
        self._plugins: dict[str, PluginInfo] = {}
        self._providers: dict[str, type] = {}
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
                        path=plugin_dir,
                        providers=data.get("providers", []),
                        entry_point=data.get("entry_point", ""),
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
        """Load a single plugin: import module + register providers."""
        if info.loaded:
            return len(info.providers)

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

        info.loaded = True
        return count

    # ── Registration (called by plugins) ─────────────────────────────

    def register_provider(self, name: str, provider_class: type):
        """Register a capability provider. Called by plugin entry points."""
        with self._lock:
            self._providers[name] = provider_class

    # ── Query ────────────────────────────────────────────────────────

    def get_providers(self) -> dict[str, type]:
        """Get all registered providers (built-in + plugins)."""
        return dict(self._providers)

    def get_provider(self, name: str) -> Optional[type]:
        """Get a specific provider by name."""
        return self._providers.get(name)

    def list_plugins(self) -> list[dict]:
        """List all discovered plugins with status."""
        return [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "providers": [pr["name"] for pr in p.providers],
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
