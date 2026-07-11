"""Plugin manifest security policy tests."""

from pathlib import Path

import pytest

from aitest.platform.plugin import PluginManager


def _plugin(tmp_path: Path, manifest: str) -> Path:
    plugin = tmp_path / "secure-plugin"
    plugin.mkdir()
    (plugin / "aitest_plugin.yaml").write_text(manifest, encoding="utf-8")
    return plugin


def test_plugin_permissions_are_enforced(monkeypatch, tmp_path):
    plugin = _plugin(tmp_path, "name: secure-plugin\npermissions: [network:http]\n")
    monkeypatch.delenv("AITEST_PLUGIN_ALLOWED_PERMISSIONS", raising=False)
    manager = PluginManager(search_paths=[plugin.parent])

    assert manager.discover() == []


def test_plugin_permissions_can_be_allowlisted(monkeypatch, tmp_path):
    plugin = _plugin(tmp_path, "name: secure-plugin\npermissions: [network:http]\n")
    monkeypatch.setenv("AITEST_PLUGIN_ALLOWED_PERMISSIONS", "network:http")
    manager = PluginManager(search_paths=[plugin.parent])

    assert [item.name for item in manager.discover()] == ["secure-plugin"]


def test_plugin_skill_path_cannot_escape_plugin_directory(monkeypatch, tmp_path):
    plugin = _plugin(tmp_path, "name: secure-plugin\nskills:\n  - name: unsafe\n    file: ../outside.md\n")
    monkeypatch.setenv("AITEST_PLUGIN_ALLOWED_PERMISSIONS", "")
    manager = PluginManager(search_paths=[plugin.parent])

    assert manager.discover() == []
