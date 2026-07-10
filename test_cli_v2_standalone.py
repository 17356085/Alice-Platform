"""
独立测试脚本 - 验证 CLI v2 命令结构。

不依赖 aitest 包，只测试 CLI 定义。
"""

import sys
import os

# 添加项目根目录到 sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

def test_cli_structure():
    """测试 CLI 命令结构"""
    print("=" * 60)
    print("测试 CLI v2 命令结构")
    print("=" * 60)

    try:
        from typer.testing import CliRunner
        from aitest.cli.main import app

        runner = CliRunner()

        # 测试 1: 顶级命令
        print("\n[1] 测试顶级命令: aitest --help")
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0, f"Exit code: {result.exit_code}"
        assert "run" in result.stdout, "缺少 'run' 命令组"
        assert "agent" in result.stdout, "缺少 'agent' 命令组"
        assert "workflow" in result.stdout, "缺少 'workflow' 命令组"
        print("   ✓ 顶级命令包含 run/agent/workflow")

        # 测试 2: run 命令组
        print("\n[2] 测试 run 命令组: aitest run --help")
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0, f"Exit code: {result.exit_code}"
        assert "create" in result.stdout, "缺少 'create' 子命令"
        assert "list" in result.stdout, "缺少 'list' 子命令"
        assert "show" in result.stdout, "缺少 'show' 子命令"
        print("   ✓ run 命令组包含 create/list/show")

        # 测试 3: run create 命令
        print("\n[3] 测试 run create: aitest run create --help")
        result = runner.invoke(app, ["run", "create", "--help"])
        assert result.exit_code == 0, f"Exit code: {result.exit_code}"
        assert "--target" in result.stdout, "缺少 --target 参数"
        assert "--module" in result.stdout, "缺少 --module 参数"
        assert "--output" in result.stdout, "缺少 --output 参数"
        print("   ✓ run create 包含 --target/--module/--output")

        # 测试 4: agent 命令组
        print("\n[4] 测试 agent 命令组: aitest agent --help")
        result = runner.invoke(app, ["agent", "--help"])
        assert result.exit_code == 0, f"Exit code: {result.exit_code}"
        assert "list" in result.stdout, "缺少 'list' 子命令"
        assert "show" in result.stdout, "缺少 'show' 子命令"
        print("   ✓ agent 命令组包含 list/show")

        # 测试 5: agent show 命令
        print("\n[5] 测试 agent show: aitest agent show --help")
        result = runner.invoke(app, ["agent", "show", "--help"])
        assert result.exit_code == 0, f"Exit code: {result.exit_code}"
        assert "--version" in result.stdout, "缺少 --version 参数"
        assert "--output" in result.stdout, "缺少 --output 参数"
        print("   ✓ agent show 包含 --version/--output")

        # 测试 6: 向后兼容 - graph 命令
        print("\n[6] 测试向后兼容: aitest graph --help")
        result = runner.invoke(app, ["graph", "--help"])
        assert result.exit_code == 0, f"Exit code: {result.exit_code}"
        assert "run" in result.stdout, "缺少 'run' 子命令"
        assert "已废弃" in result.stdout or "deprecated" in result.stdout.lower(), "缺少废弃标记"
        print("   ✓ graph 命令组保留并标记为已废弃")

        # 测试 7: project 命令组（保留）
        print("\n[7] 测试 project 命令组: aitest project --help")
        result = runner.invoke(app, ["project", "--help"])
        assert result.exit_code == 0, f"Exit code: {result.exit_code}"
        assert "init" in result.stdout, "缺少 'init' 子命令"
        assert "list" in result.stdout, "缺少 'list' 子命令"
        assert "set" in result.stdout, "缺少 'set' 子命令"
        print("   ✓ project 命令组保留 init/list/set")

        # 测试 8: server 命令组（保留）
        print("\n[8] 测试 server 命令组: aitest server --help")
        result = runner.invoke(app, ["server", "--help"])
        assert result.exit_code == 0, f"Exit code: {result.exit_code}"
        assert "start" in result.stdout, "缺少 'start' 子命令"
        assert "stop" in result.stdout, "缺少 'stop' 子命令"
        assert "status" in result.stdout, "缺少 'status' 子命令"
        print("   ✓ server 命令组保留 start/stop/status")

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！CLI v2 命令结构正确")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_resolver():
    """测试配置解析器"""
    print("\n" + "=" * 60)
    print("测试配置解析器")
    print("=" * 60)

    try:
        from aitest.cli.utils.config import ConfigResolver
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_file.write_text("defaults:\n  llm_provider: claude\n")

            resolver = ConfigResolver(config_file)

            # 测试 1: CLI 参数优先
            result = resolver.resolve(
                cli_value="openai",
                env_var="TEST_PROVIDER",
                config_key="defaults.llm_provider",
                default="deepseek"
            )
            assert result == "openai", f"CLI 参数优先级错误: {result}"
            print("   ✓ CLI 参数优先级最高")

            # 测试 2: 配置文件
            result = resolver.resolve(
                cli_value=None,
                env_var="TEST_PROVIDER",
                config_key="defaults.llm_provider",
                default="deepseek"
            )
            assert result == "claude", f"配置文件优先级错误: {result}"
            print("   ✓ 配置文件次于 CLI 参数")

            # 测试 3: 默认值
            result = resolver.resolve(
                cli_value=None,
                env_var="TEST_PROVIDER",
                config_key="nonexistent.key",
                default="deepseek"
            )
            assert result == "deepseek", f"默认值错误: {result}"
            print("   ✓ 默认值优先级最低")

            # 测试 4: 设置和获取
            resolver.set("test.key", "value")
            result = resolver.get("test.key")
            assert result == "value", f"设置/获取错误: {result}"
            print("   ✓ 设置和获取配置正常")

        print("\n✅ 配置解析器测试通过")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_output_formatter():
    """测试输出格式化工具"""
    print("\n" + "=" * 60)
    print("测试输出格式化工具")
    print("=" * 60)

    try:
        from aitest.cli.utils.output import format_output, print_success, print_error
        import io
        import sys

        # 测试 1: JSON 输出
        captured = io.StringIO()
        sys.stdout = captured
        format_output({"key": "value"}, output_format="json")
        sys.stdout = sys.__stdout__
        output = captured.getvalue()
        assert '"key"' in output and '"value"' in output, "JSON 输出格式错误"
        print("   ✓ JSON 输出格式正常")

        # 测试 2: YAML 输出
        captured = io.StringIO()
        sys.stdout = captured
        format_output({"key": "value"}, output_format="yaml")
        sys.stdout = sys.__stdout__
        output = captured.getvalue()
        assert "key:" in output and "value" in output, "YAML 输出格式错误"
        print("   ✓ YAML 输出格式正常")

        # 测试 3: 成功消息
        captured = io.StringIO()
        sys.stdout = captured
        print_success("测试成功")
        sys.stdout = sys.__stdout__
        output = captured.getvalue()
        assert "测试成功" in output, "成功消息输出错误"
        print("   ✓ 成功消息输出正常")

        print("\n✅ 输出格式化工具测试通过")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "🚀 " * 20)
    print("CLI v2 命令结构验证")
    print("🚀 " * 20 + "\n")

    all_passed = True

    all_passed &= test_cli_structure()
    all_passed &= test_config_resolver()
    all_passed &= test_output_formatter()

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！CLI v2 重构成功")
    else:
        print("❌ 部分测试失败")
    print("=" * 60 + "\n")

    sys.exit(0 if all_passed else 1)
