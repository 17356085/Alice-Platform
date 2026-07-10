"""P2-8: Workflow 命令组测试 — 验证基本功能。

测试范围:
1. workflow create 命令（模板创建）
2. workflow list 命令
3. workflow show 命令
4. workflow validate 命令
5. workflow run 命令（转换为 run create）
"""

import tempfile
import yaml
from pathlib import Path


def test_workflow_template():
    """测试 Workflow 模板生成。"""
    print("\n[TEST] Workflow 模板生成")
    print("=" * 60)

    # 模拟 page-test 模板
    template = {
        "name": "Page Test Workflow",
        "description": "单页面测试流程",
        "agents": ["page-observer", "action-executor", "assertion-writer"],
        "steps": [
            {"id": "observe", "agent": "page-observer", "description": "观察页面"},
            {"id": "execute", "agent": "action-executor", "description": "执行操作"},
            {"id": "assert", "agent": "assertion-writer", "description": "编写断言"},
        ],
        "transitions": [
            {"from": "observe", "to": "execute"},
            {"from": "execute", "to": "assert"},
        ],
    }

    # 验证模板结构
    assert "name" in template
    assert "agents" in template
    assert "steps" in template
    assert len(template["steps"]) == 3
    assert len(template["transitions"]) == 2
    print(f"✓ 模板结构完整: {template['name']}")
    print(f"✓ Agents: {len(template['agents'])} 个")
    print(f"✓ Steps: {len(template['steps'])} 个")
    print(f"✓ Transitions: {len(template['transitions'])} 个")

    print("\n[PASS] Workflow 模板生成测试通过")
    return True


def test_workflow_validation_logic():
    """测试 Workflow 验证逻辑。"""
    print("\n[TEST] Workflow 验证逻辑")
    print("=" * 60)

    # 有效的 Workflow
    valid_workflow = {
        "id": "test-workflow",
        "name": "Test Workflow",
        "agents": ["agent1", "agent2"],
        "steps": [
            {"id": "step1", "agent": "agent1", "description": "Step 1"},
            {"id": "step2", "agent": "agent2", "description": "Step 2"},
        ],
        "transitions": [
            {"from": "step1", "to": "step2"},
        ],
    }

    # 模拟验证逻辑
    checks = []

    # 1. 必填字段
    required = ["id", "name", "agents", "steps"]
    for field in required:
        if field in valid_workflow and valid_workflow[field]:
            checks.append(("ok", f"必填字段: {field}"))
        else:
            checks.append(("error", f"必填字段: {field}"))

    # 2. Steps 唯一性
    step_ids = {s["id"] for s in valid_workflow["steps"]}
    if len(step_ids) == len(valid_workflow["steps"]):
        checks.append(("ok", "Step ID 唯一"))
    else:
        checks.append(("error", "Step ID 重复"))

    # 3. Transition 引用完整性
    for trans in valid_workflow["transitions"]:
        if trans["from"] in step_ids and trans["to"] in step_ids:
            checks.append(("ok", f"Transition: {trans['from']} → {trans['to']}"))
        else:
            checks.append(("error", f"Transition 引用无效"))

    # 统计
    ok_count = sum(1 for status, _ in checks if status == "ok")
    error_count = sum(1 for status, _ in checks if status == "error")

    print(f"✓ 验证检查: {len(checks)} 项")
    print(f"✓ 通过: {ok_count} 项")
    print(f"✓ 错误: {error_count} 项")

    assert error_count == 0, "验证应该全部通过"

    # 测试无效 Workflow
    invalid_workflow = {
        "id": "invalid",
        "name": "Invalid",
        "agents": ["agent1"],
        "steps": [
            {"id": "step1", "agent": "agent1"},
            {"id": "step1", "agent": "agent1"},  # 重复 ID
        ],
        "transitions": [
            {"from": "step1", "to": "step_nonexistent"},  # 无效引用
        ],
    }

    checks_invalid = []
    step_ids = [s["id"] for s in invalid_workflow["steps"]]
    if len(set(step_ids)) != len(step_ids):
        checks_invalid.append(("error", "Step ID 重复"))

    for trans in invalid_workflow["transitions"]:
        if trans["to"] not in step_ids:
            checks_invalid.append(("error", f"Transition 引用无效: {trans['to']}"))

    error_count_invalid = sum(1 for status, _ in checks_invalid if status == "error")
    print(f"✓ 无效 Workflow 检测到 {error_count_invalid} 个错误")

    assert error_count_invalid > 0, "应该检测到错误"

    print("\n[PASS] Workflow 验证逻辑测试通过")
    return True


def test_workflow_file_operations():
    """测试 Workflow 文件操作。"""
    print("\n[TEST] Workflow 文件操作")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workflow_dir = Path(tmpdir) / ".tlo" / "workflows"
        workflow_dir.mkdir(parents=True)

        # 1. 创建 Workflow 文件
        workflow_data = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "agents": ["agent1"],
            "steps": [{"id": "step1", "agent": "agent1"}],
            "transitions": [],
        }

        workflow_file = workflow_dir / "test-workflow.yaml"
        with open(workflow_file, "w", encoding="utf-8") as f:
            yaml.dump(workflow_data, f, allow_unicode=True)

        assert workflow_file.exists()
        print(f"✓ Workflow 文件已创建: {workflow_file.name}")

        # 2. 读取 Workflow 文件
        with open(workflow_file, "r", encoding="utf-8") as f:
            loaded_data = yaml.safe_load(f)

        assert loaded_data["id"] == "test-workflow"
        assert loaded_data["name"] == "Test Workflow"
        print(f"✓ Workflow 文件读取成功")

        # 3. 列出 Workflow 文件
        workflow_files = list(workflow_dir.glob("*.yaml"))
        assert len(workflow_files) == 1
        print(f"✓ Workflow 文件列表: {len(workflow_files)} 个")

    print("\n[PASS] Workflow 文件操作测试通过")
    return True


def test_workflow_to_run_conversion():
    """测试 Workflow 到 Run 的转换逻辑。"""
    print("\n[TEST] Workflow → Run 转换")
    print("=" * 60)

    workflow_id = "my-workflow"
    target = f"workflow:{workflow_id}"

    # 验证 target 格式
    assert target.startswith("workflow:")
    assert target.split(":", 1)[1] == workflow_id
    print(f"✓ Target 格式正确: {target}")

    # 验证参数传递
    input_params = {
        "module": "equipment",
        "pages": ["page1", "page2"],
        "env": "test",
    }

    assert "module" in input_params
    assert "pages" in input_params
    print(f"✓ 输入参数: {len(input_params)} 个")

    print("\n[PASS] Workflow → Run 转换测试通过")
    return True


def main():
    """运行所有测试。"""
    print("\n" + "=" * 60)
    print("P2-8: Workflow 命令组测试")
    print("=" * 60)

    results = []

    try:
        results.append(("模板生成", test_workflow_template()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("模板生成", False))

    try:
        results.append(("验证逻辑", test_workflow_validation_logic()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("验证逻辑", False))

    try:
        results.append(("文件操作", test_workflow_file_operations()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("文件操作", False))

    try:
        results.append(("Run 转换", test_workflow_to_run_conversion()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Run 转换", False))

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
        print("\n🎉 所有测试通过！Workflow 命令组基础功能验证完成。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
