"""Smoke coverage for external resource command groups."""

from typer.testing import CliRunner

from aitest.cli.main import app


def test_external_resource_groups_are_discoverable():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in ("mcp", "plugin", "env", "secret"):
        assert command in result.stdout


def test_mcp_commands_are_listed():
    result = CliRunner().invoke(app, ["mcp", "--help"])

    assert result.exit_code == 0
    for command in ("list", "show", "start", "stop"):
        assert command in result.stdout
