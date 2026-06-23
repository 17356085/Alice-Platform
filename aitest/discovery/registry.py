"""
Discovery Plugin Registry — maps strategy names to BaseDiscovery implementations.

Usage:
    from aitest.discovery.registry import DiscoveryRegistry

    # Get a discovery plugin by strategy name
    discovery = DiscoveryRegistry.create("browser-use", project_id="my-app", base_url="...")

    # Also supports source-code discovery:
    discovery = DiscoveryRegistry.create("source-vue", project_id="my-app", project_path="/path/to/project")

    # Register a custom plugin:
    DiscoveryRegistry.register("my-strategy", MyDiscoveryClass)
"""

import logging
from typing import Type, Optional, List

from aitest.discovery.base import BaseDiscovery

logger = logging.getLogger(__name__)


class DiscoveryRegistry:
    """
    Plugin registry for discovery strategies.

    Built-in strategies:
      - "browser-use": BrowserUseDiscovery (requires URL, credentials)
      - "source-vue": SourceDiscoveryPipeline (requires project path)
      - "source-react": SourceDiscoveryPipeline (future, same pipeline)
      - "openapi": SourceDiscoveryPipeline (future, API spec)
      - "manual": ManualDiscovery (from project.yaml)
    """

    _plugins: dict[str, Type[BaseDiscovery]] = {}

    @classmethod
    def register(cls, name: str, plugin_class: Type[BaseDiscovery]):
        """Register a discovery plugin class."""
        if not issubclass(plugin_class, BaseDiscovery):
            raise TypeError(f"{plugin_class.__name__} must be a BaseDiscovery subclass")
        cls._plugins[name] = plugin_class
        logger.info(f"Discovery plugin registered: {name} → {plugin_class.__name__}")

    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseDiscovery]]:
        """Get a registered plugin class. Falls back to lazy import for built-in strategies."""
        if name in cls._plugins:
            return cls._plugins[name]
        # Lazy import for built-in strategies
        return cls._lazy_import(name)

    @classmethod
    def create(cls, name: str, **kwargs) -> BaseDiscovery:
        """
        Create a discovery plugin instance.

        Args:
            name: Strategy name (e.g. "browser-use", "source-vue")
            **kwargs: Passed to the discovery class constructor.
                      browser-use: project_id, base_url, credentials, headless, provider
                      source-vue: project_id, project_path
                      source-react: project_id, project_path
        """
        plugin_cls = cls.get(name)
        if plugin_cls is None:
            available = cls.list()
            raise ValueError(
                f"Unknown discovery strategy: '{name}'. Available: {available}"
            )
        return plugin_cls(**kwargs)

    @classmethod
    def list(cls) -> List[str]:
        """List all available strategy names (built-in + registered)."""
        builtins = cls._discover_builtins()
        registered = list(cls._plugins.keys())
        return sorted(set(builtins + registered))

    @classmethod
    def _lazy_import(cls, name: str) -> Optional[Type[BaseDiscovery]]:
        """Lazy-import built-in discovery strategies."""
        if name == "browser-use":
            from aitest.discovery.browser_use import BrowserUseDiscovery
            cls._plugins[name] = BrowserUseDiscovery
            return BrowserUseDiscovery
        elif name in ("source-vue", "source-react", "source-code"):
            from aitest.discovery.source.pipeline import SourceDiscoveryPipeline
            cls._plugins[name] = SourceDiscoveryPipeline
            return SourceDiscoveryPipeline
        elif name == "openapi":
            from aitest.discovery.source.pipeline import SourceDiscoveryPipeline
            cls._plugins[name] = SourceDiscoveryPipeline
            return SourceDiscoveryPipeline
        elif name == "manual":
            # Manual discovery reads from project.yaml navigation config
            from aitest.discovery.browser_use import BrowserUseDiscovery
            cls._plugins[name] = BrowserUseDiscovery  # placeholder
            return BrowserUseDiscovery
        return None

    @classmethod
    def _discover_builtins(cls) -> List[str]:
        """List built-in strategies (always available)."""
        return ["browser-use", "source-vue", "source-react", "source-code", "openapi", "manual"]


# ── Auto-register built-in strategies on import ──────────────────────────
# Trigger lazy imports so DiscoveryRegistry.list() works immediately
DiscoveryRegistry._discover_builtins()
