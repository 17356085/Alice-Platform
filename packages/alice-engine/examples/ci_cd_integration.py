"""CI/CD 集成 — 在 GitHub Actions / GitLab CI 中使用。"""

import sys
from alice_engine import Engine


def run_ci_tests(project_path: str, module: str, pages: list[str] = None):
    """CI/CD 测试入口。

    返回码:
        0 - 全部通过
        1 - 有失败
        2 - 配置错误
    """
    engine = Engine(project_path=project_path, llm_provider="mock")

    # 验证
    validation = engine.validate()
    if not validation.valid:
        print(f"配置错误: {validation.errors}", file=sys.stderr)
        return 2

    # 执行
    result = engine.run(module, pages=pages)

    # 输出结果
    print(f"Module: {module}")
    print(f"Status: {result.status}")
    print(f"Elapsed: {result.elapsed_seconds}s")
    print(f"Phases: {len(result.completed_phases)}/{len(result.completed_phases) + len(result.failed_phases)}")

    if result.failed_phases:
        print(f"Failed: {result.failed_phases}", file=sys.stderr)

    return 0 if result.success else 1


if __name__ == "__main__":
    # 从命令行参数或环境变量读取配置
    project_path = sys.argv[1] if len(sys.argv) > 1 else "."
    module = sys.argv[2] if len(sys.argv) > 2 else "equipment"

    exit_code = run_ci_tests(project_path, module)
    sys.exit(exit_code)
