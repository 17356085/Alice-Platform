"""
aitest run show — 显示 Run 详情。
"""

import typer
import httpx
from aitest.cli.utils.output import format_output, print_error
from aitest.cli.utils.config import get_resolver


def run_show(
    run_id: str = typer.Argument(..., help="Run ID"),
    output: str = typer.Option(
        "table",
        "--output", "-o",
        help="输出格式 (table/json/yaml)"
    ),
):
    """
    显示 Run 详情。

    示例:

      aitest run show run_abc123
      aitest run show run_abc123 --output json
    """
    # 解析配置
    resolver = get_resolver()
    api_base = resolver.resolve(
        cli_value=None,
        env_var="AITEST_API_BASE",
        config_key="api.base_url",
        default="http://localhost:8000"
    )

    # 发送请求
    try:
        response = httpx.get(
            f"{api_base}/api/v1/runs/{run_id}",
            timeout=10.0,
        )
        response.raise_for_status()
        result = response.json()

        # 输出结果
        if output in ("json", "yaml"):
            format_output(result, output_format=output)
        else:
            # 格式化关键信息
            run = result.get("run", result)
            table_data = {
                "run_id": run["run_id"],
                "target": f"{run['target']['type']}:{run['target']['id']}",
                "status": run["status"],
                "module": run.get("module", "N/A"),
                "pages": ", ".join(run.get("pages", [])) if run.get("pages") else "N/A",
                "agent": run.get("agent", "N/A"),
                "created_at": run.get("created_at", "N/A"),
                "completed_at": run.get("completed_at", "N/A"),
                "duration": f"{run.get('duration_seconds', 0):.2f}s" if run.get("duration_seconds") else "N/A",
            }

            format_output(
                table_data,
                output_format="table",
                title=f"Run 详情: {run_id[:12]}..."
            )

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            print_error(f"Run 不存在: {run_id}")
        else:
            print_error(f"API 请求失败: {e.response.status_code}")
            print_error(e.response.text)
        raise typer.Exit(1)
    except httpx.RequestError as e:
        print_error(f"网络错误: {e}")
        print_error(f"请确认测试工作台已启动: aitest server start")
        raise typer.Exit(1)
