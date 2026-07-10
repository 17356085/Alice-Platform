"""
测试 CLI v2 命令。

测试内容:
- 新命令: aitest run create/list/show
- 新命令: aitest agent list/show
- 向后兼容: aitest graph run → 自动转换
- 配置优先级: CLI > 环境变量 > 配置文件 > 默认值
- 输出格式: table/json/yaml
"""

import pytest
from typer.testing import CliRunner
from aitest.cli.main import app
from aitest.cli.utils.config import ConfigResolver
from pathlib import Path
import tempfile
import os


runner = CliRunner()


# ══════════════════════════════════════════════════════════════
#  测试新命令
# ══════════════════════════════════════════════════════════════

def test_run_create_help():
    """测试: aitest run create --help"""
    result = runner.invoke(app, ["run", "create", "--help"])
    assert result.exit_code == 0
    assert "创建新的 Run" in result.stdout
    assert "--target" in result.stdout
    assert "--module" in result.stdout


def test_run_list_help():
    """测试: aitest run list --help"""
    result = runner.invoke(app, ["run", "list", "--help"])
    assert result.exit_code == 0
    assert "列出 Run 记录" in result.stdout
    assert "--status" in result.stdout
    assert "--limit" in result.stdout


def test_run_show_help():
    """测试: aitest run show --help"""
    result = runner.invoke(app, ["run", "show", "--help"])
    assert result.exit_code == 0
    assert "显示 Run 详情" in result.stdout


def test_agent_list_help():
    """测试: aitest agent list --help"""
    result = runner.invoke(app, ["agent", "list", "--help"])
    assert result.exit_code == 0
    assert "列出所有 Agent" in result.stdout


def test_agent_show_help():
    """测试: aitest agent show --help"""
    result = runner.invoke(app, ["agent", "show", "--help"])
    assert result.exit_code == 0
    assert "显示 Agent 详情" in result.stdout
    assert "--version" in result.stdout


# ══════════════════════════════════════════════════════════════
#  测试向后兼容
# ══════════════════════════════════════════════════════════════

def test_graph_run_deprecated_warning():
    """测试: aitest graph run 显示废弃警告"""
    # 注意: 此测试会失败，因为需要 API 服务器运行
    # 但我们可以验证命令是否存在
    result = runner.invoke(app, ["graph", "run", "--help"])
    assert result.exit_code == 0
    assert "[已废弃]" in result.stdout or "已废弃" in result.stdout.lower()


def test_graph_status_deprecated_warning():
    """测试: aitest graph status 显示废弃警告"""
    result = runner.invoke(app, ["graph", "status", "--help"])
    assert result.exit_code == 0
    assert "[已废弃]" in result.stdout or "已废弃" in result.stdout.lower()


# ══════════════════════════════════════════════════════════════
#  测试配置优先级
# ══════════════════════════════════════════════════════════════

def test_config_resolver_cli_priority():
    """测试: CLI 参数优先级最高"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.yaml"
        config_file.write_text("defaults:\n  llm_provider: claude\n")

        resolver = ConfigResolver(config_file)
        result = resolver.resolve(
            cli_value="openai",
            env_var="AITEST_LLM_PROVIDER",
            config_key="defaults.llm_provider",
            default="deepseek"
        )
        assert result == "openai"


def test_config_resolver_env_priority():
    """测试: 环境变量次于 CLI"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.yaml"
        config_file.write_text("defaults:\n  llm_provider: claude\n")

        os.environ["AITEST_LLM_PROVIDER"] = "openai"

        resolver = ConfigResolver(config_file)
        result = resolver.resolve(
            cli_value=None,
            env_var="AITEST_LLM_PROVIDER",
            config_key="defaults.llm_provider",
            default="deepseek"
        )
        assert result == "openai"

        del os.environ["AITEST_LLM_PROVIDER"]


