"""Integration: Plugin System v3.2.

Verifies plugin discovery, manifest parsing, registration, and
CapabilityRouter integration.

No real plugins needed — tests use a temporary directory.
"""
import pytest
import tempfile
import yaml
from pathlib import Path


class TestPluginDiscovery:
    """Test the PluginManager discovery and loading pipeline."""

    def test_discover_finds_valid_plugin(self):
        """Scan a directory with a valid aitest_plugin.yaml."""
        from aitest.platform.plugin import PluginManager

        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "my-plugin"
            plugin_dir.mkdir()
            manifest = plugin_dir / "aitest_plugin.yaml"
            manifest.write_text(yaml.dump({
                "name": "test-plugin",
                "version": "1.0.0",
                "description": "A test plugin",
                "providers": [
                    {"name": "test_browser", "class": "not.a.real.module:FakeClass"}
                ],
            }), encoding="utf-8")

            pm = PluginManager(search_paths=[Path(tmp)])
            discovered = pm.discover()

            assert len(discovered) == 1
            assert discovered[0].name == "test-plugin"
            assert discovered[0].version == "1.0.0"
            assert len(discovered[0].providers) == 1

    def test_discover_ignores_directory_without_manifest(self):
        """Directories without aitest_plugin.yaml are silently skipped."""
        from aitest.platform.plugin import PluginManager

        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "not-a-plugin").mkdir()
            pm = PluginManager(search_paths=[Path(tmp)])
            discovered = pm.discover()
            assert len(discovered) == 0

    def test_discover_handles_invalid_yaml(self):
        """Malformed YAML is skipped with warning, not crashed."""
        from aitest.platform.plugin import PluginManager

        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "bad-plugin"
            plugin_dir.mkdir()
            (plugin_dir / "aitest_plugin.yaml").write_text("{ invalid yaml !!! [[[ ", encoding="utf-8")

            pm = PluginManager(search_paths=[Path(tmp)])
            # Should not raise
            discovered = pm.discover()
            assert len(discovered) == 0

    def test_discover_handles_missing_name(self):
        """Manifest without 'name' field is skipped."""
        from aitest.platform.plugin import PluginManager

        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "noname"
            plugin_dir.mkdir()
            (plugin_dir / "aitest_plugin.yaml").write_text("version: 1.0\n", encoding="utf-8")

            pm = PluginManager(search_paths=[Path(tmp)])
            discovered = pm.discover()
            assert len(discovered) == 0

    def test_registration_via_manager(self):
        """register_provider and get_providers contract."""
        from aitest.platform.plugin import PluginManager

        pm = PluginManager(search_paths=[])

        class FakeProvider:
            pass

        pm.register_provider("my_cap", FakeProvider)
        providers = pm.get_providers()
        assert "my_cap" in providers
        assert providers["my_cap"] is FakeProvider

    def test_singleton_plugin_manager(self):
        """get_plugin_manager returns the same instance."""
        from aitest.platform.plugin import get_plugin_manager
        pm1 = get_plugin_manager()
        pm2 = get_plugin_manager()
        assert pm1 is pm2

    def test_list_plugins_returns_status(self):
        """list_plugins() returns structured status for each plugin."""
        from aitest.platform.plugin import PluginManager

        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "status-plugin"
            plugin_dir.mkdir()
            (plugin_dir / "aitest_plugin.yaml").write_text(yaml.dump({
                "name": "status-plugin",
                "version": "0.1.0",
                "providers": [],
            }), encoding="utf-8")

            pm = PluginManager(search_paths=[Path(tmp)])
            pm.discover()
            status = pm.list_plugins()

            assert len(status) == 1
            assert status[0]["name"] == "status-plugin"
            assert "loaded" in status[0]
            assert "error" in status[0]
