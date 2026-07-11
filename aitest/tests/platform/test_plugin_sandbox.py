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
