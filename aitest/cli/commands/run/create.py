"""
aitest run create — 创建新的 Run。

支持执行类型:
- agent:<agent_id>: 执行单个 Agent
- workflow:<workflow_id>: 执行工作流
- skill:<skill_id>: 执行单个 Skill
- evaluation:<eval_id>: 运行评估
"""

import typer
from typing import Optional
import httpx
from aitest.cli.utils.output import format_output, print_success, print_error
from aitest.cli.utils.config import get_resolver


def run_create(
    target: str = typer.Option(
        ...,
        "--target", "-t",
        help="执行目标，格式: <type>:<id>，例如: agent:page-observer, workflow:test-sop"
    ),
    module: Optional[str] = typer.Option(
        None,
        "--module", "-m",
        help="模块名（Agent 类型必需）"
    ),
    pages: Optional[str] = typer.Option(
        None,
        "--pages", "-p",
        help="页面列表，逗号分隔（Agent 类型可选）"
    ),
    env: Optional[str] = typer.Option(
        None,
        "--env", "-e",
        help="环境 ID（使用已注册的 Environment 资源）"
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        help="Provider ID（使用已注册的 ModelProvider 资源）"
    ),
    mock_llm: bool = typer.Option(
        False,
        "--mock-llm",
        help="使用 Mock LLM（测试用）"
    ),
    wait: bool = typer.Option(
        True,
        "--wait/--no-wait",
        help="等待执行完成"
    ),
    output: str = typer.Option(
        "table",
        "--output", "-o",
        help="输出格式 (table/json/yaml)"
    ),
):
    """
    创建新的 Run。

    示例:

      # 执行 Agent
      aitest run create --target agent:page-observer --module equipment

      # 执行 Agent（指定页面）
      aitest run create --target agent:page-observer --module equipment --pages alarm-config,camera

      # 执行 Workflow
      aitest run create --target workflow:test-automation-sop --module equipment

      # 执行 Skill
      aitest run create --target skill:page-observe --module equipment --pages alarm-config

      # 执行 Evaluation
      aitest run create --target evaluation:eval_001

    目标类型:

      - agent:<agent_id>: 执行单个 Agent（需要 --module）
      - workflow:<workflow_id>: 执行工作流（可选 --module）
      - skill:<skill_id>: 执行单个 Skill（需要 --module 和 --pages）
      - evaluation:<eval_id>: 运行评估
    """
    # 解析 target
    if ":" not in target:
        print_error(f"目标格式错误: {target}，应为 <type>:<id>")
        raise typer.Exit(1)

    target_type, target_id = target.split(":", 1)

    # 验证必需参数
    if target_type == "agent" and not module:
        print_error("Agent 类型需要 --module 参数")
        raise typer.Exit(1)
    if target_type == "skill" and (not module or not pages):
        print_error("Skill 类型需要 --module 和 --pages 参数")
        raise typer.Exit(1)

    # 解析配置
    resolver = get_resolver()
    api_base = resolver.resolve(
        cli_value=None,
        env_var="AITEST_API_BASE",
        config_key="api.base_url",
        default="http://localhost:8000"
    )

    # 构造请求
    payload = {
        "target": {
            "type": target_type,
            "id": target_id,
            "version": None,  # 使用最新版本
        },
        "config": {
            "module": module,
            "pages": pages.split(",") if pages else None,
            "environment_id": env,
            "provider_id": provider,
            "mock_llm": mock_llm,
        },
        "wait": wait,
    }

    # 发送请求
    try:
        response = httpx.post(
            f"{api_base}/api/v1/runs",
            json=payload,
            timeout=300.0 if wait else 10.0,
        )
        response.raise_for_status()
        result = response.json()

        # 输出结果
        if output in ("json", "yaml"):
            format_output(result, output_format=output)
        else:
            print_success(f"Run 创建成功: {result['run_id']}")
            format_output(
                {
                    "run_id": result["run_id"],
                    "target": f"{target_type}:{target_id}",
                    "status": result["status"],
                    "created_at": result.get("created_at", "N/A"),
                },
                output_format="table",
                title="Run 详情"
            )

    except httpx.HTTPStatusError as e:
        print_error(f"API 请求失败: {e.response.status_code}")
        print_error(e.response.text)
        raise typer.Exit(1)
    except httpx.RequestError as e:
        print_error(f"网络错误: {e}")
        print_error(f"请确认测试工作台已启动: aitest server start")
        raise typer.Exit(1)
