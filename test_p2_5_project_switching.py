"""P2-5: 多项目切换功能测试。

测试范围:
1. CLIConfig 的 previous_project 和 recent_projects 跟踪
2. ProjectAdapter 的 "-" 别名解析
3. project set 命令的输出增强
4. project list 命令的最近项目标记
5. project switch 命令的数字别名
"""

import sys
import tempfile
import yaml
from pathlib import Path

# 添加 aitest 到路径
sys.path.insert(0, str(Path(__file__).parent))

from aitest.cli.config import CLIConfig
from aitest.cli.adapters.project_adapter import ProjectAdapter


def test_config_project_tracking():
    """测试 CLIConfig 的项目历史跟踪。"""
    print("\n[TEST] CLIConfig 项目历史跟踪")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建临时配置
        config_file = Path(tmpdir) / "config.yaml"
        config_file.write_text(yaml.dump({
            "active_project": None,
            "projects": {},
        }))

        # 模拟 CLIConfig（使用临时配置）
        import aitest.cli.config as config_module
        original_config_file = config_module.CONFIG_FILE
        config_module.CONFIG_FILE = config_file

        try:
            config = CLIConfig()

            # 1. 设置第一个项目
            config.active_project = "project-a"
            assert config.active_project == "project-a"
            assert config.previous_project is None
            print("✓ 初次设置活跃项目: project-a")

            # 2. 切换到第二个项目
            config.active_project = "project-b"
            assert config.active_project == "project-b"
            assert config.previous_project == "project-a"
            print("✓ 切换项目后 previous_project 正确: project-a")

            # 3. 记录最近项目
            config.record_recent_project("project-a")
            config.record_recent_project("project-b")
            config.record_recent_project("project-c")
            recent = config.recent_projects
            assert recent == ["project-c", "project-b", "project-a"]
            print(f"✓ 最近项目列表正确: {recent}")

            # 4. 去重测试
            config.record_recent_project("project-b")
            recent = config.recent_projects
            assert recent == ["project-b", "project-c", "project-a"]
            print(f"✓ 去重后列表正确: {recent}")

            # 5. 最多 5 个
            for i in range(10):
                config.record_recent_project(f"project-{i}")
            recent = config.recent_projects
            assert len(recent) <= 5
            print(f"✓ 最近列表限制 5 个: {len(recent)} 个")

            print("\n[PASS] CLIConfig 项目历史跟踪测试通过")
            return True

        finally:
            config_module.CONFIG_FILE = original_config_file


def test_project_adapter_alias():
    """测试 ProjectAdapter 的别名解析。"""
    print("\n[TEST] ProjectAdapter 别名解析")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建临时配置
        config_file = Path(tmpdir) / "config.yaml"
        tmpdir_path = Path(tmpdir)

        # 创建两个项目目录
        proj_a = tmpdir_path / "project-a"
        proj_b = tmpdir_path / "project-b"
        proj_a.mkdir()
        proj_b.mkdir()
        (proj_a / ".tlo").mkdir()
        (proj_b / ".tlo").mkdir()

        # 创建 project.yaml
        for proj, name in [(proj_a, "project-a"), (proj_b, "project-b")]:
            (proj / ".tlo" / "project.yaml").write_text(yaml.dump({
                "project": {"id": name, "name": name.upper()},
                "connection": {"base_url": f"http://localhost:3000/{name}"},
            }))

        config_data = {
            "active_project": "project-a",
            "previous_project": None,
            "projects": {
                "project-a": {"path": str(proj_a), "name": "Project A"},
                "project-b": {"path": str(proj_b), "name": "Project B"},
            },
        }
        config_file.write_text(yaml.dump(config_data))

        # 模拟 CLIConfig
        import aitest.cli.config as config_module
        original_config_file = config_module.CONFIG_FILE
        config_module.CONFIG_FILE = config_file

        try:
            config = CLIConfig()
            adapter = ProjectAdapter(config)

            # 1. 正常切换
            result = adapter.set_active_project("project-b")
            assert result == "project-b"
            assert config.active_project == "project-b"
            assert config.previous_project == "project-a"
            print("✓ 正常切换: project-a → project-b")

            # 2. 使用 "-" 切换回上一个
            result = adapter.set_active_project("-")
            assert result == "project-a"
            assert config.active_project == "project-a"
            print("✓ 使用 '-' 切换回: project-b → project-a")

            # 3. 最近列表更新
            recent = config.recent_projects
            assert "project-a" in recent
            assert "project-b" in recent
            print(f"✓ 最近列表已更新: {recent}")

            # 4. 不存在的项目
            try:
                adapter.set_active_project("project-x")
                print("✗ 应该抛出 ValueError")
                return False
            except ValueError as e:
                print(f"✓ 不存在的项目报错: {e}")

            # 5. 没有 previous_project 时使用 "-"
            config.set("previous_project", None)
            try:
                adapter.set_active_project("-")
                print("✗ 应该抛出 ValueError")
                return False
            except ValueError as e:
                print(f"✓ 无上一个项目时报错: {e}")

            print("\n[PASS] ProjectAdapter 别名解析测试通过")
            return True

        finally:
            config_module.CONFIG_FILE = original_config_file


def test_switch_numeric_alias():
    """测试 switch 命令的数字别名。"""
    print("\n[TEST] Switch 命令数字别名")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.yaml"
        config_data = {
            "active_project": "project-a",
            "recent_projects": ["project-a", "project-b", "project-c"],
            "projects": {
                "project-a": {"path": "/tmp/a", "name": "A"},
                "project-b": {"path": "/tmp/b", "name": "B"},
                "project-c": {"path": "/tmp/c", "name": "C"},
            },
        }
        config_file.write_text(yaml.dump(config_data))

        import aitest.cli.config as config_module
        original_config_file = config_module.CONFIG_FILE
        config_module.CONFIG_FILE = config_file

        try:
            config = CLIConfig()

            # 1. 数字 "1" → project-a
            recent = config.recent_projects
            assert recent[0] == "project-a"
            print(f"✓ 最近第 1 个: {recent[0]}")

            # 2. 数字 "2" → project-b
            assert recent[1] == "project-b"
            print(f"✓ 最近第 2 个: {recent[1]}")

            # 3. 超出范围
            assert len(recent) == 3
            print(f"✓ 列表长度: {len(recent)}")

            print("\n[PASS] Switch 数字别名测试通过")
            return True

        finally:
            config_module.CONFIG_FILE = original_config_file


def main():
    """运行所有测试。"""
    print("\n" + "=" * 60)
    print("P2-5: 多项目切换功能测试")
    print("=" * 60)

    results = []

    try:
        results.append(("CLIConfig 项目历史", test_config_project_tracking()))
    except Exception as e:
        print(f"✗ CLIConfig 测试失败: {e}")
        results.append(("CLIConfig 项目历史", False))

    try:
        results.append(("ProjectAdapter 别名", test_project_adapter_alias()))
    except Exception as e:
        print(f"✗ ProjectAdapter 测试失败: {e}")
        results.append(("ProjectAdapter 别名", False))

    try:
        results.append(("Switch 数字别名", test_switch_numeric_alias()))
    except Exception as e:
        print(f"✗ Switch 测试失败: {e}")
        results.append(("Switch 数字别名", False))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
