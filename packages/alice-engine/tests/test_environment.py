"""Standalone SDK environment discovery tests."""

from alice_engine.env import load_environment


def test_load_environment_discovers_dotenv_from_current_project(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("MIMO_API_KEY=dotenv-key\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MIMO_API_KEY", raising=False)

    load_environment()

    assert __import__("os").environ["MIMO_API_KEY"] == "dotenv-key"


def test_load_environment_does_not_override_explicit_environment(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("MIMO_API_KEY=dotenv-key\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MIMO_API_KEY", "process-key")

    load_environment()

    assert __import__("os").environ["MIMO_API_KEY"] == "process-key"
