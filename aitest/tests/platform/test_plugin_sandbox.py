"""Process-isolated Plugin Sandbox contract tests."""

from pathlib import Path

from aitest.platform.plugin_sandbox import PluginSandbox


def test_plugin_sandbox_runs_entrypoint_outside_parent_process(tmp_path):
    plugin = tmp_path / "plugin"
    plugin.mkdir()
    (plugin / "sandbox_impl.py").write_text(
        "def handle(payload):\n    return {'pid': __import__('os').getpid(), 'value': payload['value'] * 2}\n",
        encoding="utf-8",
    )
    sandbox = PluginSandbox(plugin, "sandbox_impl:handle")
    try:
        assert sandbox.start()["status"] == "ready"
        response = sandbox.invoke({"value": 21})
        assert response["result"]["value"] == 42
        assert response["result"]["pid"] != __import__("os").getpid()
    finally:
        sandbox.stop()


def test_plugin_sandbox_provider_rpc(tmp_path):
    plugin = tmp_path / "plugin"
    plugin.mkdir()
    (plugin / "sandbox_impl.py").write_text(
        "class Echo:\n    def call(self, payload):\n        return {'echo': payload['value']}\nPROVIDERS = {'echo': Echo}\n"
        "def handle(payload):\n    return payload\n",
        encoding="utf-8",
    )
    sandbox = PluginSandbox(plugin, "sandbox_impl:handle")
    try:
        result = sandbox.call_provider("echo", "call", {"value": "ok"})
        assert result["result"] == {"echo": "ok"}
    finally:
        sandbox.stop()


def test_strict_os_isolation_fails_closed_without_wrapper(tmp_path):
    plugin = tmp_path / "plugin"
    plugin.mkdir()
    (plugin / "sandbox_impl.py").write_text("def handle(payload): return payload\n", encoding="utf-8")
    from aitest.platform.plugin_sandbox import PluginSandboxError, SandboxPolicy
    sandbox = PluginSandbox(plugin, "sandbox_impl:handle", SandboxPolicy(strict_os_isolation=True))
    import pytest
    with pytest.raises(PluginSandboxError, match="isolation_command"):
        sandbox.start()
