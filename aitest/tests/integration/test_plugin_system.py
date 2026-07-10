"""Integration: Plugin System v3.2.

Verifies plugin discovery, manifest parsing, registration, and
CapabilityRouter integration.

P6-3: 扩展支持 Skill/CLI/API 路由扩展。

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


# ============================================================================
# P6-3: Skill 扩展测试
# ============================================================================

class TestPluginSkillExtension:
    """Test Skill extension support."""

    def test_discover_plugin_with_skills(self):
        """Discover plugin with skills field."""
        from aitest.platform.plugin import PluginManager

        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "skill-plugin"
            plugin_dir.mkdir()
            skills_dir = plugin_dir / "skills"
            skills_dir.mkdir()

            # Create skill file
            skill_file = skills_dir / "custom_skill.md"
            skill_file.write_text("# Custom Skill\n\nThis is a custom skill.", encoding="utf-8")

            manifest = plugin_dir / "aitest_plugin.yaml"
            manifest.write_text(yaml.dump({
                "name": "skill-plugin",
                "version": "1.0.0",
                "skills": [
                    {"name": "custom-skill", "file": "skills/custom_skill.md"}
                ],
            }), encoding="utf-8")

            pm = PluginManager(search_paths=[Path(tmp)])
            discovered = pm.discover()

            assert len(discovered) == 1
            assert len(discovered[0].skills) == 1
            assert discovered[0].skills[0]["name"] == "custom-skill"

    def test_load_plugin_skills(self):
        """Load plugin and register skills."""
        from aitest.platform.plugin import PluginManager

        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "skill-plugin"
            plugin_dir.mkdir()
            skills_dir = plugin_dir / "skills"
            skills_dir.mkdir()

            skill_file = skills_dir / "test_skill.md"
            skill_file.write_text("# Test Skill", encoding="utf-8")

            manifest = plugin_dir / "aitest_plugin.yaml"
            manifest.write_text(yaml.dump({
                "name": "skill-plugin",
                "skills": [
                    {"name": "test-skill", "file": "skills/test_skill.md"}
                ],
            }), encoding="utf-8")

            pm = PluginManager(search_paths=[Path(tmp)])
            pm.discover()
            pm.load_all()

            skills = pm.get_skills()
            assert "test-skill" in skills
            assert skills["test-skill"].exists()
            assert skills["test-skill"].name == "test_skill.md"

    def test_register_skill_manually(self):
        """Manually register a skill via entry point."""
        from aitest.platform.plugin import PluginManager

        pm = PluginManager(search_paths=[])

        with tempfile.TemporaryDirectory() as tmp:
            skill_path = Path(tmp) / "manual_skill.md"
            skill_path.write_text("# Manual Skill", encoding="utf-8")

            pm.register_skill("manual-skill", skill_path)

            skills = pm.get_skills()
            assert "manual-skill" in skills
            assert skills["manual-skill"] == skill_path


# ============================================================================
# P6-3: CLI 命令扩展测试
# ============================================================================

class TestPluginCLIExtension:
    """Test CLI command extension support."""

    def test_discover_plugin_with_cli_commands(self):
        """Discover plugin with cli_commands field."""
        from aitest.platform.plugin import PluginManager

        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "cli-plugin"
            plugin_dir.mkdir()

            manifest = plugin_dir / "aitest_plugin.yaml"
            manifest.write_text(yaml.dump({
                "name": "cli-plugin",
                "version": "1.0.0",
                "cli_commands": [
                    {"name": "custom-cmd", "class": "not.real:FakeCommand"}
                ],
            }), encoding="utf-8")

            pm = PluginManager(search_paths=[Path(tmp)])
            discovered = pm.discover()

            assert len(discovered) == 1
            assert len(discovered[0].cli_commands) == 1
            assert discovered[0].cli_commands[0]["name"] == "custom-cmd"

    def test_register_cli_command_manually(self):
        """Manually register a CLI command."""
        from aitest.platform.plugin import PluginManager

        pm = PluginManager(search_paths=[])

        class FakeCommand:
            pass

        pm.register_cli_command("test-cmd", FakeCommand)

        commands = pm.get_cli_commands()
        assert "test-cmd" in commands
        assert commands["test-cmd"] is FakeCommand


# ============================================================================
# P6-3: API 路由扩展测试
# ============================================================================

class TestPluginAPIExtension:
    """Test API route extension support."""

    def test_discover_plugin_with_api_routes(self):
        """Discover plugin with api_routes field."""
        from aitest.platform.plugin import PluginManager

        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "api-plugin"
            plugin_dir.mkdir()

            manifest = plugin_dir / "aitest_plugin.yaml"
            manifest.write_text(yaml.dump({
                "name": "api-plugin",
                "version": "1.0.0",
                "api_routes": [
                    {"prefix": "/api/v1/custom", "class": "not.real:FakeRouter"}
                ],
            }), encoding="utf-8")

            pm = PluginManager(search_paths=[Path(tmp)])
            discovered = pm.discover()

            assert len(discovered) == 1
            assert len(discovered[0].api_routes) == 1
            assert discovered[0].api_routes[0]["prefix"] == "/api/v1/custom"

    def test_register_api_route_manually(self):
        """Manually register an API route."""
        from aitest.platform.plugin import PluginManager

        pm = PluginManager(search_paths=[])

        class FakeRouter:
            pass

        pm.register_api_route("/api/v1/test", FakeRouter)

        routes = pm.get_api_routes()
        assert len(routes) == 1
        assert routes[0][0] == "/api/v1/test"
        assert routes[0][1] is FakeRouter


# ============================================================================
# P6-3: 综合测试
# ============================================================================

class TestPluginSystemV2:
    """Test v2.0 plugin system with all extension types."""

    def test_plugin_with_all_extensions(self):
        """Plugin with providers + skills + cli + api."""
        from aitest.platform.plugin import PluginManager

        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "full-plugin"
            plugin_dir.mkdir()

            # Create skill file
            skills_dir = plugin_dir / "skills"
            skills_dir.mkdir()
            (skills_dir / "skill.md").write_text("# Skill", encoding="utf-8")

            manifest = plugin_dir / "aitest_plugin.yaml"
            manifest.write_text(yaml.dump({
                "name": "full-plugin",
                "version": "2.0.0",
                "description": "A plugin with all extension types",
                "author": "Alice Team",
                "homepage": "https://example.com",
                "providers": [
                    {"name": "prov1", "class": "fake:Prov"}
                ],
                "skills": [
                    {"name": "skill1", "file": "skills/skill.md"}
                ],
                "cli_commands": [
                    {"name": "cmd1", "class": "fake:Cmd"}
                ],
                "api_routes": [
                    {"prefix": "/api/v1/test", "class": "fake:Router"}
                ],
                "dependencies": ["requests>=2.28.0"],
            }), encoding="utf-8")

            pm = PluginManager(search_paths=[Path(tmp)])
            discovered = pm.discover()

            assert len(discovered) == 1
            info = discovered[0]
            assert info.name == "full-plugin"
            assert info.version == "2.0.0"
            assert info.author == "Alice Team"
            assert info.homepage == "https://example.com"
            assert len(info.providers) == 1
            assert len(info.skills) == 1
            assert len(info.cli_commands) == 1
            assert len(info.api_routes) == 1
            assert len(info.dependencies) == 1

    def test_list_plugins_v2(self):
        """list_plugins() returns v2.0 extended status."""
        from aitest.platform.plugin import PluginManager

        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "v2-plugin"
            plugin_dir.mkdir()
            skills_dir = plugin_dir / "skills"
            skills_dir.mkdir()
            (skills_dir / "s.md").write_text("# S", encoding="utf-8")

            manifest = plugin_dir / "aitest_plugin.yaml"
            manifest.write_text(yaml.dump({
                "name": "v2-plugin",
                "providers": [{"name": "p1", "class": "f:P"}],
                "skills": [{"name": "s1", "file": "skills/s.md"}],
                "cli_commands": [{"name": "c1", "class": "f:C"}],
                "api_routes": [{"prefix": "/api/v1/x", "class": "f:R"}],
            }), encoding="utf-8")

            pm = PluginManager(search_paths=[Path(tmp)])
            pm.discover()
            status = pm.list_plugins()

            assert len(status) == 1
            s = status[0]
            assert s["name"] == "v2-plugin"
            assert s["providers"] == ["p1"]
            assert s["skills"] == ["s1"]
            assert s["cli_commands"] == ["c1"]
            assert s["api_routes"] == ["/api/v1/x"]