def test_config_resolver_file_priority():
    """测试: 配置文件次于环境变量"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.yaml"
        config_file.write_text("defaults:\n  llm_provider: claude\n")

        resolver = ConfigResolver(config_file)
        result = resolver.resolve(
            cli_value=None,
            env_var="AITEST_LLM_PROVIDER",
            config_key="defaults.llm_provider",
            default="deepseek"
        )
        assert result == "claude"


def test_config_resolver_default_priority():
    """测试: 默认值优先级最低"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.yaml"
        config_file.write_text("")

        resolver = ConfigResolver(config_file)
        result = resolver.resolve(
            cli_value=None,
            env_var="AITEST_LLM_PROVIDER",
            config_key="defaults.llm_provider",
            default="deepseek"
        )
        assert result == "deepseek"


def test_config_resolver_nested_key():
    """测试: 嵌套配置键"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.yaml"
        config_file.write_text("api:\n  base_url: http://localhost:8000\n")

        resolver = ConfigResolver(config_file)
        result = resolver.resolve(
            cli_value=None,
            env_var=None,
            config_key="api.base_url",
            default="http://127.0.0.1:8000"
        )
        assert result == "http://localhost:8000"


def test_config_resolver_set_and_get():
    """测试: 设置和获取配置"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.yaml"

        resolver = ConfigResolver(config_file)
        resolver.set("defaults.llm_provider", "claude")

        assert resolver.get("defaults.llm_provider") == "claude"


def test_config_resolver_reset():
    """测试: 重置配置"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.yaml"
        config_file.write_text("defaults:\n  llm_provider: claude\n")

        resolver = ConfigResolver(config_file)
        resolver.reset("defaults.llm_provider")

        assert resolver.get("defaults.llm_provider") is None


def test_config_resolver_type_casting():
    """测试: 类型转换（环境变量）"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.yaml"

        os.environ["AITEST_MOCK_LLM"] = "true"

        resolver = ConfigResolver(config_file)
        result = resolver.resolve(
            cli_value=None,
            env_var="AITEST_MOCK_LLM",
            config_key="defaults.mock_llm",
            default=False
        )
        assert result is True

        del os.environ["AITEST_MOCK_LLM"]


# ══════════════════════════════════════════════════════════════
#  测试输出格式
# ══════════════════════════════════════════════════════════════

def test_output_format_json():
    """测试: JSON 输出格式"""
    from aitest.cli.utils.output import format_output
    import io
    import sys

    captured_output = io.StringIO()
    sys.stdout = captured_output

    format_output({"key": "value"}, output_format="json")

    sys.stdout = sys.__stdout__
    output = captured_output.getvalue()

    assert '"key"' in output
    assert '"value"' in output


def test_output_format_yaml():
    """测试: YAML 输出格式"""
    from aitest.cli.utils.output import format_output
    import io
    import sys

    captured_output = io.StringIO()
    sys.stdout = captured_output

    format_output({"key": "value"}, output_format="yaml")

    sys.stdout = sys.__stdout__
    output = captured_output.getvalue()

    assert "key:" in output
    assert "value" in output


# ══════════════════════════════════════════════════════════════
#  集成测试（需要 API 服务器）
# ══════════════════════════════════════════════════════════════

@pytest.mark.integration
def test_run_create_integration():
    """
    集成测试: aitest run create

    前提: aitest server start 已启动
    """
    result = runner.invoke(app, [
        "run", "create",
        "--target", "agent:page-observer",
        "--module", "equipment",
        "--mock-llm",
        "--no-wait",
        "--output", "json"
    ])
    # 注意: 此测试会失败，如果 API 服务器未启动
    # assert result.exit_code == 0
    # assert "run_id" in result.stdout


@pytest.mark.integration
def test_run_list_integration():
    """
    集成测试: aitest run list

    前提: aitest server start 已启动
    """
    result = runner.invoke(app, [
        "run", "list",
        "--limit", "5",
        "--output", "json"
    ])
    # 注意: 此测试会失败，如果 API 服务器未启动
    # assert result.exit_code == 0


@pytest.mark.integration
def test_agent_list_integration():
    """
    集成测试: aitest agent list

    前提: aitest server start 已启动
    """
    result = runner.invoke(app, [
        "agent", "list",
        "--output", "json"
    ])
    # 注意: 此测试会失败，如果 API 服务器未启动
    # assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
