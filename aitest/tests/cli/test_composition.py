from contextlib import nullcontext
from types import SimpleNamespace

from aitest.cli.commands.graph.run import run_command
from aitest.cli.commands.server.worker import worker_command
from aitest.cli.core.composition import (
    get_cli_execution_service,
    resolve_cli_project_dir,
)


def test_resolve_cli_project_dir_uses_active_project(monkeypatch, tmp_path):
    class _Config:
        active_project_path = str(tmp_path)

    monkeypatch.setattr("aitest.cli.config.CLIConfig", lambda: _Config())

    assert resolve_cli_project_dir(None) == tmp_path


def test_run_command_uses_cli_composition_root(monkeypatch, tmp_path):
    calls = {}

    class _Service:
        def execute(self, ctx, **kwargs):
            calls["ctx"] = ctx
            calls["kwargs"] = kwargs
            return SimpleNamespace(
                status="completed",
                run_id="run-1",
                duration_ms=12.5,
                completed_phases=["Requirement"],
                failed_phases=[],
                error_message="",
                success=True,
            )

    monkeypatch.setattr("aitest.cli.commands.graph.run.resolve_cli_project_dir", lambda project_path: tmp_path)
    monkeypatch.setattr("aitest.cli.commands.graph.run.get_cli_execution_service", lambda: _Service())
    monkeypatch.setattr("aitest.cli.commands.graph.run.cli_runtime_scope", lambda *args, **kwargs: nullcontext())

    run_command(project_path=str(tmp_path), module="equipment", pages=["alarm"], llm_provider="mock")

    assert calls["ctx"].metadata["project_path"] == str(tmp_path)
    assert calls["kwargs"]["provider"] == "mock"


def test_worker_command_uses_shared_execution_service(monkeypatch):
    calls = {}

    class _Worker:
        worker_id = "worker-1"

        def start(self):
            calls["started"] = True

        def stop(self):
            calls["stopped"] = True

    class _Service:
        pass

    monkeypatch.setattr("aitest.cli.commands.server.worker.get_cli_execution_service", lambda: _Service())
    monkeypatch.setattr("aitest.cli.commands.server.worker.get_execution_worker", lambda **kwargs: calls.update(kwargs) or _Worker())
    monkeypatch.setattr("aitest.cli.commands.server.worker.time.sleep", lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))

    worker_command(worker_id="worker-1", poll_interval=0.5)

    assert calls["started"] is True
    assert calls["stopped"] is True
    assert isinstance(calls["service"], _Service)
